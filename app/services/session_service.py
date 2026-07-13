"""Session orchestration — the engine's runtime.

Owns canonical state (in-memory SessionStore), drives the graph each turn,
streams the chosen generation over the AI boundary, tracks mastery/clean-pass
progression, advances nodes on completion, and flags a module for remediation
when the clean pass-rate drops below 50%.

Product state is persisted through Supabase/Postgres only. AI generation can
fall back locally, but learner profiles, credits, sessions, progress, and
history must not silently disappear into local files.
"""
import asyncio
import copy
import hashlib
import json
import os
import re
import time
import uuid
import logging
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass

logger = logging.getLogger("zidd.session")


class ProgressionUnavailableError(RuntimeError):
    """Raised when a valid module exists but user progress cannot be read."""


class AwaitingNextSkillError(RuntimeError):
    """Raised when a learner answers before the next-node opening is visible."""


class SessionNotActiveError(RuntimeError):
    """Raised when a closed or handed-off session receives a learner turn."""


class SessionScoringUnavailableError(RuntimeError):
    """Raised when a test-mode session cannot be scored yet."""


def _bump_session_version(state: dict) -> None:
    state["session_version"] = int(state.get("session_version") or 1) + 1


def _mark_terminal(state: dict, reason: str) -> None:
    """Make a coaching session immutable after learner/module completion."""
    if (
        state.get("status") != "ended"
        or state.get("block_reason") != reason
        or state.get("input_allowed") is not False
    ):
        _bump_session_version(state)
    state["session_over"] = True
    state["status"] = "ended"
    state["input_allowed"] = False
    state["block_reason"] = reason


def _mark_active_turn_processing(state: dict, client_turn_id: str | None) -> None:
    if not client_turn_id:
        return
    state["active_turn_id"] = client_turn_id
    state["active_turn_status"] = "processing"
    state["input_allowed"] = False
    state["block_reason"] = "turn_processing"


def _finish_active_turn(state: dict, client_turn_id: str | None, status: str) -> None:
    if client_turn_id and state.get("active_turn_id") == client_turn_id:
        state["last_turn_id"] = client_turn_id
        state["last_turn_status"] = status
        state["active_turn_id"] = None
    state["active_turn_status"] = status
    if state.get("block_reason") == "turn_processing":
        if (
            state.get("status", "active") == "active"
            and not state.get("pending_node_transition")
            and not state.get("module_done")
            and not state.get("session_over")
        ):
            state["input_allowed"] = True
            state["block_reason"] = None


def turn_block_reason(state: dict) -> str | None:
    """Return the stable API error code when a learner turn is not allowed."""
    if state.get("status", "active") != "active":
        reason = str(state.get("block_reason") or "")
        if reason in {"module_done", "learner_ended", "session_over", "session_expired"}:
            return reason
        return "session_not_active"
    if state.get("pending_node_transition"):
        return "awaiting_next_skill"
    if state.get("module_done"):
        return "module_done"
    if state.get("session_over"):
        return str(state.get("block_reason") or "session_over")
    if state.get("input_allowed") is False or state.get("block_reason"):
        return str(state.get("block_reason") or "input_blocked")
    if not state.get("opening_streamed", True) and not state.get("messages"):
        return "opening_required"
    return None


def opening_block_reason(state: dict) -> str | None:
    """Return a stable API error code when /opening must not mutate a session.

    Transcripts for ended sessions remain readable, but opening streams append a
    new assistant message and can clear transition state. They must therefore be
    blocked once a source session has been handed off, ended, or is waiting for
    the next skill to start in a new session.
    """
    if state.get("status", "active") != "active":
        reason = str(state.get("block_reason") or "")
        if reason in {"module_done", "learner_ended", "session_over", "session_expired"}:
            return reason
        return "session_not_active"
    if state.get("session_over"):
        return str(state.get("block_reason") or "session_over")
    if state.get("pending_node_transition"):
        return "awaiting_next_skill"
    return None


@dataclass(frozen=True)
class GamePrompt:
    """Gamified fill-blank item yielded instead of a text stream on scaffold turns.

    The API layer maps this to an `event: game_prompt` SSE frame. `answer_key`
    is stripped from the client payload; the learner submits their fill as normal
    text on the next turn, which the graph scores via evaluate_node as usual."""

    type: str
    sentence: str
    hint: str
    context: str
    answer_key: str     # server-side only — not forwarded to the client
    options: list[str] | None = None
    turn_id: str | None = None


@dataclass(frozen=True)
class NodeAdvance:
    """Marker yielded by run_turn between old-node feedback and new-node opening.

    run_turn yields plain string tokens for the pedagogy/opening stream; on an
    advancing turn it yields exactly one NodeAdvance between the OLD-node feedback
    tokens and the NEW-node opening tokens. The API layer maps it to a discrete
    `event: node_advance` SSE frame on the same connection so the UI renders the
    two as separate bubbles (kills level-bleed)."""

    from_node: str
    to_node: str


@dataclass(frozen=True)
class ProgressUpdate:
    """Per-turn mastery signal for the UI progress bar.

    Emitted after every scored turn so the client can update mastery display
    without waiting for the `done` event. The `done` snapshot also carries this
    data — ProgressUpdate lets the UI animate the bar mid-stream."""

    node_id: str
    mastery: float          # current EMA (0-1)
    readiness_score: float  # latest enforced rubric readiness (0-1)
    clean_streak: int       # consecutive clean passes on this node
    attempts: int           # total attempts on this node


@dataclass(frozen=True)
class SessionRecap:
    """Summary frame emitted when module_done=True (all nodes completed).

    Carries the structured recap so the UI can render a 'session complete'
    screen without a second API call. The `done` event fires immediately after."""

    nodes_completed: list   # list of node_id strings from node_history
    weaknesses: list        # weakness_context rows (skill_id, hit_count, last_raw)
    score_metric: str       # readiness for career prep; mastery for legacy learning
    readiness_score: float  # latest enforced rubric readiness at close
    mastery_score: float    # current EMA mastery at close
    avg_score: float        # deprecated compatibility alias for mastery_score


@dataclass(frozen=True)
class AdaptationCue:
    """Selector rationale surfaced to the UI when the path adapts.

    Emitted on advancing turns (ADVANCE / REMEDIATE) right after ProgressUpdate
    and before NodeAdvance, carrying the selector's decision so the UI can show a
    short 'adapting your path' cue. Read verbatim from state['last_selection'];
    suppressed on REPEAT and on module-done turns (last_selection is None there)."""

    action: str
    band: str
    rationale: str

from app.config import get_settings
from app.ai.calls import (
    GEMINI_FLASH,
    GenSpec,
    evaluate_placement,
    select_next_content,
    stream_generation,
    summarize_session,
)
from app.ai.schemas import SelectionDecision
from app.services.selector import (
    build_selection_snapshot,
    compute_valid_candidates,
    fallback_decision,
    validate_decision,
)
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_opening_prompt, coach_view, sanitize_memory_text
from app.ai.test_gen import generate_test_items
from app.graph.answer_check import is_blank_nonanswer
from app.content.registry import (
    SELF_REPORT_CEFR,
    all_node_ids,
    get_module,
    get_node,
    grade_placement_node,
    is_voice_node,
    module_of,
    next_node,
    placement_node,
    uses_grade_placement,
)
from app.content.motions import motion_for_node
from app.content.skills import coerce_skill_id
from app.content.task_types import (
    TaskType,
    prep_counterpart,
    task_type_of,
    test_counterpart,
)
from app.graph.build import get_graph
from app.services.rubric_engine import (
    compute_attempt_credit,
    gd_topic_family,
    infer_gd_topic_from_messages,
    resolve_core_gd_topic,
    resolve_prompt_gd_topic,
)
from app.services.career_context import build_career_context
from app.services.career_task_contract import CareerTaskContract
from app.services.learning_profile import CareerLearningProfileService
from app.services.tutor_plan import (
    int01_decision_for_planned_action,
    qualified_core_evidence,
    validated_attempt_type_for_tutor_plan,
    validated_tutor_next_action,
)
from app.services.assessment_plan import ensure_assessment_plan
from app.services.simulation_config import resolve_simulation_config
from app.services.simulation_service import score_session, stream_simulation_round
from app.storage import get_storage

# Assessment ("test") task types run the multi-persona SIMULATION instead of the
# coaching graph; the contribution is scored at session end, not coached mid-turn.
_TEST_TASK_TYPES = frozenset({TaskType.INTERVIEW_TEST.value, TaskType.GD_TEST.value})
_CAREER_PREP_TASK_TYPES = frozenset({TaskType.INTERVIEW_PREP.value, TaskType.GD_PREP.value})
_CAREER_HISTORY_PER_MODE_LIMIT = 3
_TEST_HISTORY_TOTAL_LIMIT = 2 * _CAREER_HISTORY_PER_MODE_LIMIT
_EVALUATION_RETRY_TEXT = (
    "I couldn't review that answer reliably, so I haven't counted it. "
    "Please send the same answer once more."
)

_TRANSFER_ANCHOR_STOPWORDS = {
    "about", "after", "answer", "ask", "before", "close", "context", "different",
    "final", "first", "give", "interview", "keep", "meaningfully", "name", "new",
    "next", "preserve", "response", "show", "specific", "state", "story", "task",
    "transfer", "use", "using", "value", "with", "would", "your",
}


def _task_role_from_text(text: str) -> str:
    match = re.search(
        r"\b(?:close\s+a|for\s+(?:a|the)|hiring\s+for\s+the)\s+"
        r"([A-Z][A-Za-z&/-]*(?:\s+[A-Z][A-Za-z&/-]*){0,4}\s+"
        r"(?:Engineer|Manager|Analyst|Consultant|Designer|Specialist|Lead))"
        r"(?:\s+interview|\s+role|\b)",
        str(text or ""),
        re.IGNORECASE,
    )
    return " ".join(match.group(1).split()) if match else ""


def _visible_transfer_anchors(text: str) -> list[str]:
    """Extract anchor groups from the visible assignment, never from node identity."""
    clean = " ".join(str(text or "").split())
    transfer_match = re.search(r"\bTransfer\s+(?:task|check)\s*:\s*(.+)", clean, re.IGNORECASE)
    body = transfer_match.group(1) if transfer_match else clean
    anchors: list[str] = []
    role = _task_role_from_text(body)
    if role:
        anchors.append(role.casefold())
    learner_owned_new_context = bool(re.search(
        r"\bdifferent\b[^.]{0,80}\b(?:your\s+own\s+experience|achievement|story)\b",
        body,
        re.IGNORECASE,
    ))
    if learner_owned_new_context:
        anchors.append("learner owned new context")
        return anchors[:2]
    for quoted in re.findall(r"['\"]([^'\"]{8,180})['\"]", body):
        tokens = [
            token for token in re.findall(r"[a-z][a-z0-9-]{3,}", quoted.casefold())
            if token not in _TRANSFER_ANCHOR_STOPWORDS
        ]
        if tokens:
            anchors.append(" ".join(dict.fromkeys(tokens))[:160])
    for sentence in re.split(r"(?<=[.!?])\s+", body)[:2]:
        tokens = [
            token for token in re.findall(r"[a-z][a-z0-9-]{3,}", sentence.casefold())
            if token not in _TRANSFER_ANCHOR_STOPWORDS
        ]
        group = " ".join(dict.fromkeys(tokens))[:160]
        if group and group not in anchors:
            anchors.append(group)
    return anchors[:2]


def _gd_task_participant_claims(node_id: str, text: str) -> list[dict[str, str]]:
    if node_id == "gd_08_include_quiet":
        quiet_marker = re.search(
            r"\b(?:has\s+not|hasn't|did\s+not)\s+(?:spoken|entered|contributed)|"
            r"\bsays\s+(?:she|he|they)\s+has\s+nothing",
            text,
            re.IGNORECASE,
        )
        name = ""
        if quiet_marker:
            prefix = text[max(0, quiet_marker.start() - 120):quiet_marker.start()]
            candidates = re.findall(r"\b[A-Z][\w'’-]{1,24}\b", prefix)
            excluded = {"The", "Analyst", "Challenger", "Pressure", "Check", "Transfer", "Motion"}
            name = next((candidate for candidate in reversed(candidates) if candidate not in excluded), "")
        if not name:
            match = re.search(
                r"\b(?:address|invite)\s+([A-Z][\w'’-]{1,24})\b|"
                r"^\s*([A-Z][\w'’-]{1,24})\s*,",
                text,
                re.IGNORECASE,
            )
            if match:
                name = next(group for group in match.groups() if group)
        if not name:
            return []
        return [{
            "participant_id": name.casefold(),
            "display_name": name,
            "status": "quiet",
        }]
    if node_id != "gd_10_drive_consensus":
        return []
    if not re.search(r"\bMaya\b", text, re.IGNORECASE) or not re.search(r"\bDev\b", text, re.IGNORECASE):
        return []
    maya_claim = "the evidence supports the motion"
    dev_claim = "the evidence is too mixed to accept without qualification"
    if re.search(r"\bspeed\b", text, re.IGNORECASE):
        maya_claim = "speed supports moving forward"
    if re.search(r"\bsafety\b", text, re.IGNORECASE):
        dev_claim = "safety requires qualification before moving forward"
    return [
        {
            "participant_id": "maya",
            "display_name": "Maya",
            "claim": maya_claim,
            "stance": "support",
        },
        {
            "participant_id": "dev",
            "display_name": "Dev",
            "claim": dev_claim,
            "stance": "qualified_opposition",
        },
    ]


def _derived_career_task_payload(state: dict, message: dict) -> dict:
    content = " ".join(str(message.get("content") or "").split())
    node_id = str(message.get("node_id") or state.get("competency_node") or "").strip()
    attempt_type = str(
        "scaffolded"
        if str(message.get("message_kind") or "") == "game_prompt"
        else
        state.get("pending_prompt_attempt_type")
        or state.get("active_prompt_attempt_type")
        or "independent"
    ).strip()
    topic = ""
    if str(state.get("task_type") or "") == TaskType.GD_PREP.value:
        topic = str(state.get("pending_gd_prompt_topic") or resolve_prompt_gd_topic(state) or "").strip()
    anchors = (
        _visible_transfer_anchors(content)
        if attempt_type == "transfer" and node_id.startswith("int_")
        else []
    )
    role = _task_role_from_text(content)
    context_fingerprint = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"{node_id}|{attempt_type}|{content}",
    ).hex[:16]
    return {
        "context_id": f"{node_id}:{attempt_type}:{context_fingerprint}",
        "active_role": role,
        "active_topic": topic,
        "semantic_anchors": list(anchors),
        "participant_claims": _gd_task_participant_claims(node_id, content),
        "evidence_policy": "learner_owned_or_sourced",
        "hypothetical": bool(
            state.get("task_type") == TaskType.GD_PREP.value
            or re.search(r"\b(?:hypothetical|transfer\s+task|pressure\s+check|premise)\b", content, re.IGNORECASE)
        ),
    }


def _coach_response_assigns_task(state: dict) -> bool:
    if not state.get("active_task_contract") or state.get("last_graded_bridge"):
        return True
    result = state.get("last_rubric_result")
    if isinstance(result, dict) and (
        bool(result.get("pass_eligible"))
        and not result.get("required_missing")
        and not result.get("blockers")
    ):
        return True
    pending_topic = str(state.get("pending_gd_prompt_topic") or "").strip()
    active_topic = str((state.get("active_task_contract") or {}).get("active_topic") or "").strip()
    return bool(pending_topic and pending_topic != active_topic)


def _commit_career_task_contract(state: dict, message: dict) -> None:
    """Bind evaluation to the Career prompt that has actually become visible."""
    if str(state.get("task_type") or "") not in _CAREER_PREP_TASK_TYPES:
        return
    if str(message.get("message_kind") or "") == "coach_fallback":
        return
    explicit_payload = message.get("task_contract")
    explicit = explicit_payload if isinstance(explicit_payload, dict) else None
    message_kind = str(message.get("message_kind") or "")
    assigns_new_task = bool(
        explicit is not None
        or message_kind == "opening"
        or message_kind == "game_prompt"
    )
    if not assigns_new_task and state.get("active_task_contract"):
        return
    derived = _derived_career_task_payload(state, message)
    explicit = {**derived, **(explicit or {})}
    prompt_id = str(
        explicit.get("prompt_id")
        or message.get("message_id")
        or message.get("turn_id")
        or ""
    ).strip()
    if not prompt_id:
        return
    node_id = str(message.get("node_id") or state.get("competency_node") or "").strip()
    attempt_type = str(
        state.get("pending_prompt_attempt_type")
        or state.get("active_prompt_attempt_type")
        or "independent"
    ).strip()
    context_id = str(
        explicit.get("context_id")
        or f"{node_id}:{attempt_type}:{prompt_id}"
    ).strip()
    career = state.get("career_context") or {}
    scenario = state.get("scenario_config") or {}
    active_role = str(
        explicit.get("active_role")
        or career.get("primary_role")
        or scenario.get("target_role")
        or ""
    ).strip()
    active_topic = str(explicit.get("active_topic") or "").strip()
    if not active_topic and str(state.get("task_type") or "") == TaskType.GD_PREP.value:
        active_topic = resolve_prompt_gd_topic(state)
    contract = CareerTaskContract(
        prompt_id=prompt_id,
        context_id=context_id,
        active_role=active_role,
        active_topic=active_topic,
        semantic_anchors=tuple(
            explicit.get("semantic_anchors")
            if isinstance(explicit.get("semantic_anchors"), (list, tuple))
            else ()
        ),
        participant_claims=tuple(
            explicit.get("participant_claims")
            if isinstance(explicit.get("participant_claims"), (list, tuple))
            else ()
        ),
        evidence_policy=(
            str(explicit.get("evidence_policy") or "learner_owned_or_sourced").strip()
            or "learner_owned_or_sourced"
        ),
        hypothetical=bool(explicit.get("hypothetical")),
    )
    state["active_task_contract"] = contract.model_dump()
_CELEBRATORY_OPENING_RE = re.compile(
    r"^\s*(?:great job|great effort|great start|great progress(?: so far)?|good job|nice(?: work| touch)?|well done|"
    r"brilliant(?: work)?|outstanding(?: work)?|you(?:'ve| have)?\s+crushed\s+(?:that|this)(?:\s+answer)?|"
    r"excellent(?: work)?|awesome(?: work)?|"
    r"(?:strong|solid)\s+(?:answer|response)|"
    r"this\s+is\s+(?:a\s+)?(?:strong|solid)\s+(?:answer|response)|"
    r"you(?:'ve| have)? nailed it|"
    r"you(?:'ve|’ve| have)? made good progress|"
    r"you(?:'ve|’ve| have)?(?:\s+effectively)? outlined|"
    r"you(?:'ve|’ve| have)? done well(?:\s+(?:by|in))?|"
    r"you(?:'ve|’ve| have)?\s+(?:(?:effectively|clearly|successfully|nicely)\s+)?"
    r"(?:highlighted|included|provided|articulated|showed|explained|demonstrated|demonstrates)|"
    r"your\s+(?:pitch|answer|response)\s+"
    r"(?:(?:effectively|clearly|successfully|nicely)\s+)?"
    r"(?:highlighted|included|provided|articulated|showed|explained|demonstrated|demonstrates))"
    r"(?:\s*[,:\-\u2013\u2014]\s*)?(?:[.!?]\s*)?",
    re.IGNORECASE,
)
_ACTIONABLE_COACHING_MARKER_RE = re.compile(
    r"\b(?:now|next|try|add|rewrite|revise|pressure-test|to\s+strengthen|strengthen|make|cut|answer|give|state|name|show|include|tighten)\b",
    re.IGNORECASE,
)
_COPYABLE_EXAMPLE_RE = re.compile(
    r"\s*(?:"
    r"for example[:,-]?\s*(?:\"[^\"\n]{1,700}\"|(?:you\s+(?:could|might)\s+|try\s+saying|say\s+)[^.!?\n]{1,700}[.!?])"
    r"|(?:this could be something like|you could say something like|you could start with(?: a clear position like)?)[:,-]?\s*"
    r"(?:\"[^\"\n]{1,700}\"|[^.!?\n]{1,700}[.!?])"
    r")",
    re.IGNORECASE,
)
_COPYABLE_SCENARIO_RE = re.compile(
    r"\s*Imagine [\s\S]{1,900}?Instead of saying [\s\S]{1,900}?"
    r"(?=(?:Now,\s*)?(?:apply|try|use)\b)",
    re.IGNORECASE,
)
_COPYABLE_IMAGINE_RE = re.compile(
    r"\s*Imagine\s+(?:you're|you are)\s+[^.!?\n]{1,700}[.!?]\s*",
    re.IGNORECASE,
)
_COPYABLE_MODEL_ANSWER_RE = re.compile(
    r"\s*(?:a\s+(?:better|stronger)\s+version\s+would\s+be|"
    r"try\s+saying|you\s+can\s+say|say\s+it\s+like\s+this)[:,-]?\s*"
    r"(?:\"[^\"\n]{1,700}\"|[^.!?\n]{1,700}[.!?])",
    re.IGNORECASE,
)
_INFLATED_PRAISE_FRAGMENT_RE = re.compile(
    r"\s*(?:[-\u2013\u2014]\s*)?"
    r"(?:you(?:'ve|’ve| have)?\s+(?:hit|covered|included)\s+(?:all\s+)?(?:the\s+)?"
    r"(?:right|key|important)\s+(?:points|areas|elements)|"
    r"you(?:'ve|’ve| have)?\s+made\s+good\s+progress[^.!?]{0,180}|"
    r"you(?:'ve|’ve| have)?\s+done\s+well(?:\s+(?:by|in))?[^.!?]{0,180}|"
    r"you(?:'ve|’ve| have)?\s+hit\s+all\s+the\s+right\s+points|"
    r"that\s+(?:covers|hits)\s+all\s+the\s+right\s+points)"
    r"[.!?]?\s*",
    re.IGNORECASE,
)
_UNRELATED_CAREER_SAMPLE_TERMS = (
    "customer churn",
    "sales",
    "marketing",
    "client deliverable",
    "client-deliverable",
    "retention dashboard",
)
_UNRELATED_CAREER_SAMPLE_SENTENCE_RE = re.compile(
    r"[^.!?\n]*(?:customer\s+churn|sales|marketing|client[-\s]deliverable|"
    r"retention\s+dashboard)[^.!?\n]*[.!?]?",
    re.IGNORECASE,
)
_CAREER_REPEAT_OUTCOME_GAP_RE = (
    re.compile(
        r"\bbut\s+there(?:'s|’s| is)\s+still\s+room\s+for\s+including\s+"
        r"a\s+specific\s+instance\s+where[^.!?]{1,220}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bTo\s+meet\s+our\s+goal,\s*focus\s+on\s+adding\s+concrete\s+"
        r"evidence\s+of[^.!?]{1,220}[.!?]?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bfocus\s+on\s+adding\s+(?:a\s+)?specific\s+outcome[^.!?]{0,180}[.!?]?\s*",
        re.IGNORECASE,
    ),
)
_CAREER_REPEAT_WEAKNESS_GAP_RE = (
    re.compile(
        r"\b(?:however|but),?\s+ensure\s+you\s+explicitly\s+state\s+the\s+"
        r"initial\s+weakness[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bYour\s+next\s+step\s+is\s+to\s+start\s+by\s+naming\s+your\s+"
        r"original\s+tendency[\s\S]{0,700}?(?:stakeholder\s+communication|these\s+elements)[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bHow\s+will\s+you\s+revise\s+your\s+answer\s+to\s+include\s+these\s+elements\?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:however|but),?\s+ensure\s+you\s+explicitly\s+contrast\s+your\s+"
        r"initial\s+tendency[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bFor\s+your\s+next\s+response,\s+reframe\s+the\s+opening\s+statement\s+"
        r"to\s+directly\s+name\s+your\s+original\s+behavior[\s\S]{0,420}?"
        r"(?:evolved|transition|contrast)[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bFocus\s+on\s+making\s+this\s+transition\s+clear\s+and\s+impactful[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bHow\s+would\s+you\s+revise\s+the\s+opening\s+to\s+highlight\s+this\s+contrast\?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bYour\s+next\s+step\s+is\s+to\s+revise\s+the\s+opening\s+to\s+name\s+"
        r"your\s+original\s+behavior\s+more\s+directly[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bFocus\s+on\s+making\s+that\s+transition\s+as\s+clear\s+and\s+"
        r"impactful\s+as\s+possible[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bRevisit\s+your\s+opening\s+statement\s+to\s+make\s+it\s+sharper\s+"
        r"and\s+more\s+direct[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:but\s+there(?:'s| is)\s+still\s+room\s+for\s+)?tightening\s+up\s+"
        r"each\s+segment[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bFocus\s+on\s+making\s+sure\s+that\s+when\s+you\s+transition\s+from\s+"
        r"stating\s+your\s+weakness[\s\S]{0,420}?"
        r"(?:overlaps?|redundanc(?:y|ies))[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bYour\s+next\s+task\s+is\s+to\s+deliver\s+this\s+three-part\s+answer"
        r"[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:Practise|Practice)\s+delivering\s+the\s+three-part\s+weakness\s+"
        r"answer[^.!?]{0,180}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:however,\s*)?let(?:'s| us)\s+revisit\s+the\s+original\s+task:?\s*"
        r"name\s+a\s+real\s+weakness[^.!?]{0,240}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bTry\s+that\s+out\s+now[.!?]\s*",
        re.IGNORECASE,
    ),
)
_CAREER_REPEAT_WEAKNESS_REQUEST_RE = re.compile(
    r"\b(?:initial\s+weakness|initial\s+tendency|original\s+behavior|"
    r"original\s+tendency|opening\s+statement|reframe\s+the\s+opening|"
    r"revise\s+the\s+opening|name\s+your\s+original|deliver\s+this\s+"
    r"three-part\s+answer|three-part\s+weakness\s+answer|"
    r"practi[cs]e\s+delivering|revisit\s+the\s+original\s+task|"
    r"name\s+a\s+real\s+weakness|overlaps?\s+or\s+redundanc(?:y|ies)|smooth\s+flow)\b",
    re.IGNORECASE,
)
_CAREER_COMPLETED_WEAKNESS_RETRY_DIRECTIVE_RE = re.compile(
    r"\b(?:revise|refine|retry|restate|repeat|redeliver|"
    r"try(?:\s+delivering)?(?:\s+the)?(?:\s+revised)?(?:\s+version)?\s+again|"
    r"give\s+it\s+another\s+shot|deliver[^.!?]{0,100}\b(?:again|under|within)\b)\b",
    re.IGNORECASE,
)
_CAREER_COMPLETED_WEAKNESS_RETRY_TARGET_RE = re.compile(
    r"\b(?:weakness|mitigation|corrective\s+habit|progress\s+evidence|"
    r"evidence\s+of\s+progress|measurable\s+result|transition|link(?:ing|age)|"
    r"flow|overlaps?|redundanc(?:y|ies)|(?:under|within)\s+\d+\s+seconds?)\b",
    re.IGNORECASE,
)
_CAREER_REPEAT_FUTURE_GOAL_GAP_RE = (
    re.compile(
        r"\b(?:however|but),?\s+(?:the\s+)?future\s+goal[^.!?]{0,260}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:for\s+the\s+revision|task):?\s+[^.!?]{0,180}\b(?:future\s+goal|next\s+career\s+move|next\s+career\s+step)[^.!?]{0,220}[.!?]\s*",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:focus\s+on|think\s+about|revisit)[^.!?]{0,160}\b(?:future\s+goal|career\s+goal|next\s+goal)[^.!?]{0,220}[.!?]\s*",
        re.IGNORECASE,
    ),
)
_OUTCOME_EVIDENCE_TERMS = (
    "result", "outcome", "found", "avoided", "reduced", "improved", "increased",
    "decreased", "measured", "metric", "metrics", "rollback", "support risk",
    "confidence", "expanded", "saved", "faster", "slower rollout",
)
_WEAKNESS_SIGNAL_TERMS = (
    "weakness", "tendency", "struggle", "improving", "under pressure",
    "jumping straight", "technical details", "business impact",
)
_MITIGATION_SIGNAL_TERMS = (
    "manage", "mitigate", "corrected", "correct", "habit", "strategy",
    "decision criteria", "first stating", "phased", "compare options",
)
_WEAKNESS_CORE_CRITERIA = frozenset({
    "real_weakness",
    "mitigation_habit",
    "progress_evidence",
})
_WEAKNESS_EXPLICIT_HISTORY_RE = re.compile(
    r"\b(?:my\s+weakness|one\s+weakness|weakness\s+(?:is|was)|"
    r"i\s+(?:used\s+to|tended\s+to|sometimes)\s+(?:lead|explain|jump|over[-\s]?explain|"
    r"go\s+straight)|earlier[^.!?]{0,120}\bi\s+(?:led|tended|explained|jumped|"
    r"over[-\s]?explained))\b",
    re.IGNORECASE,
)
_WEAKNESS_CONCRETE_HISTORY_RE = re.compile(
    r"\b(?:caught|found|avoided|reduced|improved|increased|measured|rollback|"
    r"retry|latency|reconciliation|support[-\s]?ticket|revenue|product|week\s+one|"
    r"one\s+meeting|metric|failure\s+rate)\b",
    re.IGNORECASE,
)
_FUTURE_GOAL_TERMS = (
    "next goal",
    "next role",
    "next step",
    "i want to",
    "i aim to",
    "moving toward",
    "want to own",
    "grow into",
    "looking to",
)
_GD_GENERIC_TOPIC_PHRASES = (
    "remote work policies",
    "mandatory daily check-ins",
    "digital payments",
    "digital payment methods",
    "mandatory for all businesses",
    "remote work",
    "single-use plastics",
    "social media",
    "electric cars",
    "bike lanes",
    "online courses",
    "whether the budget should grow at all",
    "budget should grow",
)
_COACHING_STREAM_KINDS = frozenset(
    {"teach", "bridge", "strengthen", "challenge", "redirect", "clarify", "ease"}
)
_INCOMPLETE_COACH_END_RE = re.compile(
    r"\b(?:for\s+instance|for\s+example|such\s+as|including|because|but|however|"
    r"instead\s+of|while|whereas)\s*[:,;]?$",
    re.IGNORECASE,
)

# Precomputed probe banks (Phase 4 Layer B) go stale as the learner's prep
# weaknesses shift; a bank older than this is treated as a cache miss and the
# TEST start regenerates. One week is long enough that a normal prep->test gap
# reuses the precache, short enough that drifted weaknesses don't fossilize.
TEST_ITEM_TTL = 7 * 24 * 3600  # seconds
OPENING_STREAM_TIMEOUT_SECONDS = 18.0

