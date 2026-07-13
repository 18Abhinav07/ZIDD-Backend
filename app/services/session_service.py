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
import json
import os
import re
import time
import uuid
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass

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
    clean_streak: int       # consecutive clean passes on this node
    attempts: int           # total attempts on this node


@dataclass(frozen=True)
class SessionRecap:
    """Summary frame emitted when module_done=True (all nodes completed).

    Carries the structured recap so the UI can render a 'session complete'
    screen without a second API call. The `done` event fires immediately after."""

    nodes_completed: list   # list of node_id strings from node_history
    weaknesses: list        # weakness_context rows (skill_id, hit_count, last_raw)
    avg_score: float        # current_mastery at close


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
from app.services.rubric_engine import compute_attempt_credit
from app.services.career_context import build_career_context
from app.services.learning_profile import CareerLearningProfileService
from app.services.assessment_plan import ensure_assessment_plan
from app.services.simulation_config import resolve_simulation_config
from app.services.simulation_service import score_session, stream_simulation_round
from app.storage import get_storage

# Assessment ("test") task types run the multi-persona SIMULATION instead of the
# coaching graph; the contribution is scored at session end, not coached mid-turn.
_TEST_TASK_TYPES = frozenset({TaskType.INTERVIEW_TEST.value, TaskType.GD_TEST.value})
_CELEBRATORY_OPENING_RE = re.compile(
    r"^\s*(?:great job|great start|good job|nice(?: work| touch)?|well done|"
    r"excellent(?: work)?|awesome(?: work)?|"
    r"(?:strong|solid)\s+(?:answer|response)|"
    r"this\s+is\s+(?:a\s+)?(?:strong|solid)\s+(?:answer|response)|"
    r"you(?:'ve| have)? nailed it|"
    r"you(?:'ve|’ve| have)? made good progress|"
    r"you(?:'ve|’ve| have)?(?:\s+effectively)? outlined|"
    r"you(?:'ve|’ve| have)? done well(?:\s+(?:by|in))?|"
    r"you\s+(?:(?:effectively|clearly|successfully|nicely)\s+)?"
    r"(?:highlighted|included|provided|articulated|showed|explained|demonstrated|demonstrates)|"
    r"your\s+(?:pitch|answer|response)\s+"
    r"(?:(?:effectively|clearly|successfully|nicely)\s+)?"
    r"(?:highlighted|included|provided|articulated|showed|explained|demonstrated|demonstrates))"
    r"(?:\s*[,:\-\u2013\u2014]\s*)?(?:[.!?]\s*)?",
    re.IGNORECASE,
)
_ACTIONABLE_COACHING_MARKER_RE = re.compile(
    r"\b(?:now|next|try|add|rewrite|revise|pressure-test|make|cut|answer|give|state|name|show|include|tighten)\b",
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
    score = _recent_score_for_tone(state)
    return bool(state.get("last_graded_bridge")) or (
        isinstance(score, (int, float)) and score < 0.85
    )


def _gd_topic_phrase_for_state(state: dict) -> str:
    context = state.get("career_context") or {}
    topics = [
        str(topic).strip()
        for topic in (context.get("gd_topics") or [])
        if str(topic).strip()
    ]
    scenario = state.get("scenario_config") or {}
    topic = (
        topics[0]
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
    if cleaned != text or _CAREER_REPEAT_WEAKNESS_REQUEST_RE.search(text):
        return _deterministic_coach_repair_text(state)
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
        return (
            "That version now has the three-part shape: past tendency, corrective habit, "
            "and measurable progress. Keep it as the interview answer. Next, pressure-test "
            "it with one follow-up about tradeoffs, stakeholder pushback, or what changed "
            "after the rollout."
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
    if node_id.startswith("gd_") and topic:
        return (
            f"Now build back to the full skill: write one clear GD contribution on "
            f"{topic} that commits to a side and adds one concrete safeguard or reason."
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
_TRANSIENT_KEYS = ("pending", "pending_game", "last_selection")


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
            return session_id, state

    store = get_storage()
    if not hasattr(store, "get_active_session_runtime_for_node"):
        return None
    row = await store.get_active_session_runtime_for_node(
        user_id,
        node_id,
        task_type,
        bool(test_mode),
    )
    if not row:
        return None
    state = _hydrate_runtime_state(row)
    if state.get("session_over"):
        return None
    if _expire_state_if_needed(state):
        await _persist_runtime_state(state)
        return None
    SessionStore[state["session_id"]] = state
    return state["session_id"], state


async def handoff_transition_to_session(
    source_session_id: str,
    source_transition_id: str,
    target_session_id: str,
    target_node_id: str,
    user_id: str,
) -> None:
    """Close a completed source session after its next skill starts elsewhere."""
    state = await get_session_state(source_session_id)
    if state is None or state.get("user_id") != user_id:
        raise ValueError("source_session_not_found")

    pending = state.get("pending_node_transition")
    if not isinstance(pending, dict):
        raise ValueError("source_transition_missing")
    if pending.get("transition_id") != source_transition_id:
        raise ValueError("source_transition_mismatch")
    if pending.get("to_node") != target_node_id:
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
        final_summary=f"Next skill continued in session {target_session_id}.",
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
        "scaffold_successes": 0,
        "meaningful_attempts": 0,
        "readiness_score": 0.0,
        "last_gap": "",
        "mastery_evidence": [],
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


# ---------- public API ----------

async def start_session(
    user_id: str,
    node_id: str,
    learner_name: str = "",
    test_mode: bool = False,
    reattempt: bool = False,
    simulation_config: dict | None = None,
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
    session_id = uuid.uuid4().hex
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

    store = get_storage()
    await store.ensure_profile(user_id, learner_name)
    prof = await store.get_profile(user_id) or {}
    career_context = build_career_context(prof)
    career_context_private = career_context.private_dict()
    try:
        career_context_private["career_memory_context"] = (
            await CareerLearningProfileService(store).get_career_memory_context(user_id)
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
            current_mastery = p["ema"]
            attempts = p["attempts"]
            break

    memory_context = await store.load_context(user_id, task_type)
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
    }
    
    # Apply loaded progress
    state["current_mastery"] = current_mastery
    state["attempts"] = attempts
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
    await store.create_session(
        session_id,
        user_id,
        task_type,
        module_id,
        node_id,
        test_mode=is_test,
        career_context=career_context_private,
        scenario_config=resolved_sim.private_dict(),
        persona_roster=resolved_sim.persona_roster if is_test else [],
        context_hash=resolved_sim.context_hash,
    )
    SessionStore[session_id] = state
    await _persist_runtime_state(state)
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
        topic = (
            state.get("sim_topic")
            or (state.get("scenario_config") or {}).get("topic")
            or getattr(node, "title", "this skill")
        )
        return f"Let's practice {topic}. Give your first clear contribution now."
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

    deterministic_test_opening = _assessment_opening_text(state, node)
    if deterministic_test_opening and not pending_transition:
        message_id = f"{session_id}:opening:{opening_key}"
        message = {
            "message_id": message_id,
            "role": "assistant",
            "content": deterministic_test_opening,
            "node_id": state["competency_node"],
            "transition_id": None,
            "message_kind": "opening",
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
    state["messages"].append({"role": "assistant", "content": text})
    state["turn_count"] += 1


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
            state["messages"].append({"role": "assistant", "content": closing})
            _finish_active_turn(state, client_turn_id, "completed")
            await _persist_runtime_state(state)
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
            closing = (
                "That's where we'll close the session. Tap finish to see your "
                "scored feedback and where to focus next."
            )
            state["messages"].append({"role": "assistant", "content": closing})
            _finish_active_turn(state, client_turn_id, "completed")
            await _persist_runtime_state(state)
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

    # Graph = decision brain: evaluate the answer, pick the pedagogy move,
    # build its prompt. Returns partial-state updates we merge back.
    graph = get_graph()
    updates = await graph.ainvoke(state)
    state.update(updates)

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
    progress_clean_streak: int | None = None
    progress_attempts: int | None = None
    suppress_same_node_response = False
    advanced_or_done = False
    same_node_generation_failed = False
    scored_turn_persisted = False
    if did_eval:
        _update_progress(state)
        will_attempt_advance = state.get("clean_streak", 0) >= int(
            state.get("advance_streak") or ADVANCE_STREAK
        )
        # BACK-07: after exactly DOWN_LADDER_FAILS consecutive hard fails, re-query
        # weaknesses live so the NEXT turn's coach prompt surfaces fresh weak spots.
        # Only fires at the threshold (not every fail after it) to avoid repeated DB
        # round-trips.
        progress_mastery = round(state["current_mastery"], 4)
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
            suppress_same_node_response = True

    # Gamified path: teach_node produced a FillBlankGame instead of a GenSpec.
    # Yield the game frame directly and skip text streaming for this turn.
    # The learner's next input (filling the blank) is scored by evaluate_node
    # as a normal answer, so no special handling is needed downstream.
    if not suppress_same_node_response:
        game: dict | None = state.get("pending_game")
        if game is not None:
            public_game = {
                "type": game.get("type", "fill_blank"),
                "sentence": game.get("sentence", ""),
                "hint": game.get("hint", ""),
                "context": game.get("context", ""),
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
            state["messages"].append({
                "role": "assistant",
                "content": f"[Fill in the blank] {game.get('sentence', '')}",
                "turn_id": client_turn_id,
            })
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
            state["messages"].append(assistant_message)
            state["turn_count"] += 1
            state["pending"] = None

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

    if did_eval and not advanced_or_done and not same_node_generation_failed:
        # Same-node turns are committed only after the learner-visible assistant
        # response has streamed successfully. If response generation fails, the
        # fallback asks for a retry and the answer is not counted as progress.
        await _track_turn(state, prev_node)
        if state.get("level_fails", 0) == DOWN_LADDER_FAILS:
            await _maybe_refresh_weaknesses(state)
        await _persist_mastery(state)
        scored_turn_persisted = True

    if did_eval and scored_turn_persisted:
        # Emit per-turn mastery update so the UI progress bar animates mid-stream.
        yield ProgressUpdate(
            node_id=prev_node,
            mastery=progress_mastery or 0.0,
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
            yield SessionRecap(
                nodes_completed=[
                    get_node(node_id).title
                    for node_id in state.get("node_history", {}).keys()
                ],
                weaknesses=state.get("weakness_context", []),
                avg_score=round(state["current_mastery"], 4),
            )
        elif state["competency_node"] != prev_node:
            # Desync fix: the answer advanced us to a new node.
            # We yield NodeAdvance to signal the frontend, but we NO LONGER
            # auto-stream the new opening. The frontend will present a "Next Skill"
            # break and call /opening manually.
            yield NodeAdvance(
                from_node=prev_node, to_node=state["competency_node"]
            )

    if did_eval and scored_turn_persisted and not advanced_or_done:
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


async def end_session(session_id: str) -> str:
    """Back-compat wrapper: close the session and return its closing summary.

    Many callers (scripts, the older tests) depend on the bare-string return.
    `close_session` is the full-payload entry point the /end route uses to also
    surface the scored simulation report."""
    return (await close_session(session_id))["summary"]


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
    node = get_node(state["competency_node"])
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
            if report.validity_status != "invalid_simulation":
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
    if summary:
        await store.write_memory(
            state["user_id"],
            session_id,
            state["competency_node"],
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
            "node_id": state.get("competency_node"),
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

    # Check active sessions for this module. A reattempt on a completed node
    # is exposed as metadata but must not downgrade the node's durable
    # mastered status on the map.
    active = [
        s for s in SessionStore.values()
        if s.get("user_id") == user_id
        and s.get("status", "active") == "active"
        and _state_module(s) == module_id
    ]
    if not active:
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
                        SessionStore[resumed_state["session_id"]] = resumed_state
                        active.append(resumed_state)
        if not active:
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
                        active.append(resumed_state)
                        break
    primary_active = next((s for s in active if not s.get("reattempt")), None)
    curr_node = primary_active.get("competency_node") if primary_active else None
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
        elif stored_display_status:
            status = stored_display_status
        elif is_current:
            status = "active"
            found_active = True
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
            "best_independent_score": best_independent_score,
            "independent_passes": int(p.get("independent_passes") or 0) if p else 0,
            "transfer_passes": int(p.get("transfer_passes") or 0) if p else 0,
            "pressure_passes": int(p.get("pressure_passes") or 0) if p else 0,
            "scaffold_successes": int(p.get("scaffold_successes") or 0) if p else 0,
            "last_gap": p.get("last_gap", "") if p else "",
            "mastery_evidence": list(p.get("mastery_evidence") or []) if p else [],
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
    
    # Persist the placement if a user is authenticated. We mark all preceding nodes
    # in the module as fully mastered/completed so the progression map advances.
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
        "estimated_cefr": estimated_cefr,
        "rationale": rationale,
    }


# ---------- internals ----------

def _require(session_id: str) -> dict:
    state = SessionStore.get(session_id)
    if state is None:
        raise KeyError(f"no active session: {session_id}")
    return state


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
            },
            rubric_result,
            scaffolded=bool(state.get("last_graded_bridge")),
        )
        state.update(credit)
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
    state["scaffold_successes"] = 0
    state["meaningful_attempts"] = 0
    state["readiness_score"] = 0.0
    state["last_gap"] = ""
    state["mastery_evidence"] = []
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


def _update_session_learning_delta(state: dict, rubric_result: dict, user_answer: str) -> None:
    delta = state.setdefault("session_learning_delta", {
        "strengths": [],
        "active_gaps": [],
        "repeated_issue_counts": {},
        "growth_signals": [],
        "resolved_candidates": [],
        "latest_evidence_quotes": [],
    })
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
    for criterion in rubric_result.get("criteria") or []:
        if not isinstance(criterion, dict):
            continue
        criterion_id = str(criterion.get("id") or "").strip()
        if criterion_id and criterion.get("met") is False:
            criterion_key = f"criterion:{criterion_id}"
            repeated[criterion_key] = max(int(repeated.get(criterion_key) or 0), 1)
        quote = str(criterion.get("evidence_quote") or "").strip()
        if quote:
            _append_unique_limited(evidence_quotes, quote[:260], limit=8)
    if not evidence_quotes and user_answer:
        _append_unique_limited(evidence_quotes, " ".join(user_answer.split())[:260], limit=8)


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
        _update_session_learning_delta(
            state,
            dict(rubric_result),
            str(state.get("user_input") or ""),
        )
        await store.record_turn_evaluation(
            evaluation_id=f"{state['session_id']}:{turn_id or attempt_index}:{node_id}",
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
            model_name=get_settings().ollama_model if get_settings().ai_backend == "local" else "gemini",
            prompt_version="prep-eval-v1",
        )
        await CareerLearningProfileService(store).record_prep_turn_evaluation(
            evaluation_id=f"{state['session_id']}:{turn_id or attempt_index}:{node_id}",
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
    items = await generate_test_items(
        state["user_id"],
        test_tt,
        career_context=state.get("career_context") or {},
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