MASTERY_COMPLETE = 0.8       # node "mastered" (EMA) — kept for DB clean-flag only
CLEAN_PASS_MAX_ATTEMPTS = 2  # mastered in <=2 scored answers == "clean"
PASSRATE_FLOOR = 0.5         # module clean-rate below this -> remediation

# Progression is gated on a CONSECUTIVE clean-pass streak, not the EMA mastery
# value. The EMA (update_mastery, alpha 0.3) converges toward the score and a
# steady 0.8 never crosses a strict >0.8 gate, so the old mastery gate could
# softlock a learner who was answering correctly. A streak of clean passes is
# both reachable and a truer signal of "ready to move on".
PASS_SCORE = 0.7         # a single answer at/above this is a clean pass
ADVANCE_STREAK = 2       # this many consecutive clean passes -> advance node
FAIL_SCORE = 0.4         # below this counts as a hard fail at this level
INCOMPLETE_SCORE = 0.5   # neutral "couldn't assess" marker — never persist a silent 0.0
DOWN_LADDER_FAILS = 2    # this many hard fails -> scaffold HARD (down-ladder)
MAX_INPUT_CHARS = 2000   # cap learner input; protects ctx window + cost

# Short learner messages matching these end the session gracefully.
_END_PHRASES = {
    "done", "stop", "bye", "goodbye", "quit", "exit", "that's all",
    "thats all", "im done", "i'm done", "end", "finish", "no more",
    # temporal goodbye variants ("im done for today" etc.)
    "done for now", "done for today", "im done now", "i'm done now",
    "im done for today", "i'm done for today", "done here",
}

# Pure farewell tokens — they appear ONLY as goodbyes, never inside a real answer,
# so a single occurrence anywhere in the message ends the session (no length gate).
_FAREWELL_TOKENS = {"bye", "goodbye", "ciao", "tata"}
# Ambiguous end words — also ordinary CONTENT words ("I had to quit my last job",
# "we should exit that market segment"), so they only signal a farewell in a SHORT
# message. A bare "quit"/"exit" is still caught by the exact-match _END_PHRASES tier.
_AMBIGUOUS_END_TOKENS = {"quit", "exit"}
# Phrases that signal discouragement -> pivot to support on the next turn.
_FRUSTRATION_PHRASES = (
    "i can't", "i cant", "give up", "too hard", "i'm confused", "im confused",
    "i don't get", "i dont get", "this is hard", "i'm lost", "im lost",
    "i give up", "frustrated", "i can not",
)
# Positive / negated idioms that CONTAIN a frustration phrase but are NOT
# discouragement ("I can't wait", "I'm not frustrated", "hard work pays off").
# These veto a match so the support pivot never patronises a confident learner.
_FRUSTRATION_OVERRIDES = (
    "can't wait", "cant wait", "can not wait", "cannot wait",
    "not frustrated", "n't frustrated", "not confused", "n't confused",
    "not lost", "n't lost", "not hard", "n't hard", "not that hard",
    "not so hard", "not too hard", "n't too hard", "n't so hard",
    "n't that hard", "never give up", "not giving up",
    "won't give up", "wont give up", "don't give up", "dont give up",
    "do not give up", "hard work",
)


def _recent_score_for_tone(state: dict) -> float | None:
    score = state.get("last_clean_pass_score", state.get("last_eval_score"))
    return score if isinstance(score, (int, float)) else None


def _sanitize_coaching_opening_praise(text: str, state: dict, spec_kind: str) -> str:
    """Remove inflated opening praise when the scored context has not earned it."""
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    match = _CELEBRATORY_OPENING_RE.match(text)
    if not match:
        return text

    score = _recent_score_for_tone(state)
    scaffolded = bool(state.get("last_graded_bridge"))
    remainder = text[match.end():].lstrip()
    if remainder:
        marker = _ACTIONABLE_COACHING_MARKER_RE.search(remainder)
        if marker and marker.start() > 0:
            remainder = remainder[marker.start():].lstrip()
        for index, character in enumerate(remainder):
            if character.isalpha():
                if character.islower():
                    remainder = remainder[:index] + character.upper() + remainder[index + 1:]
                break
    if scaffolded:
        opener = "Good, that scaffolded step is in place - not the whole skill yet. "
    elif score is not None and score < PASS_SCORE:
        opener = "Let's tighten this. "
    else:
        opener = "That answer is on the right track. "
    return opener + remainder if remainder else opener.strip()


def _needs_full_coaching_sanitize(state: dict, spec_kind: str) -> bool:
    if state.get("task_type") in _TEST_TASK_TYPES:
        return False
    if spec_kind not in _COACHING_STREAM_KINDS:
        return False
    if str(state.get("competency_node") or "").startswith("gd_") and _gd_topic_phrase_for_state(state):
        return True
    return True


def _gd_topic_phrase_for_state(state: dict) -> str:
    context = state.get("career_context") or {}
    topics = [
        str(topic).strip()
        for topic in (context.get("gd_topics") or [])
        if str(topic).strip()
    ]
    scenario = state.get("scenario_config") or {}
    active_prompt_topic = str(state.get("active_gd_prompt_topic") or "").strip()
    topic = (
        active_prompt_topic
        if active_prompt_topic
        else topics[0]
        if topics
        else str(scenario.get("resolved_topic") or scenario.get("topic") or "").strip()
    )
    if not topic:
        return ""
    clean = topic.strip().strip("\"'").strip()
    clean = clean[:-1].strip() if clean.endswith("?") else clean
    if not clean.lower().startswith("should "):
        return clean
    rest = clean[len("Should "):].strip()
    words = rest.split()
    if "be" in [word.lower() for word in words]:
        be_index = next(i for i, word in enumerate(words) if word.lower() == "be")
        if be_index > 0:
            subject = " ".join(words[:be_index])
            remainder = " ".join(words[be_index + 1:])
            return " ".join(part for part in (subject, "being", remainder) if part).strip()
    if len(words) < 2:
        return rest
    subject, verb, remainder = words[0], words[1], " ".join(words[2:])
    ing = {
        "abolish": "abolishing",
        "allow": "allowing",
        "ban": "banning",
        "be": "being",
        "do": "doing",
        "get": "getting",
        "have": "having",
        "make": "making",
        "replace": "replacing",
        "require": "requiring",
        "teach": "teaching",
        "use": "using",
    }.get(verb.lower())
    if not ing:
        return rest
    return " ".join(part for part in (subject, ing, remainder) if part).strip()


def _sanitize_gd_topic_drift(text: str, state: dict) -> str:
    if not text or not str(state.get("competency_node") or "").startswith("gd_"):
        return text
    topic_phrase = _gd_topic_phrase_for_state(state)
    if not topic_phrase:
        return text
    topic_lower = topic_phrase.lower()
    cleaned = text
    for phrase in _GD_GENERIC_TOPIC_PHRASES:
        if phrase.lower() in topic_lower:
            continue
        replacement = (
            f"the trade-offs in {topic_phrase}"
            if phrase == "mandatory daily check-ins"
            else topic_phrase
        )
        cleaned = re.sub(re.escape(phrase), replacement, cleaned, flags=re.IGNORECASE)
    return cleaned


def _sanitize_unrelated_career_sample_domain(text: str, state: dict, spec_kind: str) -> str:
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    node_id = str(state.get("competency_node") or "")
    if not (node_id.startswith("int_") or node_id.startswith("gd_")):
        return text
    text_lower = text.lower()
    found_terms = [term for term in _UNRELATED_CAREER_SAMPLE_TERMS if term in text_lower]
    if not found_terms:
        return text
    context = state.get("career_context") or {}
    allowed_context = " ".join(
        [
            _recent_user_feedback_text(state, limit=1600),
            str(context.get("primary_role") or ""),
            str(context.get("role_family") or ""),
            " ".join(str(item) for item in context.get("resume_facts") or []),
            " ".join(str(item) for item in context.get("gd_topics") or []),
        ]
    ).lower()
    disallowed = [term for term in found_terms if term not in allowed_context]
    if not disallowed:
        return text
    cleaned = _UNRELATED_CAREER_SAMPLE_SENTENCE_RE.sub(
        " Keep the revision inside your own answer: make your action and result easier to hear. ",
        text,
    )
    return re.sub(r"\s{2,}", " ", cleaned).strip()


_ANCHOR_STOPWORDS = frozenset({
    "about", "after", "again", "answer", "because", "before", "being", "could",
    "their", "there", "these", "thing", "those", "through", "under", "would",
    "your", "youre", "youve", "with", "without", "what", "when", "where",
    "which", "while", "this", "that", "from", "into", "more", "need",
    "needs", "make", "made", "work", "working", "story", "example",
})


def _latest_user_feedback_excerpt(state: dict, limit: int = 140) -> str:
    current = " ".join(str(state.get("user_input") or "").split())
    if current:
        if len(current) <= limit:
            return current
        trimmed = current[: max(0, limit - 3)].rstrip()
        if " " in trimmed:
            trimmed = trimmed.rsplit(" ", 1)[0].rstrip()
        return f"{trimmed}..."
    for message in reversed(state.get("messages") or []):
        if message.get("role") != "user":
            continue
        text = " ".join(str(message.get("content") or "").split())
        if not text:
            continue
        if len(text) <= limit:
            return text
        trimmed = text[: max(0, limit - 3)].rstrip()
        if " " in trimmed:
            trimmed = trimmed.rsplit(" ", 1)[0].rstrip()
            return f"{trimmed}..."
    return ""


def _bounded_exact_excerpt(text: str, limit: int = 220) -> str:
    excerpt = str(text or "").strip()
    if len(excerpt) <= limit:
        return excerpt
    excerpt = excerpt[:limit].rstrip()
    if " " in excerpt:
        excerpt = excerpt.rsplit(" ", 1)[0].rstrip()
    return excerpt


def _grounded_display_evidence(
    learner_answer: str,
    evidence_quote: str,
    limit: int = 220,
) -> str:
    answer = " ".join(str(learner_answer or "").split())
    quote = " ".join(str(evidence_quote or "").split())
    if not answer or not quote or limit <= 0:
        return ""
    match = re.search(re.escape(quote), answer, flags=re.IGNORECASE)
    if match is None:
        return ""

    sentence_spans: list[tuple[int, int]] = []
    start = 0
    for boundary in re.finditer(r"[.!?]+(?:[\"')\]]+)?(?=\s|$)", answer):
        end = boundary.end()
        sentence_spans.append((start, end))
        start = end
        while start < len(answer) and answer[start].isspace():
            start += 1
    if start < len(answer):
        sentence_spans.append((start, len(answer)))

    containing = [
        span
        for span in sentence_spans
        if span[0] <= match.start() and span[1] >= match.end()
    ]
    for span_start, span_end in containing:
        candidate = answer[span_start:span_end].strip()
        if candidate and len(candidate) <= limit:
            return candidate

    clause_boundary = re.compile(
        r"[;:]|,(?=\s+(?:and|but|so|yet|while|although|however|then)\b)",
        flags=re.IGNORECASE,
    )
    for sentence_start, sentence_end in containing:
        sentence = answer[sentence_start:sentence_end]
        clause_start = 0
        clause_spans: list[tuple[int, int]] = []
        for boundary in clause_boundary.finditer(sentence):
            clause_spans.append((clause_start, boundary.start()))
            clause_start = boundary.end()
        clause_spans.append((clause_start, len(sentence)))
        for local_start, local_end in clause_spans:
            absolute_start = sentence_start + local_start
            absolute_end = sentence_start + local_end
            if absolute_start > match.start() or absolute_end < match.end():
                continue
            candidate = answer[absolute_start:absolute_end].strip()
            if candidate and len(candidate) <= limit:
                return candidate
    return ""


def _exact_rubric_evidence_quote(user_input: str, evidence_quote: str) -> str:
    candidate = str(evidence_quote or "").strip()
    if not candidate:
        return ""
    tokens = candidate.split()
    if not tokens:
        return ""
    match = re.search(
        r"\s+".join(re.escape(token) for token in tokens),
        str(user_input or ""),
        flags=re.IGNORECASE,
    )
    if match is None:
        return ""
    return _bounded_exact_excerpt(match.group(0))


def _completion_feedback_text(rubric_result: dict, user_input: str) -> str:
    criteria_labels: list[str] = []
    evidence_by_id: dict[str, str] = {}
    for row in rubric_result.get("criteria") or []:
        if not isinstance(row, dict) or row.get("met") is not True:
            continue
        criterion_id = str(row.get("id") or row.get("criterion_id") or "").strip()
        if criterion_id:
            label = (
                "answering the question"
                if criterion_id == "answers_question"
                else criterion_id.replace("_", " ").replace("-", " ")
            )
            if label not in criteria_labels:
                criteria_labels.append(label)
        quote = _exact_rubric_evidence_quote(user_input, row.get("evidence_quote") or "")
        if criterion_id and quote:
            evidence_by_id.setdefault(criterion_id, quote)

    weakness_ids = {"real_weakness", "mitigation_habit", "progress_evidence"}
    if weakness_ids.issubset(evidence_by_id):
        progress_quote = evidence_by_id["progress_evidence"]
        return (
            "Keep this version. It names the weakness, the management habit, and the progress "
            f'signal, grounded in "{progress_quote}". No required gap remains, so this skill is '
            "ready to carry forward."
        )

    criteria = criteria_labels[:3]
    if len(criteria) > 1:
        criteria_text = ", ".join(criteria[:-1]) + f", and {criteria[-1]}"
    elif criteria:
        criteria_text = criteria[0]
    else:
        criteria_text = "the required criteria"

    quote_priority = (
        "result",
        "impact_signal",
        "progress_evidence",
        "learner_action",
        "mitigation_habit",
    )
    candidates = [evidence_by_id[item] for item in quote_priority if evidence_by_id.get(item)]
    if not candidates:
        candidates = list(evidence_by_id.values())
    quotes: list[str] = []
    for quote in candidates:
        if quote not in quotes:
            quotes.append(quote)
        if len(quotes) == 2:
            break
    if not quotes:
        fallback = _bounded_exact_excerpt(user_input)
        if fallback:
            quotes = [fallback]
    quoted_evidence = " and ".join(f'"{quote}"' for quote in quotes)
    proof_text = (
        f", using {quoted_evidence} as proof"
        if quoted_evidence
        else ""
    )
    return (
        f"Keep this version. It covers {criteria_text}{proof_text}. "
        "No required gap remains, so this skill is ready to carry forward."
    )


def _recent_user_feedback_text(state: dict, *, max_messages: int = 4, limit: int = 1200) -> str:
    parts: list[str] = []
    current = " ".join(str(state.get("user_input") or "").split())
    if current:
        parts.append(current)
    for message in reversed(state.get("messages") or []):
        if len(parts) >= max_messages:
            break
        if message.get("role") != "user":
            continue
        text = " ".join(str(message.get("content") or "").split())
        if not text or text in parts:
            continue
        parts.append(text)
    combined = " ".join(parts)
    return combined[:limit]


def _meaningful_anchor_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) >= 5 and token not in _ANCHOR_STOPWORDS
    }


def _ensure_career_feedback_anchor(text: str, state: dict, spec_kind: str) -> str:
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    node_id = str(state.get("competency_node") or "")
    if not (node_id.startswith("int_") or node_id.startswith("gd_")):
        return text
    latest = _latest_user_feedback_excerpt(state)
    if not latest:
        return text
    text_tokens = _meaningful_anchor_tokens(text)
    latest_tokens = _meaningful_anchor_tokens(latest)
    topic = _gd_topic_phrase_for_state(state)
    role = str((state.get("career_context") or {}).get("primary_role") or "").strip()
    topic_or_role_anchored = bool(
        (topic and topic.lower() in text.lower()) or
        (role and role.lower() in text.lower())
    )
    if topic_or_role_anchored or len(text_tokens & latest_tokens) >= 2:
        return text
    return f"In your answer, you said \"{latest}\". {text}"


def _sanitize_repeated_outcome_gap(text: str, state: dict, spec_kind: str) -> str:
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    latest = _latest_user_feedback_excerpt(state, limit=260).lower()
    if not latest:
        return text
    has_outcome = sum(1 for term in _OUTCOME_EVIDENCE_TERMS if term in latest) >= 2
    if not has_outcome:
        return text
    cleaned = text
    for pattern in _CAREER_REPEAT_OUTCOME_GAP_RE:
        cleaned = pattern.sub(
            "Now tighten that outcome into one compact result sentence. ",
            cleaned,
            count=1,
        )
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _rubric_covers_weakness_core(state: dict) -> bool:
    result = state.get("last_rubric_result")
    if not isinstance(result, dict):
        return False
    missing = {str(item) for item in (result.get("required_missing") or [])}
    if missing & _WEAKNESS_CORE_CRITERIA:
        return False
    blockers = {str(item).lower() for item in (result.get("blockers") or [])}
    for criterion_id in _WEAKNESS_CORE_CRITERIA:
        if any(criterion_id in blocker for blocker in blockers):
            return False
    criteria = result.get("criteria") or []
    met_by_id: dict[str, bool] = {}
    for row in criteria:
        if hasattr(row, "model_dump"):
            row = row.model_dump()
        if not isinstance(row, dict):
            continue
        criterion_id = str(row.get("id") or row.get("criterion_id") or "")
        if criterion_id:
            met_by_id[criterion_id] = bool(row.get("met"))
    criteria_core_met = (
        bool(met_by_id)
        and all(met_by_id.get(criterion_id) for criterion_id in _WEAKNESS_CORE_CRITERIA)
    )
    return bool(result.get("pass_eligible")) or criteria_core_met


def _text_covers_weakness_core(text: str) -> bool:
    lower = str(text or "").lower()
    if not lower:
        return False
    has_weakness = bool(_WEAKNESS_EXPLICIT_HISTORY_RE.search(lower))
    has_mitigation = any(term in lower for term in _MITIGATION_SIGNAL_TERMS)
    has_outcome = sum(1 for term in _OUTCOME_EVIDENCE_TERMS if term in lower) >= 2
    has_concrete_marker = bool(_WEAKNESS_CONCRETE_HISTORY_RE.search(lower))
    return has_weakness and has_mitigation and has_outcome and has_concrete_marker


def _history_covers_weakness_core(state: dict) -> bool:
    for message in state.get("messages") or []:
        if not isinstance(message, dict) or message.get("role") != "user":
            continue
        if _text_covers_weakness_core(str(message.get("content") or "")):
            return True
    return _text_covers_weakness_core(str(state.get("user_input") or ""))


def _looks_like_completed_weakness_retry(text: str) -> bool:
    return bool(
        _CAREER_COMPLETED_WEAKNESS_RETRY_DIRECTIVE_RE.search(text)
        and _CAREER_COMPLETED_WEAKNESS_RETRY_TARGET_RE.search(text)
    )


def _weakness_next_challenge_text(state: dict) -> str:
    latest = _recent_user_feedback_text(state, max_messages=2, limit=900).lower()
    pressure_already_answered = any(
        phrase in latest
        for phrase in (
            "if challenged",
            "pushed back",
            "pushback",
            "stakeholder challenge",
            "defend the",
        )
    )
    if pressure_already_answered:
        return (
            "That version already shows the past tendency, corrective habit, measurable "
            "progress, and a defended tradeoff. Keep it as the interview answer. Next, "
            "transfer the same improvement to a different setting: give one complete "
            "weakness answer about a decision that did not work, the habit you used, and "
            "the measurable change afterward."
        )
    return (
        "That version now has the three-part shape: past tendency, corrective habit, "
        "and measurable progress. Keep it as the interview answer. Next, pressure-test it "
        "in a harder context: give one complete weakness answer where an interviewer "
        "pushes back on your tradeoff and you defend it with a measurable result."
    )


def _weakness_pressure_retry_text() -> str:
    return (
        "Your defense has useful evidence, but it still needs to answer the pushback "
        "directly. Try the same pressure question once: what evidence makes your chosen "
        "tradeoff safer than the faster alternative, and which metric proves it?"
    )


def _sanitize_repeated_weakness_gap(text: str, state: dict, spec_kind: str) -> str:
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    if str(state.get("competency_node") or "") != "int_03_weakness_framing":
        return text
    recent = _recent_user_feedback_text(state).lower()
    if not recent:
        return text
    has_weakness = any(term in recent for term in _WEAKNESS_SIGNAL_TERMS)
    has_mitigation = any(term in recent for term in _MITIGATION_SIGNAL_TERMS)
    has_outcome = sum(1 for term in _OUTCOME_EVIDENCE_TERMS if term in recent) >= 2
    rubric_core_covered = _rubric_covers_weakness_core(state)
    history_core_covered = _history_covers_weakness_core(state)
    has_rubric_result = isinstance(state.get("last_rubric_result"), dict)
    rubric_result = state.get("last_rubric_result") or {}
    rubric_attempt_type = str(rubric_result.get("attempt_type") or "independent")
    missing_core = {
        str(item) for item in (rubric_result.get("required_missing") or [])
    } & _WEAKNESS_CORE_CRITERIA
    if has_rubric_result and missing_core and rubric_attempt_type == "independent":
        return text
    if (
        has_rubric_result
        and missing_core
        and rubric_attempt_type in {"transfer", "pressure"}
        and not _has_valid_core_qualification(state)
    ):
        return text
    heuristic_core_covered = (
        not has_rubric_result
        and has_weakness
        and has_mitigation
        and has_outcome
    )
    if not (rubric_core_covered or history_core_covered or heuristic_core_covered):
        return text

    replacement = (
        "You already have the weakness, the corrective habit, and a progress signal; "
        "now pressure-test it against one realistic follow-up. "
    )
    cleaned = text
    for pattern in _CAREER_REPEAT_WEAKNESS_GAP_RE:
        cleaned = pattern.sub(replacement, cleaned, count=1)
    if (
        cleaned != text
        or _CAREER_REPEAT_WEAKNESS_REQUEST_RE.search(text)
        or _looks_like_completed_weakness_retry(text)
    ):
        if rubric_attempt_type == "pressure":
            state["active_prompt_attempt_type"] = "pressure"
            return _weakness_pressure_retry_text()
        state["active_prompt_attempt_type"] = "transfer"
        return _weakness_next_challenge_text(state)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _sanitize_repeated_future_goal_gap(text: str, state: dict, spec_kind: str) -> str:
    if not text or state.get("task_type") in _TEST_TASK_TYPES:
        return text
    if spec_kind not in _COACHING_STREAM_KINDS:
        return text
    if str(state.get("competency_node") or "") != "int_01_elevator_pitch":
        return text
    latest = _latest_user_feedback_excerpt(state, limit=360).lower()
    if not latest or not any(term in latest for term in _FUTURE_GOAL_TERMS):
        return text
    cleaned = text
    replacement = (
        "Your direction is present; now make the final sentence sharper by naming "
        "the scope and impact you want next. "
    )
    for pattern in _CAREER_REPEAT_FUTURE_GOAL_GAP_RE:
        cleaned = pattern.sub(replacement, cleaned, count=1)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _clean_star_pass_followup_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "int_04_star_behavioral":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None
    if (
        not result.get("pass_eligible")
        or result.get("required_missing")
        or result.get("blockers")
        or plan.get("verdict") != "independent_pass"
    ):
        return None

    requested_action = str(plan.get("next_action") or "")
    next_action = validated_tutor_next_action(plan, state)
    if (
        requested_action in {"request_pressure", "request_consolidation"}
        and next_action == "request_fresh_independent"
    ):
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Before I challenge the causal link, give a new STAR story from your own "
            "experience. Include the situation, your task, your specific actions, and a "
            "measurable result."
        )
    elif next_action == "request_transfer":
        state["pending_prompt_attempt_type"] = "transfer"
        task = (
            "Next task: Give a different STAR story from your own experience about a "
            "meaningfully different challenge. Keep Situation and Task brief, spend most "
            "of the answer on your actions, and end with a measurable result."
        )
    elif next_action == "request_pressure":
        core_excerpt = _qualified_core_answer_excerpt(state, "int_04_star_behavioral")
        if not core_excerpt:
            state["pending_prompt_attempt_type"] = "independent"
            task = (
                "Before I challenge the causal link, give a new STAR story from your own "
                "experience. Include the situation, your task, your specific actions, and a "
                "measurable result."
            )
        else:
            state["pending_prompt_attempt_type"] = "pressure"
            task = (
                f'Next task: Return to the earlier STAR story that began: "{core_excerpt}". '
                "A skeptical interviewer asks which of your actions most directly caused the "
                "result. Defend that causal link with one piece of evidence from that qualified story."
            )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        core_excerpt = _qualified_core_answer_excerpt(state, "int_04_star_behavioral")
        core_instruction = (
            f'Return to the earlier STAR story that began: "{core_excerpt}". '
            if core_excerpt
            else "Return to the earlier STAR story you established. "
        )
        task = (
            f"Next task: {core_instruction}Deliver that STAR answer once in under 60 seconds without "
            "removing the action-to-result link."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Next task: Give a fresh STAR story using a different learner-owned example, "
            "with brief setup, specific actions, and a measurable result."
        )
    latest = _latest_user_feedback_excerpt(state, limit=180)
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    return (
        f"{anchor}All STAR parts are present: context, responsibility, specific actions, "
        f"and a measurable result. Keep this version. {task}"
    )


def _early_interview_feedback_text(state: dict) -> str | None:
    if state.get("task_type") != "interview_prep":
        return None
    node_id = str(state.get("competency_node") or "")
    if node_id not in {"int_02_strength_with_evidence", "int_03_weakness_framing"}:
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None
    answer = " ".join(str(state.get("user_input") or "").split())
    answer_lower = answer.lower()
    quotes_by_id: dict[str, str] = {}
    for row in result.get("criteria") or []:
        if not isinstance(row, dict) or row.get("met") is not True:
            continue
        criterion_id = str(row.get("id") or row.get("criterion_id") or "").strip()
        quote = " ".join(str(row.get("evidence_quote") or "").split())
        if criterion_id and quote and quote.lower() in answer_lower:
            quotes_by_id.setdefault(criterion_id, _bounded_exact_excerpt(quote, 180))
    evidence_priority = (
        ("impact_signal", "learner_action", "specific_evidence", "strength_claim")
        if node_id == "int_02_strength_with_evidence"
        else ("progress_evidence", "mitigation_habit", "real_weakness")
    )
    evidence = next(
        (quotes_by_id[criterion_id] for criterion_id in evidence_priority if quotes_by_id.get(criterion_id)),
        "",
    )
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    attempt_type = str(result.get("attempt_type") or "independent")
    if not result.get("pass_eligible") or required_missing or blockers:
        state["pending_prompt_attempt_type"] = (
            attempt_type if attempt_type in {"transfer", "pressure"} else "independent"
        )
        anchor = f'Your answer already gives this usable evidence: "{evidence}". ' if evidence else ""
        criterion_focus = {
            "strength_claim": "state the strength clearly",
            "specific_evidence": "add one specific learner-owned example",
            "learner_action": "show the action that proves the strength",
            "impact_signal": "state the observable result",
            "real_weakness": "name one genuine past tendency",
            "mitigation_habit": "state the corrective habit you now use",
            "progress_evidence": "add one concrete progress signal",
            "non_self_sabotage": "bound the weakness so it does not disqualify you for the role",
            "transfer_context": "use the newly assigned context rather than repeating the core answer",
            "core_consistency": "keep the harder answer consistent with the qualified version",
        }
        gaps = [criterion_focus[item] for item in required_missing if item in criterion_focus]
        focus = "; and ".join(gaps) or "complete the active skill with learner-owned evidence"
        if "core_consistency" in required_missing:
            core = qualified_core_evidence(state, node_id)
            core_excerpt = _bounded_exact_excerpt(
                str((core or {}).get("learner_answer") or ""),
                150,
            )
            if core_excerpt:
                return (
                    f'{anchor}That result belongs to the transfer scenario. Return to the qualified '
                    f'answer that began: "{core_excerpt}". Defend that same weakness, habit, and '
                    "result; change only the defense."
                )
        return f"{anchor}The missing step is to {focus}. Revise only that part using the same story."

    action = validated_tutor_next_action(plan, state)
    if node_id == "int_02_strength_with_evidence":
        anchor = (
            f'Your proof is specific and learner-owned: "{evidence}". '
            if evidence
            else "Your strength, action, and result are all present. "
        )
        tasks = {
            "request_transfer": (
                "Transfer task: show stakeholder communication as a different strength. Prove it "
                "with one specific action used to align a client, partner, or stakeholder and one observable result."
            ),
            "request_pressure": (
                "Pressure check: the interviewer says the result may belong to the team. "
                "Name your personal contribution and the evidence that connects it to the outcome."
            ),
            "request_consolidation": (
                "Final delivery: state the strength, one proof example, and the result in two concise sentences."
            ),
        }
        task = tasks.get(action, "Use a different strength and support it with one action and one result.")
    else:
        anchor = (
            f'Your answer now shows concrete progress: "{evidence}". '
            if evidence
            else "Your weakness, management habit, and progress signal are all present. "
        )
        core = qualified_core_evidence(state, node_id)
        core_excerpt = _bounded_exact_excerpt(
            str((core or {}).get("learner_answer") or ""),
            150,
        )
        pressure_task = (
            f'Return to the qualified answer that began: "{core_excerpt}". The interviewer '
            "challenges whether that corrective habit really works. Defend the same habit with "
            "one concrete result from that answer."
            if core_excerpt
            else (
                "Pressure check: defend why your corrective habit works with one concrete result, "
                "without disguising a strength as a weakness."
            )
        )
        tasks = {
            "request_transfer": (
                "Now transfer that structure to estimation under ambiguity. In three concise sentences, "
                "name the tendency, the habit you use when requirements are uncertain, and one measurable "
                "sign that the habit is working."
            ),
            "request_pressure": pressure_task,
            "request_consolidation": (
                "Final delivery: give the real weakness, corrective habit, and progress evidence in three concise sentences."
            ),
        }
        task = tasks.get(action, "Use a different real weakness and show the habit and progress evidence.")
    if action == "request_transfer":
        state["pending_prompt_attempt_type"] = "transfer"
    elif action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
    else:
        state["pending_prompt_attempt_type"] = "independent"
    return f"{anchor}{task}"


def _int05_opening_text(state: dict) -> str:
    role = str((state.get("career_context") or {}).get("primary_role") or "the target role").strip()
    return (
        f"Today we'll build a specific, researched company-motivation answer for a {role} opportunity. "
        "Choose a company you are genuinely considering, name one verified product, "
        "engineering practice, or strategic move, then explain why it matters to you "
        f"and why your experience fits the {role} role."
    )


def _int05_feedback_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "int_05_why_this_role":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    role = str((state.get("career_context") or {}).get("primary_role") or "the target role").strip()
    latest = _latest_user_feedback_excerpt(state, limit=180)
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]

    if result.get("pass_eligible") and not required_missing and not blockers:
        next_action = validated_tutor_next_action(plan, state)
        if next_action == "request_transfer":
            state["pending_prompt_attempt_type"] = "transfer"
            task = (
                "Transfer task: keep the company and evidence you chose, but answer for a "
                f"skeptical engineering manager hiring for the {role} role. Make the link "
                "between the company fact and the work you would contribute explicit."
            )
        elif next_action == "request_pressure":
            state["pending_prompt_attempt_type"] = "pressure"
            task = (
                "Pressure check: an interviewer says, 'You could do this work anywhere; why "
                "this company specifically?' Defend your choice in two sentences using the "
                "company fact and your own experience."
            )
        elif next_action == "request_consolidation":
            state["pending_prompt_attempt_type"] = "independent"
            task = (
                f"Consolidation task: deliver the same {role} answer in under 30 seconds "
                "without losing the company fact, personal motivation, or role-fit link."
            )
        else:
            state["pending_prompt_attempt_type"] = "independent"
            task = (
                "Next task: choose a different company you would genuinely apply to. Name one "
                "verified company fact, then connect it to your personal motivation and your "
                f"fit for a {role} role."
            )
        return (
            f"{anchor}You covered a concrete company fact, personal motivation, and fit "
            f"for the {role} role. Keep this answer. {task}"
        )

    missing_labels = {
        "company_specific_fact": "one verified company-specific fact",
        "personal_motivation_link": "why that fact matters to you personally",
        "role_relevance": f"why your experience fits the {role} role",
    }
    missing = [missing_labels[item] for item in required_missing if item in missing_labels]
    if not missing:
        unmet = {
            str(row.get("id") or "")
            for row in (result.get("criteria") or [])
            if isinstance(row, dict) and not row.get("met")
        }
        if "non_generic" in unmet:
            missing = ["a specific reason beyond reputation, growth, or general admiration"]
    if not missing:
        missing = ["one rubric-backed link between the company fact, your motivation, and role fit"]
    revision = "; and ".join(missing)
    return (
        f"{anchor}Keep the company you named and the {role} role fixed. The missing piece is "
        f"{revision}. One targeted revision: add only that missing link in your own words; "
        "do not replace your company or story."
    )


def _qualified_core_answer_excerpt(state: dict, node_id: str, limit: int = 150) -> str:
    evidence = qualified_core_evidence(state, node_id)
    if evidence is None:
        return ""
    answer = " ".join(str(evidence.get("learner_answer") or "").split())
    if len(answer) <= limit:
        return answer
    excerpt = answer[: max(1, limit - 3)].rsplit(" ", 1)[0].rstrip()
    return f"{excerpt}..."


def _int06_core_incident_excerpt(state: dict, limit: int = 150) -> str:
    return _qualified_core_answer_excerpt(state, "int_06_own_a_failure", limit)


def _int06_pressure_feedback_text(state: dict, result: dict, plan: dict) -> str:
    if not _int06_core_incident_excerpt(state):
        state["pending_prompt_attempt_type"] = "independent"
        return (
            "I cannot fairly continue this challenge because the original incident is not "
            "available. Give a new failure story from your own experience with ownership, "
            "impact, your immediate response, and the prevention change."
        )
    required_ids = ("pressure_response", "evidence_defense", "core_consistency")
    rows_by_id: dict[str, list[dict]] = {criterion_id: [] for criterion_id in required_ids}
    for row in result.get("criteria") or []:
        if not isinstance(row, dict):
            continue
        criterion_id = str(row.get("id") or "")
        if criterion_id in rows_by_id:
            rows_by_id[criterion_id].append(row)

    learner_answer = str(state.get("user_input") or "")
    normalized_answer = " ".join(re.sub(r"[^a-z0-9\s]", " ", learner_answer.lower()).split())
    evidence: dict[str, str] = {}
    invalid_required: list[str] = []
    for criterion_id in required_ids:
        rows = rows_by_id[criterion_id]
        row = rows[0] if len(rows) == 1 else None
        quote = str((row or {}).get("evidence_quote") or "").strip()
        normalized_quote = " ".join(re.sub(r"[^a-z0-9\s]", " ", quote.lower()).split())
        if (
            row is None
            or row.get("met") is not True
            or not normalized_quote
            or normalized_quote not in normalized_answer
        ):
            invalid_required.append(criterion_id)
            continue
        evidence[criterion_id] = quote

    explicit_missing = [
        str(item) for item in (result.get("required_missing") or [])
        if str(item) in required_ids
    ]
    missing = list(dict.fromkeys([*explicit_missing, *invalid_required]))
    labels = {
        "pressure_response": "a direct answer to the interviewer pushback",
        "evidence_defense": "a learner-owned reason or concrete defense",
        "core_consistency": "consistency with the qualified incident",
    }
    core_excerpt = _int06_core_incident_excerpt(state)
    core_instruction = (
        f'Return to the qualified incident that began: "{core_excerpt}"'
        if core_excerpt
        else "Return to the qualified incident from your independent pass"
    )

    if missing:
        state["pending_prompt_attempt_type"] = "pressure"
        proven = "; ".join(
            f'{labels[criterion_id]}: "{evidence[criterion_id]}"'
            for criterion_id in required_ids
            if criterion_id in evidence
        )
        proven_text = f"Already proven in this pressure answer: {proven}. " if proven else ""
        missing_text = "; and ".join(labels[criterion_id] for criterion_id in missing)
        return (
            f"{proven_text}The missing pressure proof is {missing_text}. {core_instruction}. "
            "Answer the same pushback once using only that incident's facts; do not retell a different story."
        )

    if (
        result.get("pass_eligible")
        and not result.get("blockers")
        and plan.get("verdict") == "independent_pass"
    ):
        proof = (
            f'direct response: "{evidence["pressure_response"]}"; '
            f'evidence defense: "{evidence["evidence_defense"]}"; '
            f'core consistency: "{evidence["core_consistency"]}".'
        )
        if str(plan.get("next_action") or "") == "request_consolidation":
            state["pending_prompt_attempt_type"] = "independent"
            return (
                f"Your pressure answer provides this proof: {proof} {core_instruction}. "
                "Final delivery: Retell that qualified incident once without changing any facts, "
                "in this order: ownership, impact, immediate response, and prevention."
            )

    state["pending_prompt_attempt_type"] = "pressure"
    return (
        f"{core_instruction}. Answer the interviewer pushback once using only that incident's "
        "facts and the prevention evidence you already established."
    )


def _int06_feedback_text(state: dict) -> str | None:
    if (
        state.get("task_type") != "interview_prep"
        or str(state.get("competency_node") or "") != "int_06_own_a_failure"
    ):
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    if str(result.get("attempt_type") or "independent") == "pressure":
        return _int06_pressure_feedback_text(state, result, plan)

    required_ids = ("ownership", "impact", "response_action", "prevention")
    rows_by_id: dict[str, list[dict]] = {criterion_id: [] for criterion_id in required_ids}
    for row in result.get("criteria") or []:
        if not isinstance(row, dict):
            continue
        criterion_id = str(row.get("id") or "")
        if criterion_id in rows_by_id:
            rows_by_id[criterion_id].append(row)

    learner_answer = str(state.get("user_input") or "")
    normalized_answer = re.sub(r"[^a-z0-9\s]", " ", learner_answer.lower())
    normalized_answer = " ".join(normalized_answer.split())
    evidence: dict[str, str] = {}
    invalid_required: list[str] = []
    for criterion_id in required_ids:
        rows = rows_by_id[criterion_id]
        row = rows[0] if len(rows) == 1 else None
        quote = str((row or {}).get("evidence_quote") or "").strip()
        normalized_quote = re.sub(r"[^a-z0-9\s]", " ", quote.lower())
        normalized_quote = " ".join(normalized_quote.split())
        if (
            row is None
            or row.get("met") is not True
            or not normalized_quote
            or normalized_quote not in normalized_answer
        ):
            invalid_required.append(criterion_id)
            continue
        evidence[criterion_id] = quote

    explicit_missing = [
        str(item) for item in (result.get("required_missing") or [])
        if str(item) in required_ids
    ]
    missing = list(dict.fromkeys([*explicit_missing, *invalid_required]))
    labels = {
        "ownership": "first-person ownership without blame",
        "impact": "the user, customer, business, or team impact",
        "response_action": "the immediate response or repair action",
        "prevention": "the prevention or process change afterward",
    }
    if missing:
        missing_text = "; and ".join(labels[criterion_id] for criterion_id in missing)
        proven = "; ".join(
            f'{labels[criterion_id]}: "{evidence[criterion_id]}"'
            for criterion_id in required_ids
            if criterion_id in evidence
        )
        proven_text = f"Already proven in your answer: {proven}. " if proven else ""
        return (
            f"{proven_text}The missing required part is {missing_text}. Add only that missing part "
            "to the same incident in your own words; do not replace the incident."
        )

    if (
        not result.get("pass_eligible")
        or result.get("blockers")
        or plan.get("verdict") != "independent_pass"
    ):
        return None

    requested_action = str(plan.get("next_action") or "")
    next_action = validated_tutor_next_action(plan, state)
    next_attempt_type = validated_attempt_type_for_tutor_plan(plan, state)
    if (
        requested_action in {"request_pressure", "request_consolidation"}
        and next_action == "request_fresh_independent"
    ):
        next_attempt_type = "independent"
        task = (
            "Before I challenge your judgment, give a new failure story from your own "
            "experience. Include ownership, impact, your immediate response, and the "
            "prevention change."
        )
    elif next_action == "request_fresh_independent":
        task = (
            "Next task: Give exactly one different incident from your own experience with "
            "a different cause. Preserve ownership, impact, immediate response, and prevention."
        )
    elif next_action == "request_transfer":
        task = (
            "Transfer task: Give one different incident from your own experience where one "
            "meaningful constraint changed what response was possible. Preserve ownership, "
            "impact, immediate response, and prevention."
        )
    elif next_action == "request_pressure":
        core_excerpt = _int06_core_incident_excerpt(state)
        if not core_excerpt:
            next_attempt_type = "independent"
            task = (
                "Before I challenge your judgment, give a new failure story from your own "
                "experience. Include ownership, impact, your immediate response, and the "
                "prevention change."
            )
        else:
            task = (
                f'Pressure task: Return to your qualified incident, which began: "{core_excerpt}". '
                "Answer this interviewer pushback: 'Why should I trust your judgment after that "
                "failure?' Defend your ownership, response, and prevention using only your own "
                "evidence; do not invent a new story."
            )
    elif next_action == "request_consolidation":
        task = (
            "Final delivery: Retell the same proven incident once without changing any facts. "
            "Keep the order ownership, impact, immediate response, and prevention."
        )
    else:
        next_attempt_type = "independent"
        task = (
            "Keep this incident and its facts unchanged. Deliver it once in this order: "
            "ownership, impact, immediate response, and prevention."
        )

    state["pending_prompt_attempt_type"] = next_attempt_type or "independent"

    proof = (
        f'ownership: "{evidence["ownership"]}"; '
        f'impact: "{evidence["impact"]}"; '
        f'immediate response: "{evidence["response_action"]}"; '
        f'prevention: "{evidence["prevention"]}".'
    )
    return (
        f"Your answer provides this proof: {proof} All four required parts are present, "
        f"so there is no content gap. {task}"
    )


def _int07_feedback_text(state: dict) -> str | None:
    if (
        state.get("task_type") != "interview_prep"
        or str(state.get("competency_node") or "") != "int_07_clarify_before_answering"
    ):
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    latest = _latest_user_feedback_excerpt(state, limit=190)
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    if str(result.get("attempt_type") or "independent") == "pressure":
        if not qualified_core_evidence(state, "int_07_clarify_before_answering"):
            state["pending_prompt_attempt_type"] = "independent"
            return (
                f"{anchor}I cannot fairly continue this challenge because the earlier "
                "clarification is not available. Ask a new scope-narrowing question and answer "
                "the interpretation you choose."
            )
        rows = {
            str(row.get("id") or ""): row
            for row in (result.get("criteria") or [])
            if isinstance(row, dict)
        }
        met = {criterion_id for criterion_id, row in rows.items() if row.get("met") is True}
        if required_missing or blockers or not result.get("pass_eligible"):
            state["pending_prompt_attempt_type"] = "pressure"
            if set(required_missing) == {"core_consistency"} and {
                "pressure_response", "evidence_defense"
            }.issubset(met):
                return (
                    f"{anchor}You already answered the no-clarification pushback and gave a "
                    "reasoned answer. Connect that assumption to your earlier clarification, "
                    "then answer once more without changing the scenario."
                )
            labels = {
                "pressure_response": "state the assumption you will use when the interviewer will not clarify",
                "evidence_defense": "give a focused answer under that assumption",
                "core_consistency": "keep the assumption connected to the earlier ambiguous prompt",
            }
            gaps = [labels[item] for item in required_missing if item in labels]
            gap = "; and ".join(gaps) or "answer the no-clarification pushback directly"
            return f"{anchor}The missing pressure step is to {gap}. Retry only that response."

        next_action = validated_tutor_next_action(plan, state)
        state["pending_prompt_attempt_type"] = (
            "independent" if next_action == "request_consolidation" else "pressure"
        )
        return (
            f"{anchor}You stated a clear assumption and answered under it without stalling. "
            "Final delivery: Ask one concise clarifier, handle 'use your judgment' by stating "
            "your assumption, and give the focused answer."
        )

    if not result.get("pass_eligible") or required_missing or blockers:
        if set(required_missing) == {"states_answer_frame"}:
            return (
                f"{anchor}Your clarifying question already narrows the scope. Add a focused "
                "answer to the interpretation you selected; keep the clarifier unchanged."
            )
        labels = {
            "recognizes_ambiguity": "show the two plausible interpretations you need to distinguish",
            "asks_targeted_question": "ask one concise A-or-B clarifying question",
            "states_answer_frame": "answer the interpretation you select after the clarification",
        }
        missing = [labels[item] for item in required_missing if item in labels]
        gap = "; and ".join(missing) or "ask one scope-narrowing question, then answer the chosen scope"
        return (
            f"{anchor}The missing step is to {gap}. Revise only that part using the same "
            "question."
        )

    next_action = validated_tutor_next_action(plan, state)
    if next_action == "request_transfer":
        state["pending_prompt_attempt_type"] = "transfer"
        task = (
            "Transfer task: An interviewer asks, 'How would you improve our product?' Ask whether "
            "they want onboarding, reliability, or retention, then answer one scope you choose."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        task = (
            "Pressure check: The interviewer replies, 'Use your judgment; I will not narrow it.' "
            "State the assumption you are making, then answer under that assumption without stalling."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Final delivery: Ask one concise A-or-B clarifier, state which interpretation you "
            "will answer, and give the focused answer without extra setup."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Next interview question: 'Tell me about your leadership.' Ask whether the interviewer "
            "means people management or technical direction, then answer the interpretation you choose."
        )
    return (
        f"{anchor}You narrowed the ambiguity and answered the scope you selected. Keep that "
        f"two-step structure. {task}"
    )


def _int08_feedback_text(state: dict) -> str | None:
    if (
        state.get("task_type") != "interview_prep"
        or str(state.get("competency_node") or "") != "int_08_quantify_impact"
    ):
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None
    rows = {
        str(row.get("id") or ""): row
        for row in (result.get("criteria") or [])
        if isinstance(row, dict)
    }

    def evidence(criterion_id: str) -> str:
        row = rows.get(criterion_id) or {}
        if row.get("met") is not True:
            return ""
        return _grounded_display_evidence(
            str(state.get("user_input") or ""),
            str(row.get("evidence_quote") or ""),
            220,
        )

    metric = evidence("quantified_before_after") or evidence("impact_claim")
    action = evidence("learner_contribution")
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    attempt_type = str(result.get("attempt_type") or "independent")
    if not result.get("pass_eligible") or required_missing or blockers:
        state["pending_prompt_attempt_type"] = attempt_type
        if set(required_missing) == {"learner_contribution"} and metric:
            sentence_end = "" if metric.endswith((".", "!", "?")) else "."
            return (
                f'The result is measurable: "{metric}"{sentence_end} '
                "Add what you changed to cause that result; "
                "keep the numbers unchanged."
            )
        labels = {
            "impact_claim": "name the outcome that changed",
            "quantified_before_after": "give a baseline and a measurable result",
            "learner_contribution": "state what you personally changed",
            "transfer_context": "use the newly assigned context rather than the earlier example",
            "pressure_response": "answer the challenge to the metric directly",
            "evidence_defense": "defend the metric with a concrete reason or source",
            "core_consistency": "keep the defense consistent with the original achievement",
        }
        gaps = [labels[item] for item in required_missing if item in labels]
        gap = "; and ".join(gaps) or "connect your action to a before-and-after result"
        sentence_end = "" if metric.endswith((".", "!", "?")) else "."
        anchor = (
            f'The measurable evidence you already gave is "{metric}"{sentence_end} '
            if metric else ""
        )
        return f"{anchor}The missing step is to {gap}. Revise only that part."

    metric_end = "" if metric.endswith((".", "!", "?")) else "."
    if action and metric and action.casefold() == metric.casefold():
        proof = (
            "Your action and measurable result appear together in this sentence: "
            f'"{metric}"{metric_end} '
        )
    elif action and metric:
        proof = f'Your answer links "{action}" to "{metric}"{metric_end} '
    elif metric:
        proof = f'Your answer gives measurable evidence: "{metric}"{metric_end} '
    else:
        proof = "Your action and measurable result are both present. "
    next_action = validated_tutor_next_action(plan, state)
    if next_action == "request_transfer":
        state["pending_prompt_attempt_type"] = "transfer"
        task = (
            "Transfer task: Choose a customer, operational, or team outcome outside system "
            "reliability. Give the baseline, your action, and the measurable result."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        task = (
            "Pressure check: The interviewer says, 'That improvement may have been the team's, "
            "not yours.' Identify your contribution and defend why the metric changed because of it."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Final delivery: In two sentences, state the baseline, your action, and the resulting "
            "metric without adding a new example."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        task = (
            "Use a different achievement. State the baseline, what you changed, and the measurable "
            "result in one compact answer."
        )
    return f"{proof}{task}"


_LATE_INTERVIEW_FEEDBACK = {
    "int_09_diplomatic_pushback": {
        "labels": {
            "acknowledges_view": "acknowledge one fair part of the interviewer's premise",
            "clear_counterposition": "state a clear counter-position",
            "requirement_based_reasoning": "tie the disagreement to a requirement or trade-off",
            "collaborative_tone": "remove combative wording and preserve rapport",
            "transfer_context": "use the newly assigned premise",
            "core_consistency": "keep the harder answer consistent with the qualified position",
        },
        "fresh": (
            "Next interview premise: 'Extensive manual testing is always safer than automated "
            "tests in high-transaction systems.' Acknowledge one fair point, state your counter, "
            "and ground it in a requirement or trade-off."
        ),
        "transfer": (
            "Transfer task: The interviewer says, 'The strongest engineers should work alone.' "
            "Acknowledge one fair point, disagree clearly, and connect your view to a team requirement."
        ),
        "pressure": (
            "Pressure check: The interviewer says, 'That sounds indecisive - pick one approach.' "
            "Acknowledge the concern, preserve rapport, hold your counter-position, and defend it "
            "with the governing requirement."
        ),
        "consolidation": (
            "Final delivery: In two sentences, acknowledge the concern, state your position, and "
            "give the requirement or trade-off that decides it."
        ),
    },
    "int_10_close_strong": {
        "labels": {
            "specific_closing_question": "ask one substantive question about success, team, role, or priorities",
            "role_relevance": "make the question specific to the target role",
            "role_fit_evidence": "name the specific value you would bring",
            "professional_close": "include one concise confident fit statement",
            "non_generic": "replace generic feedback or benefits questions with a substantive one",
            "transfer_context": "close for the newly assigned role context",
            "core_consistency": "keep the harder close consistent with the qualified version",
        },
        "fresh": (
            "Close a Backend Software Engineer interview with one substantive role or team question "
            "and one concise sentence naming the value you would bring. Use either natural order."
        ),
        "transfer": (
            "Transfer task: Close a Platform Engineer interview. Ask about the team's first-six-month "
            "reliability priority and state the specific value you would bring."
        ),
        "pressure": (
            "Pressure check: You have only twenty seconds. Ask one sharp question and give one "
            "specific fit statement without filler."
        ),
        "consolidation": (
            "Final delivery: Give the substantive question and specific fit statement in two concise sentences."
        ),
    },
    "int_11_salary_negotiation": {
        "labels": {
            "clear_anchor": "state one concrete salary number or range",
            "market_or_value_reason": "justify the anchor with market, scope, or demonstrated value",
            "collaborative_flexibility": "offer flexibility on package structure without collapsing the anchor",
            "calm_tone": "remove apology or immediate backpedaling",
            "transfer_context": "negotiate the newly assigned offer context",
            "core_consistency": "keep the harder negotiation consistent with the qualified anchor",
        },
        "fresh": (
            "State a salary range for this role, give one market-or-value reason, and name one "
            "package element you could discuss without lowering the range immediately."
        ),
        "transfer": (
            "Transfer task: The base salary is fixed but the package includes bonus and equity. "
            "Keep a clear total-value anchor, justify it, and negotiate one flexible component."
        ),
        "pressure": (
            "Pressure check: The recruiter says the budget is below your range. Hold the anchor "
            "calmly, repeat the evidence, and offer one package trade-off without apologizing."
        ),
        "consolidation": (
            "Final delivery: Give the range, one evidence-based reason, and one flexible package option in three sentences or fewer."
        ),
    },
    "int_12_explain_a_gap": {
        "labels": {
            "brief_context": "give the honest reason briefly",
            "non_blaming_tone": "remove blame, gossip, or defensiveness",
            "productive_use_or_learning": "state what you did, learned, or recovered during the period",
            "forward_focus": "connect the explanation to readiness for the next role",
            "transfer_context": "use the newly assigned gap or departure context",
            "core_consistency": "keep the harder explanation consistent with the qualified facts",
        },
        "fresh": (
            "Explain a six-month career gap in three parts: the brief reason, what you did or learned, "
            "and why you are ready for the next role."
        ),
        "transfer": (
            "Transfer task: Explain leaving a role because growth had plateaued. Stay factual, name "
            "what you learned, and connect the move to what you want next."
        ),
        "pressure": (
            "Pressure check: The interviewer asks, 'Why did the gap last that long?' Answer briefly, "
            "name one productive thing you did or learned, avoid blame or apology, then return to current readiness."
        ),
        "consolidation": (
            "Final delivery: Give the reason, productive use or learning, and forward intent in three concise sentences."
        ),
    },
}


def _late_interview_feedback_text(state: dict) -> str | None:
    if state.get("task_type") != "interview_prep":
        return None
    node_id = str(state.get("competency_node") or "")
    config = _LATE_INTERVIEW_FEEDBACK.get(node_id)
    if not config:
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None
    learner_answer = str(state.get("user_input") or "")
    evidence: dict[str, str] = {}
    for row in result.get("criteria") or []:
        if not isinstance(row, dict) or row.get("met") is not True:
            continue
        quote = _grounded_display_evidence(
            learner_answer,
            str(row.get("evidence_quote") or ""),
            240,
        )
        if quote:
            evidence[str(row.get("id") or "")] = quote
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    attempt_type = str(result.get("attempt_type") or "independent")
    if not result.get("pass_eligible") or required_missing or blockers:
        state["pending_prompt_attempt_type"] = attempt_type if attempt_type in {"transfer", "pressure"} else "independent"
        gaps = [config["labels"].get(item) for item in required_missing]
        gaps = [gap for gap in gaps if gap]
        proven = next(iter(evidence.values()), "")
        sentence_end = "" if proven.endswith((".", "!", "?")) else "."
        anchor = (
            f'You already provided this usable part: "{proven}"{sentence_end} '
            if proven else ""
        )
        gap = "; and ".join(gaps) or "complete the active skill using the same facts"
        return f"{anchor}The missing step is to {gap}. Revise only that part."

    quoted: list[str] = []
    for quote in evidence.values():
        lowered = quote.lower()
        if any(lowered in prior.lower() or prior.lower() in lowered for prior in quoted):
            continue
        quoted.append(quote)
        if len(quoted) == 2:
            break
    if quoted:
        sentence_end = "" if quoted[-1].endswith((".", "!", "?")) else "."
        proof = (
            "The required parts are present in your own wording: "
            + "; ".join(f'"{quote}"' for quote in quoted)
            + sentence_end
            + " "
        )
    else:
        proof = "The required parts are present. "
    action = validated_tutor_next_action(plan, state)
    if action == "request_transfer":
        state["pending_prompt_attempt_type"] = "transfer"
        task = config["transfer"]
    elif action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        task = config["pressure"]
    elif action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        task = config["consolidation"]
    else:
        state["pending_prompt_attempt_type"] = "independent"
        task = config["fresh"]
    return f"{proof}{task}"


_GD_TRANSFER_MOTIONS = (
    "Should companies use AI in hiring only with human oversight?",
    "Should four-day workweeks become the standard for knowledge-work teams?",
    "Should social-media platforms verify every user identity?",
)


def _next_gd_transfer_motion(state: dict, current_topic: str) -> str:
    context = state.get("career_context") or {}
    excluded_families = {gd_topic_family(current_topic)}
    core_topic = resolve_core_gd_topic(
        state,
        str(state.get("competency_node") or ""),
    )
    if core_topic:
        excluded_families.add(gd_topic_family(core_topic))
    configured = [
        str(topic).strip()
        for topic in (context.get("gd_topics") or context.get("custom_gd_topics") or [])
        if str(topic).strip()
        and gd_topic_family(str(topic).strip()) not in excluded_families
    ]
    if configured:
        return configured[0]
    fallback = next(
        (
            motion for motion in _GD_TRANSFER_MOTIONS
            if gd_topic_family(motion) not in excluded_families
        ),
        "",
    )
    if not fallback:
        raise RuntimeError("no distinct GD transfer topic is available")
    return fallback


def _gd_prompt_topic_for_state(state: dict) -> str:
    return resolve_prompt_gd_topic(state) or "the active motion"


def _gd02_feedback_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "gd_02_support_with_evidence":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    latest = _latest_user_feedback_excerpt(state, limit=170).rstrip(".!?")
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    current_topic = _gd_prompt_topic_for_state(state)

    if not result.get("pass_eligible") or required_missing or blockers:
        if "concrete_evidence" in required_missing:
            repair = "Add one learner-owned example, named-source fact, explicit analogy, or labelled hypothetical"
        elif "clear_stance" in required_missing:
            repair = "State the side you are defending before the evidence"
        elif "topic_relevance" in required_missing:
            repair = f"Tie the contribution directly to the motion: {current_topic}"
        else:
            repair = "Add one sentence explaining why the same evidence supports your stated position"
        return (
            f"{anchor}{repair}. Revise only that missing link using the same evidence and motion; "
            "do not move to a new topic yet."
        )

    next_action = validated_tutor_next_action(plan, state)
    if next_action in {"request_pressure", "request_consolidation"}:
        core = qualified_core_evidence(state, "gd_02_support_with_evidence")
        current_topic = str((core or {}).get("active_topic") or current_topic).strip()
    if next_action == "request_transfer":
        next_topic = _next_gd_transfer_motion(state, current_topic)
        state["pending_prompt_attempt_type"] = "transfer"
        state["pending_gd_prompt_topic"] = next_topic
        task = (
            f'Transfer task. Motion: "{next_topic}" Take a clear side, add one learner-owned '
            "example or named-source fact, and state why that evidence supports the side you chose."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            f'Pressure check on "{current_topic}": another participant says your example proves '
            "correlation, not causation. Defend the claim with the same evidence in two or three sentences."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            f'Consolidation task on "{current_topic}": deliver the stance, evidence, and explicit link '
            "once in no more than three sentences."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            f'Next check on "{current_topic}": keep the same side but use a different learner-owned '
            "example and explain why it supports the claim."
        )
    return f"{anchor}The stance, concrete evidence, and claim link are present. Keep that answer. {task}"


def _gd03_feedback_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "gd_03_take_the_floor":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    latest = _latest_user_feedback_excerpt(state, limit=170).rstrip(".!?")
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    if not result.get("pass_eligible") or required_missing or blockers:
        if "polite_entry_phrase" in required_missing:
            repair = "Open with a short bridge such as 'Building on that point'"
        elif "links_prior_point" in required_missing:
            repair = "Name the specific prior point before adding your view"
        elif "adds_new_value" in required_missing:
            repair = "Add one implication, example, or mitigation after the link"
        else:
            repair = "Claim the floor in one polite sentence, then add one substantive idea"
        return f"{anchor}{repair}. Revise only that entry; keep the same discussion context."

    current_topic = _gd_prompt_topic_for_state(state)
    next_action = validated_tutor_next_action(plan, state)
    if next_action in {"request_pressure", "request_consolidation"}:
        core = qualified_core_evidence(state, "gd_03_take_the_floor")
        current_topic = str((core or {}).get("active_topic") or current_topic).strip()
    if next_action == "request_transfer":
        next_topic = _next_gd_transfer_motion(state, current_topic)
        state["pending_prompt_attempt_type"] = "transfer"
        state["pending_gd_prompt_topic"] = next_topic
        task = (
            f'Transfer task on "{next_topic}": another participant raises a fairness concern. '
            "Enter by linking to that concern, then add one distinct operational implication."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Pressure check: a dominant participant finishes a long point and immediately tries to continue. "
            "Claim the floor politely, link to one part of the point, and add your new contribution."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Consolidation task: enter in one bridge phrase, reference the prior point precisely, "
            "and add one implication in no more than three sentences."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Next mini-discussion: another participant says remote onboarding weakens team culture. "
            "Enter politely, link directly to that concern, and add one concrete mitigation."
        )
    return (
        f"{anchor}You linked to the prior point and added a substantive idea without sounding aggressive. "
        f"Keep that entry. {task}"
    )


def _gd04_feedback_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "gd_04_build_on_others":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    latest = _latest_user_feedback_excerpt(state, limit=170).rstrip(".!?")
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    if not result.get("pass_eligible") or required_missing or blockers:
        if "credits_prior_speaker" in required_missing:
            repair = "Credit the prior contribution before adding your view"
        elif "extends_idea" in required_missing:
            repair = "Add one implication, example, or safeguard that was not already stated"
        elif "topic_relevance" in required_missing:
            repair = "Keep the extension tied to the active motion"
        else:
            repair = "Name the prior point, then extend it with one distinct idea"
        return f"{anchor}{repair}. Revise only that link and extension in the same context."

    current_topic = _gd_prompt_topic_for_state(state)
    next_action = validated_tutor_next_action(plan, state)
    if next_action in {"request_pressure", "request_consolidation"}:
        core = qualified_core_evidence(state, "gd_04_build_on_others")
        current_topic = str((core or {}).get("active_topic") or current_topic).strip()
    if next_action == "request_transfer":
        next_topic = _next_gd_transfer_motion(state, current_topic)
        state["pending_prompt_attempt_type"] = "transfer"
        state["pending_gd_prompt_topic"] = next_topic
        lowered_topic = next_topic.lower()
        if "remote work" in lowered_topic:
            prior_point = "remote work broadens hiring access"
        elif "ai" in lowered_topic and "hiring" in lowered_topic:
            prior_point = "data-driven screening can reduce unconscious bias"
        elif "four-day" in lowered_topic:
            prior_point = "a shorter workweek can improve focus and retention"
        elif "verify" in lowered_topic and "identity" in lowered_topic:
            prior_point = "identity verification can reduce coordinated abuse"
        else:
            prior_point = "the proposal could improve consistency and access"
        task = (
            f'Transfer task on "{next_topic}": another participant says {prior_point}. '
            "Credit that point, then add one limitation or safeguard they missed."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Pressure check: another participant says you merely repeated their idea. Credit the exact "
            "part you used, then state the new implication your contribution adds."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Consolidation task: credit one prior point and extend it with one clear implication "
            "in no more than three sentences."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Next mini-discussion: another participant says remote work widens hiring access. "
            "Credit that point and add one different operational benefit or risk."
        )
    return (
        f"{anchor}You credited the prior point and extended it with a distinct implication. "
        f"Keep that contribution. {task}"
    )


def _gd05_claim_for_topic(topic: str) -> str:
    lowered = topic.lower()
    if "remote work" in lowered:
        return "remote work improves hiring access, so it should always be the default"
    if "ai" in lowered and "hiring" in lowered:
        return "AI screening reduces human bias, so companies should rely on it"
    if "four-day" in lowered:
        return "a shorter workweek improves focus and retention, so every team should adopt it"
    if "verify" in lowered and "identity" in lowered:
        return "identity verification reduces coordinated abuse, so every user should be verified"
    return "the proposal's main benefit outweighs every implementation risk"


def _gd05_feedback_text(state: dict) -> str | None:
    if str(state.get("competency_node") or "") != "gd_05_disagree_respectfully":
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None

    latest = _latest_user_feedback_excerpt(state, limit=170).rstrip(".!?")
    anchor = f'In your answer, you said "{latest}". ' if latest else ""
    required_missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    if not result.get("pass_eligible") or required_missing or blockers:
        if "transfer_context" in required_missing:
            current_topic = _gd_prompt_topic_for_state(state)
            next_topic = _next_gd_transfer_motion(state, current_topic)
            state["pending_prompt_attempt_type"] = "transfer"
            state["pending_gd_prompt_topic"] = next_topic
            claim = _gd05_claim_for_topic(next_topic)
            return (
                f"{anchor}That response stays in the same topic family, so it does not count as transfer evidence. "
                f'Transfer task on "{next_topic}": a participant says {claim}. '
                "Concede one valid benefit, then disagree with a clear topic-based reason."
            )
        if "acknowledges_valid_point" in required_missing:
            repair = "Concede one fair part of the other view before disagreeing"
        elif "clear_counter" in required_missing:
            repair = "State the exact claim you reject after the concession"
        elif "reasoned_basis" in required_missing:
            repair = "Give one topic-based reason for the counterpoint"
        else:
            repair = "Challenge the idea without judging the person"
        return f"{anchor}{repair}. Revise only that disagreement in the same context."

    current_topic = _gd_prompt_topic_for_state(state)
    next_action = validated_tutor_next_action(plan, state)
    if next_action in {"request_pressure", "request_consolidation"}:
        core = qualified_core_evidence(state, "gd_05_disagree_respectfully")
        current_topic = str((core or {}).get("active_topic") or current_topic).strip()
    if next_action == "request_transfer":
        next_topic = _next_gd_transfer_motion(state, current_topic)
        state["pending_prompt_attempt_type"] = "transfer"
        state["pending_gd_prompt_topic"] = next_topic
        claim = _gd05_claim_for_topic(next_topic)
        task = (
            f'Transfer task on "{next_topic}": a participant says {claim}. '
            "Concede one valid benefit, then disagree with a clear topic-based reason."
        )
    elif next_action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Pressure check: the participant says your concession undermines your disagreement. "
            "Explain why the conceded benefit is real but does not outweigh your counterpoint."
        )
    elif next_action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Consolidation task: concede one valid point, state the counter, and give one reason "
            "in no more than three sentences."
        )
    else:
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        task = (
            "Next mini-discussion: a participant says human oversight makes AI hiring fully safe. "
            "Concede what oversight improves, then disagree with one remaining risk."
        )
    return (
        f"{anchor}You conceded a valid point, stated a clear counter, and gave a topic-based reason "
        f"without attacking the speaker. Keep that structure. {task}"
    )


_LATE_GD_LABELS: dict[str, dict[str, str]] = {
    "gd_06_balanced_view": {
        "names_both_sides": "state one valid point on each side",
        "weighs_tradeoff": "say which trade-off is decisive and why",
        "returns_to_position": "land on one clear recommendation",
        "topic_relevance": "keep both sides tied to the stated motion",
    },
    "gd_07_steer_back": {
        "identifies_derailment": "flag the drift neutrally",
        "redirects_to_topic": "restate the actual motion or decision",
        "gives_next_step": "offer one useful angle for the group to examine next",
        "non_controlling_tone": "facilitate without ordering the group around",
    },
    "gd_08_include_quiet": {
        "names_quiet_participant": "address the quieter participant directly",
        "topic_linked_invite": "connect the invitation to the active motion",
        "respectful_floor_give": "give them the floor naturally",
        "non_pressuring_tone": "invite without embarrassing or forcing them",
    },
    "gd_09_manage_dominator": {
        "acknowledges_contribution": "credit the speaker's useful point",
        "redistributes_floor": "create explicit room for another participant or the group",
        "topic_link": "tie the boundary to the active motion",
        "respectful_boundary": "set the limit without sounding personal or rude",
    },
    "gd_10_drive_consensus": {
        "summarizes_key_points": "summarize at least two distinct points raised",
        "identifies_common_ground": "name the group's shared ground",
        "proposes_next_step": "propose one concrete recommendation or decision rule",
        "balanced_credit": "credit the group's contributions, not only your own view",
    },
}

_LATE_GD_COMMON_LABELS = {
    "core_consistency": "keep the harder response consistent with the position you already qualified",
    "transfer_context": "apply the skill to a genuinely different motion",
}

_LATE_GD_FEEDBACK_CRITERIA: dict[str, tuple[tuple[str, str], ...]] = {
    "gd_06_balanced_view": (
        ("weighs_tradeoff", "You identified the decisive trade-off"),
        ("returns_to_position", "You returned to a clear recommendation"),
        ("names_both_sides", "You stated a valid point on each side"),
        ("topic_relevance", "You kept both sides tied to the motion"),
    ),
    "gd_07_steer_back": (
        ("gives_next_step", "You gave the group a concrete next step"),
        ("redirects_to_topic", "You restated the active motion"),
        ("identifies_derailment", "You flagged the drift neutrally"),
        ("non_controlling_tone", "You kept the redirect facilitative"),
    ),
    "gd_08_include_quiet": (
        ("topic_linked_invite", "You linked the invitation to the active motion"),
        ("respectful_floor_give", "You gave the quieter participant the floor"),
        ("non_pressuring_tone", "You made the invitation optional"),
        ("names_quiet_participant", "You addressed the quieter participant directly"),
    ),
    "gd_09_manage_dominator": (
        ("redistributes_floor", "You redistributed the floor explicitly"),
        ("respectful_boundary", "You set a respectful speaking boundary"),
        ("topic_link", "You tied the turn-sharing boundary to the motion"),
        ("acknowledges_contribution", "You credited the speaker's useful point"),
    ),
    "gd_10_drive_consensus": (
        ("proposes_next_step", "You proposed a concrete way forward"),
        ("identifies_common_ground", "You named the common ground"),
        ("summarizes_key_points", "You summarized the two positions distinctly"),
        ("balanced_credit", "You credited the group's contributions"),
    ),
}


def _late_gd_task(node_id: str, stage: str, topic: str) -> str:
    quoted_topic = f'"{topic}"'
    tasks = {
        "gd_06_balanced_view": {
            "fresh": f"Next mini-discussion on {quoted_topic}: use a different trade-off, state the strongest point on each side, then decide which side outweighs the other and why.",
            "transfer": f"Transfer motion: {quoted_topic} State one fair benefit and one serious risk, weigh the decisive trade-off, and land on a recommendation.",
            "pressure": f"Pressure check on {quoted_topic}: another participant calls your position fence-sitting. Defend why acknowledging both sides still leads to one clear recommendation.",
            "consolidation": f"Consolidation on {quoted_topic}: give both sides, the decisive trade-off, and your final position in no more than three sentences.",
        },
        "gd_07_steer_back": {
            "fresh": f"On {quoted_topic}, the group drifts into personal preferences. Flag the drift, restate the motion, and offer one decision-relevant angle to examine next.",
            "transfer": f"Transfer motion: {quoted_topic} The panel has drifted into an unrelated example. Redirect it neutrally to this motion and propose the next useful question.",
            "pressure": f"Pressure check on {quoted_topic}: a participant ignores your first redirect. Re-centre the group firmly but respectfully and name the next useful angle.",
            "consolidation": f"Consolidation on {quoted_topic}: flag the drift, restate the motion, and give the next discussion step in two concise sentences.",
        },
        "gd_08_include_quiet": {
            "fresh": f"On {quoted_topic}, Maya has not spoken after two strong voices. Link her perspective to one unresolved angle and invite her without putting her on the spot.",
            "transfer": f"Transfer motion: {quoted_topic} Dev has not entered the discussion. Connect a useful lens to the motion and give him the floor naturally.",
            "pressure": f"Pressure check on {quoted_topic}: Maya says she has nothing new to add. Invite one specific lens while making it safe for her to pass.",
            "consolidation": f"Consolidation on {quoted_topic}: address Maya directly, link her invitation to one unresolved point, make it safe to decline, and yield the floor in two sentences.",
        },
        "gd_09_manage_dominator": {
            "fresh": f"On {quoted_topic}, Rohan interrupts and repeats the same argument. Credit its useful part, set a calm boundary, and open the floor to another perspective.",
            "transfer": f"Transfer motion: {quoted_topic} A dominant participant takes another long turn. Acknowledge the point, redistribute the floor, and keep the group on the motion.",
            "pressure": f"Pressure check on {quoted_topic}: the speaker says they need more time to finish. Acknowledge their useful point, hold the boundary respectfully, tie the turn-sharing need to the motion, and name whose perspective the group needs next.",
            "consolidation": f"Consolidation on {quoted_topic}: acknowledge the contribution, set the boundary, and redistribute the floor in two concise sentences.",
        },
        "gd_10_drive_consensus": {
            "fresh": f"On {quoted_topic}, Maya says the evidence supports the motion; Dev says the evidence is too mixed to accept it without qualification. Summarize both positions, name their shared need for a reliable decision standard, and propose one next step.",
            "transfer": f"Transfer motion: {quoted_topic} Maya says the evidence supports the motion; Dev says it is too mixed to accept without qualification. Summarize both, identify their shared demand for reliable evidence, and propose a concrete decision rule.",
            "pressure": f"Pressure check on {quoted_topic}: Dev rejects the emerging consensus because the evidence remains uncertain. Credit that concern, restate Maya's support and Dev's qualification plus their common ground, then refine the decision rule.",
            "consolidation": f"Final synthesis on {quoted_topic}: credit both sides, state the common ground, and close with one recommendation in three sentences.",
        },
    }
    return tasks[node_id][stage]


def _late_gd_feedback_text(state: dict) -> str | None:
    if state.get("task_type") != "gd_prep":
        return None
    node_id = str(state.get("competency_node") or "")
    labels = _LATE_GD_LABELS.get(node_id)
    if not labels:
        return None
    result = state.get("last_rubric_result")
    plan = state.get("tutor_turn_plan")
    if not isinstance(result, dict) or not isinstance(plan, dict):
        return None
    learner_answer = str(state.get("user_input") or "")
    missing = [str(item) for item in (result.get("required_missing") or [])]
    blockers = [str(item) for item in (result.get("blockers") or [])]
    ineligible_criteria = set(missing)
    ineligible_criteria.update(
        blocker.removeprefix("missing_required:")
        for blocker in blockers
        if blocker.startswith("missing_required:")
    )
    met_rows: dict[str, dict] = {}
    for row in result.get("criteria") or []:
        if not isinstance(row, dict) or row.get("met") is not True:
            continue
        criterion_id = str(row.get("id") or row.get("criterion_id") or "").strip()
        if criterion_id and criterion_id not in ineligible_criteria:
            met_rows.setdefault(criterion_id, row)

    criterion_feedback = _LATE_GD_FEEDBACK_CRITERIA[node_id]
    priority = tuple(item[0] for item in criterion_feedback)
    acknowledgements = dict(criterion_feedback)
    selected_id = next((item for item in priority if item in met_rows), None)
    evidence_quote = ""
    for criterion_id in priority:
        row = met_rows.get(criterion_id)
        if row is None:
            continue
        quote = _grounded_display_evidence(
            learner_answer,
            str(row.get("evidence_quote") or ""),
            220,
        )
        if quote:
            selected_id = criterion_id
            evidence_quote = quote
            break
    acknowledgement = acknowledgements.get(selected_id or "", "")
    if acknowledgement and evidence_quote:
        sentence_end = "" if evidence_quote.endswith((".", "!", "?")) else "."
        anchor = f'{acknowledgement}: "{evidence_quote}"{sentence_end} '
    elif acknowledgement:
        anchor = f"{acknowledgement}. "
    else:
        anchor = ""
    attempt_type = str(result.get("attempt_type") or "independent")
    current_topic = _gd_prompt_topic_for_state(state)
    if not result.get("pass_eligible") or missing or blockers:
        if "transfer_context" in missing:
            core_topic = resolve_core_gd_topic(state, node_id) or current_topic
            known_families = {
                "ai_hiring",
                "remote_work",
                "four_day_workweek",
                "social_identity",
                "digital_payments",
            }
            if (
                gd_topic_family(core_topic) not in known_families
                and gd_topic_family(current_topic) in known_families
            ):
                core_topic = current_topic
            next_topic = _next_gd_transfer_motion(state, core_topic)
            state["pending_prompt_attempt_type"] = "transfer"
            state["pending_gd_prompt_topic"] = next_topic
            return (
                f"{anchor}That contribution repeats the core topic family, so it does not prove transfer. "
                f"{_late_gd_task(node_id, 'transfer', next_topic)}"
            )
        state["pending_prompt_attempt_type"] = (
            attempt_type if attempt_type in {"transfer", "pressure"} else "independent"
        )
        gap_labels = {**_LATE_GD_COMMON_LABELS, **labels}
        gaps = [gap_labels[item] for item in missing if item in gap_labels]
        gap = "; and ".join(gaps) or "complete the active discussion move on the stated motion"
        return f"{anchor}The missing move is to {gap}. Revise only that part; do not change motions yet."

    action = validated_tutor_next_action(plan, state)
    if action in {"request_pressure", "request_consolidation"}:
        core = qualified_core_evidence(state, node_id)
        current_topic = str((core or {}).get("active_topic") or current_topic).strip()
    if action == "request_transfer":
        current_topic = _next_gd_transfer_motion(state, current_topic)
        state["pending_prompt_attempt_type"] = "transfer"
        state["pending_gd_prompt_topic"] = current_topic
        stage = "transfer"
    elif action == "request_pressure":
        state["pending_prompt_attempt_type"] = "pressure"
        state["pending_gd_prompt_topic"] = current_topic
        stage = "pressure"
    elif action == "request_consolidation":
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        stage = "consolidation"
    else:
        state["pending_prompt_attempt_type"] = "independent"
        state["pending_gd_prompt_topic"] = current_topic
        stage = "fresh"
    return f"{anchor}{_late_gd_task(node_id, stage, current_topic)}"


def _looks_incomplete_coach_text(text: str) -> bool:
    clean = " ".join(str(text or "").split())
    if not clean:
        return True
    if clean.endswith(("...", "…")):
        return True
    if _INCOMPLETE_COACH_END_RE.search(clean):
        return True
    return clean[-1] not in ".!?)]}\"'"


def _deterministic_coach_repair_text(state: dict) -> str:
    node_id = str(state.get("competency_node") or "")
    if node_id == "int_03_weakness_framing":
        return _weakness_next_challenge_text(state)
    if node_id == "int_02_strength_with_evidence":
        return (
            "Keep the strength you named. Rewrite the answer with one learner-owned situation, "
            "the action you personally took, and the observable result."
        )
    if node_id == "gd_08_include_quiet":
        return (
            "Address the assigned quieter participant by name, connect one unresolved angle to "
            "the motion, yield the floor naturally, and make it safe to decline."
        )
    if node_id == "gd_10_drive_consensus":
        return (
            "Attribute both assigned positions fairly, preserve their real disagreement, name only "
            "the common ground both support, and propose one decision rule or next step."
        )
    if node_id.startswith("int_"):
        return (
            "Use your answer as the base; now make the strongest evidence easier to hear. "
            "Rewrite it once with a clear situation, your action, and the result in your own words."
        )
    if node_id.startswith("gd_"):
        topic = _gd_topic_phrase_for_state(state)
        topic_clause = f" on {topic}" if topic else ""
        return (
            f"Keep the answer grounded in the motion; now make it sound like a group-discussion contribution{topic_clause}. "
            "Give one clear stance, one reason, and one bridge to another participant's concern."
        )
    return "Use your answer as the base; now tighten it into one clear version in your own words."


def _sanitize_coaching_response(text: str, state: dict, spec_kind: str) -> str:
    """Deterministically clean coaching text for weak/borderline turns.

    Prompt directives reduce the chance of inflated praise/model answers, but
    the local model can still emit them. For turns that have not earned a strong
    score, buffer and clean the full response before showing it.
    """
    if (
        state.get("task_type") not in _TEST_TASK_TYPES
        and spec_kind in _COACHING_STREAM_KINDS
    ):
        existing_plan = state.get("tutor_turn_plan")
        int01_decision = int01_decision_for_planned_action(
            state.get("last_rubric_result"),
            state,
            existing_plan if isinstance(existing_plan, dict) else {},
        )
        if int01_decision is not None:
            state["pending_prompt_attempt_type"] = int01_decision.attempt_type
            return int01_decision.visible_text
        early_interview_followup = _early_interview_feedback_text(state)
        if early_interview_followup is not None:
            return early_interview_followup
        star_followup = _clean_star_pass_followup_text(state)
        if star_followup is not None:
            return star_followup
        why_company_followup = _int05_feedback_text(state)
        if why_company_followup is not None:
            return why_company_followup
        failure_story_followup = _int06_feedback_text(state)
        if failure_story_followup is not None:
            return failure_story_followup
        clarification_followup = _int07_feedback_text(state)
        if clarification_followup is not None:
            return clarification_followup
        quantified_impact_followup = _int08_feedback_text(state)
        if quantified_impact_followup is not None:
            return quantified_impact_followup
        late_interview_followup = _late_interview_feedback_text(state)
        if late_interview_followup is not None:
            return late_interview_followup
        gd_evidence_followup = _gd02_feedback_text(state)
        if gd_evidence_followup is not None:
            return gd_evidence_followup
        gd_entry_followup = _gd03_feedback_text(state)
        if gd_entry_followup is not None:
            return gd_entry_followup
        gd_build_followup = _gd04_feedback_text(state)
        if gd_build_followup is not None:
            return gd_build_followup
        gd_disagree_followup = _gd05_feedback_text(state)
        if gd_disagree_followup is not None:
            return gd_disagree_followup
        late_gd_followup = _late_gd_feedback_text(state)
        if late_gd_followup is not None:
            return late_gd_followup

    if (
        state.get("task_type") == "interview_prep"
        and str(state.get("user_input") or "").strip()
    ):
        grounded_context = " ".join((
            str(state.get("user_input") or ""),
            str(state.get("career_context") or ""),
        )).lower()
        grounded_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", grounded_context))
        unsupported_numbers = [
            token for token in re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
            if token.lower() not in grounded_numbers
        ]
        claimed_entities = set(re.findall(
            r"(?:^|[.!?]\s+)([A-Z][A-Za-z0-9&.-]{2,})\s+"
            r"(?:reported|lost|cut|reduced|increased|achieved|launched|built|grew|saved|"
            r"published|redesigned|tracks|uses)\b",
            text,
        ))
        claimed_entities.update(re.findall(
            r"\b(?:at|for|with|from|inside)\s+([A-Z][A-Za-z0-9&.-]{2,})\b",
            text,
        ))
        unsupported_entities = [
            entity for entity in claimed_entities
            if entity.lower() not in grounded_context
        ]
        if unsupported_numbers or unsupported_entities:
            return _deterministic_coach_repair_text(state)

    cleaned = _sanitize_coaching_opening_praise(text, state, spec_kind)
    if not _needs_full_coaching_sanitize(state, spec_kind):
        cleaned = _sanitize_repeated_outcome_gap(cleaned, state, spec_kind)
        cleaned = _sanitize_repeated_weakness_gap(cleaned, state, spec_kind)
        cleaned = _sanitize_repeated_future_goal_gap(cleaned, state, spec_kind)
        cleaned = _sanitize_unrelated_career_sample_domain(cleaned, state, spec_kind)
        return _ensure_career_feedback_anchor(
            _sanitize_gd_topic_drift(cleaned, state),
            state,
            spec_kind,
        )
    cleaned = _COPYABLE_SCENARIO_RE.sub(" ", cleaned, count=1)
    if str(state.get("competency_node") or "").startswith("gd_"):
        cleaned = _COPYABLE_IMAGINE_RE.sub(" ", cleaned, count=1)
    cleaned = _COPYABLE_MODEL_ANSWER_RE.sub(" Keep it in your own words.", cleaned, count=1)
    cleaned = _COPYABLE_EXAMPLE_RE.sub(
        " Keep it in your own words.",
        cleaned,
        count=1,
    )
    cleaned = _INFLATED_PRAISE_FRAGMENT_RE.sub(" ", cleaned, count=1)
    cleaned = _sanitize_gd_topic_drift(cleaned, state)
    cleaned = _sanitize_repeated_outcome_gap(cleaned, state, spec_kind)
    cleaned = _sanitize_repeated_weakness_gap(cleaned, state, spec_kind)
    cleaned = _sanitize_repeated_future_goal_gap(cleaned, state, spec_kind)
    cleaned = _sanitize_unrelated_career_sample_domain(cleaned, state, spec_kind)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return _ensure_career_feedback_anchor(cleaned, state, spec_kind)



def _bridge_full_answer_task(state: dict) -> str:
    node_id = str(state.get("competency_node") or "")
    topic = _gd_topic_phrase_for_state(state)
    participant_claims = (
        (state.get("active_task_contract") or {}).get("participant_claims")
        if isinstance(state.get("active_task_contract"), dict)
        else []
    )
    quiet_name = next((
        str(claim.get("display_name") or claim.get("participant_id") or "").strip()
        for claim in (participant_claims or [])
        if isinstance(claim, dict)
        and str(claim.get("status") or claim.get("role") or "").casefold() == "quiet"
    ), "Maya")
    gd_tasks = {
        "gd_06_balanced_view": (
            "state one valid point on each side, explain the decisive trade-off, "
            "and land on one clear recommendation"
        ),
        "gd_07_steer_back": (
            "flag the drift neutrally, restate the actual motion, and offer one "
            "useful angle for the group to examine next"
        ),
        "gd_08_include_quiet": (
            f"address {quiet_name} directly, link the invitation to one unresolved "
            "topic angle, and yield the floor without pressure"
        ),
        "gd_09_manage_dominator": (
            "acknowledge the speaker's useful point, set a respectful boundary, "
            "and redistribute the floor while staying on topic"
        ),
        "gd_10_drive_consensus": (
            "summarize Maya's view that the evidence supports the motion and Dev's view that it "
            "remains too mixed, name their shared demand for reliable evidence, and propose one "
            "concrete decision rule"
        ),
    }
    if node_id in gd_tasks:
        topic_clause = f" on {topic}" if topic else ""
        return (
            f"Now build back to the full skill{topic_clause}: "
            f"{gd_tasks[node_id]}."
        )
    if node_id.startswith("gd_") and topic:
        return (
            f"Now build back to the full skill: write one clear GD contribution on "
            f"{topic} that commits to a side and adds one concrete safeguard or reason."
        )
    if node_id == "int_09_diplomatic_pushback":
        return (
            "Now build back to the full skill: acknowledge one fair part of the "
            "interviewer's premise, state your counter-position, tie it to one requirement "
            "or trade-off, and keep the tone collaborative."
        )
    if node_id == "int_02_strength_with_evidence":
        return (
            "Now build back to the full skill: name the strength, give one learner-owned situation, "
            "state the action you personally took, and finish with the observable result."
        )
    if node_id == "int_10_close_strong":
        return (
            "Now build back to the full skill: ask one substantive role or team question "
            "and add one confident sentence about the specific value you would bring."
        )
    if node_id == "int_11_salary_negotiation":
        return (
            "Now build back to the full skill: give one salary range, justify it with "
            "market or role-value evidence, and state one flexible package option without apologizing."
        )
    if node_id == "int_12_explain_a_gap":
        return (
            "Now build back to the full skill: give the brief reason, what you did or learned, "
            "and why you are ready for the next role without blaming anyone."
        )
    if node_id.startswith("int_"):
        return (
            "Now build back to the full skill: answer the interview prompt in your "
            "own story with a clear action and result."
        )
    return "Now build back to the full skill in one clear answer using your own words."


def _deterministic_closed_bridge_feedback(state: dict) -> str:
    """Give fast, bounded feedback after a closed bridge answer.

    Fill-blank and MCQ bridges are already graded by answer key. Calling the model
    again here adds latency and can reintroduce generic examples, so same-node
    closed-bridge follow-up text stays deterministic.
    """
    if not state.get("last_graded_bridge"):
        return ""
    score = _recent_score_for_tone(state)
    if isinstance(score, (int, float)) and score >= PASS_SCORE:
        return (
            "Good, that scaffolded step is in place - not the whole skill yet. "
            f"{_bridge_full_answer_task(state)}"
        )

    diagnosis = state.get("last_diagnosis") or {}
    gap = str(diagnosis.get("next_focus") or "use the target move more clearly").strip()
    return (
        "Let's tighten this scaffold. "
        f"The missing move is: {gap}. "
        f"{_bridge_full_answer_task(state)}"
    )


async def _stream_coaching_generation(spec: GenSpec, state: dict) -> AsyncIterator[str]:
    """Stream a generation while sanitizing only the opening praise prefix."""
    if (
        state.get("task_type") in _TEST_TASK_TYPES
        or spec.kind not in _COACHING_STREAM_KINDS
    ):
        async for tok in stream_generation(spec):
            yield tok
        return

    node_id = str(state.get("competency_node") or "")
    professional_prep_node = node_id.startswith("int_") or node_id.startswith("gd_")
    if professional_prep_node or _needs_full_coaching_sanitize(state, spec.kind):
        full: list[str] = []
        async for tok in stream_generation(spec):
            full.append(tok)
        text = _sanitize_coaching_response("".join(full), state, spec.kind)
        if _looks_incomplete_coach_text(text):
            text = _deterministic_coach_repair_text(state)
        if text:
            yield text
        return

    buffer = ""
    emitted_prefix = False
    async for tok in stream_generation(spec):
        if emitted_prefix:
            yield tok
            continue
        buffer += tok
        if len(buffer) >= 180 or re.search(r"[.!?]\s", buffer):
            yield _sanitize_coaching_opening_praise(buffer, state, spec.kind)
            emitted_prefix = True
    if buffer and not emitted_prefix:
        yield _sanitize_coaching_opening_praise(buffer, state, spec.kind)

# session_id -> TutorState dict
SessionStore: dict[str, dict] = {}

# E24 fix: per-session lock so concurrent turns on ONE session serialize their
# read-modify-write of canonical state (race corrupts messages/counters).
# Per-session, NOT global — different sessions still run concurrently.
_SESSION_LOCKS: dict[str, asyncio.Lock] = {}


def _lock_for(session_id: str) -> asyncio.Lock:
    lock = _SESSION_LOCKS.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _SESSION_LOCKS[session_id] = lock
    return lock

# Keys that are transient within a single turn and must NOT be persisted:
# `pending` holds a GenSpec (a frozen dataclass, not JSON-serializable, and only
# meaningful for the in-flight stream). `pending_game` holds a FillBlankGame dict
# for scaffold turns — consumed this turn, never written to disk. `last_selection`
# is the Spec B selector's read of the most recent advance (action/band/rationale),
# meaningful only for the current turn's adaptation cues — not persisted.
_TRANSIENT_KEYS = (
    "pending",
    "pending_game",
    "pending_prompt_attempt_type",
    "pending_gd_prompt_topic",
    "last_evaluated_task_contract",
    "last_selection",
    "_prepared_session_record",
)


def _stage_pending_prompt_attempt_type(state: dict, previous_active: str | None) -> None:
    """Keep the evaluated prompt active until its replacement is committed."""
    if (
        state.get("pending_prompt_attempt_type") is None
        and previous_active in {"independent", "transfer", "pressure"}
    ):
        state["pending_prompt_attempt_type"] = previous_active
    if state.get("pending_prompt_attempt_type") is not None:
        state["active_prompt_attempt_type"] = previous_active


def _commit_pending_prompt_attempt_type(state: dict) -> None:
    pending = state.get("pending_prompt_attempt_type")
    if pending is not None:
        state["active_prompt_attempt_type"] = pending
    pending_topic = state.get("pending_gd_prompt_topic")
    if pending_topic:
        state["active_gd_prompt_topic"] = pending_topic
    state["pending_prompt_attempt_type"] = None
    state["pending_gd_prompt_topic"] = None


def _store_path() -> str:
    """Local disk session snapshots are disabled by product policy."""
    return ""


def save_sessions() -> None:
    """Snapshot the in-memory store to disk (atomic). No-op if disabled.

    Durability fix #1: lets live sessions survive a process restart. Transient
    keys are stripped; everything else in TutorState is JSON-serializable."""
    path = _store_path()
    if not path:
        return
    snapshot = {
        sid: {k: v for k, v in state.items() if k not in _TRANSIENT_KEYS}
        for sid, state in SessionStore.items()
    }
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(snapshot, f)
    os.replace(tmp, path)  # atomic on POSIX — no half-written store on crash


def load_sessions() -> None:
    """Restore the store from disk. No-op if disabled or the file is absent."""
    path = _store_path()
    if not path or not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for state in data.values():
        for k in _TRANSIENT_KEYS:
            state.setdefault(k, None)   # restore transient keys stripped at save
    SessionStore.update(data)


def _json_safe(value):
    """Return a JSON-safe deep copy for runtime snapshots."""
    return json.loads(json.dumps(value, default=str))


def _runtime_snapshot(state: dict) -> dict:
    snapshot = {
        k: v for k, v in state.items()
        if k not in _TRANSIENT_KEYS
    }
    return _json_safe(snapshot)


async def _persist_runtime_state(state: dict) -> None:
    """Persist live session state to the product store.

    SessionStore remains a process cache; this is the durable truth used for
    reload, restart, multi-worker reads, and recovery.
    """
    store = get_storage()
    if not hasattr(store, "upsert_session_runtime"):
        save_sessions()
        return
    snapshot = _runtime_snapshot(state)
    await store.upsert_session_runtime(
        session_id=state["session_id"],
        user_id=state["user_id"],
        current_node=state["competency_node"],
        module_id=module_of(state["competency_node"]),
        task_type=state.get("task_type"),
        test_mode=state.get("task_type") in _TEST_TASK_TYPES,
        status=state.get("status", "active"),
        state_snapshot=snapshot,
        pending_transition=state.get("pending_node_transition"),
        session_version=int(state.get("session_version") or 1),
        active_turn_id=state.get("active_turn_id"),
        active_opening_id=state.get("active_opening_id"),
        last_error=state.get("last_error"),
    )
    if hasattr(store, "replace_session_messages"):
        await store.replace_session_messages(
            state["session_id"],
            list(snapshot.get("messages") or []),
        )
    save_sessions()


def _prepared_session_record(state: dict) -> dict:
    prepared = state.get("_prepared_session_record")
    if isinstance(prepared, dict):
        return dict(prepared)
    node_id = state["competency_node"]
    task_type = str(state.get("task_type") or task_type_of(node_id).value)
    return {
        "session_id": state["session_id"],
        "user_id": state["user_id"],
        "task_type": task_type,
        "module_id": str(state.get("module_id") or module_of(node_id)),
        "node_id": node_id,
        "test_mode": task_type in _TEST_TASK_TYPES,
        "career_context": dict(state.get("career_context") or {}),
        "scenario_config": dict(state.get("scenario_config") or {}),
        "persona_roster": list(state.get("personas") or []),
        "context_hash": str(state.get("context_hash") or "default"),
    }


def _prepared_runtime_record(state: dict) -> dict:
    snapshot = _runtime_snapshot(state)
    return {
        "session_id": state["session_id"],
        "user_id": state["user_id"],
        "current_node": state["competency_node"],
        "module_id": str(state.get("module_id") or module_of(state["competency_node"])),
        "task_type": state.get("task_type"),
        "test_mode": state.get("task_type") in _TEST_TASK_TYPES,
        "status": state.get("status", "active"),
        "state_snapshot": snapshot,
        "pending_transition": state.get("pending_node_transition"),
        "session_version": int(state.get("session_version") or 1),
        "active_turn_id": state.get("active_turn_id"),
        "active_opening_id": state.get("active_opening_id"),
        "last_error": state.get("last_error"),
    }


async def commit_prepared_session(state: dict) -> None:
    """Persist a prepared session for trusted internal callers."""
    store = get_storage()
    record = _prepared_session_record(state)
    await store.create_session(
        record["session_id"],
        record["user_id"],
        record["task_type"],
        record["module_id"],
        record["node_id"],
        test_mode=record["test_mode"],
        career_context=record["career_context"],
        scenario_config=record["scenario_config"],
        persona_roster=record["persona_roster"],
        context_hash=record["context_hash"],
    )
    SessionStore[state["session_id"]] = state
    await _persist_runtime_state(state)


async def commit_claimed_prepared_session(
    state: dict,
    *,
    client_start_id: str,
    claim_generation: int,
    response_json: dict,
) -> bool:
    """Atomically publish a prepared session only for the current start owner."""
    store = get_storage()
    if not hasattr(store, "commit_claimed_session_start"):
        raise RuntimeError("storage_missing_claimed_session_commit")
    runtime = _prepared_runtime_record(state)
    committed = await store.commit_claimed_session_start(
        user_id=state["user_id"],
        client_start_id=client_start_id,
        claim_generation=claim_generation,
        session_record=_prepared_session_record(state),
        runtime_record=runtime,
        messages=list(runtime["state_snapshot"].get("messages") or []),
        response_json=response_json,
    )
    if committed:
        SessionStore[state["session_id"]] = state
        save_sessions()
    return bool(committed)


async def _record_opening_attempt(state: dict) -> None:
    """Persist the billing/attempt ledger once the learner can use the session."""
    store = get_storage()
    if not hasattr(store, "record_node_attempt"):
        return
    await store.record_node_attempt(
        state["session_id"],
        state["user_id"],
        state["competency_node"],
        float(state.get("current_mastery") or 0.0),
    )


async def _mark_committed_opening_replayed(state: dict, opening_key: str) -> None:
    """Replay a committed opening without leaving the session input-blocked."""
    await _record_opening_attempt(state)
    state["opening_streamed"] = True
    pending_transition = state.get("pending_node_transition")
    if isinstance(pending_transition, dict) and pending_transition.get("transition_id") == opening_key:
        pending_transition["status"] = "committed"
        state["pending_node_transition"] = None
    if state.get("status", "active") == "active" and not state.get("pending_node_transition"):
        state["input_allowed"] = True
        state["block_reason"] = None
    await _persist_runtime_state(state)


def _hydrate_runtime_state(row: dict) -> dict:
    snapshot = dict(row.get("state_snapshot") or {})
    state = _new_state(
        row["user_id"],
        row["session_id"],
        row.get("current_node") or snapshot.get("competency_node"),
        snapshot.get("memory_context") or [],
        learner_name=snapshot.get("learner_name", ""),
        weakness_context=snapshot.get("weakness_context") or [],
        task_type=row.get("task_type") or snapshot.get("task_type", ""),
        module_id=row.get("module_id") or snapshot.get("module_id") or "",
        sim_topic=snapshot.get("sim_topic", ""),
        career_context=snapshot.get("career_context") or {},
        scenario_config=snapshot.get("scenario_config") or {},
        personas=snapshot.get("personas"),
        context_hash=snapshot.get("context_hash", "default"),
    )
    state.update(copy.deepcopy(snapshot))
    state["session_id"] = row["session_id"]
    state["user_id"] = row["user_id"]
    state["competency_node"] = row.get("current_node") or state["competency_node"]
    state["task_type"] = row.get("task_type") or state.get("task_type", "")
    state["module_id"] = row.get("module_id") or state.get("module_id") or _module_id_for_state(state["competency_node"])
    state["status"] = row.get("status") or state.get("status", "active")
    state["pending_node_transition"] = (
        row.get("pending_transition")
        if row.get("pending_transition") is not None
        else state.get("pending_node_transition")
    )
    state["session_version"] = int(row.get("session_version") or state.get("session_version") or 1)
    state.setdefault("committed_openings", {})
    state.setdefault("messages", [])
    for key in _TRANSIENT_KEYS:
        state[key] = None
    return state


async def get_session_state(session_id: str) -> dict | None:
    state = SessionStore.get(session_id)
    if state is not None:
        if _expire_state_if_needed(state):
            await _persist_runtime_state(state)
        return state
    store = get_storage()
    if not hasattr(store, "get_session_runtime"):
        return None
    row = await store.get_session_runtime(session_id)
    if not row:
        return None
    state = _hydrate_runtime_state(row)
    if _expire_state_if_needed(state):
        await _persist_runtime_state(state)
    SessionStore[session_id] = state
    return state


def _runtime_freshness(value: object) -> float:
    if value is None:
        return 0.0
    timestamp = getattr(value, "timestamp", None)
    if callable(timestamp):
        return float(timestamp())
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


async def get_resumable_active_session_for_start(
    user_id: str,
    node_id: str,
    *,
    test_mode: bool = False,
) -> tuple[str, dict] | None:
    """Return an active same-user/node/mode session for idempotent start/resume."""
    if node_id not in all_node_ids():
        return None
    task_type = task_type_of(node_id, test_mode=test_mode).value
    candidates: list[tuple[dict, float]] = []
    for session_id, state in list(SessionStore.items()):
        if (
            state.get("user_id") == user_id
            and state.get("competency_node") == node_id
            and state.get("task_type") == task_type
            and state.get("status", "active") == "active"
            and not state.get("session_over")
        ):
            if _expire_state_if_needed(state):
                await _persist_runtime_state(state)
                continue
            candidates.append((state, _runtime_freshness(state.get("last_seen_at"))))

    store = get_storage()
    if hasattr(store, "get_active_session_runtime_for_node"):
        row = await store.get_active_session_runtime_for_node(
            user_id,
            node_id,
            task_type,
            bool(test_mode),
        )
        if row:
            state = _hydrate_runtime_state(row)
            if not state.get("session_over"):
                if _expire_state_if_needed(state):
                    await _persist_runtime_state(state)
                else:
                    candidates.append((state, _runtime_freshness(row.get("updated_at"))))

    if not candidates:
        return None
    newest_by_session: dict[str, tuple[dict, float]] = {}
    for state, updated_at in candidates:
        session_id = str(state.get("session_id") or "")
        current = newest_by_session.get(session_id)
        if session_id and (current is None or updated_at >= current[1]):
            newest_by_session[session_id] = (state, updated_at)
    state, _updated_at = max(newest_by_session.values(), key=lambda item: item[1])
    SessionStore[state["session_id"]] = state
    return state["session_id"], state


async def handoff_transition_to_session(
    source_session_id: str,
    source_transition_id: str,
    target_session_id: str,
    target_node_id: str,
    user_id: str,
    *,
    same_skill_reattempt: bool = False,
) -> None:
    """Close a completed source after its next skill or same-skill drill starts."""
    state = await get_session_state(source_session_id)
    if state is None or state.get("user_id") != user_id:
        raise ValueError("source_session_not_found")

    prior_handoff = state.get("last_handed_off_transition")
    if (
        isinstance(prior_handoff, dict)
        and prior_handoff.get("transition_id") == source_transition_id
        and prior_handoff.get("handoff_session_id") == target_session_id
        and state.get("handoff_session_id") == target_session_id
    ):
        await _persist_runtime_state(state)
        await get_storage().end_session(
            source_session_id,
            final_summary=(
                f"Practice continued in session {target_session_id}."
                if same_skill_reattempt
                else f"Next skill continued in session {target_session_id}."
            ),
            avg_score=float(state.get("current_mastery") or 0.0),
        )
        return

    pending = state.get("pending_node_transition")
    if not isinstance(pending, dict):
        raise ValueError("source_transition_missing")
    if pending.get("transition_id") != source_transition_id:
        raise ValueError("source_transition_mismatch")
    expected_target = (
        pending.get("from_node")
        if same_skill_reattempt
        else pending.get("to_node")
    )
    if expected_target != target_node_id:
        raise ValueError("source_transition_target_mismatch")

    handed_off = dict(pending)
    handed_off["status"] = "handed_off"
    handed_off["handoff_session_id"] = target_session_id
    handed_off["handed_off_at"] = time.time()

    state["last_handed_off_transition"] = handed_off
    state["pending_node_transition"] = None
    state["handoff_session_id"] = target_session_id
    state["input_allowed"] = False
    state["block_reason"] = "transition_handed_off"
    state["session_over"] = True
    state["status"] = "ended"
    state["session_version"] = int(state.get("session_version") or 1) + 1
    await _persist_runtime_state(state)
    await get_storage().end_session(
        source_session_id,
        final_summary=(
            f"Practice continued in session {target_session_id}."
            if same_skill_reattempt
            else f"Next skill continued in session {target_session_id}."
        ),
        avg_score=float(state.get("current_mastery") or 0.0),
    )


def _module_id_for_state(node_id: str) -> str:
    try:
        return module_of(node_id)
    except KeyError:
        if node_id.startswith("int_"):
            return "interview"
        if node_id.startswith("gd_"):
            return "group_discussion"
        if node_id.startswith("school_"):
            return "school_english"
        return ""


def _new_state(
    user_id: str,
    session_id: str,
    node_id: str,
    memory_context: list,
    learner_name: str = "",
    weakness_context: list | None = None,
    task_type: str = "",
    module_id: str = "",
    sim_topic: str = "",
    career_context: dict | None = None,
    scenario_config: dict | None = None,
    personas: list | None = None,
    context_hash: str = "default",
) -> dict:
    now = time.time()
    ttl = max(60, int(get_settings().session_ttl_seconds))
    return {
        "user_id": user_id,
        "session_id": session_id,
        "status": "active",
        "started_at": now,
        "last_seen_at": now,
        "expires_at": now + ttl,
        "reattempt": False,
        "reattempt_of_session_id": None,
        "competency_node": node_id,
        "task_type": task_type,
        "module_id": module_id or _module_id_for_state(node_id),
        "user_input": "",
        # TEST-mode simulation state (empty/None for coaching sessions): the topic
        # the panel debates, and the persona roster cached after the first round.
        "sim_topic": sim_topic,
        "personas": personas,
        "blackboard": None,
        # Precomputed/loaded assessment probe bank (list[dict]); empty for
        # coaching sessions. Hydrated at TEST start from the precache or a
        # synchronous regeneration. Persisted (not a transient key).
        "probe_items": [],
        "assessment_plan": None,
        "assessment_events": [],
        "coverage_events": [],
        "pending_coverage_event": None,
        "visible_event_ledger": [],
        "assessment_validity_flags": [],
        "floor_handoff_queue": [],
        "simulation_segments": [],
        "career_context": career_context or {},
        "session_learning_delta": {
            "strengths": [],
            "active_gaps": [],
            "repeated_issue_counts": {},
            "growth_signals": [],
            "resolved_candidates": [],
            "latest_evidence_quotes": [],
            "applied_evaluation_ids": [],
        },
        "scenario_config": scenario_config or {},
        "context_hash": context_hash or "default",
        "current_mastery": 0.0,
        "turn_count": 0,
        "messages": [],
        "probe_cursor": 0,
        "used_probe_prompts": [],
        "simulation_report": None,
        "simulation_score": None,
        "simulation_round": 0,
        "session_version": 1,
        "input_allowed": True,
        "block_reason": None,
        "pending_node_transition": None,
        "committed_openings": {},
        # True once the fresh-session opening has been streamed (stream_opening).
        # The transcript endpoint surfaces it so a browser reload restores the
        # existing transcript instead of replaying a second opening.
        "opening_streamed": False,
        "last_diagnosis": {},
        "last_rubric_result": None,
        "tutor_turn_plan": None,
        "evaluation_retry_required": False,
        "evaluation_integrity_failure": None,
        "last_eval_score": 0.0,
        "bridge_attempts": 0,
        "clarify_attempts": 0,
        "redirect_attempts": 0,
        "attempts": 0,
        # session-scoped attempt counter (NOT restored from storage) so the
        # ceiling-escape (first strong answer -> challenge) is reachable for a
        # returning learner whose lifetime `attempts` was loaded from disk.
        "session_attempts": 0,
        # pre-authored bridge bookkeeping (deterministic grading + no-repeat)
        "pending_answer_key": None,
        "served_bridge_ids": [],
        # set per eval turn; True only when a bridge fill was graded (H1 gate)
        "last_graded_bridge": False,
        "memory_context": memory_context,
        # aggregated prior weaknesses (list of dicts: skill_id/hit_count/last_raw)
        # hydrated at start_session; Phase 1.3 threads it into _memory_block.
        "weakness_context": weakness_context or [],
        "session_summary": None,
        "pending": None,
        "pending_game": None,
        "active_game_prompt": None,
        "active_prompt_attempt_type": None,
        "pending_prompt_attempt_type": None,
        "active_task_contract": None,
        "last_evaluated_task_contract": None,
        # Spec B: the selector's read of the most recent advance (transient).
        "last_selection": None,
        "last_route": None,
        # personalization / progression bookkeeping (service-owned; coach_view
        # projects a subset of these into the private coaching directive block)
        "learner_name": learner_name,
        "clean_streak": 0,        # consecutive clean passes at current node
        "advance_streak": ADVANCE_STREAK,
        "level_fails": 0,         # consecutive hard fails at current node
        "strengthen_attempts": 0, # consecutive strengthens in the 0.4-0.6 plateau
        "scaffold": 0,            # >=1 -> scaffold HARD (down-ladder)
        "needs_support": False,   # set per-turn from frustration detection
        "frustration_turns": 0,   # consecutive turns flagged as frustrated/confused
        "session_over": False,
        # service-only bookkeeping (not consumed by the graph)
        "node_history": {},     # node_id -> {"attempts": int, "clean": bool}
        "node_mastered": False,
        "display_status": "active",
        "best_independent_score": 0.0,
        "independent_passes": 0,
        "transfer_passes": 0,
        "pressure_passes": 0,
        "core_qualified": False,
        "core_qualification_turn_id": None,
        "core_qualification_evidence": None,
        "scaffold_successes": 0,
        "meaningful_attempts": 0,
        "readiness_score": 0.0,
        "last_gap": "",
        "mastery_evidence": [],
        "credited_evidence_ids": [],
        "remediation": False,
        "module_done": False,
        # Phase 5 gamification level flags (set at the advance boundary):
        "tester_level": False,  # last advance was fast/clean -> harder challenge
        "review_level": False,  # module finished clean -> weakness-summary section
    }


def touch_session(session_id: str, now: float | None = None) -> None:
    state = SessionStore.get(session_id)
    if state is None:
        return
    ts = now if now is not None else time.time()
    ttl = max(60, int(get_settings().session_ttl_seconds))
    state["last_seen_at"] = ts
    state["expires_at"] = ts + ttl
    save_sessions()


def _expire_state_if_needed(state: dict, now: float | None = None) -> bool:
    if state.get("status", "active") != "active":
        return False
    expires_at = state.get("expires_at")
    if expires_at is None:
        return False
    try:
        expiry = float(expires_at)
    except (TypeError, ValueError):
        return False
    ts = now if now is not None else time.time()
    if expiry > ts:
        return False
    state["status"] = "expired"
    state["session_over"] = True
    state["input_allowed"] = False
    state["block_reason"] = "session_expired"
    state["pending_node_transition"] = None
    state["session_version"] = int(state.get("session_version") or 1) + 1
    return True


async def touch_session_async(session_id: str, now: float | None = None) -> None:
    state = await get_session_state(session_id)
    if state is None:
        return
    ts = now if now is not None else time.time()
    ttl = max(60, int(get_settings().session_ttl_seconds))
    state["last_seen_at"] = ts
    state["expires_at"] = ts + ttl
    store = get_storage()
    if hasattr(store, "touch_session_runtime"):
        await store.touch_session_runtime(session_id, state.get("status", "active"))


async def cleanup_sessions(now: float | None = None) -> list[str]:
    ts = now if now is not None else time.time()
    expired: list[str] = []
    for sid, state in list(SessionStore.items()):
        if state.get("status") != "active" or float(state.get("expires_at", ts + 1)) <= ts:
            state["status"] = "expired"
            expired.append(sid)
            SessionStore.pop(sid, None)
            _SESSION_LOCKS.pop(sid, None)
    if expired:
        save_sessions()
    return expired


def _seed_sim_topic(node_id: str, weaknesses: list) -> str:
    """Build the assessment simulation topic for a TEST session.

    The returned string becomes the blackboard `topic` that the persona prompt
    recites as the discussion/interview subject, so it MUST be a neutral subject
    line — never an instruction.

    GROUP DISCUSSION (P0-4): return a CONCRETE debate motion from the motion bank
    — never the node's teach_focus, which is a teaching instruction, not a
    debatable proposition. The motion is stored once and shared verbatim by the
    opening brief, the director, and every persona, so the learner argues exactly
    the motion the panel debates.

    INTERVIEW: anchored on the node's teach_focus. The learner's weakness is
    pressed through probe_items -> the director (_probe_block, "do not read this
    list aloud"), exactly as GD does — NEVER folded in here. Folding "Probe the
    learner's known weakness: X" into the topic leaked that instruction into the
    interviewer's spoken subject for a returning learner (D3). `weaknesses` is
    therefore intentionally unused; it stays in the signature for caller symmetry.
    """
    if module_of(node_id) == "group_discussion":
        return motion_for_node(node_id)
    return get_node(node_id).teach_focus


def _memory_context_identity(row: dict) -> tuple[str, ...]:
    session_id = str(row.get("session_id") or "").strip()
    if session_id:
        return ("session", session_id)
    node_id = str(row.get("node_id") or "").strip()
    raw = " ".join(str(row.get("raw") or row.get("content") or "").split()).lower()
    if raw:
        return ("content", node_id, raw)
    return ("row", json.dumps(row, sort_keys=True, default=str))


def _memory_context_matches_module(row: dict, module_id: str) -> bool:
    owners: list[str] = []
    explicit_module = str(row.get("module_id") or "").strip()
    if explicit_module:
        owners.append(explicit_module)
    node_id = str(row.get("node_id") or "").strip()
    if node_id:
        try:
            owners.append(module_of(node_id))
        except KeyError:
            pass
    task_module = {
        TaskType.INTERVIEW_PREP.value: "interview",
        TaskType.INTERVIEW_TEST.value: "interview",
        TaskType.GD_PREP.value: "group_discussion",
        TaskType.GD_TEST.value: "group_discussion",
    }.get(str(row.get("task_type") or "").strip())
    if task_module:
        owners.append(task_module)
    return bool(owners) and all(owner == module_id for owner in owners)


def _merge_test_memory_context(
    test_history: list,
    prep_history: list,
    module_id: str,
) -> list[dict]:
    merged: list[dict] = []
    seen: set[tuple[str, ...]] = set()
    for raw_row in [*test_history, *prep_history]:
        if (
            not isinstance(raw_row, dict)
            or not _memory_context_matches_module(raw_row, module_id)
        ):
            continue
        identity = _memory_context_identity(raw_row)
        if identity in seen:
            continue
        seen.add(identity)
        merged.append(copy.deepcopy(raw_row))
        if len(merged) >= _TEST_HISTORY_TOTAL_LIMIT:
            break
    return merged


# ---------- public API ----------

async def start_session(
    user_id: str,
    node_id: str,
    learner_name: str = "",
    test_mode: bool = False,
    reattempt: bool = False,
    simulation_config: dict | None = None,
    session_id: str | None = None,
    persist: bool = True,
) -> tuple[str, dict]:
    """Create a session, return (session_id, state). Opening msg streamed via
    stream_opening(). Loads prior memory for this node (best-effort).

    `learner_name` (optional) personalizes the coaching directives so the tutor
    addresses the learner by name.

    `test_mode` selects the assessment ("test") TaskType variant for modules
    that have a prep/test split (interview, group_discussion); it is a no-op for
    modules without one. The strict assessment variant then keys behavior pack,
    memory, and weaknesses for this session."""
    if node_id not in all_node_ids():
        raise ValueError(f"unknown competency node: {node_id}")
    await cleanup_sessions()
    # Voice tier is gated "coming soon" — refuse a direct start rather than coach
    # a pace/pausing voice skill as typed text (D5). Placement/advance already
    # skip these, so a normal flow never lands here; this guards a direct id.
    if is_voice_node(node_id):
        raise ValueError(f"voice practice is coming soon: {node_id}")
    session_id = session_id or uuid.uuid4().hex
    # task_type is the pedagogy axis (TaskType value) storage keys memory and
    # weaknesses on; module_id is the registry module that owns the node. They
    # diverge for interview/group_discussion (prep vs. test); test_mode picks the
    # assessment variant where one exists, else the coaching variant.
    task_type_enum = task_type_of(node_id, test_mode=test_mode)
    task_type = task_type_enum.value
    module_id = module_of(node_id)
    is_test = task_type in _TEST_TASK_TYPES
    # A TEST session logs no per-skill weaknesses of its own — it reads the prep
    # sibling's (gd_test -> gd_prep). For prep/single-mode, prep_counterpart is a
    # no-op, so this keeps the coaching path's behavior unchanged.
    weakness_key = prep_counterpart(task_type)

    memory_context: list = []
    weakness_context: list = []
    current_mastery = 0.0
    attempts = 0
    loaded_progress: dict = {}

    store = get_storage()
    await store.ensure_profile(user_id, learner_name)
    prof = await store.get_profile(user_id) or {}
    career_context = build_career_context(prof)
    career_context_private = career_context.private_dict()
    try:
        career_context_private["career_memory_context"] = (
            await CareerLearningProfileService(store).get_career_memory_context(
                user_id,
                module_id=module_id,
            )
        )
    except Exception:
        logger.warning(
            "career memory context unavailable for user=%s; continuing without feed-forward context",
            user_id,
            exc_info=True,
        )
        career_context_private["career_memory_context"] = {}
    resolved_sim = resolve_simulation_config(
        task_type_enum,
        node_id,
        simulation_config or {},
        career_context,
    )
    try:
        progression = await store.get_progression(user_id)
    except Exception as e:
        logger.exception("progression storage unavailable before session create for user=%s", user_id)
        raise ProgressionUnavailableError("progression_unavailable") from e
    for p in progression:
        if p["node_id"] == node_id:
            loaded_progress = dict(p)
            current_mastery = p["ema"]
            attempts = p["attempts"]
            break

    exact_memory_context = await store.load_context(
        user_id,
        task_type,
        k=_CAREER_HISTORY_PER_MODE_LIMIT,
    )
    if is_test:
        prep_task_type = prep_counterpart(task_type)
        prep_memory_context = await store.load_context(
            user_id,
            prep_task_type,
            k=_CAREER_HISTORY_PER_MODE_LIMIT,
        )
        memory_context = _merge_test_memory_context(
            exact_memory_context,
            prep_memory_context,
            module_id,
        )
    else:
        memory_context = exact_memory_context
    weakness_context = await store.get_weaknesses(user_id, weakness_key)

    # School 'Learn' sessions: the meaningful weak-spot signal lives in the
    # dedicated school per-skill mastery (folded from exact-graded chapter tests),
    # NOT the generic weakness table — every school skill tag coerces to OTHER
    # there. Surface the learner's weakest assessment skills so the live tutor
    # opens with a warm-up that re-tests a real gap. Prepended so they lead the
    # block. Also surface skills MASTERED earlier but gone stale, for a spaced
    # retention check (the longitudinal half of learning tracking).
    review_skills: list = []
    if task_type == TaskType.SCHOOL_ENGLISH.value:
        school_weak = await store.get_school_weak_skills(user_id)
        weakness_context = [
            {"skill_id": s.replace("_", " "), "hit_count": 1, "last_raw": ""}
            for s in school_weak
        ] + weakness_context
        review_skills = [
            s.replace("_", " ")
            for s in await store.get_school_review_skills(user_id)
        ]

    # Source the learner's display name from their stored profile (set at
    # Google sign-in) so the coach can address them by name. ensure_profile is
    # non-clobbering on an empty name, so a returning learner keeps their name.
    if not learner_name:
        if prof and prof.get("name"):
            learner_name = prof["name"]

    last_summary = ""
    if attempts > 0:
        for mem in memory_context:
            if mem.get("node_id") == node_id and mem.get("raw"):
                last_summary = sanitize_memory_text(mem.get("raw"))
                break

    # Seed the assessment topic from the node, sharpened by the learner's top
    # prep weakness so the persona panel probes exactly where they struggled.
    sim_topic = (
        resolved_sim.resolved_topic
        if is_test and resolved_sim.resolved_topic
        else _seed_sim_topic(node_id, weakness_context) if is_test else ""
    )

    state = _new_state(
        user_id,
        session_id,
        node_id,
        memory_context,
        learner_name,
        weakness_context,
        task_type,
        module_id,
        sim_topic,
        career_context=career_context_private,
        scenario_config=resolved_sim.public_dict(),
        personas=resolved_sim.persona_roster if is_test else None,
        context_hash=resolved_sim.context_hash,
    )
    state["session_learning_delta"] = {
        "strengths": [],
        "active_gaps": [],
        "repeated_issue_counts": {},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": [],
        "applied_evaluation_ids": [],
    }
    
    # Apply loaded progress
    state["current_mastery"] = current_mastery
    state["attempts"] = attempts
    if task_type in {TaskType.INTERVIEW_PREP.value, TaskType.GD_PREP.value}:
        for key in (
            "node_mastered",
            "display_status",
            "best_independent_score",
            "independent_passes",
            "transfer_passes",
            "pressure_passes",
            "scaffold_successes",
            "meaningful_attempts",
            "readiness_score",
            "last_gap",
            "mastery_evidence",
        ):
            if key in loaded_progress and loaded_progress[key] is not None:
                state[key] = loaded_progress[key]
    state["reattempt"] = bool(reattempt)
    # Spaced-review skills (school): mastered-but-stale, re-checked in the opening.
    state["review_context"] = review_skills
    # clean_streak deliberately starts at 0 even for a returning learner who
    # clean-passed this node before. Pre-crediting half of ADVANCE_STREAK let ONE
    # clean answer this session re-advance them (or a single borderline 0.7 trip
    # the clean_streak>=1 challenge gate) without re-proving anything. Retained
    # mastery is still honored: current_mastery loads the prior EMA, and a genuinely
    # strong return (score >= CEILING_SCORE on the first session attempt) still
    # routes straight to challenge via route_node's session_attempts escape,
    # independent of the streak. The learner just re-proves the streak in-session.


    if last_summary:
        state["messages"].append({
            "role": "assistant",
            "content": f"Welcome back! Here is a summary of your previous session on this level:\n\n{last_summary}"
        })
        
    # A TEST session needs its probe bank ready before the first round. Read the
    # precache (computed at the PREP sibling's end_session); on a miss or stale
    # entry, regenerate synchronously so the session still opens with a real bank.
    if is_test:
        state["probe_items"] = await _load_or_generate_probe_items(
            user_id,
            task_type,
            career_context=career_context_private,
            scenario_config=resolved_sim.private_dict(),
            context_hash=resolved_sim.context_hash,
        )
        ensure_assessment_plan(state)
    state["_prepared_session_record"] = {
        "session_id": session_id,
        "user_id": user_id,
        "task_type": task_type,
        "module_id": module_id,
        "node_id": node_id,
        "test_mode": is_test,
        "career_context": career_context_private,
        "scenario_config": resolved_sim.private_dict(),
        "persona_roster": resolved_sim.persona_roster if is_test else [],
        "context_hash": resolved_sim.context_hash,
    }
    if persist:
        await commit_prepared_session(state)
    return session_id, state


def _gd_sim_topic(state: dict) -> str:
    """The concrete GD motion to brief in the opening — only for GD assessment
    sessions. For interview/coaching, sim_topic is an instruction/focus, not a
    debatable motion, so the opening stays generic."""
    if state.get("task_type") == TaskType.GD_TEST.value:
        return state.get("sim_topic", "")
    return ""


def _opening_fallback_text(state: dict, node) -> str:
    task_type = state.get("task_type")
    if task_type == TaskType.GD_TEST.value:
        topic = _gd_sim_topic(state) or "the assigned motion"
        return (
            f"Today's group discussion focuses on the motion: \"{topic}\". "
            "State your position in one or two sentences, then give one concrete reason."
        )
    if task_type == TaskType.INTERVIEW_TEST.value:
        role = str(
            (state.get("scenario_config") or {}).get("role")
            or (state.get("scenario_config") or {}).get("target_role")
            or state.get("interview_role")
            or "this role"
        )
        title = str(getattr(node, "title", "") or "").lower()
        if "star" in title:
            return (
                f"Let's begin the {role} interview. Tell me about a specific project or situation using STAR: "
                "what was the situation, what was your task, what actions did you take, and what changed as a result?"
            )
        if "weakness" in title:
            return (
                f"Let's begin the {role} interview. What is one real weakness you are working on, "
                "and what evidence shows you are improving it?"
            )
        if "strength" in title:
            return (
                f"Let's begin the {role} interview. What is one strength you would bring to this role? "
                "Back it with a specific example and result."
            )
        return (
            f"Let's begin the {role} interview. Answer this as you would in a real interview: "
            f"{getattr(node, 'title', 'Tell me about your experience')}."
        )
    if task_type == TaskType.GD_PREP.value:
        career_context = state.get("career_context") or {}
        topics = (
            career_context.get("gd_topics")
            or career_context.get("custom_gd_topics")
            or []
        )
        topic = str(
            state.get("sim_topic")
            or (state.get("scenario_config") or {}).get("topic")
            or (topics[0] if isinstance(topics, list) and topics else "")
            or "Should remote work be the default?"
        ).strip()
        node_id = str(getattr(node, "id", "") or "")
        tasks = {
            "gd_01_take_a_stance": (
                "The moderator has opened the floor. State a clear position on the motion "
                "and give one concrete reason before anyone else responds."
            ),
            "gd_02_support_with_evidence": (
                "A participant has made a broad claim without proof. State your position, "
                "then support it with one learner-owned example, named-source fact, explicit "
                "analogy, or labelled hypothetical, and explain the link."
            ),
            "gd_03_take_the_floor": (
                "Two participants have spoken and there is a short pause. Enter naturally by "
                "linking one prior idea to a new implication of your own."
            ),
            "gd_04_build_on_others": (
                "The Analyst has raised a valid implementation point. Credit that point, then "
                "extend it with one new consequence or practical proposal."
            ),
            "gd_05_disagree_respectfully": (
                "A participant says the motion's main benefit outweighs every risk. Concede one "
                "valid benefit, then disagree with a topic-based reason without attacking them."
            ),
            "gd_06_balanced_view": (
                "One participant supports the motion for its potential benefits; another opposes "
                "it because of implementation risks. State the strongest point on each side, "
                "weigh the decisive trade-off, and land on a clear recommendation."
            ),
            "gd_07_steer_back": (
                "The panel has drifted into unrelated workplace preferences. Flag the drift "
                "neutrally, restate the core motion, and offer the next useful angle to examine."
            ),
            "gd_08_include_quiet": (
                "The Analyst and Challenger have spoken twice, but Maya has not entered. "
                "Address Maya directly, link her invitation to one useful topic lens, and give "
                "her the floor without pressure."
            ),
            "gd_09_manage_dominator": (
                "A dominant participant interrupts and repeats the same argument. Reclaim the "
                "floor calmly by acknowledging the useful part, add one topic-linked point, "
                "and create room for another participant."
            ),
            "gd_10_drive_consensus": (
                "Maya says the evidence supports the motion; Dev says it is too mixed to accept "
                "without qualification. Summarize both positions, name their shared need for a "
                "reliable decision standard, and propose a concrete next step that credits both."
            ),
        }
        task = tasks.get(
            node_id,
            "Add one substantive contribution to the discussion and move the group forward.",
        )
        return f"Group discussion motion: \"{topic}\" {task}"
    return f"Let's practice {getattr(node, 'title', 'this skill')}. Give your best attempt now."


def _assessment_opening_text(state: dict, node) -> str:
    """Return a deterministic first prompt for scored simulations.

    Test-mode openings must never depend on a slow model stream. The actual
    assessment turn still uses the structured model boundary after the learner
    answers; this only makes the first visible prompt reliable and aligned with
    the backend-owned plan.
    """
    task_type = state.get("task_type")
    if task_type == TaskType.GD_TEST.value:
        return _opening_fallback_text(state, node)
    if task_type != TaskType.INTERVIEW_TEST.value:
        return ""

    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    role = str(
        plan.get("role")
        or (state.get("scenario_config") or {}).get("target_role")
        or "this role"
    ).strip() or "this role"
    title = str(getattr(node, "title", "") or "").lower()
    if "star" in title:
        prompt = (
            f"Tell me about one specific {role} project or work situation using STAR. "
            "What was the situation, what was your task, what action did you personally take, "
            "and what changed as a result?"
        )
        prompt_id = "prompt_initial_star_story"
        skill_id = "STRUCTURE_STAR_METHOD"
    else:
        probes = [probe for probe in (plan.get("probe_plan") or []) if isinstance(probe, dict)]
        first_probe = next((probe for probe in probes if str(probe.get("prompt") or "").strip()), None)
        if not first_probe:
            return _opening_fallback_text(state, node)
        prompt = str(first_probe.get("prompt") or "").strip()
        prompt_id = str(first_probe.get("prompt_id") or first_probe.get("probe_id") or "").strip() or f"prompt_{uuid.uuid4().hex[:8]}"
        skill_id = str(first_probe.get("skill_id") or first_probe.get("probe_id") or prompt_id).strip()
    state["active_interview_probe_prompt"] = prompt
    state["active_interview_probe_prompt_id"] = prompt_id
    state["active_interview_probe_skill_id"] = skill_id
    state["pending_coverage_event"] = {
        "event_id": f"opening:{prompt_id}",
        "task_type": TaskType.INTERVIEW_TEST.value,
        "skill_id": skill_id,
        "prompt_id": prompt_id,
        "prompt_text": prompt,
        "answered": False,
    }
    used = list(state.get("used_probe_prompts") or [])
    used.append(prompt)
    state["used_probe_prompts"] = used[-12:]
    state["probe_cursor"] = max(1, int(state.get("probe_cursor") or 0))
    learner = str(state.get("learner_name") or "").strip()
    greeting = f"Welcome, {learner}. " if learner else "Welcome. "
    return f"{greeting}We'll focus on {role}. {prompt}"


def _append_opening_message_once(state: dict, message: dict) -> bool:
    """Append an opening message only if this opening is not already visible.

    Browser bootstrap can race a transcript restore against an opening retry. The
    session state owns the authoritative transcript, so protect it here too:
    same message_id wins, and for older persisted rows without message_id the
    opening kind + node + transition + content tuple is treated as the identity.
    """
    messages = state.setdefault("messages", [])
    message_id = str(message.get("message_id") or "").strip()
    node_id = message.get("node_id")
    transition_id = message.get("transition_id")
    content = str(message.get("content") or "")
    for existing in messages:
        if not isinstance(existing, dict):
            continue
        if message_id and existing.get("message_id") == message_id:
            return False
        if (
            existing.get("role") == "assistant"
            and existing.get("message_kind") == "opening"
            and existing.get("node_id") == node_id
            and existing.get("transition_id") == transition_id
            and str(existing.get("content") or "") == content
        ):
            if message_id and not existing.get("message_id"):
                existing["message_id"] = message_id
            return False
    messages.append(message)
    _commit_career_task_contract(state, message)
    state["turn_count"] = int(state.get("turn_count") or 0) + 1
    return True


def _append_simulation_messages_once(state: dict, speaker_messages: list[dict]) -> int:
    """Append streamed simulation messages without persisting adjacent duplicates.

    The browser can reconnect or replay a just-completed stream while the same
    persona text is already visible. Keep the transcript authoritative by
    collapsing only identical adjacent assistant simulation turns from the same
    speaker; different speakers or different text remain separate GD segments.
    """
    messages = state.setdefault("messages", [])
    appended = 0
    for message in speaker_messages:
        text = " ".join(str(message.get("content") or "").split())
        speaker_id = str(message.get("speaker_id") or "")
        previous = messages[-1] if messages and isinstance(messages[-1], dict) else None
        previous_text = " ".join(str((previous or {}).get("content") or "").split())
        if (
            previous
            and previous.get("role") == "assistant"
            and previous.get("message_kind") == "simulation_turn"
            and str(previous.get("speaker_id") or "") == speaker_id
            and previous_text == text
        ):
            continue
        messages.append(message)
        appended += 1
    return appended


async def _stream_generation_with_timeout(
    spec: GenSpec,
    timeout_seconds: float | None = None,
) -> AsyncIterator[str]:
    """Yield model tokens, but never let an opening hang the session shell."""
    token_timeout = OPENING_STREAM_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    stream = stream_generation(spec).__aiter__()
    while True:
        try:
            yield await asyncio.wait_for(stream.__anext__(), timeout=token_timeout)
        except StopAsyncIteration:
            break
        except asyncio.TimeoutError:
            aclose = getattr(stream, "aclose", None)
            if callable(aclose):
                try:
                    await aclose()
                except Exception:
                    logger.debug("opening stream close after timeout failed", exc_info=True)
            raise


def _int01_reattempt_opening_text(state: dict) -> str | None:
    if (
        not state.get("reattempt")
        or state.get("task_type") != TaskType.INTERVIEW_PREP.value
        or state.get("competency_node") != "int_01_elevator_pitch"
    ):
        return None

    independent_passes = int(state.get("independent_passes") or 0)
    transfer_passes = int(state.get("transfer_passes") or 0)
    pressure_passes = int(state.get("pressure_passes") or 0)
    if (
        transfer_passes >= 1
        and pressure_passes < 1
        and qualified_core_evidence(state, "int_01_elevator_pitch")
    ):
        state["pending_prompt_attempt_type"] = "pressure"
        return (
            "Your role, proof, and direction are already covered, so do not rewrite the pitch. "
            "Pressure check: a skeptical interviewer asks, 'How do I know this result would "
            "repeat or scale beyond one situation?' Answer that one pushback using only "
            "evidence from your own experience."
        )
    if transfer_passes >= 1 and pressure_passes < 1:
        state["pending_prompt_attempt_type"] = "independent"
        return (
            "I need one grounded pitch before I can challenge the evidence. Introduce yourself "
            "again using a different real achievement from your own experience."
        )
    if independent_passes >= 2 and transfer_passes < 1:
        state["pending_prompt_attempt_type"] = "transfer"
        return (
            "Your core pitch is already covered, so do not repeat it. Transfer check: create "
            "a second 30-second introduction for a non-technical hiring manager using a "
            "different achievement while preserving role, proof, and direction."
        )
    if independent_passes >= 1:
        state["pending_prompt_attempt_type"] = "independent"
        return (
            "Keep your existing pitch unchanged. Introduce yourself again using a different "
            "real achievement, with role, proof, and direction all present."
        )
    return None


async def stream_opening(
    session_id: str,
    transition_id: str | None = None,
) -> AsyncIterator[str]:
    """Stream the lesson opening for a fresh session or pending transition.

    The transition path is idempotent: a retry with the same transition id replays
    the already-committed opening instead of appending a second assistant prompt.
    """
    state = _require(session_id)
    node = get_node(state["competency_node"])
    pending_transition = state.get("pending_node_transition")
    committed = state.setdefault("committed_openings", {})
    if transition_id and transition_id in committed:
        await _mark_committed_opening_replayed(state, transition_id)
        yield committed[transition_id]
        return
    opening_key = (
        pending_transition.get("transition_id")
        if pending_transition
        else f"initial:{state['competency_node']}"
    )
    if transition_id and opening_key != transition_id:
        raise ValueError("transition_id_mismatch")

    if opening_key in committed:
        await _mark_committed_opening_replayed(state, opening_key)
        yield committed[opening_key]
        return

    reattempt_opening = _int01_reattempt_opening_text(state)
    if reattempt_opening:
        message_id = f"{session_id}:opening:{opening_key}"
        message = {
            "message_id": message_id,
            "role": "assistant",
            "content": reattempt_opening,
            "node_id": state["competency_node"],
            "transition_id": None,
            "message_kind": "opening",
        }
        _append_opening_message_once(state, message)
        committed[opening_key] = reattempt_opening
        state["last_opening_message_id"] = message_id
        _commit_pending_prompt_attempt_type(state)
        await _record_opening_attempt(state)
        state["opening_streamed"] = True
        await _persist_runtime_state(state)
        yield reattempt_opening
        return

    deterministic_prep_opening = (
        _opening_fallback_text(state, node)
        if state.get("task_type") == TaskType.GD_PREP.value
        else _int05_opening_text(state)
        if state.get("task_type") == TaskType.INTERVIEW_PREP.value
        and state.get("competency_node") == "int_05_why_this_role"
        else ""
    )
    if deterministic_prep_opening:
        message_id = f"{session_id}:opening:{opening_key}"
        message = {
            "message_id": message_id,
            "role": "assistant",
            "content": deterministic_prep_opening,
            "node_id": state["competency_node"],
            "transition_id": pending_transition.get("transition_id") if pending_transition else None,
            "message_kind": "opening",
        }
        _append_opening_message_once(state, message)
        committed[opening_key] = deterministic_prep_opening
        state["last_opening_message_id"] = message_id
        await _record_opening_attempt(state)
        state["opening_streamed"] = True
        if pending_transition:
            pending_transition["status"] = "committed"
            state["pending_node_transition"] = None
        await _persist_runtime_state(state)
        yield deterministic_prep_opening
        return

    deterministic_test_opening = _assessment_opening_text(state, node)
    if deterministic_test_opening and not pending_transition:
        message_id = f"{session_id}:opening:{opening_key}"
        opening_speaker = (
            {"speaker_name": "Moderator", "speaker_id": "moderator_timekeeper"}
            if state.get("task_type") == TaskType.GD_TEST.value
            else {"speaker_name": "Interviewer", "speaker_id": "interviewer"}
        )
        message = {
            "message_id": message_id,
            "role": "assistant",
            "content": deterministic_test_opening,
            "node_id": state["competency_node"],
            "transition_id": None,
            "message_kind": "opening",
            **opening_speaker,
        }
        _append_opening_message_once(state, message)
        committed[opening_key] = deterministic_test_opening
        state["last_opening_message_id"] = message_id
        await _record_opening_attempt(state)
        state["opening_streamed"] = True
        await _persist_runtime_state(state)
        yield deterministic_test_opening
        return

    if pending_transition:
        pending_transition["status"] = "opening_streaming"
        pending_transition["attempts"] = int(pending_transition.get("attempts") or 0) + 1
        await _persist_runtime_state(state)

    prompt = build_opening_prompt(
        node,
        state.get("memory_context", []),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        sim_topic=_gd_sim_topic(state),
        interview_test=state.get("task_type") == TaskType.INTERVIEW_TEST.value,
        review_skills=state.get("review_context", []),
        career_context=state.get("career_context") or {},
        scenario_config=state.get("scenario_config") or {},
        allow_weakness_warmup=state.get("task_type") == TaskType.SCHOOL_ENGLISH.value,
    )
    spec = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="opening")
    full = []
    try:
        async for tok in _stream_generation_with_timeout(spec):
            full.append(tok)
            yield tok
    except asyncio.TimeoutError:
        logger.warning("opening stream timed out; using fallback for session=%s", session_id)
        full = []
    except Exception:
        if pending_transition and int(pending_transition.get("attempts") or 0) < 2:
            pending_transition["status"] = "opening_failed"
            pending_transition["last_error"] = {"code": "stream_failed"}
            await _persist_runtime_state(state)
            raise
        full = []
    text = "".join(full)
    if not text.strip():
        text = _opening_fallback_text(state, node)
        yield text
    message_id = f"{session_id}:opening:{opening_key}"
    message = {
        "message_id": message_id,
        "role": "assistant",
        "content": text,
        "node_id": state["competency_node"],
        "transition_id": pending_transition.get("transition_id") if pending_transition else None,
        "message_kind": "opening",
    }
    _append_opening_message_once(state, message)
    committed[opening_key] = text
    state["last_opening_message_id"] = message_id
    # Mark the opening as streamed so a reload rehydrates instead of replaying it.
    await _record_opening_attempt(state)
    state["opening_streamed"] = True
    if pending_transition:
        pending_transition["status"] = "committed"
        state["pending_node_transition"] = None
        state["input_allowed"] = True
        state["block_reason"] = None
        state["session_version"] = int(state.get("session_version") or 1) + 1
    await _persist_runtime_state(state)


async def _stream_node_opening(state: dict) -> AsyncIterator[str]:
    """Stream a lesson opening for state's CURRENT node, append it, bump turn.

    Shared by stream_opening (fresh session) and the advance-transition in
    run_turn (desync fix). Falls back to a plain transition line if the stream
    yields nothing so an advance never ends on silence."""
    node = get_node(state["competency_node"])
    prompt = build_opening_prompt(
        node,
        state.get("memory_context", []),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
        sim_topic=_gd_sim_topic(state),
        interview_test=state.get("task_type") == TaskType.INTERVIEW_TEST.value,
        review_skills=state.get("review_context", []),
        career_context=state.get("career_context") or {},
        scenario_config=state.get("scenario_config") or {},
        allow_weakness_warmup=state.get("task_type") == TaskType.SCHOOL_ENGLISH.value,
    )
    spec = GenSpec(provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="opening")
    full = []
    try:
        async for tok in _stream_generation_with_timeout(spec):
            full.append(tok)
            yield tok
    except asyncio.TimeoutError:
        logger.warning("node opening stream timed out; using fallback for session=%s", state.get("session_id"))
        full = []
    except Exception:
        full = []
    text = "".join(full).strip()
    if not text:
        text = _opening_fallback_text(state, node)
        yield text
    message = {
        "message_id": f"{state.get('session_id')}:opening:{state.get('competency_node')}:{state.get('session_version', 1)}",
        "role": "assistant",
        "content": text,
        "node_id": state.get("competency_node"),
        "transition_id": (state.get("pending_node_transition") or {}).get("transition_id"),
        "message_kind": "opening",
    }
    _append_opening_message_once(state, message)


def _append_user_turn_message(
    state: dict,
    user_input: str,
    client_turn_id: str | None = None,
    message_kind: str = "learner_answer",
) -> bool:
    """Append the learner's accepted answer once per client turn.

    The route-level idempotency latch prevents double grading, but after an
    accepted turn fails mid-stream the same client_turn_id is allowed to retry.
    This helper makes that retry transcript-safe: the already-durable user
    answer is reused instead of inserting a duplicate bubble.
    """
    if client_turn_id:
        for message in state.get("messages", []):
            if message.get("role") == "user" and message.get("turn_id") == client_turn_id:
                return False
    message = {
        "role": "user",
        "content": user_input,
        "node_id": state.get("competency_node"),
        "message_kind": message_kind,
    }
    if client_turn_id:
        message["turn_id"] = client_turn_id
        message["message_id"] = f"{state['session_id']}:turn:{client_turn_id}:user"
    assessment_action = state.get("client_assessment_action")
    if isinstance(assessment_action, dict):
        message["assessment_action"] = dict(assessment_action)
    state["messages"].append(message)
    return True


async def _hydrate_core_qualification(state: dict) -> None:
    if state.get("task_type") not in {
        TaskType.INTERVIEW_PREP.value,
        TaskType.GD_PREP.value,
    }:
        return
    if _has_valid_core_qualification(state):
        return
    if state.get("core_qualified") or state.get("core_qualification_evidence"):
        state["core_qualified"] = False
        state["core_qualification_turn_id"] = None
        state["core_qualification_evidence"] = None
    if int(state.get("independent_passes") or 0) < 2:
        return
    store = get_storage()
    loader = getattr(store, "get_latest_passing_turn_evaluation", None)
    if not callable(loader):
        return
    row = await loader(
        state["user_id"],
        state["competency_node"],
        "independent",
    )
    evaluation_id = str((row or {}).get("evaluation_id") or "")
    valid_row = bool(
        evaluation_id
        and (row or {}).get("user_id") == state.get("user_id")
        and (row or {}).get("node_id") == state.get("competency_node")
        and (row or {}).get("attempt_type") == "independent"
        and (row or {}).get("pass_eligible") is True
        and not (row or {}).get("blockers")
    )
    if valid_row:
        context_json = (row or {}).get("context_json") or {}
        hydrated_topic = str(context_json.get("active_topic") or "").strip()
        hydrated_contract = context_json.get("task_contract")
        if not isinstance(hydrated_contract, dict) or not hydrated_contract.get("context_id"):
            hydrated_contract = {
                "prompt_id": f"legacy:{evaluation_id}",
                "context_id": f"legacy-core:{evaluation_id}",
                "active_role": "",
                "active_topic": hydrated_topic,
                "semantic_anchors": [],
                "participant_claims": [],
                "evidence_policy": "learner_owned_or_sourced",
                "hypothetical": False,
            }
        if state.get("task_type") == TaskType.GD_PREP.value and not hydrated_topic:
            return
        state["core_qualified"] = True
        state["core_qualification_turn_id"] = evaluation_id
        state["core_qualification_evidence"] = {
            "evaluation_id": evaluation_id,
            "user_id": (row or {}).get("user_id"),
            "node_id": (row or {}).get("node_id"),
            "attempt_type": (row or {}).get("attempt_type"),
            "pass_eligible": bool((row or {}).get("pass_eligible")),
            "blockers": list((row or {}).get("blockers") or []),
            "effective_score": float((row or {}).get("effective_score") or 0.0),
            "learner_answer": str((row or {}).get("user_answer") or "").strip(),
            "task_contract": copy.deepcopy(hydrated_contract),
            "active_topic": (
                hydrated_topic
                if state.get("task_type") == TaskType.GD_PREP.value
                else ""
            ),
        }


def _has_valid_core_qualification(state: dict) -> bool:
    source = str(state.get("core_qualification_turn_id") or "")
    evidence = state.get("core_qualification_evidence")
    return bool(
        state.get("core_qualified")
        and source
        and isinstance(evidence, dict)
        and evidence.get("evaluation_id") == source
        and evidence.get("user_id") == state.get("user_id")
        and evidence.get("node_id") == state.get("competency_node")
        and evidence.get("attempt_type") == "independent"
        and evidence.get("pass_eligible") is True
        and bool(str(evidence.get("learner_answer") or "").strip())
        and (
            state.get("task_type") != TaskType.INTERVIEW_PREP.value
            or (
                isinstance(evidence.get("task_contract"), dict)
                and bool(str((evidence.get("task_contract") or {}).get("context_id") or "").strip())
            )
        )
        and (
            state.get("task_type") != TaskType.GD_PREP.value
            or bool(str(evidence.get("active_topic") or "").strip())
        )
        and not evidence.get("blockers")
    )


async def refresh_session_recap(state: dict) -> dict | None:
    """Build an honest recap from durable module progress for ended prep sessions."""
    if not state.get("module_done"):
        return state.get("session_recap")
    current_node_id = str(state.get("competency_node") or "")
    recap_nodes = [
        get_node(node_id).title
        for node_id in state.get("node_history", {}).keys()
    ]
    recap_weaknesses = list(state.get("weakness_context", []))
    recap_readiness = round(float(state.get("readiness_score") or 0.0), 4)
    if state.get("task_type") in {"interview_prep", "gd_prep"}:
        try:
            module = get_module(module_of(current_node_id))
            module_node_ids = {
                node.id for node in module.nodes if not is_voice_node(node.id)
            }
            progression = await get_storage().get_progression(state["user_id"])
            rows = [
                row for row in progression
                if str(row.get("node_id") or "") in module_node_ids
            ]
            completed_ids = {
                str(row.get("node_id") or "")
                for row in rows
                if bool(row.get("node_completed"))
            }
            durable_titles = [
                node.title for node in module.nodes
                if node.id in completed_ids and not is_voice_node(node.id)
            ]
            if durable_titles:
                recap_nodes = durable_titles
            completed_scores = [
                float(row.get("readiness_score") or 0.0)
                for row in rows
                if str(row.get("node_id") or "") in completed_ids
                and float(row.get("readiness_score") or 0.0) > 0
            ]
            if completed_scores:
                recap_readiness = round(
                    sum(completed_scores) / len(completed_scores),
                    4,
                )
            recap_weaknesses = [
                {
                    "skill_id": str(row.get("node_id") or ""),
                    "hit_count": 1,
                    "last_raw": str(row.get("last_gap") or "").strip(),
                }
                for row in rows
                if str(row.get("last_gap") or "").strip()
                and not bool(row.get("node_completed"))
            ]
        except Exception:
            logger.exception(
                "could not aggregate durable career recap for session=%s",
                state.get("session_id"),
            )
            if not state.get("last_gap"):
                recap_weaknesses = []
    recap = SessionRecap(
        nodes_completed=recap_nodes,
        weaknesses=recap_weaknesses,
        score_metric=(
            "readiness"
            if state.get("task_type") in {"interview_prep", "gd_prep"}
            else "mastery"
        ),
        readiness_score=recap_readiness,
        mastery_score=round(float(state.get("current_mastery") or 0.0), 4),
        avg_score=round(float(state.get("current_mastery") or 0.0), 4),
    )
    state["session_recap"] = asdict(recap)
    return state["session_recap"]


async def run_turn(
    session_id: str,
    user_input: str,
    client_turn_id: str | None = None,
    assessment_action: dict | None = None,
) -> AsyncIterator[str]:
    """Process one learner answer: evaluate -> route -> stream the response.

    Serializes per session (E24): the whole turn — including the streamed
    generation — runs under a per-session lock so a second turn on the same
    session can't interleave its state read-modify-write with this one. The lock
    is held across yields, so concurrent turns on ONE session queue; different
    sessions are unaffected."""
    async with _lock_for(session_id):
        async for tok in _run_turn_locked(session_id, user_input, client_turn_id, assessment_action):
            yield tok


async def _run_turn_locked(
    session_id: str,
    user_input: str,
    client_turn_id: str | None = None,
    assessment_action: dict | None = None,
) -> AsyncIterator[str]:
    """run_turn body — always invoked under the session lock (see run_turn).

    Hardened: caps oversized input, ends the session gracefully on a goodbye,
    pivots to support when the learner sounds discouraged, and falls back to a
    plain message if the stream yields nothing (backend hiccup) so the turn
    never dies silently."""
    state = _require(session_id)
    await _hydrate_core_qualification(state)
    block_reason = turn_block_reason(state)
    if block_reason == "awaiting_next_skill":
        raise AwaitingNextSkillError("awaiting_next_skill")
    if block_reason:
        raise SessionNotActiveError(block_reason)
    user_input = (user_input or "")[:MAX_INPUT_CHARS]
    state["user_input"] = user_input
    if state.get("task_type") in _TEST_TASK_TYPES and assessment_action:
        state["client_assessment_action"] = dict(assessment_action)
    else:
        state.pop("client_assessment_action", None)
    client_action_kind = (
        str((state.get("client_assessment_action") or {}).get("kind") or "")
        if isinstance(state.get("client_assessment_action"), dict)
        else ""
    )
    is_test_end_control = state.get("task_type") in _TEST_TASK_TYPES and _is_session_end(user_input)
    is_test_runtime_control = is_test_end_control or client_action_kind in {"clarify", "new_angle", "move_on"}
    if state.get("task_type") in _TEST_TASK_TYPES and not is_test_end_control:
        from app.services.simulation_service import is_simulation_control_input

        is_test_runtime_control = is_test_runtime_control or is_simulation_control_input(
            str(state.get("task_type") or ""),
            user_input,
        )
    _append_user_turn_message(
        state,
        user_input,
        client_turn_id,
        message_kind="simulation_control" if is_test_runtime_control else "learner_answer",
    )
    _mark_active_turn_processing(state, client_turn_id)
    # Once a turn has passed the route idempotency gate, the learner's message is
    # durable before any model call. Otherwise a persona/coach stream failure can
    # leave the server having accepted the answer while reload shows no user turn.
    await _persist_runtime_state(state)

    # Graceful exit: a short "done / bye / stop" ends the session with a warm
    # farewell instead of being scored as an off-task answer.
    if _is_session_end(user_input):
        if state.get("task_type") in _TEST_TASK_TYPES:
            from app.services.simulation_service import Speaker

            if not state.get("session_over"):
                state["session_over"] = True
                state["input_allowed"] = False
                state["block_reason"] = "session_over"
                _bump_session_version(state)
            state["active_game_prompt"] = None
            closing = (
                "That's where we'll close the session. Tap finish to see your "
                "scored feedback and where to focus next."
            )
            closing_speaker = (
                {"speaker_name": "Moderator", "speaker_id": "moderator_timekeeper"}
                if state.get("task_type") == TaskType.GD_TEST.value
                else {"speaker_name": "Interviewer", "speaker_id": "interviewer"}
            )
            state["messages"].append({
                "role": "assistant",
                "content": closing,
                "message_kind": "simulation_control",
                "turn_id": client_turn_id,
                **closing_speaker,
            })
            _finish_active_turn(state, client_turn_id, "completed")
            await _persist_runtime_state(state)
            yield Speaker(
                speaker_id=closing_speaker["speaker_id"],
                name=closing_speaker["speaker_name"],
            )
            yield closing
            return
        _mark_terminal(state, "learner_ended")
        state["active_game_prompt"] = None
        farewell = _farewell(state)
        state["messages"].append({"role": "assistant", "content": farewell})
        _finish_active_turn(state, client_turn_id, "completed")
        await _persist_runtime_state(state)
        yield farewell
        return

    # Blank non-answer short-circuit (Wave 1.3): an empty / whitespace / pure-
    # symbol turn has nothing to grade. Sending it to the eval LLM made the coach
    # fabricate a fake summary of a prior turn live, and it was scored as a real
    # attempt. Short-circuit with a fixed honest re-prompt BEFORE the graph runs —
    # no eval, no score, no attempt increment, no LLM call. Coaching path only;
    # a blank in a TEST-mode sim falls through to the panel as before.
    if state.get("task_type") not in _TEST_TASK_TYPES and is_blank_nonanswer(user_input):
        reprompt = (
            "Hmm, I didn't catch that — type your answer to the task above "
            "and we'll keep going."
        )
        state["messages"].append({"role": "assistant", "content": reprompt})
        state["turn_count"] += 1
        _finish_active_turn(state, client_turn_id, "completed")
        await _persist_runtime_state(state)
        yield reprompt
        return

    state["active_game_prompt"] = None

    # TEST-mode (assessment) turns run a multi-persona SIMULATION, not the
    # coaching graph: record the learner's contribution, stream the panel's next
    # round (Speaker markers + text), capture the spoken text as one assistant
    # turn, and DEFER scoring to end_session (score_session) — no eval, no
    # progression, no advance here.
    if state.get("task_type") in _TEST_TASK_TYPES:
        from app.services.simulation_service import Speaker
        # The sim self-terminated on a prior round (Director close or the hard
        # round cap set session_over). Don't run another round — wind down and
        # point the learner at their scored recap (via /end).
        if state.get("session_over"):
            from app.services.simulation_service import Speaker

            closing = (
                "That's where we'll close the session. Tap finish to see your "
                "scored feedback and where to focus next."
            )
            closing_speaker = (
                {"speaker_name": "Moderator", "speaker_id": "moderator_timekeeper"}
                if state.get("task_type") == TaskType.GD_TEST.value
                else {"speaker_name": "Interviewer", "speaker_id": "interviewer"}
            )
            state["messages"].append({
                "role": "assistant",
                "content": closing,
                "message_kind": "simulation_control",
                "turn_id": client_turn_id,
                **closing_speaker,
            })
            _finish_active_turn(state, client_turn_id, "completed")
            await _persist_runtime_state(state)
            yield Speaker(
                speaker_id=closing_speaker["speaker_id"],
                name=closing_speaker["speaker_name"],
            )
            yield closing
            return
        speaker_messages: list[dict] = []
        current_speaker: Speaker | None = None
        current_chunks: list[str] = []

        def flush_speaker_message() -> None:
            nonlocal current_chunks, current_speaker
            text = "".join(current_chunks).strip()
            if current_speaker and text:
                speaker_messages.append({
                    "role": "assistant",
                    "content": text,
                    "speaker_name": current_speaker.name,
                    "speaker_id": current_speaker.speaker_id,
                    "node_id": state["competency_node"],
                    "turn_id": client_turn_id,
                    "message_kind": "simulation_turn",
                })
            current_chunks = []

        try:
            async for item in stream_simulation_round(state):
                if isinstance(item, Speaker):
                    flush_speaker_message()
                    current_speaker = item
                elif isinstance(item, str):
                    current_chunks.append(item)
                yield item
        except Exception:
            _finish_active_turn(state, client_turn_id, "failed")
            await _persist_runtime_state(state)
            raise
        flush_speaker_message()
        _append_simulation_messages_once(state, speaker_messages)
        state["turn_count"] += 1
        state.pop("client_assessment_action", None)
        if not state.get("session_over"):
            _bump_session_version(state)
        _finish_active_turn(state, client_turn_id, "completed")
        await _persist_runtime_state(state)
        return

    # Sentiment pivot: flag support BEFORE the graph builds its prompt so the
    # coaching directives (via coach_view) reflect it this turn.
    state["needs_support"] = _detect_frustration(user_input)
    pre_scored_snapshot = copy.deepcopy(state)

    # turn 0 was the opening (assistant-only), so turn_count>=1 means there is a
    # real learner answer to score this turn. Capture before the graph runs.
    did_eval = state["turn_count"] >= 1
    if did_eval:
        state["last_evaluated_task_contract"] = copy.deepcopy(
            pre_scored_snapshot.get("active_task_contract") or {}
        )

    # Graph = decision brain: evaluate the answer, pick the pedagogy move,
    # build its prompt. Returns partial-state updates we merge back.
    if state.get("task_type") == TaskType.GD_PREP.value:
        state["last_evaluated_gd_topic"] = _gd_prompt_topic_for_state(state)
    graph = get_graph()
    updates = await graph.ainvoke(state)
    state.update(updates)
    _stage_pending_prompt_attempt_type(
        state,
        pre_scored_snapshot.get("active_prompt_attempt_type"),
    )

    if did_eval and state.get("evaluation_retry_required"):
        state["active_game_prompt"] = None
        state["pending"] = None
        state["pending_game"] = None
        state["pending_prompt_attempt_type"] = None
        state["messages"].append({
            "role": "assistant",
            "content": _EVALUATION_RETRY_TEXT,
            "node_id": state.get("competency_node"),
            "turn_id": client_turn_id,
            "message_kind": "evaluation_retry",
        })
        state["turn_count"] += 1
        _bump_session_version(state)
        _finish_active_turn(state, client_turn_id, "completed")
        await _persist_runtime_state(state)
        yield _EVALUATION_RETRY_TEXT
        return

    counted_eval = did_eval and not _is_non_scorable_prep_integrity(state)
    if did_eval and not counted_eval:
        state["evaluation_integrity_failure"] = {
            "code": "invalid_transfer_context",
            "criterion_ids": ["transfer_context"],
        }

    # Post-graph affect: LLM diagnosis is more reliable than regex. Upgrade
    # needs_support if the eval flagged frustration/confusion this turn.
    diag_affect = state.get("last_diagnosis", {}).get("affect", "neutral")
    if diag_affect in ("frustrated", "confused"):
        state["needs_support"] = True
        state["frustration_turns"] = state.get("frustration_turns", 0) + 1
    else:
        state["frustration_turns"] = 0

    # Post-graph goodbye: natural farewells ("I need to head out") evade the
    # pre-graph exact-match gate. Check LLM diagnosis and close gracefully.
    if state.get("last_diagnosis", {}).get("goodbye", False):
        _mark_terminal(state, "learner_ended")
        state["active_game_prompt"] = None
        farewell = _farewell(state)
        state["messages"].append({"role": "assistant", "content": farewell})
        _finish_active_turn(state, client_turn_id, "completed")
        await _persist_runtime_state(state)
        yield farewell
        return

    prev_node = state["competency_node"]
    progress_mastery: float | None = None
    progress_readiness_score: float | None = None
    progress_clean_streak: int | None = None
    progress_attempts: int | None = None
    suppress_same_node_response = False
    advanced_or_done = False
    same_node_generation_failed = False
    scored_turn_persisted = False
    completion_feedback: str | None = None
    if counted_eval:
        _update_progress(state)
        completion_rubric_result = copy.deepcopy(state.get("last_rubric_result"))
        will_attempt_advance = state.get("clean_streak", 0) >= int(
            state.get("advance_streak") or ADVANCE_STREAK
        )
        # BACK-07: after exactly DOWN_LADDER_FAILS consecutive hard fails, re-query
        # weaknesses live so the NEXT turn's coach prompt surfaces fresh weak spots.
        # Only fires at the threshold (not every fail after it) to avoid repeated DB
        # round-trips.
        progress_mastery = round(state["current_mastery"], 4)
        progress_readiness_score = float(state.get("readiness_score") or 0.0)
        progress_clean_streak = state.get("clean_streak", 0)
        progress_attempts = state.get("attempts", 0)
        if will_attempt_advance:
            # _maybe_advance clears the scored diagnosis for the next node, so
            # commit advancing turns before calling it. Same-node turns wait
            # until their assistant response is safely generated.
            await _track_turn(state, prev_node)
            if state.get("level_fails", 0) == DOWN_LADDER_FAILS:
                await _maybe_refresh_weaknesses(state)
            scored_turn_persisted = True
        await _maybe_advance(state)
        if state["module_done"] or state["competency_node"] != prev_node:
            advanced_or_done = True
            # The graph prepared a same-node follow-up before the service knew
            # this answer completed the node. Do not leak that stale exercise
            # into the transcript; the frontend transition card owns the break.
            state["pending"] = None
            state["pending_game"] = None
            state["pending_prompt_attempt_type"] = None
            state["active_prompt_attempt_type"] = None
            suppress_same_node_response = True
            if isinstance(completion_rubric_result, dict):
                completion_feedback = _completion_feedback_text(
                    completion_rubric_result,
                    user_input,
                )
                state["messages"].append({
                    "role": "assistant",
                    "content": completion_feedback,
                    "node_id": prev_node,
                    "turn_id": client_turn_id,
                    "message_kind": "completion_feedback",
                })
                state["turn_count"] += 1

    # Gamified path: teach_node produced a FillBlankGame instead of a GenSpec.
    # Yield the game frame directly and skip text streaming for this turn.
    # The learner's next input (filling the blank) is scored by evaluate_node
    # as a normal answer, so no special handling is needed downstream.
    if not suppress_same_node_response:
        game: dict | None = state.get("pending_game")
        if game is not None:
            bridge_feedback = (
                _deterministic_closed_bridge_feedback(state)
                if did_eval and state.get("last_graded_bridge")
                else ""
            )
            game_context = str(game.get("context", "") or "").strip()
            if bridge_feedback:
                game_context = " ".join(
                    part for part in (bridge_feedback, game_context) if part
                )
            public_game = {
                "type": game.get("type", "fill_blank"),
                "sentence": game.get("sentence", ""),
                "hint": game.get("hint", ""),
                "context": game_context,
                "options": game.get("options"),
                "turn_id": client_turn_id,
            }
            yield GamePrompt(
                type=public_game["type"],
                sentence=public_game["sentence"],
                hint=public_game["hint"],
                context=public_game["context"],
                answer_key=game.get("answer_key", ""),
                options=public_game["options"],
                turn_id=client_turn_id,
            )
            state["active_game_prompt"] = public_game
            # Record a minimal assistant turn so conversation history stays valid.
            game_message = {
                "role": "assistant",
                "content": "\n\n".join(part for part in (
                    bridge_feedback,
                    f"[Fill in the blank] {game.get('sentence', '')}",
                ) if part),
                "node_id": state.get("competency_node"),
                "turn_id": client_turn_id,
                "message_kind": "game_prompt",
            }
            game_contract_message = {
                **game_message,
                "content": str(game.get("sentence") or ""),
            }
            game_message["task_contract"] = _derived_career_task_payload(
                state,
                game_contract_message,
            )
            state["messages"].append(game_message)
            _commit_career_task_contract(state, game_message)
            _commit_pending_prompt_attempt_type(state)
            state["turn_count"] += 1
            state["pending_game"] = None
        else:
            spec: GenSpec | None = state.get("pending")
            bridge_feedback = (
                _deterministic_closed_bridge_feedback(state)
                if did_eval and state.get("last_graded_bridge")
                else ""
            )
            full = []
            fallback_text = (
                "Sorry - I lost my train of thought for a second there. "
                "Could you try that once more for me?"
            )
            fallback_message: dict | None = None
            if bridge_feedback:
                full.append(bridge_feedback)
                yield bridge_feedback
            elif spec is not None:
                try:
                    async for tok in _stream_coaching_generation(spec, state):
                        full.append(tok)
                        yield tok
                except asyncio.CancelledError:
                    if did_eval and not advanced_or_done:
                        state.clear()
                        state.update(pre_scored_snapshot)
                        state["pending"] = None
                        state["pending_game"] = None
                        state["active_game_prompt"] = None
                        state["last_error"] = {"code": "response_generation_cancelled"}
                        fallback_message = {
                            "role": "assistant",
                            "content": fallback_text,
                            "node_id": state.get("competency_node"),
                            "turn_id": client_turn_id,
                            "message_kind": "coach_fallback",
                        }
                        state["messages"].append(fallback_message)
                        state["turn_count"] = int(pre_scored_snapshot.get("turn_count") or 0) + 1
                        await _persist_runtime_state(state)
                    raise
                except Exception:
                    same_node_generation_failed = did_eval and not advanced_or_done
                    full = []  # discard partial; emit the fallback below
            text = "".join(full).strip()
            if not text:
                text = fallback_text
                yield text
            elif _looks_incomplete_coach_text(text):
                text = _deterministic_coach_repair_text(state)
                yield text
            assistant_message = {
                "role": "assistant",
                "content": text,
                "node_id": state.get("competency_node"),
                "turn_id": client_turn_id,
                "message_kind": "coach_fallback" if same_node_generation_failed else "coach_response",
            }
            if not same_node_generation_failed and _coach_response_assigns_task(state):
                assistant_message["task_contract"] = _derived_career_task_payload(
                    state,
                    assistant_message,
                )
            state["messages"].append(assistant_message)
            _commit_career_task_contract(state, assistant_message)
            state["turn_count"] += 1
            state["pending"] = None

            if not same_node_generation_failed:
                _commit_pending_prompt_attempt_type(state)

            if same_node_generation_failed:
                fallback_message = assistant_message
                state.clear()
                state.update(pre_scored_snapshot)
                state["pending"] = None
                state["pending_game"] = None
                state["active_game_prompt"] = None
                state["last_error"] = {"code": "response_generation_failed"}
                state["messages"].append(fallback_message)
                state["turn_count"] = int(pre_scored_snapshot.get("turn_count") or 0) + 1

    if counted_eval and not advanced_or_done and not same_node_generation_failed:
        # Same-node turns are committed only after the learner-visible assistant
        # response has streamed successfully. If response generation fails, the
        # fallback asks for a retry and the answer is not counted as progress.
        await _track_turn(state, prev_node)
        if state.get("level_fails", 0) == DOWN_LADDER_FAILS:
            await _maybe_refresh_weaknesses(state)
        await _persist_mastery(state)
        scored_turn_persisted = True

    if counted_eval and scored_turn_persisted:
        if completion_feedback:
            yield completion_feedback

        # Emit per-turn mastery update so the UI progress bar animates mid-stream.
        yield ProgressUpdate(
            node_id=prev_node,
            mastery=progress_mastery or 0.0,
            readiness_score=progress_readiness_score or 0.0,
            clean_streak=progress_clean_streak or 0,
            attempts=progress_attempts or 0,
        )

        # Selector rationale cue: surface WHY the path adapted, on advancing
        # turns only. last_selection is None on REPEAT and module-done turns,
        # so this naturally suppresses there. Fires after progress_update and
        # before node_advance so the UI can show the cue then open the new node.
        sel = state.get("last_selection")
        if sel and sel.get("action") in ("ADVANCE", "REMEDIATE"):
            yield AdaptationCue(
                action=sel["action"],
                band=sel.get("band", "standard"),
                rationale=sel.get("rationale", ""),
            )

        if state["module_done"]:
            recap = await refresh_session_recap(state)
            if recap:
                yield SessionRecap(**recap)
        elif state["competency_node"] != prev_node:
            # Desync fix: the answer advanced us to a new node.
            # We yield NodeAdvance to signal the frontend, but we NO LONGER
            # auto-stream the new opening. The frontend will present a "Next Skill"
            # break and call /opening manually.
            yield NodeAdvance(
                from_node=prev_node, to_node=state["competency_node"]
            )

    if did_eval and not advanced_or_done:
        _bump_session_version(state)

    _finish_active_turn(state, client_turn_id, "completed")
    await _persist_runtime_state(state)


_GD_SUBSCORES = ("participation_score", "relevance_score", "language_score")
_INT_SUBSCORES = ("clarity_score", "confidence_score")


def _project_report_subscores(report: dict, task_type: str) -> dict:
    """Null the sub-scores that belong to the OTHER assessment mode.

    The scorer always emits all five sub-scores and zeroes the inapplicable ones,
    so an interview report carried participation_score=0.0 / relevance_score=0.0
    (GD-only metrics) and a GD report carried clarity/confidence=0.0 — reading to
    the learner as a hard zero on something their session never measured. Set the
    other mode's keys to None so the UI omits them instead of showing a fake 0."""
    if task_type == TaskType.GD_TEST.value:
        drop = _INT_SUBSCORES
    elif task_type == TaskType.INTERVIEW_TEST.value:
        drop = _GD_SUBSCORES
    else:
        return report
    for k in drop:
        if k in report:
            report[k] = None
    return report


def sanitize_simulation_report_delivery(state: dict, report: dict | None) -> dict | None:
    if not isinstance(report, dict):
        return report
    from app.services.simulation_service import sanitize_report_for_delivery

    return sanitize_report_for_delivery(state, report)


async def end_session(session_id: str) -> str:
    """Back-compat wrapper: close the session and return its closing summary.

    Many callers (scripts, the older tests) depend on the bare-string return.
    `close_session` is the full-payload entry point the /end route uses to also
    surface the scored simulation report."""
    return (await close_session(session_id))["summary"]


def _closing_prep_node_id(state: dict) -> str:
    current = str(state.get("competency_node") or "")
    if state.get("task_type") not in {
        TaskType.INTERVIEW_PREP.value,
        TaskType.GD_PREP.value,
    }:
        return current
    transition = state.get("pending_node_transition")
    if not isinstance(transition, dict):
        return current
    if str(transition.get("status") or "") != "awaiting_next_opening":
        return current
    return str(transition.get("from_node") or current)


async def close_session(session_id: str) -> dict:
    """Summarize/score the session, persist memory, close it out, and return the
    full closing payload: ``{summary, report, score}``.

    For TEST-mode (assessment) sessions the whole transcript is scored once via
    `score_session`, and `report` is the full `SimulationReport` dict — the five
    sub-scores plus strengths and improvements, i.e. the deferred feedback the
    learner earned across the simulation. For coaching ("prep") sessions `report`
    is None and only the summary applies. Returning the report here is the fix for
    the recap that previously discarded every score but the one-line summary."""
    state = await get_session_state(session_id)
    if state is None:
        return {"summary": "", "report": None, "score": 0.0}
    if state.get("status") == "ended":
        return {
            "summary": state.get("session_summary") or "",
            "report": state.get("simulation_report"),
            "score": float(
                state.get("simulation_score")
                if state.get("simulation_score") is not None
                else state.get("current_mastery") or 0.0
            ),
        }
    closing_node_id = _closing_prep_node_id(state)
    node = get_node(closing_node_id)
    # TEST-mode sessions are scored once over the whole transcript (deferred from
    # the streamed rounds); the report's summary is the closing summary and its
    # score is the persisted result. PREP sessions summarise the coaching dialog.
    is_test = state.get("task_type") in _TEST_TASK_TYPES
    avg_score = state.get("current_mastery", 0.0)
    report_dict: dict | None = None
    if is_test:
        try:
            report = await score_session(state)
            summary = report.summary
            avg_score = report.score
            # The full report (sub-scores + strengths + improvements) is the
            # learner-facing payload — persisted to memory below and returned to
            # the /end route so it actually reaches the learner. Null the other
            # mode's sub-scores so the learner never sees a fake 0 on an unmeasured
            # metric (4.2).
            report_dict = _project_report_subscores(
                report.model_dump(), state.get("task_type", "")
            )
            state["simulation_report"] = report_dict
            await CareerLearningProfileService(get_storage()).record_session_report(
                user_id=state["user_id"],
                session_id=session_id,
                report_type=state.get("task_type", "test_report"),
                task_type=state.get("task_type", ""),
                module_id=state.get("module_id", ""),
                report=report_dict,
            )
        except Exception:
            logger.exception("simulation scoring failed for session=%s", session_id)
            state["last_error"] = {"code": "simulation_scoring_unavailable"}
            await _persist_runtime_state(state)
            raise SessionScoringUnavailableError("simulation_scoring_unavailable")
    else:
        try:
            summary = await summarize_session(node, state["messages"])
        except Exception:
            summary = ""
        summary = sanitize_memory_text(summary)

    # Close + persist long-term memory. This is user history, not a cache; do
    # not silently drop it if storage fails.
    store = get_storage()
    await store.end_session(
        session_id,
        final_summary=summary,
        avg_score=avg_score,
    )
    report_validity = str((report_dict or {}).get("validity_status") or "").strip()
    adaptive_memory_allowed = (
        not is_test
        or report_validity not in {"invalid_simulation", "insufficient_evidence"}
    )
    if summary and adaptive_memory_allowed:
        await store.write_memory(
            state["user_id"],
            session_id,
            closing_node_id,
            summary,
            state.get("task_type", ""),
            score=avg_score,
        )

    # Precache the TEST sibling's probe bank now that this PREP module is done,
    # so a later TEST start opens instantly instead of blocking on generation.
    # No-op for TEST sessions and single-mode modules (no distinct test sibling).
    if not is_test:
        # Best-effort optimization that warms the TEST sibling's probe bank by
        # calling the LLM. Under shared-model load that call can raise — but the
        # session is already scored and persisted above, so a precache failure must
        # NEVER 500 the /end response and lose the learner's report. Swallow + log.
        try:
            await _precache_test_items(state)
        except Exception:
            logger.warning(
                "close_session: probe precache failed for session=%s; "
                "report still returned",
                session_id,
                exc_info=True,
            )

    logger.info(
        "session_end_analytics",
        extra={
            "session_id": session_id,
            "user_id": state.get("user_id"),
            "task_type": state.get("task_type"),
            "node_id": closing_node_id,
            "turn_count": state.get("turn_count", 0),
            "avg_score": avg_score,
            "module_done": state.get("module_done", False)
        }
    )

    state["session_summary"] = summary
    state["simulation_score"] = avg_score
    state["simulation_round"] = int((state.get("blackboard") or {}).get("turn") or 0)
    if is_test:
        state["session_over"] = True
    state["status"] = "ended"
    await _persist_runtime_state(state)
    SessionStore.pop(session_id, None)
    _SESSION_LOCKS.pop(session_id, None)  # E24: don't leak a lock per closed session
    save_sessions()
    return {"summary": summary, "report": report_dict, "score": avg_score}


def get_state(session_id: str) -> dict | None:
    return SessionStore.get(session_id)


async def get_progression_map(user_id: str, module_id: str = "communication") -> list[dict]:
    """Progression map for the user for a specific module.
    Returns the full ordered list of nodes with locked/active/mastered status.
    """
    from app.content.registry import get_module

    module = get_module(module_id)

    store = get_storage()
    try:
        prog = await store.get_progression(user_id)
    except Exception as e:
        logger.exception("progression storage unavailable for user=%s module=%s", user_id, module_id)
        raise ProgressionUnavailableError("progression_unavailable") from e

    prog_by_node = {p["node_id"]: p for p in prog}

    def _state_module(state: dict) -> str | None:
        try:
            return module_of(state.get("competency_node", ""))
        except KeyError:
            return None

    # Compare process-local candidates with durable state on every map read.
    # Different workers can hold stale active sessions, so cache presence alone
    # cannot decide which skill the learner should resume.
    candidates: list[tuple[dict, float]] = []
    for state in list(SessionStore.values()):
        if (
            state.get("user_id") != user_id
            or state.get("status", "active") != "active"
            or _state_module(state) != module_id
        ):
            continue
        if _expire_state_if_needed(state):
            await _persist_runtime_state(state)
            continue
        candidates.append((state, _runtime_freshness(state.get("last_seen_at"))))

    if hasattr(store, "get_latest_active_session_runtime_for_module"):
        row = await store.get_latest_active_session_runtime_for_module(
            user_id,
            module_id,
            False,
        )
        if row:
            resumed_state = _hydrate_runtime_state(row)
            if not resumed_state.get("session_over") and _state_module(resumed_state) == module_id:
                if _expire_state_if_needed(resumed_state):
                    await _persist_runtime_state(resumed_state)
                else:
                    candidates.append((resumed_state, _runtime_freshness(row.get("updated_at"))))

    if not candidates:
        for node in module.nodes:
            if is_voice_node(node.id):
                continue
            resumed = await get_resumable_active_session_for_start(
                user_id,
                node.id,
                test_mode=False,
            )
            if resumed:
                _session_id, resumed_state = resumed
                if _state_module(resumed_state) == module_id:
                    candidates.append((resumed_state, _runtime_freshness(resumed_state.get("last_seen_at"))))
                    break

    by_session: dict[str, tuple[dict, float]] = {}
    for state, updated_at in candidates:
        session_id = str(state.get("session_id") or "")
        current = by_session.get(session_id)
        if session_id and (current is None or updated_at >= current[1]):
            by_session[session_id] = (state, updated_at)
    ordered = sorted(by_session.values(), key=lambda item: item[1], reverse=True)
    active = [state for state, _updated_at in ordered]
    for state in active:
        SessionStore[state["session_id"]] = state
    primary_active = next((s for s in active if not s.get("reattempt")), None)
    curr_node = primary_active.get("competency_node") if primary_active else None
    if curr_node and bool((prog_by_node.get(curr_node) or {}).get("node_completed")):
        curr_node = None
    curr_streak = primary_active.get("clean_streak", 0) if primary_active else 0
    reattempt_by_node = {
        s.get("competency_node"): s.get("session_id")
        for s in active
        if s.get("reattempt")
    }

    out = []
    found_active = False

    for node in module.nodes:
        # Voice nodes are gated "coming soon" and excluded from placement and
        # the advance ladder — so they must not appear on the learner's path
        # either, or it shows steps that never unlock and a "complete" module
        # with locked nodes trailing below it.
        if is_voice_node(node.id):
            continue
        p = prog_by_node.get(node.id)
        mastery = float(p.get("ema") or 0.0) if p else 0.0
        best_mastery = float(p.get("best_ema") or mastery) if p else 0.0
        best_independent_score = float(p.get("best_independent_score") or 0.0) if p else 0.0
        # Career prep separates "advanced past this node" from actual mastery.
        # Older school/communication modules keep the legacy completed=>mastered
        # display contract. Do not let new nullable/default columns on old rows
        # turn completed school/communication nodes back into active nodes.
        career_prep_module = module_id in {"interview", "group_discussion"}
        is_complete = bool(p.get("node_completed")) if p else False
        stored_mastered = p.get("node_mastered") if p else None
        if career_prep_module:
            node_mastered = bool(stored_mastered)
        else:
            node_mastered = bool(stored_mastered) or is_complete
        display_mastery = (
            1.0
            if node_mastered
            else max(mastery, best_mastery, best_independent_score)
        )
        is_current = node.id == curr_node
        streak = curr_streak if is_current else 0

        stored_display_status = (
            p.get("display_status")
            if p and p.get("display_status")
            else ""
        )
        if node_mastered:
            status = "mastered"
        elif is_complete and career_prep_module:
            status = (
                stored_display_status
                if stored_display_status in {"ready_to_advance", "proficient", "needs_remediation"}
                else "ready_to_advance"
            )
        elif is_complete:
            status = "mastered"
        elif is_current:
            status = "active"
            found_active = True
        elif stored_display_status == "needs_remediation":
            status = stored_display_status
        elif not found_active and not curr_node:
            status = "active"
            found_active = True
        else:
            status = "locked"

        out.append({
            "node_id": node.id,
            "title": node.title,
            "mastery": mastery,
            "raw_mastery": mastery,
            "best_mastery": best_mastery,
            "display_mastery": display_mastery,
            "completed": is_complete,
            "mastered": node_mastered,
            "node_mastered": node_mastered,
            "display_status": status,
            "attempts": int(p.get("attempts") or 0) if p else 0,
            "best_independent_score": best_independent_score,
            "independent_passes": int(p.get("independent_passes") or 0) if p else 0,
            "transfer_passes": int(p.get("transfer_passes") or 0) if p else 0,
            "pressure_passes": int(p.get("pressure_passes") or 0) if p else 0,
            "scaffold_successes": int(p.get("scaffold_successes") or 0) if p else 0,
            "last_gap": p.get("last_gap", "") if p else "",
            "mastery_evidence": (
                public_mastery_evidence(list(p.get("mastery_evidence") or []))
                if p and node_mastered
                else []
            ),
            "clean_streak": streak,
            "status": status,
            "reattempt_session_id": reattempt_by_node.get(node.id),
        })

    return out


async def place_user(
    module_id: str,
    writing_sample: str | None = None,
    self_report: str | None = None,
    grade: int | None = None,
    user_id: str | None = None,
) -> dict:
    """Onboarding placement: pick the STARTING node in a module.

    school_english places by school grade (2-5), not CEFR — a primary ladder,
    not a proficiency continuum (Phase 0.3). For comm/interview/gd, a writing
    sample drives a Flash-Lite CEFR estimate; otherwise the learner's
    self-report bucket (beginner/intermediate/advanced/fluent) maps to a band.
    Falls back to B1 if neither is usable. Returns the starting node so the UI
    can show what was placed and why before starting the session.
    """
    module = get_module(module_id)  # raises KeyError on unknown module

    if uses_grade_placement(module_id):
        g = grade if grade is not None else 2
        node = grade_placement_node(g)
        
        if user_id:
            try:
                store = get_storage()
                for n in module.nodes:
                    if n.id == node.id:
                        break
                    await store.upsert_mastery(
                        user_id=user_id,
                        node_id=n.id,
                        ema=1.0,
                        attempts=2,
                        clean_pass=True,
                        node_completed=True,
                    )
            except Exception as e:
                logger.warning("Failed to persist placement for %s: %s", user_id, e)

        return {
            "module_id": module_id,
            "module_title": module.title,
            "starting_node": node.id,
            "node_title": node.title,
            "node_cefr": node.cefr,
            "grade": max(2, min(5, g)),
            "rationale": f"Placed by school grade {g}.",
        }

    estimated_cefr = "B1"
    rationale = "Default placement — no sample or self-report provided."
    if writing_sample and writing_sample.strip():
        try:
            result = await evaluate_placement(module.title, writing_sample)
            # local model under-scores samples; one band of headroom corrects it
            estimated_cefr = _bump_band(result.cefr)
            rationale = result.rationale
        except Exception:
            # AI offline -> degrade to self-report / default, never block onboarding
            if self_report:
                estimated_cefr = SELF_REPORT_CEFR.get(self_report.lower(), "B1")
                rationale = f"Estimated from self-report: {self_report}."
    elif self_report:
        estimated_cefr = SELF_REPORT_CEFR.get(self_report.lower(), "B1")
        rationale = f"Estimated from self-report: {self_report}."

    node = placement_node(module_id, estimated_cefr)
    
    # Preserve legacy placement persistence for non-Career modules only. Career
    # placement selects a starting node without claiming evidence for prior skills.
    if user_id and module_id not in {"interview", "group_discussion"}:
        try:
            store = get_storage()
            for n in module.nodes:
                if n.id == node.id:
                    break
                await store.upsert_mastery(
                    user_id=user_id,
                    node_id=n.id,
                    ema=1.0,
                    attempts=2,
                    clean_pass=True,
                    node_completed=True,
                )
        except Exception as e:
            logger.warning("Failed to persist placement for %s: %s", user_id, e)

    return {
        "module_id": module_id,
        "module_title": module.title,
        "starting_node": node.id,
        "node_title": node.title,
        "node_cefr": node.cefr,
        "estimated_cefr": estimated_cefr,
        "rationale": rationale,
    }


# ---------- internals ----------

def _require(session_id: str) -> dict:
    state = SessionStore.get(session_id)
    if state is None:
        raise KeyError(f"no active session: {session_id}")
    return state


def _is_non_scorable_prep_integrity(state: dict) -> bool:
    result = state.get("last_rubric_result")
    return bool(
        isinstance(result, dict)
        and "minimum_gate:transfer_context" in set(result.get("blockers") or [])
    )


def _career_progress_evidence_id(state: dict, rubric_result: dict) -> str:
    contract = state.get("last_evaluated_task_contract")
    if not isinstance(contract, dict):
        contract = state.get("active_task_contract") if isinstance(state.get("active_task_contract"), dict) else {}
    prompt_text = ""
    seen_latest_user = False
    for message in reversed(state.get("messages") or []):
        if message.get("role") == "user":
            seen_latest_user = True
            continue
        if seen_latest_user and message.get("role") == "assistant":
            prompt_text = " ".join(str(message.get("content") or "").casefold().split())
            break
    identity = {
        "user_id": str(state.get("user_id") or ""),
        "node_id": str(state.get("competency_node") or ""),
        "attempt_type": str(rubric_result.get("attempt_type") or "independent"),
        "prompt_text": prompt_text,
        "active_role": str(contract.get("active_role") or "").casefold(),
        "active_topic": str(contract.get("active_topic") or "").casefold(),
        "semantic_anchors": sorted(str(item).casefold() for item in contract.get("semantic_anchors") or []),
        "participant_claims": contract.get("participant_claims") or [],
    }
    payload = json.dumps(identity, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _update_progress(state: dict) -> None:
    """Fold the latest score into the clean-pass streak + down-ladder counters.

    Called once per scored turn, before _maybe_advance. A clean pass extends the
    streak and clears the struggle counters; a non-pass breaks the streak, and a
    run of hard fails turns on the scaffold so the next pedagogy turn drops to an
    almost-automatic task."""
    # Non-struggle guards — turns that score 0.0 but are NOT skill failures must
    # not break the clean streak or trip level_fails/scaffold:
    #   * fluent-but-off-task (council fix #1/#6): graph routes to redirect.
    #   * non-English / gibberish (B11/B12, Test-fix-01): graph routes to clarify;
    #     not producing English is a comprehension gap, not a failed attempt.
    diag = state.get("last_diagnosis", {})
    if not diag.get("english", True):
        return
    # Competent English again: the consecutive non-English run that drives the
    # clarify cap is broken, so refund clarify_attempts (P1, mirrors the redirect
    # refund below). This sits ABOVE the on_task guard on purpose — producing
    # English ends the clarify streak whether or not the answer is on-task — and it
    # cannot defeat the cap, because an english=True turn never routes through
    # clarify (clarify only fires, and increments, when english is False, on which
    # turns this function early-returns above without touching the counter).
    state["clarify_attempts"] = 0
    if not diag.get("on_task", True):
        return
    # Back on-task: the fluent-off-task streak is over, so refund the redirect cap
    # (P0-6) — a learner who strayed then returned is not penalized on their next
    # stray.
    state["redirect_attempts"] = 0
    score = state.get("last_clean_pass_score", state.get("last_eval_score", 0.0))
    rubric_result = state.get("last_rubric_result")
    is_career_prep = state.get("task_type") in {TaskType.INTERVIEW_PREP.value, TaskType.GD_PREP.value}
    if is_career_prep and _is_non_scorable_prep_integrity(state):
        return
    if is_career_prep and not isinstance(rubric_result, dict):
        # Career prep must be governed by criterion-level rubric evidence. If a
        # model/schema/runtime failure prevents that evidence from reaching the
        # service, fail closed instead of falling back to the legacy scalar
        # clean-streak path that caused premature "next skill ready" states.
        state["clean_streak"] = 0
        if score < FAIL_SCORE:
            state["level_fails"] = state.get("level_fails", 0) + 1
        if state.get("level_fails", 0) >= DOWN_LADDER_FAILS:
            state["scaffold"] = 1
        return
    if isinstance(rubric_result, dict):
        credit = compute_attempt_credit(
            {
                "node_mastered": state.get("node_mastered", False),
                "display_status": state.get("display_status", "active"),
                "best_independent_score": state.get("best_independent_score", 0.0),
                "independent_passes": state.get("independent_passes", 0),
                "transfer_passes": state.get("transfer_passes", 0),
                "pressure_passes": state.get("pressure_passes", 0),
                "scaffold_successes": state.get("scaffold_successes", 0),
                "meaningful_attempts": state.get("meaningful_attempts", 0),
                "readiness_score": state.get("readiness_score", 0.0),
                "last_gap": state.get("last_gap", ""),
                "mastery_evidence": state.get("mastery_evidence", []),
                "credited_evidence_ids": state.get("credited_evidence_ids", []),
            },
            rubric_result,
            scaffolded=bool(state.get("last_graded_bridge")),
            evidence_id=_career_progress_evidence_id(state, rubric_result),
        )
        state.update(credit)
        if (
            int(state.get("independent_passes") or 0) >= 2
            and not state.get("core_qualified")
            and str(rubric_result.get("attempt_type") or "independent") == "independent"
            and bool(rubric_result.get("pass_eligible"))
        ):
            state["core_qualified"] = True
            turn_ref = state.get("active_turn_id") or state.get("attempts") or "unknown"
            state["core_qualification_turn_id"] = (
                f"{state.get('session_id')}:{turn_ref}:{state.get('competency_node')}"
            )
            state["core_qualification_evidence"] = {
                "evaluation_id": state["core_qualification_turn_id"],
                "user_id": state.get("user_id"),
                "node_id": state.get("competency_node"),
                "attempt_type": "independent",
                "pass_eligible": True,
                "blockers": [],
                "effective_score": float(rubric_result.get("effective_score") or 0.0),
                "learner_answer": str(state.get("user_input") or "").strip(),
                "task_contract": copy.deepcopy(state.get("active_task_contract") or {}),
                "active_topic": (
                    _gd_prompt_topic_for_state(state)
                    if state.get("task_type") == TaskType.GD_PREP.value
                    else ""
                ),
            }
    clean_pass_eligible = score >= PASS_SCORE
    if isinstance(rubric_result, dict):
        clean_pass_eligible = (
            bool(rubric_result.get("pass_eligible"))
            and state.get("display_status") in {"ready_to_advance", "mastered"}
        )
    if clean_pass_eligible:
        # A correct BRIDGE fill (graded deterministically against its answer key,
        # BRIDGE_CORRECT_SCORE == PASS_SCORE) is a scaffolded sub-step, NOT a clean
        # pass at this node: it still breaks the fail streak and refunds the bridge
        # cap (below), but must NOT accrue toward the advance streak — else two
        # scaffolded-down fills would promote a struggling learner to harder
        # content (H1). `last_route` is the wrong signal here (route_node has
        # already moved it past "bridge" for a >= PASS score), so gate on the
        # bridge-grade flag evaluate_node set THIS turn.
        if not state.get("last_graded_bridge"):
            if isinstance(rubric_result, dict):
                state["clean_streak"] = max(
                    state.get("clean_streak", 0) + 1,
                    int(state.get("advance_streak") or ADVANCE_STREAK),
                )
            else:
                state["clean_streak"] = state.get("clean_streak", 0) + 1
        state["level_fails"] = 0
        state["strengthen_attempts"] = 0
        # Clean pass: the learner climbed out of bridge (sub-0.4) territory, so the
        # consecutive-bridge run is over — refund the bridge cap (P1). Gated on a
        # full PASS, NOT merely score >= FAIL_SCORE: route_node runs BEFORE this
        # fold (graph.ainvoke precedes _update_progress in the turn) and increments
        # bridge_attempts on the same turn it picks bridge, and a >= PASS answer
        # provably never routes to bridge — so resetting here can never wipe a fresh
        # increment and re-open the infinite-bridge soft-lock. Mirrors level_fails /
        # strengthen_attempts, the sibling down-ladder counters that also clear only
        # on a clean pass.
        state["bridge_attempts"] = 0
        state["scaffold"] = 0
        return
    state["clean_streak"] = 0
    if score < FAIL_SCORE:
        state["level_fails"] = state.get("level_fails", 0) + 1
    if state.get("level_fails", 0) >= DOWN_LADDER_FAILS:
        state["scaffold"] = 1


async def _maybe_advance(state: dict) -> None:
    """Advance the node on a consecutive clean-pass streak (NOT EMA mastery).

    Records the just-finished node's clean flag, recomputes module pass-rate for
    remediation, then runs the Spec B two-stage selector to pick the next node
    and resets every per-node counter for it.

    Spec B selector (advancement primitive): the deterministic stage
    (`compute_valid_candidates`) narrows the valid next-content set; only when it
    leaves more than one candidate does the single LLM call (`select_next_content`)
    decide. In the linear MVP module there is exactly ONE candidate (the linear
    next node), so the fast path below synthesizes the same ADVANCE decision the
    old `next_node` block produced — no model call — and the reset is byte-for-byte
    the previous behavior. That is why the existing advance tests stay green."""
    # Clear any stale read from a prior turn before the gate so a non-advancing
    # turn reports no selection (transient; never persisted).
    state["last_selection"] = None
    if state.get("clean_streak", 0) < state.get("advance_streak", ADVANCE_STREAK):
        return

    node_id = state["competency_node"]
    is_career_prep = state.get("task_type") in {TaskType.INTERVIEW_PREP.value, TaskType.GD_PREP.value}
    clean = (
        bool(state.get("node_mastered"))
        if is_career_prep
        else state["attempts"] <= CLEAN_PASS_MAX_ATTEMPTS
    )
    state["node_history"][node_id] = {"attempts": state["attempts"], "clean": clean}
    state["remediation"] = _passrate_below_floor(state)

    # Stage 1: deterministic valid candidates. Empty -> module finished.
    candidates = compute_valid_candidates(state)
    if not candidates:
        state["module_done"] = True
        _mark_terminal(state, "module_done")
        state["active_prompt_attempt_type"] = None
        state["pending_prompt_attempt_type"] = None
        # Module finished above the clean-rate floor -> surface a review section.
        state["review_level"] = not state["remediation"]
        # Mark the last node as completed in the DB on module finish.
        await get_storage().upsert_mastery(
            state["user_id"],
            node_id,
            state["current_mastery"],
            state["attempts"],
            clean,
            node_completed=True,
            node_mastered=bool(state.get("node_mastered")) if is_career_prep else clean,
            display_status=(
                state.get("display_status") or "ready_to_advance"
                if is_career_prep
                else "mastered" if clean else "completed"
            ),
            best_independent_score=state.get("best_independent_score", 0.0),
            independent_passes=state.get("independent_passes", 0),
            transfer_passes=state.get("transfer_passes", 0),
            pressure_passes=state.get("pressure_passes", 0),
            scaffold_successes=state.get("scaffold_successes", 0),
            last_gap=state.get("last_gap", ""),
            mastery_evidence=state.get("mastery_evidence", []),
        )
        return

    if len(candidates) == 1:
        # Fast path: deterministic next step. Reproduces the old linear advance
        # exactly — no LLM call (Spec B: never call the model with one candidate).
        cand = candidates[0]
        decision = SelectionDecision(
            action=cand["action"],
            next_ref=cand["next_ref"],
            band=cand.get("band", "standard"),
            rationale="ready for the next skill",
        )
    else:
        # Stage 2: more than one candidate -> one structured LLM call, then
        # validate/backstop. A model/transport failure never blocks the advance.
        snapshot = build_selection_snapshot(state)
        try:
            decision = await select_next_content(snapshot, candidates)
        except Exception:
            decision = fallback_decision(state, candidates)
        decision = validate_decision(decision, candidates, state)

    # Surface the selector's read for this turn's adaptation cues (transient).
    state["last_selection"] = {
        "action": decision.action,
        "band": decision.band,
        "rationale": decision.rationale,
    }

    # REPEAT keeps the learner on the current node: hold position, reset the
    # streak so they must earn the next advance again.
    if decision.action == "REPEAT":
        state["clean_streak"] = 0
        return

    # Mark the completed node in the DB. Career prep stores "ready/proficient"
    # separately from true mastery; legacy modules still pass mastered status
    # through the non-career branch below.
    await get_storage().upsert_mastery(
        state["user_id"],
        node_id,
        state["current_mastery"],
        state["attempts"],
        clean,
        node_completed=True,
        node_mastered=bool(state.get("node_mastered")) if is_career_prep else clean,
        display_status=(
            state.get("display_status") or "ready_to_advance"
            if is_career_prep
            else "mastered" if clean else "completed"
        ),
        best_independent_score=state.get("best_independent_score", 0.0),
        independent_passes=state.get("independent_passes", 0),
        transfer_passes=state.get("transfer_passes", 0),
        pressure_passes=state.get("pressure_passes", 0),
        scaffold_successes=state.get("scaffold_successes", 0),
        last_gap=state.get("last_gap", ""),
        mastery_evidence=state.get("mastery_evidence", []),
    )

    # Fast clean advance (cleared the node within the clean-pass cap) earns a
    # harder tester stretch on the next node; a grind-it-out advance does not.
    state["tester_level"] = clean
    # `review_level` is a per-node SECTION flag set only when a module finishes
    # (above). It is NOT auto-cleared, and level_kind reads it BEFORE tester_level,
    # so a value leaking in from a prior finished module would mask every node in
    # the next module as "review". Reset it here with the rest of the per-node
    # slate so a normal advance always starts the new node section-clean.
    state["review_level"] = False
    # advance: fresh mastery/attempt/streak counters for the next node
    transition = {
        "transition_id": uuid.uuid4().hex,
        "from_node": node_id,
        "from_title": get_node(node_id).title,
        "from_display_status": state.get("display_status", "active"),
        "from_node_mastered": bool(state.get("node_mastered", False)),
        "from_last_gap": state.get("last_gap", ""),
        "from_readiness_score": float(state.get("readiness_score") or 0.0),
        "from_mastery": float(state.get("current_mastery") or 0.0),
        "from_clean_streak": int(state.get("clean_streak") or 0),
        "from_attempts": int(state.get("attempts") or 0),
        "to_node": decision.next_ref,
        "to_title": get_node(decision.next_ref).title,
        "status": "awaiting_next_opening",
        "created_at": time.time(),
        "attempts": 0,
        "last_error": None,
    }
    state["competency_node"] = decision.next_ref
    state["current_mastery"] = 0.0
    state["attempts"] = 0
    state["session_attempts"] = 0   # re-arm ceiling-escape at the new node
    state["bridge_attempts"] = 0
    state["clarify_attempts"] = 0
    state["redirect_attempts"] = 0
    state["served_bridge_ids"] = []
    state["pending_answer_key"] = None
    state["clean_streak"] = 0
    state["level_fails"] = 0
    state["strengthen_attempts"] = 0
    state["scaffold"] = 0
    state["needs_support"] = False
    state["last_diagnosis"] = {}
    state["last_rubric_result"] = None
    state["tutor_turn_plan"] = None
    state["last_eval_score"] = 0.0
    state["last_clean_pass_score"] = 0.0
    state["node_mastered"] = False
    state["display_status"] = "active"
    state["best_independent_score"] = 0.0
    state["independent_passes"] = 0
    state["transfer_passes"] = 0
    state["pressure_passes"] = 0
    state["core_qualified"] = False
    state["core_qualification_turn_id"] = None
    state["core_qualification_evidence"] = None
    state["scaffold_successes"] = 0
    state["meaningful_attempts"] = 0
    state["readiness_score"] = 0.0
    state["last_gap"] = ""
    state["mastery_evidence"] = []
    state["credited_evidence_ids"] = []
    state["active_prompt_attempt_type"] = None
    state["pending_prompt_attempt_type"] = None
    state["opening_streamed"] = False
    state["pending_node_transition"] = transition
    state["input_allowed"] = False
    state["block_reason"] = "awaiting_next_skill"
    state["session_version"] = int(state.get("session_version") or 1) + 1


def _passrate_below_floor(state: dict) -> bool:
    history = state["node_history"]
    if not history:
        return False
    clean = sum(1 for h in history.values() if h["clean"])
    return (clean / len(history)) < PASSRATE_FLOOR


def _append_unique_limited(items: list, value: str, *, limit: int = 8) -> None:
    text = str(value or "").strip()
    if not text or text in items:
        return
    items.append(text)
    del items[:-limit]


def public_mastery_evidence(state_or_items: dict | list) -> list:
    if isinstance(state_or_items, dict):
        if not state_or_items.get("node_mastered"):
            return []
        items = state_or_items.get("mastery_evidence") or []
    else:
        items = state_or_items
    public: list = []
    for item in items or []:
        if isinstance(item, str):
            if item.strip():
                public.append(item)
            continue
        if not isinstance(item, dict) or not item.get("criteria"):
            continue
        public.append({
            key: copy.deepcopy(value)
            for key, value in item.items()
            if key != "evidence_id"
        })
    return public[-8:]


def _update_session_learning_delta(
    state: dict,
    rubric_result: dict,
    user_answer: str,
    evaluation_id: str,
) -> None:
    delta = state.setdefault("session_learning_delta", {
        "strengths": [],
        "active_gaps": [],
        "repeated_issue_counts": {},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": [],
        "applied_evaluation_ids": [],
    })
    applied_ids = delta.setdefault("applied_evaluation_ids", [])
    if evaluation_id in applied_ids:
        return
    applied_ids.append(evaluation_id)
    del applied_ids[:-100]
    delta["module_id"] = state.get("module_id") or _module_id_for_state(str(state.get("competency_node") or ""))
    delta["task_type"] = state.get("task_type", "")
    strengths = delta.setdefault("strengths", [])
    active_gaps = delta.setdefault("active_gaps", [])
    growth_signals = delta.setdefault("growth_signals", [])
    resolved_candidates = delta.setdefault("resolved_candidates", [])
    evidence_quotes = delta.setdefault("latest_evidence_quotes", [])
    repeated = delta.setdefault("repeated_issue_counts", {})

    for strength in rubric_result.get("strengths") or []:
        _append_unique_limited(strengths, str(strength), limit=8)

    gap = str(rubric_result.get("next_focus") or "").strip()
    score = float(rubric_result.get("effective_score", rubric_result.get("score", 0.0)) or 0.0)
    if gap and score < PASS_SCORE:
        _append_unique_limited(active_gaps, gap, limit=8)
        repeated[gap] = int(repeated.get(gap) or 0) + 1
    elif gap and bool(rubric_result.get("pass_eligible")):
        _append_unique_limited(growth_signals, gap, limit=8)
    if gap and bool(rubric_result.get("mastery_eligible")):
        _append_unique_limited(resolved_candidates, gap, limit=8)

    for criterion_id in rubric_result.get("required_missing") or []:
        criterion_key = f"criterion:{str(criterion_id or '').strip()}"
        if criterion_key != "criterion:":
            repeated[criterion_key] = int(repeated.get(criterion_key) or 0) + 1
    normalized_answer = re.sub(r"\s+", " ", str(user_answer or "").strip()).lower()
    for criterion in rubric_result.get("criteria") or []:
        if not isinstance(criterion, dict):
            continue
        criterion_id = str(criterion.get("id") or "").strip()
        if criterion_id and criterion.get("met") is False:
            criterion_key = f"criterion:{criterion_id}"
            repeated[criterion_key] = max(int(repeated.get(criterion_key) or 0), 1)
        quote = " ".join(str(criterion.get("evidence_quote") or "").split())
        if (
            quote
            and quote.lower() in normalized_answer
        ):
            _append_unique_limited(evidence_quotes, quote[:260], limit=8)


async def _track_turn(state: dict, node_id: str) -> None:
    """Log the scored answer + aggregate a weakness, through the dispatcher.

    Storage failure is a real product error: losing turns/weaknesses breaks
    personalization, progress, and assessment targeting."""
    diag = state.get("last_diagnosis", {})
    score = state.get("last_eval_score", 0.0)
    on_task = diag.get("on_task", True)
    english = diag.get("english", True)
    affect = diag.get("affect", "neutral")
    # Stash the affect/score of THIS scored answer (FIX #4). On an advancing turn,
    # _maybe_advance (called after _track_turn) clears last_diagnosis/last_eval_score
    # BEFORE the SSE "done" frame is built, so the done frame would otherwise show
    # neutral/0.0 instead of the real affect of the answer that advanced. This field
    # is NOT cleared on advance, so _state_snapshot can source the display values here.
    state["last_turn_affect"] = {
        "affect": affect,
        "on_task": on_task,
        "english": english,
        "last_eval_score": score,
        "scaffolded": bool(state.get("last_graded_bridge")),
    }
    store = get_storage()
    await store.record_turn(
        state["session_id"],
        state["user_id"],
        node_id,
        score,
        on_task=on_task,
        english=english,
        affect=affect,
    )
    rubric_result = state.get("last_rubric_result") or {}
    tutor_plan = state.get("tutor_turn_plan") or {}
    if rubric_result and hasattr(store, "record_turn_evaluation"):
        turn_id = state.get("active_turn_id") or state.get("last_turn_id")
        attempt_index = int(state.get("attempts") or 0)
        evaluation_id = f"{state['session_id']}:{turn_id or attempt_index}:{node_id}"
        await store.record_turn_evaluation(
            evaluation_id=evaluation_id,
            session_id=state["session_id"],
            user_id=state["user_id"],
            node_id=node_id,
            turn_id=turn_id,
            attempt_index=attempt_index,
            attempt_type=str(rubric_result.get("attempt_type") or "independent"),
            user_answer=str(state.get("user_input") or ""),
            rubric_version="prep-rubric-v1",
            raw_score=float(rubric_result.get("raw_score", rubric_result.get("score", score)) or 0.0),
            effective_score=float(rubric_result.get("effective_score", score) or 0.0),
            criteria_json=list(rubric_result.get("criteria") or []),
            blockers=list(rubric_result.get("blockers") or []),
            pass_eligible=bool(rubric_result.get("pass_eligible")),
            advance_eligible=state.get("display_status") in {"ready_to_advance", "mastered"},
            mastery_eligible=bool(rubric_result.get("mastery_eligible")),
            tutor_plan_json=dict(tutor_plan),
            context_json={
                "active_topic": str(state.get("last_evaluated_gd_topic") or ""),
                "task_type": str(state.get("task_type") or ""),
                "task_contract": copy.deepcopy(
                    state.get("last_evaluated_task_contract")
                    or state.get("active_task_contract")
                    or {}
                ),
            },
            model_name=get_settings().ollama_model if get_settings().ai_backend == "local" else "gemini",
            prompt_version="prep-eval-v1",
        )
        _update_session_learning_delta(
            state,
            dict(rubric_result),
            str(state.get("user_input") or ""),
            evaluation_id,
        )
        await CareerLearningProfileService(store).record_prep_turn_evaluation(
            evaluation_id=evaluation_id,
            state=state,
            rubric_result=dict(rubric_result),
            tutor_plan=dict(tutor_plan),
            user_answer=str(state.get("user_input") or ""),
            attempt_index=attempt_index,
        )
    # A genuinely weak answer aggregates a weakness row keyed by SkillID.
    # Skip the fluent-but-off-task case (competent English to the wrong
    # question is not a skill weakness — mirrors _update_progress's guard).
    if score < FAIL_SCORE and not (english and not on_task):
        # Non-English answers are a language weakness regardless of next_focus;
        # otherwise coerce the model's focus hint onto the closed taxonomy.
        skill_id = (
            "LANGUAGE_NOT_ENGLISH"
            if not english
            else coerce_skill_id(diag.get("next_focus", ""))
        )
        await store.bump_weakness(
            state["user_id"],
            state.get("task_type", ""),
            skill_id,
            score,
            raw=diag.get("next_focus", ""),
        )


async def _load_or_generate_probe_items(
    user_id: str,
    task_type: str,
    career_context: dict | None = None,
    scenario_config: dict | None = None,
    context_hash: str = "default",
) -> list[dict]:
    """Probe bank for a TEST session: precache first, else regenerate (sync).

    Reads the bank precomputed at the PREP sibling's end_session, honouring the
    TTL so a drifted entry counts as a miss. On miss/stale, generates inline and
    writes it back so a later start in the same window is fast. Returns
    list[dict] (JSON-persistable on TutorState); ProbeItem objects are projected
    via model_dump()."""
    store = get_storage()
    cached = await store.get_cached_test_items(
        user_id, task_type, context_hash=context_hash, max_age=TEST_ITEM_TTL
    )
    if cached:
        return cached
    items = await generate_test_items(
        user_id,
        task_type,
        career_context=career_context or {},
        scenario_config=scenario_config or {},
    )
    dicts = [it.model_dump() for it in items]
    await store.cache_test_items(user_id, task_type, dicts, context_hash=context_hash)
    return dicts


async def _precache_test_items(state: dict) -> None:
    """At PREP end, precompute + cache the TEST sibling's probe bank.

    Resolves the distinct test sibling via test_counterpart; value-equality means
    the module has no assessment variant (single-mode / already a test value), so
    there is nothing to precache and we skip. Best-effort: never let a precache
    miss break session teardown. The caller catches and logs this optimization."""
    prep_tt = state.get("task_type", "")
    test_tt = test_counterpart(prep_tt)
    if test_tt == prep_tt:
        return  # no distinct TEST sibling -> nothing to precache
    generation_context = copy.deepcopy(state.get("career_context") or {})
    hot_delta = state.get("session_learning_delta")
    if (
        isinstance(hot_delta, dict)
        and str(hot_delta.get("task_type") or "").strip() == prep_tt
        and str(hot_delta.get("module_id") or "").strip()
        == str(state.get("module_id") or "").strip()
    ):
        generation_context["session_learning_delta"] = copy.deepcopy(hot_delta)
    items = await generate_test_items(
        state["user_id"],
        test_tt,
        career_context=generation_context,
        scenario_config=state.get("scenario_config") or {},
    )
    await get_storage().cache_test_items(
        state["user_id"],
        test_tt,
        [it.model_dump() for it in items],
        context_hash=state.get("context_hash") or "default",
    )


async def _maybe_refresh_weaknesses(state: dict) -> None:
    """Re-query the weakness table and update state at the hard-fail threshold.

    Called once per node when level_fails first reaches DOWN_LADDER_FAILS.
    Refreshing here means the NEXT turn's coach prompt gets a live weakness
    snapshot (new bumps from THIS session included), not just the session-start
    load. prep_counterpart normalises test sessions to their prep sibling's key."""
    store = get_storage()
    task_type = state.get("task_type", "")
    weakness_key = prep_counterpart(task_type)
    fresh = await store.get_weaknesses(state["user_id"], weakness_key)
    if fresh:
        state["weakness_context"] = fresh


async def _persist_mastery(state: dict) -> None:
    """Persist current-node mastery."""
    # In-progress rows must never persist clean_pass. clean_pass is only written
    # by _maybe_advance when node_completed=True, otherwise it falsely marks a
    # weak/incomplete node as mastered across progress, billing, and tiles.
    await get_storage().upsert_mastery(
        state["user_id"],
        state["competency_node"],
        state["current_mastery"],
        state["attempts"],
        False,
        node_mastered=bool(state.get("node_mastered", False)),
        display_status=state.get("display_status", "active"),
        best_independent_score=state.get("best_independent_score", 0.0),
        independent_passes=state.get("independent_passes", 0),
        transfer_passes=state.get("transfer_passes", 0),
        pressure_passes=state.get("pressure_passes", 0),
        scaffold_successes=state.get("scaffold_successes", 0),
        last_gap=state.get("last_gap", ""),
        mastery_evidence=state.get("mastery_evidence", []),
    )


# ---------- conversational helpers (teacher-feel) ----------

def _is_session_end(user_input: str) -> bool:
    """True when the learner's message is a farewell, not an answer.

    Three-tier detection:
    1. Exact-match against _END_PHRASES (≤5-word gate kept for weak tokens
       like "done"/"stop" that appear in real answers).
    2. Token-scan for PURE farewell tokens ("bye", "goodbye", "ciao", "tata") —
       these never appear inside a real answer, so no length gate is needed.
    3. Length-gated scan for AMBIGUOUS end words ("quit", "exit"): they are also
       ordinary content words, so they only end a SHORT message. A substantive
       answer like "I had to quit my previous job because of a relocation" must
       still reach scoring, not be silently discarded as a farewell.
    """
    text = (user_input or "").strip().lower().rstrip(".!,")
    if not text:
        return False

    # Exact-match path (original behaviour, guards against "done with homework")
    if len(text.split()) <= 5 and text in _END_PHRASES:
        return True

    # Token-scan: split on whitespace + strip punctuation from each word
    words = {re.sub(r"[^a-z']", "", w) for w in text.split()}
    if words & _FAREWELL_TOKENS:
        return True
    # "quit"/"exit" only signal a farewell when the whole message is short.
    if len(text.split()) <= 3 and words & _AMBIGUOUS_END_TOKENS:
        return True
    return False


def _detect_frustration(user_input: str) -> bool:
    """True when the learner's message carries a discouragement signal.

    A HIGH-PRECISION pre-gate, not the only signal: the LLM affect read upgrades
    needs_support after the graph runs, so a borderline case this misses is still
    caught next turn. We therefore favour precision. A naive substring scan fired
    support on upbeat messages like "I can't wait to start, this is fun!" and
    "I'm not frustrated at all" — patronising a confident learner. We veto known
    positive/negated idioms (_FRUSTRATION_OVERRIDES) and match phrases on word
    boundaries. Deeply ambiguous literal content (e.g. "I gave up smoking") is
    intentionally left to the LLM affect backstop rather than chased with brittle
    rules.
    """
    text = (user_input or "").lower()
    if any(ov in text for ov in _FRUSTRATION_OVERRIDES):
        return False
    return any(
        re.search(r"\b" + re.escape(p) + r"\b", text) for p in _FRUSTRATION_PHRASES
    )


def _farewell(state: dict) -> str:
    """Evidence-calibrated sign-off naming the learner, no scoring claims."""
    name = (state.get("learner_name") or "").strip()
    who = f", {name}" if name else ""
    streak = int(state.get("clean_streak") or 0)
    score = float(state.get("last_eval_score") or state.get("current_mastery") or 0.0)
    focus = (
        (state.get("last_diagnosis") or {}).get("next_focus")
        or state.get("next_focus")
        or ""
    )
    if streak >= 2:
        note = f"You had {streak} clean passes today; keep proving that standard across harder prompts."
    elif streak == 1:
        note = "One clean pass landed today; next time we will check whether it holds without help."
    elif state.get("needs_support") or score < 0.5:
        note = (
            f"The next useful focus is {focus.strip()}"
            if focus
            else "The next useful focus is one smaller, clearer revision."
        )
    else:
        note = "You put in a real attempt; next time we will keep tightening the same skill."
    return (
        f"Session saved{who}. {note} Come back when you want to continue and "
        "we'll pick up from this point."
    )


def _bump_band(cefr: str) -> str:
    """Nudge a CEFR estimate up one band (cap C2).

    The local qwen model under-scores writing samples, so a raw placement tends
    to under-place a capable learner into trivially easy early nodes. One band of
    headroom corrects this; capped at C2 so it can never overshoot the ladder."""
    order = ["A1", "A2", "B1", "B2", "C1", "C2"]
    try:
        i = order.index(cefr)
    except ValueError:
        return cefr
    return order[min(i + 1, len(order) - 1)]
