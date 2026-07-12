"""TEST-mode multi-persona simulation (writers'-room loop).

The coaching ("prep") modes run the tutor ladder. The assessment ("test") modes
— interview_test, gd_test — run a *simulation* instead: distinct personas (GD
participants with stances, or an interview panel) speak, the learner responds,
and the contribution is scored, not coached mid-stream.

Each round is a writers'-room beat: the Director (a structured LLM decision over
the shared Blackboard) picks WHO speaks and with WHAT intent, then a single
Persona executor STREAMS that one speaker's turn. The round yields a `Speaker`
marker, a `SimulationState` marker (turn/tension snapshot), then the persona's
text tokens. The API layer maps `Speaker` -> `event: speaker`, `SimulationState`
-> `event: simulation_state`, and plain string tokens -> `event: message`,
mirroring how run_turn maps `NodeAdvance` to `event: node_advance`.
"""
import asyncio
import logging
import zlib
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.calls import evaluate_simulation
from app.ai.prompts import sanitize_memory_text
from app.ai.schemas import DirectorDecision, SimulationReport
from app.content.task_types import TaskType
from app.services.simulation.blackboard import apply_decision, new_blackboard, note_turn
from app.services.simulation.director import _next_in_rotation, decide_round
from app.services.simulation.persona import stream_persona_turn
from app.services.simulation_config import DEFAULT_GD_PERSONAS, GD_PERSONA_LIBRARY
from app.services.interview_probes import (
    build_interview_probe_plan,
    default_interview_probes_for_role,
    normalize_interview_probe,
)
from app.services.gd_discussion_text import (
    gd_integrity_fallback_text,
    gd_persona_fallback_text,
    gd_repeat_fallbacks,
    gd_topic_phrase,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Speaker:
    """Marker yielded when a new persona begins speaking.

    Mirrors NodeAdvance: the simulation stream is a single sequence of plain
    string tokens interleaved with these markers; the API maps each to an
    `event: speaker` SSE frame so the UI opens a new speaker bubble."""

    speaker_id: str
    name: str


@dataclass(frozen=True)
class SimulationState:
    """Marker yielded once per round with the Director's post-decision snapshot.

    The API maps it to an `event: simulation_state` SSE frame so the UI can show
    round count and tension. Carried alongside the stream like Speaker; the
    session runner forwards it untouched (it is neither a Speaker nor a str).

    `should_close` surfaces the Director's wind-down signal (or the hard round
    cap) to the client so the UI can prompt the learner to finish — previously
    the Director decided this every round and nothing ever read it."""

    turn: int
    speaker_id: str
    tension: float
    should_close: bool = False


# A live simulation must self-terminate even if the Director never calls close.
# After this many rounds the round runner forces should_close and flags the
# session over so a learner cannot loop a TEST sim indefinitely.
MAX_SIM_ROUNDS = 10
ASSESSMENT_TURN_TIMEOUT_SECONDS = 55.0

# Cross-talk schedule (GD only): how many EXTRA panelists react after the
# Director's chosen speaker, keyed on the phase the discussion is currently in
# (read BEFORE the Director's decision). A GD opens with a single voice so the
# learner isn't dogpiled on their first contribution, then the panel argues with
# itself as it heats up. Interview is always single-voice (one interviewer).
_GD_EXCHANGE_BY_PHASE: dict[str, int] = {
    "opening": 0,
    "probing": 1,
    "pressure": 2,
    "winddown": 0,
}

_EMPTY_TURN_FALLBACK = "Let's stay with that — can you say more?"

_INTERVIEW_DEFAULT_PROBES = (
    "Walk me through one project relevant to {role}. What trade-off did you personally own, and why did you choose that path?",
    "Describe a disagreement with a teammate or stakeholder. What did you say, what changed, and what did you learn?",
    "Tell me about a debugging problem under pressure. How did you isolate the cause and communicate progress?",
    "Give me an example of taking ownership when something was ambiguous or going wrong.",
    "Explain a technical or work decision to a non-technical stakeholder. How did you make it clear?",
    "What impact did your work create? Use one concrete result, metric, or user outcome.",
    "Why is this role the right next step for you, based on the work you have actually done?",
    "Tell me about a mistake or failure. What did you change afterward?",
    "How do you prioritize when two important requests compete for your time?",
    "What question would you ask us to judge whether this role is a good fit for you?",
)

_MOVE_ON_TERMS = (
    "move on",
    "different topic",
    "different angle",
    "another topic",
    "new angle",
    "covered that",
    "already answered",
    "already covered",
    "let's move",
    "next question",
    "change topic",
)

_TEAM_CONFLICT_TERMS = (
    "teammate",
    "team mate",
    "coworker",
    "colleague",
    "stakeholder",
    "disagreement",
    "conflict",
    "argument",
)

_GD_CONFUSION_TERMS = (
    "i don't understand",
    "i dont understand",
    "do not understand",
    "don't understand",
    "dont understand",
    "what is going on",
    "what should i do",
    "i am confused",
    "i'm confused",
    "confused",
    "lost",
    "can you clarify",
    "could you clarify",
    "please clarify",
)

_INTERVIEW_CONFUSION_TERMS = _GD_CONFUSION_TERMS + (
    "what do you mean",
    "can you explain",
    "please explain",
    "clarify",
    "not sure what",
    "what are you asking",
)

_CONFUSION_CONTROL_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\bi\s+(?:don't|dont|do not)\s+understand\b",
        r"\b(?:what is going on|what should i do|what do you mean|what are you asking)\b",
        r"\b(?:can you explain|please explain|could you explain)\b",
        r"\b(?:i am|i'm|i feel|feeling)\s+confused\b",
        r"\b(?:i am|i'm|i feel|feeling)\s+lost\b",
        r"\bnot sure what\b",
        r"^\s*(?:confused|lost|clarify|explain)\s*[.!?]*\s*$",
    )
)


def _has_confusion_control_intent(text: str) -> bool:
    lower = (text or "").lower()
    return any(pattern.search(lower) for pattern in _CONFUSION_CONTROL_PATTERNS)


def _extra_speakers(prev_phase: str, should_close: bool, task_type: TaskType) -> int:
    """How many reactor turns follow the primary speaker this round.

    Only GD assessments cross-talk; everything else stays single-voice. We never
    pile reactors onto a closing round (the panel should be winding down, not
    escalating)."""
    if task_type != TaskType.GD_TEST or should_close:
        return 0
    return _GD_EXCHANGE_BY_PHASE.get(prev_phase, 1)


def _reactor_intent(prev_name: str) -> str:
    """Templated intent for a reactor jumping in on the previous speaker.

    No extra Director LLM call per reactor — the intent is fixed: react to the
    voice that just spoke, by name, so the turn is genuine panel cross-talk
    rather than another speech aimed at the learner."""
    return (
        f"Jump straight in and react to what {prev_name} just said — address "
        f"{prev_name} by name and either push back hard from your own stance or "
        "sharpen their point, then add one new angle. This is panel cross-talk "
        "between you two, not a reply to the learner."
    )


def _reactor_pool(personas: list[dict]) -> list[dict]:
    """The roster a cross-talk reactor may be drawn from: debaters only.

    Cross-talk is debater-to-debater. The Moderator still reaches the floor as
    the Director's PRIMARY speaker (to facilitate / transition phases), but must
    never be picked as a REACTOR — _reactor_intent ("push back from your stance,
    add one new angle") is a debater move, out of character for a neutral
    facilitator. Without this filter, rotating off the last debater (gd_c) wraps
    to personas[0] == the Moderator, so the facilitator would "jump in" to argue.
    Falls back to the full roster if filtering would leave nothing to rotate
    through (a degenerate roster), since _next_in_rotation rejects an empty list.
    """
    debaters = [
        p for p in personas
        if p.get("role_type") != "moderator" and p.get("speaker_id") != "moderator"
    ]
    return debaters or personas


def _primary_role_label(state: dict) -> str:
    scenario = state.get("scenario_config") or {}
    career = state.get("career_context") or {}
    return (
        str(
            scenario.get("target_role")
            or career.get("primary_role")
            or (career.get("target_roles") or [""])[0]
            or "the target role"
        ).strip()
        or "the target role"
    )


def _default_interview_probes(state: dict) -> list[dict]:
    role = _primary_role_label(state)
    return default_interview_probes_for_role(role)


def _last_user_message(messages: list[dict]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


_FALLBACK_SUBSTANCE_MARKERS = (
    " because ",
    " example",
    " evidence",
    " metric",
    " measure",
    " result",
    " impact",
    " changed",
    " trade",
    " risk",
    " support",
    " oppose",
    " i ",
    " my ",
    " we ",
)


def _deterministic_fallback_assessment(state: dict) -> tuple[bool, float, list[str]]:
    """Detect whether a failed structured turn followed a substantive answer.

    A model timeout is simulator integrity debt. The answer may keep the live
    session moving, but the deterministic repair must not become trusted rubric
    evidence in the final score.
    """
    answer = " ".join(_last_user_message(state.get("messages") or []).split())
    if not answer:
        return False, 0.0, []
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9'-]*", answer)
    word_count = len(tokens)
    lowered = f" {answer.lower()} "
    has_substance_marker = any(marker in lowered for marker in _FALLBACK_SUBSTANCE_MARKERS)
    question_only = answer.endswith("?") and word_count < 18 and not has_substance_marker
    scorable = word_count >= 14 and not question_only and (has_substance_marker or word_count >= 24)
    if not scorable:
        return False, 0.0, []
    quality = 0.46 + min(word_count, 70) / 350.0
    if any(marker in lowered for marker in (" result", " impact", " metric", " measure", " changed")):
        quality += 0.06
    if any(marker in lowered for marker in (" because ", " trade", " risk", " evidence")):
        quality += 0.04
    return True, round(max(0.48, min(0.72, quality)), 4), [_latest_user_excerpt(state)]


def _has_score_excluding_repair(flags: list[dict] | tuple[dict, ...] | None) -> bool:
    for flag in flags or []:
        if not isinstance(flag, dict):
            continue
        if str(flag.get("code") or "") in _SCORE_EXCLUDING_REPAIR_CODES:
            return True
    return False


def _recent_assistant_tokens(messages: list[dict], limit: int = 4) -> list[set[str]]:
    prompts: list[set[str]] = []
    for message in reversed(messages or []):
        if message.get("role") != "assistant":
            continue
        text = str(message.get("content") or "")
        tokens = _tokens_for_repetition(text)
        if tokens:
            prompts.append(tokens)
        if len(prompts) >= limit:
            break
    return prompts


def _is_repeated_probe(prompt: str, recent_tokens: list[set[str]], used: list[str]) -> bool:
    candidate = _tokens_for_repetition(prompt)
    if len(candidate) < 4:
        return False
    for tokens in recent_tokens:
        containment = len(candidate & tokens) / max(1, min(len(candidate), len(tokens)))
        if _token_similarity(candidate, tokens) >= _REPEAT_SIMILARITY_THRESHOLD or containment >= 0.78:
            return True
    for previous in used[-8:]:
        prev_tokens = _tokens_for_repetition(previous)
        containment = len(candidate & prev_tokens) / max(1, min(len(candidate), len(prev_tokens)))
        if _token_similarity(candidate, prev_tokens) >= _REPEAT_SIMILARITY_THRESHOLD or containment >= 0.78:
            return True
    return False


def _requested_interview_pivot(state: dict) -> dict | None:
    last_user = _last_user_message(state.get("messages") or [])
    lower = last_user.lower()
    if not any(term in lower for term in _MOVE_ON_TERMS):
        return None
    role = _primary_role_label(state)
    if any(term in lower for term in _TEAM_CONFLICT_TERMS):
        return {
            "prompt": (
                f"Let's move to collaboration. Tell me about a disagreement with a "
                f"teammate or stakeholder while working toward {role}. What did "
                "you do, and what changed?"
            ),
            "aim": "show collaboration, ownership, and a clear outcome",
        }
    return {
        "prompt": (
            f"Let's move to a new dimension for {role}. Give me a different "
            "specific story that shows ownership, judgment, and communication."
        ),
        "aim": "switch topics and avoid repeating the last answer",
    }


def _set_active_interview_probe(
    state: dict,
    prompt: str,
    *,
    skill_id: str | None = None,
    prompt_id: str | None = None,
) -> None:
    prompt = str(prompt or "").strip()
    state["active_interview_probe_prompt"] = prompt
    stable_id = _event_prompt_id(prompt, "interview_probe")
    state["active_interview_probe_skill_id"] = skill_id or stable_id
    state["active_interview_probe_prompt_id"] = prompt_id or stable_id


def _persona_requested_by_learner(text: str, personas: list[dict]) -> dict | None:
    lower = text.lower()
    alias_hits: dict[str, list[dict]] = {}
    for persona in personas:
        name = str(persona.get("name") or "").strip()
        speaker_id = str(persona.get("speaker_id") or "").strip()
        if name and name.lower() in lower:
            return persona
        if speaker_id and speaker_id.replace("_", " ") in lower:
            return persona
        for alias in {part.lower() for part in re.findall(r"[a-zA-Z][a-zA-Z-]+", name)}:
            if len(alias) < 4:
                continue
            if re.search(rf"\b{re.escape(alias)}\b", lower):
                alias_hits.setdefault(alias, []).append(persona)
    unique_hits = [hits[0] for hits in alias_hits.values() if len(hits) == 1]
    if len(unique_hits) == 1:
        return unique_hits[0]
    return None


def _moderator_persona(personas: list[dict]) -> dict:
    for persona in personas:
        if _is_moderator_persona(persona):
            return persona
    return personas[0]


def _is_moderator_persona(persona: dict) -> bool:
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    return role_type == "moderator" or "moderator" in speaker_id or "moderator" in name


def _gd_persona_request_roster() -> list[dict]:
    """All public GD personas a learner may name as a runtime control request."""
    return [dict(persona) for persona in GD_PERSONA_LIBRARY.values()]


def _has_gd_persona_control_request(text: str) -> bool:
    """True only when the learner is routing the floor to a named persona.

    Mentioning a persona as part of an argument ("I agree with the expert")
    remains scorable. The turn becomes runtime control only when the wording asks
    the system to hand the floor to that persona.
    """
    if _persona_requested_by_learner(text, _gd_persona_request_roster()) is None:
        return False
    return bool(
        re.search(
            r"\b(?:hear from|let|ask|invite|bring in|call on|what does|what do|"
            r"what\s+is|what's|what\s+are|can|could|please)\b",
            text,
        )
        or re.search(r"\b(?:respond|reply|speak|view|opinion|take)\b", text)
    )


def _gd_control_decision(state: dict, personas: list[dict], bb: dict) -> DirectorDecision | None:
    if state.get("task_type") != TaskType.GD_TEST.value:
        return None
    last_user = _last_user_message(state.get("messages") or [])
    lower = last_user.lower()
    requested = _persona_requested_by_learner(lower, personas)
    if requested and _has_gd_persona_control_request(lower):
        name = requested.get("name") or "this speaker"
        if _is_moderator_persona(requested):
            intent = (
                "The learner explicitly asked the Moderator to steer the room. "
                "Facilitate the current motion directly: restate the live angle, "
                "surface one concrete tension the group should weigh, and invite "
                "contrasting participant views without taking a side yourself."
            )
        else:
            intent = (
                f"{name}, the learner explicitly asked to hear from you. "
                "Give your view directly, connect it to the current topic, and "
                "add one concrete counterpoint or metric the group should weigh. "
                "Do not interview the learner."
            )
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=requested["speaker_id"],
            intent=intent,
            tension=bb.get("tension", 0.3),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    unavailable_requested = _persona_requested_by_learner(lower, _gd_persona_request_roster())
    if unavailable_requested and _has_gd_persona_control_request(lower):
        moderator = _moderator_persona(personas)
        requested_name = unavailable_requested.get("name") or "that speaker"
        available = [
            str(persona.get("name") or persona.get("speaker_id") or "").strip()
            for persona in personas
            if str(persona.get("role_type") or "").lower() != "moderator"
        ]
        available_text = ", ".join(name for name in available if name) or "the current panel"
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=moderator["speaker_id"],
            intent=(
                f"Pause and explain that {requested_name} is not in this panel. "
                f"Name the available voices: {available_text}. Invite the learner "
                "to pick one of those voices or answer the current topic directly. "
                "Then restate the live motion and give one clear discussion "
                "direction. Do not pretend the missing persona spoke."
            ),
            tension=max(0.2, float(bb.get("tension", 0.3)) - 0.1),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    if _has_confusion_control_intent(lower):
        moderator = _moderator_persona(personas)
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=moderator["speaker_id"],
            intent=(
                "Pause the debate and explain what is happening in simple terms: "
                "the learner should take a position, add one reason, and invite "
                "one panelist to respond. Then restate the live motion and give "
                "one clear discussion direction. Do not demand advanced evidence yet."
            ),
            tension=max(0.2, float(bb.get("tension", 0.3)) - 0.15),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    if any(term in lower for term in _MOVE_ON_TERMS):
        moderator = _moderator_persona(personas)
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=moderator["speaker_id"],
            intent=(
                "Acknowledge that the learner wants to move on. Briefly close the "
                "repeated thread, then name a different angle for the group: a concrete "
                "stakeholder, feasibility, or synthesis lens on the same topic. Do not "
                "repeat the same evidence demand again."
            ),
            tension=max(0.25, float(bb.get("tension", 0.3)) - 0.1),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    return None


def is_simulation_control_input(task_type_value: str, text: str) -> bool:
    """True when a TEST-mode learner turn is a runtime command, not an answer.

    The structured assessment engine now classifies clarification / move-on /
    persona-request intent semantically. Keep regex control marking out of the
    normal path so natural GD requests ("Devil's Advocate, what is the risk?")
    remain learner turns with typed analysis evidence. Hard end commands are
    handled before this helper by session_service._is_session_end.
    """
    return False


def _interview_control_decision(state: dict, personas: list[dict], bb: dict) -> DirectorDecision | None:
    if state.get("task_type") != TaskType.INTERVIEW_TEST.value:
        return None
    last_user = _last_user_message(state.get("messages") or [])
    lower = last_user.lower()
    interviewer = personas[0] if personas else {"speaker_id": "interviewer", "name": "Interviewer"}
    if _has_confusion_control_intent(lower):
        role = _primary_role_label(state)
        clarified_prompt = (
            "What situation can you use as your example, what did you personally "
            "do, and what changed because of it?"
        )
        _set_active_interview_probe(
            state,
            clarified_prompt,
            skill_id="interview_clarified_example_structure",
        )
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=interviewer["speaker_id"],
            intent=(
                "Pause the assessment briefly and explain the current interview "
                f"task in plain language for a {role} candidate. Tell the learner "
                "one simple way to answer: name the situation, what they did, and "
                f"the result. Then ask this one simple clarified question: {clarified_prompt} "
                "Do not score, shame, or demand a full answer yet."
            ),
            tension=max(0.2, float(bb.get("tension", 0.3)) - 0.2),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    if any(term in lower for term in _MOVE_ON_TERMS):
        pivot = _requested_interview_pivot(state)
        prompt = pivot["prompt"] if pivot else (
            "Let's move to a different interview dimension. Tell me one specific "
            "story that shows ownership, judgment, and communication."
        )
        _set_active_interview_probe(
            state,
            prompt,
            skill_id=(
                "interview_collaboration_pivot"
                if any(term in lower for term in _TEAM_CONFLICT_TERMS)
                else "interview_topic_pivot"
            ),
        )
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=interviewer["speaker_id"],
            intent=(
                "Acknowledge the learner's request to move on. Do not revisit the "
                f"same question. Ask this new prompt clearly: {prompt}"
            ),
            tension=max(0.25, float(bb.get("tension", 0.3)) - 0.1),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    return None


def _select_next_interview_probe(state: dict) -> dict:
    explicit_pivot = _requested_interview_pivot(state)
    if explicit_pivot:
        return explicit_pivot

    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    planned = [p for p in (plan.get("probe_plan") or []) if isinstance(p, dict)]
    authored_prompts = {
        " ".join(str(p.get("prompt") or "").lower().split())
        for p in (state.get("probe_items") or [])
        if isinstance(p, dict) and str(p.get("prompt") or "").strip()
    }
    planned_prompts = {
        " ".join(str(p.get("prompt") or "").lower().split())
        for p in planned
        if str(p.get("prompt") or "").strip()
    }
    if authored_prompts and not authored_prompts.issubset(planned_prompts):
        planned = build_interview_probe_plan(state)
        if isinstance(plan, dict):
            plan["probe_plan"] = planned
            state["assessment_plan"] = plan
    probes = [
        p for p in (planned or build_interview_probe_plan(state))
        if isinstance(p, dict) and (p.get("prompt") or "").strip()
    ]
    cursor = int(state.get("probe_cursor") or 0)
    used = list(state.get("used_probe_prompts") or [])
    recent = _recent_assistant_tokens(state.get("messages") or [])
    covered_skills = {
        str(event.get("skill_id") or "").strip()
        for event in state.get("coverage_events") or []
        if isinstance(event, dict)
        and event.get("answered") is True
        and str(event.get("skill_id") or "").strip()
    }
    pending = state.get("pending_coverage_event")
    if isinstance(pending, dict) and str(pending.get("skill_id") or "").strip():
        covered_skills.add(str(pending.get("skill_id")).strip())

    for prefer_uncovered in (True, False):
        for offset in range(len(probes)):
            index = (cursor + offset) % len(probes)
            candidate = probes[index]
            skill_id = str(candidate.get("skill_id") or "").strip()
            if prefer_uncovered and skill_id in covered_skills:
                continue
            if not _is_repeated_probe(candidate.get("prompt", ""), recent, used):
                state["probe_cursor"] = cursor + offset + 1
                return candidate

    state["probe_cursor"] = cursor + 1
    return probes[cursor % len(probes)]


def _interview_probe_intent(state: dict, fallback_intent: str) -> str:
    """Return the next deterministic interview probe intent.

    Interview tests are one-voice simulations. If the Director is given the same
    full probe bank every round, a local model can keep pressing the same topic.
    The session state therefore owns a cursor over the generated probe plan and
    each round receives exactly the next unused probe.
    """
    if state.get("task_type") != TaskType.INTERVIEW_TEST.value:
        return fallback_intent
    probe = _select_next_interview_probe(state)
    _set_active_interview_probe(
        state,
        probe.get("prompt", ""),
        skill_id=probe.get("skill_id") or probe.get("id"),
        prompt_id=probe.get("prompt_id"),
    )
    used = list(state.get("used_probe_prompts") or [])
    used.append(probe.get("prompt", ""))
    state["used_probe_prompts"] = used[-12:]
    aim = (probe.get("aim") or "").strip()
    aim_line = f" A strong answer should {aim}." if aim else ""
    return (
        f"Ask the learner this new interview probe, then follow up only on this "
        f"answer: {probe['prompt']}{aim_line} Do not return to already-covered "
        "questions unless the learner explicitly asks to revisit them."
    )


def _probe_from_pending_or_active(state: dict) -> dict:
    pending = state.get("pending_coverage_event") if isinstance(state.get("pending_coverage_event"), dict) else {}
    prompt_id = str(pending.get("prompt_id") or state.get("active_interview_probe_prompt_id") or "").strip()
    skill_id = str(pending.get("skill_id") or state.get("active_interview_probe_skill_id") or prompt_id).strip()
    prompt = str(pending.get("prompt_text") or state.get("active_interview_probe_prompt") or "").strip()
    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    role = _primary_role_label(state)
    for probe in plan.get("probe_plan") or build_interview_probe_plan(state):
        if not isinstance(probe, dict):
            continue
        if prompt_id and prompt_id == str(probe.get("prompt_id") or ""):
            return normalize_interview_probe(dict(probe), role=role)
        if skill_id and skill_id == str(probe.get("skill_id") or "") and prompt == str(probe.get("prompt") or "").strip():
            return normalize_interview_probe(dict(probe), role=role)
    return {
        "probe_id": prompt_id or skill_id or "active_probe",
        "prompt_id": prompt_id or _event_prompt_id(prompt or "active_probe"),
        "skill_id": skill_id or prompt_id or "active_probe",
        "prompt": prompt,
        "aim": "",
        "criteria": [],
        "phase": "probing",
    }


def _canonicalize_persisted_interview_probe_plan(state: dict) -> None:
    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else None
    if not plan:
        return
    role = _primary_role_label(state)
    normalized = [
        normalize_interview_probe(dict(probe), role=role)
        for probe in plan.get("probe_plan") or []
        if isinstance(probe, dict)
    ]
    if normalized and normalized != list(plan.get("probe_plan") or []):
        plan["probe_plan"] = normalized
        state["assessment_plan"] = plan


def _prepare_interview_assessment_turn_context(state: dict) -> None:
    if state.get("task_type") != TaskType.INTERVIEW_TEST.value:
        return
    _canonicalize_persisted_interview_probe_plan(state)
    answered_probe = _probe_from_pending_or_active(state)
    probe_cursor_before = int(state.get("probe_cursor") or 0)
    used_prompts_before = list(state.get("used_probe_prompts") or [])
    next_probe = normalize_interview_probe(
        _select_next_interview_probe(state),
        role=_primary_role_label(state),
    )
    _set_active_interview_probe(
        state,
        str(next_probe.get("prompt") or ""),
        skill_id=next_probe.get("skill_id") or next_probe.get("probe_id"),
        prompt_id=next_probe.get("prompt_id"),
    )
    used = list(state.get("used_probe_prompts") or [])
    prompt = str(next_probe.get("prompt") or "").strip()
    if prompt:
        used.append(prompt)
        state["used_probe_prompts"] = used[-12:]
    covered_ids = [
        str(event.get("skill_id") or event.get("prompt_id") or "").strip()
        for event in _coverage_events_from_state(state)
        if str(event.get("skill_id") or event.get("prompt_id") or "").strip()
    ]
    state["assessment_turn_context"] = {
        "mode": TaskType.INTERVIEW_TEST.value,
        "active_role": _primary_role_label(state),
        "answered_probe": answered_probe,
        "next_probe": dict(next_probe),
        "probe_cursor_before": probe_cursor_before,
        "used_prompts_before": used_prompts_before,
        "used_prompt_ids": [
            str(item.get("prompt_id") or item.get("probe_id") or "")
            for item in (state.get("assessment_plan") or {}).get("probe_plan", [])
            if str(item.get("prompt") or "") in set(state.get("used_probe_prompts") or [])
        ],
        "covered_skill_ids": sorted(set(covered_ids)),
        "recent_assistant_prompts": [
            str(message.get("content") or "").strip()
            for message in (state.get("messages") or [])[-8:]
            if isinstance(message, dict) and message.get("role") == "assistant"
        ][-4:],
        "visible_response_contract": (
            "For normal answers, ask the next_probe.prompt as the next visible question. "
            "Do not repeat answered_probe.prompt or any recent assistant prompt."
        ),
    }


_INTERVIEW_MODEL_ANSWER_PATTERNS = (
    re.compile(r"\bi would\s+(?:start|begin|frame|approach|handle|explain|say|respond|structure)\b"),
    re.compile(r"\bmy answer would\b"),
    re.compile(r"\ba strong answer would\b"),
)


def _looks_like_interview_model_answer(text: str) -> bool:
    """True when the interviewer starts answering the candidate's task.

    Local models sometimes turn an interview probe into a mini model answer
    ("I would start by... For example... How would you elaborate?"). In scored
    assessment mode that teaches instead of testing, so the caller falls back to
    the selected probe for the round.
    """
    lower = (text or "").lower()
    if not any(pattern.search(lower) for pattern in _INTERVIEW_MODEL_ANSWER_PATTERNS):
        return False
    return any(
        marker in lower
        for marker in (
            "for example",
            "how would you",
            "can you elaborate",
            "could you elaborate",
            "what would you",
        )
    )


def _safe_interview_turn_text(state: dict, generated: str) -> str:
    """Replace repeated interviewer output with the selected probe.

    The Director/probe selector is deterministic, but the local persona model can
    still ignore that intent and re-ask a recent question. For scored interview
    tests, do not stream a repeated prompt to the learner: fall back to the exact
    selected probe for this round.
    """
    selected = str(state.get("active_interview_probe_prompt") or "").strip()
    text = (generated or "").strip()
    if not selected:
        return text or _EMPTY_TURN_FALLBACK
    context = state.get("assessment_turn_context") if isinstance(state.get("assessment_turn_context"), dict) else {}
    if isinstance(context.get("next_probe"), dict):
        return selected
    recent = _recent_assistant_tokens(state.get("messages") or [], limit=4)
    selected_is_repeated = _is_repeated_probe(selected, recent, [])
    if not text:
        return _fresh_interview_fallback_probe(state, recent) if selected_is_repeated else selected
    if _looks_like_interview_model_answer(text):
        return _fresh_interview_fallback_probe(state, recent) if selected_is_repeated else selected
    if _is_repeated_probe(text, recent, []):
        if not selected_is_repeated:
            return selected
        return _fresh_interview_fallback_probe(state, recent)
    answered = context.get("answered_probe") if isinstance(context.get("answered_probe"), dict) else {}
    next_probe = context.get("next_probe") if isinstance(context.get("next_probe"), dict) else {}
    answered_tokens = _tokens_for_repetition(str(answered.get("prompt") or ""))
    next_tokens = _tokens_for_repetition(str(next_probe.get("prompt") or selected))
    text_tokens = _tokens_for_repetition(text)
    answered_overlap = len(text_tokens & answered_tokens) / max(1, len(answered_tokens))
    next_overlap = len(text_tokens & next_tokens) / max(1, len(next_tokens))
    # The backend owns the interview probe plan. A model-written paraphrase is
    # acceptable only when it is clearly about the selected next probe; an
    # answer-specific follow-up on the just-covered probe is not.
    if next_tokens and (next_overlap < 0.28 or answered_overlap >= next_overlap):
        return selected
    return text


def _restore_interview_probe_after_control(state: dict) -> None:
    context = state.get("assessment_turn_context") if isinstance(state.get("assessment_turn_context"), dict) else {}
    answered = context.get("answered_probe") if isinstance(context.get("answered_probe"), dict) else {}
    prompt = str(answered.get("prompt") or "").strip()
    if not prompt:
        return
    state["probe_cursor"] = int(context.get("probe_cursor_before") or 0)
    state["used_probe_prompts"] = list(context.get("used_prompts_before") or [])
    _set_active_interview_probe(
        state,
        prompt,
        skill_id=answered.get("skill_id") or answered.get("probe_id"),
        prompt_id=answered.get("prompt_id"),
    )


def _fresh_interview_fallback_probe(state: dict, recent: list[set[str]] | None = None) -> str:
    """Return a non-repeated deterministic probe when the selected probe is stale."""
    recent = recent if recent is not None else _recent_assistant_tokens(state.get("messages") or [], limit=4)
    used = list(state.get("used_probe_prompts") or [])
    selected = str(state.get("active_interview_probe_prompt") or "").strip()
    for probe in _default_interview_probes(state):
        prompt = str(probe.get("prompt") or "").strip()
        if not prompt or prompt == selected:
            continue
        if not _is_repeated_probe(prompt, recent, used):
            _set_active_interview_probe(
                state,
                prompt,
                skill_id=probe.get("skill_id") or probe.get("id"),
                prompt_id=probe.get("prompt_id"),
            )
            used.append(prompt)
            state["used_probe_prompts"] = used[-12:]
            return prompt
    role = _primary_role_label(state)
    fallback = (
        f"Let's move to a fresh interview dimension for {role}. Tell me about a "
        "time you disagreed with a teammate or stakeholder, what you said, and "
        "what changed afterward."
    )
    _set_active_interview_probe(
        state,
        fallback,
        skill_id="interview_collaboration_pivot",
    )
    used.append(fallback)
    state["used_probe_prompts"] = used[-12:]
    return fallback


_HANDOFF_TERMS = (
    "respond",
    "reply",
    "take",
    "view",
    "opposite",
    "weigh in",
    "jump in",
    "come in",
    "contribute",
    "what do you think",
    "could you",
    "can you",
    "please",
)

_PRIOR_SPEAKER_REFERENCE_PATTERNS = (
    r"{name}\s*,\s+you\s+(?:raise|raised|mention|mentioned|said|bring|brought|argue|argued)",
    r"{name}\s*,.*\bwhat\s+you\s+(?:said|mentioned|argued|raised|noted)\s+earlier\b",
    r"{name}\s*,.*\b(?:your|the)\s+(?:earlier|previous|last)\s+(?:point|argument|claim|view)\b",
    r"as\s+{name}\s+(?:said|mentioned|pointed|argued|noted)",
    r"{name}\s+(?:raises|raised|mentioned|said|argued|pointed out|noted)",
)


def _ensure_assessment_state(state: dict) -> None:
    state.setdefault("visible_event_ledger", [])
    state.setdefault("assessment_validity_flags", [])
    state.setdefault("floor_handoff_queue", [])
    state.setdefault("simulation_segments", [])


def _client_assessment_action(state: dict) -> dict:
    action = state.get("client_assessment_action")
    return dict(action) if isinstance(action, dict) else {}


def _client_assessment_action_kind(state: dict) -> str:
    return str(_client_assessment_action(state).get("kind") or "").strip()


def _active_gd_topic(state: dict) -> str:
    scenario = state.get("scenario_config") or {}
    return (
        str(
            scenario.get("topic")
            or scenario.get("resolved_topic")
            or state.get("sim_topic")
            or "this topic"
        ).strip()
        or "this topic"
    )


def _as_sentence(text: str) -> str:
    value = (text or "").strip() or "this topic"
    return value if value.endswith((".", "?", "!")) else f"{value}."


def _append_validity_flag(
    state: dict,
    code: str,
    message: str,
    *,
    severity: str = "partial",
    speaker_id: str | None = None,
    target_speaker_id: str | None = None,
) -> None:
    _ensure_assessment_state(state)
    flags = list(state.get("assessment_validity_flags") or [])
    flag = {
        "code": code,
        "message": message,
        "severity": severity,
    }
    if speaker_id:
        flag["speaker_id"] = speaker_id
    if target_speaker_id:
        flag["target_speaker_id"] = target_speaker_id
    if not any(
        item.get("code") == flag["code"]
        and item.get("message") == flag["message"]
        and item.get("speaker_id") == flag.get("speaker_id")
        and item.get("target_speaker_id") == flag.get("target_speaker_id")
        for item in flags
        if isinstance(item, dict)
    ):
        flags.append(flag)
    state["assessment_validity_flags"] = flags[-20:]


def _speaker_visible_keys(state: dict) -> set[str]:
    keys: set[str] = set()
    for event in state.get("visible_event_ledger") or []:
        if not isinstance(event, dict):
            continue
        if event.get("role") not in {"assistant", "simulation_segment"}:
            continue
        for field in ("speaker_id", "speaker_name"):
            value = str(event.get(field) or "").strip().lower()
            if value:
                keys.add(value)
    for message in state.get("messages") or []:
        if message.get("role") != "assistant":
            continue
        for field in ("speaker_id", "speaker_name"):
            value = str(message.get(field) or "").strip().lower()
            if value:
                keys.add(value)
    return keys


def _persona_is_visible(state: dict, persona: dict) -> bool:
    keys = _speaker_visible_keys(state)
    return (
        str(persona.get("speaker_id") or "").strip().lower() in keys
        or str(persona.get("name") or "").strip().lower() in keys
    )


def _detect_handoff_target(text: str, personas: list[dict], current_speaker_id: str) -> dict | None:
    lower = (text or "").lower()
    if not any(term in lower for term in _HANDOFF_TERMS):
        return None
    for persona in personas:
        speaker_id = str(persona.get("speaker_id") or "").strip()
        if not speaker_id or speaker_id == current_speaker_id:
            continue
        name = str(persona.get("name") or "").strip()
        candidates = [name.lower(), speaker_id.replace("_", " ").lower()]
        if any(candidate and re.search(rf"\b{re.escape(candidate)}\b", lower) for candidate in candidates):
            return persona
    return None


def _queue_floor_handoff(state: dict, target: dict, source: dict, reason: str) -> None:
    _ensure_assessment_state(state)
    speaker_id = str(target.get("speaker_id") or "").strip()
    if not speaker_id:
        return
    queue = [
        item for item in (state.get("floor_handoff_queue") or [])
        if isinstance(item, dict) and item.get("speaker_id") != speaker_id
    ]
    queue.append({
        "speaker_id": speaker_id,
        "speaker_name": target.get("name") or speaker_id,
        "source_speaker_id": source.get("speaker_id"),
        "reason": reason,
    })
    state["floor_handoff_queue"] = queue[-4:]


def _detect_unseen_prior_speaker_reference(
    state: dict,
    text: str,
    personas: list[dict],
    current_speaker_id: str,
) -> dict | None:
    lower = (text or "").lower()
    for persona in personas:
        speaker_id = str(persona.get("speaker_id") or "").strip()
        if not speaker_id or speaker_id == current_speaker_id:
            continue
        name = str(persona.get("name") or "").strip()
        if not name:
            continue
        normalized_name = re.escape(name.lower())
        referenced_as_prior = any(
            re.search(pattern.format(name=normalized_name), lower)
            for pattern in _PRIOR_SPEAKER_REFERENCE_PATTERNS
        )
        if referenced_as_prior and not _persona_is_visible(state, persona):
            return persona
    return None


def _gd_integrity_fallback(state: dict, persona: dict) -> str:
    topic = _active_gd_topic(state)
    role_type = str(persona.get("role_type") or "").lower()
    is_moderator = role_type == "moderator" or str(persona.get("speaker_id") or "").lower() == "moderator"
    return gd_integrity_fallback_text(topic, is_moderator=is_moderator)


def _record_visible_segment(
    state: dict,
    persona: dict,
    text: str,
    *,
    kind: str = "simulation_segment",
) -> None:
    from app.services.assessment_events import next_visible_event_id

    _ensure_assessment_state(state)
    segment = {
        "event_id": next_visible_event_id(state),
        "role": "assistant",
        "kind": kind,
        "speaker_id": persona.get("speaker_id"),
        "speaker_name": persona.get("name"),
        "content": text,
    }
    state["visible_event_ledger"] = [*(state.get("visible_event_ledger") or []), segment][-80:]
    state["simulation_segments"] = [*(state.get("simulation_segments") or []), segment][-80:]


def _gd_repeat_fallback_text(
    state: dict,
    persona: dict,
    recent: list[set[str]],
    used: list[str],
) -> str:
    topic = (
        str(
            state.get("sim_topic")
            or (state.get("scenario_config") or {}).get("topic")
            or "this topic"
        ).strip()
        or "this topic"
    )
    role_type = str(persona.get("role_type") or "").lower()
    speaker_id = str(persona.get("speaker_id") or "").lower()
    name = str(persona.get("name") or "").lower()
    is_moderator = (
        role_type == "moderator"
        or "moderator" in speaker_id
        or "moderator" in name
    )
    templates = gd_repeat_fallbacks(topic, is_moderator=is_moderator)
    topic_phrase = gd_topic_phrase(topic)
    cursor = int(state.get("gd_repeat_fallback_cursor") or 0)
    for offset in range(len(templates)):
        candidate = templates[(cursor + offset) % len(templates)].format(
            topic=topic_phrase,
            topic_sentence=_as_sentence(topic),
        )
        if not _is_repeated_probe(candidate, recent, used):
            state["gd_repeat_fallback_cursor"] = cursor + offset + 1
            return candidate
    state["gd_repeat_fallback_cursor"] = cursor + 1
    return (
        f"Push this into implementation for {topic}: name one guardrail, one metric, "
        "and one action the group should take if that metric worsens."
    )


def _gd_safe_repair_text(state: dict, persona: dict, generated: str) -> str:
    recent = _recent_assistant_tokens(state.get("messages") or [], limit=5)
    used = list(state.get("used_gd_prompts") or [])
    text = (generated or "").strip() or _assessment_repair_text(state, TaskType.GD_TEST, persona)
    if _is_repeated_probe(text, recent, used):
        text = _gd_repeat_fallback_text(state, persona, recent, used)
    used.append(text)
    state["used_gd_prompts"] = used[-12:]
    return text


def _safe_gd_turn_text(state: dict, persona: dict, generated: str) -> str:
    """Validate GD panel text before it becomes visible to the learner."""
    _ensure_assessment_state(state)
    text = (generated or "").strip()
    current_speaker_id = str(persona.get("speaker_id") or "").strip()
    if not text:
        _append_validity_flag(
            state,
            "empty_gd_visible_response_repaired",
            f"{persona.get('name') or current_speaker_id} produced an empty visible response, so the backend replaced it with a GD contribution.",
            severity="partial",
            speaker_id=current_speaker_id,
        )
        return _gd_safe_repair_text(
            state,
            persona,
            _assessment_repair_text(state, TaskType.GD_TEST, persona),
        )
    from app.services.assessment_validity import (
        gd_moderator_interview_question_text,
        gd_panelist_ask_only_text,
        gd_panelist_formulaic_meta_text,
        self_label_or_meta_text,
    )

    if self_label_or_meta_text(text, persona):
        current_speaker_id = str(persona.get("speaker_id") or "").strip()
        _append_validity_flag(
            state,
            "self_label_or_meta_response",
            f"{persona.get('name') or current_speaker_id} produced self-label or meta handoff text.",
            severity="partial",
            speaker_id=current_speaker_id,
        )
        return _gd_safe_repair_text(
            state,
            persona,
            _assessment_repair_text(state, TaskType.GD_TEST, persona),
        )
    personas = state.get("personas") or []
    unseen = _detect_unseen_prior_speaker_reference(
        state,
        text,
        personas,
        current_speaker_id,
    )
    if unseen:
        _append_validity_flag(
            state,
            "hidden_speaker_reference",
            (
                f"{persona.get('name') or current_speaker_id} referenced "
                f"{unseen.get('name') or unseen.get('speaker_id')} as if they had "
                "already spoken visibly."
            ),
            severity="invalid",
            speaker_id=current_speaker_id,
            target_speaker_id=unseen.get("speaker_id"),
        )
        return _gd_safe_repair_text(state, persona, _gd_integrity_fallback(state, persona))
    if gd_panelist_ask_only_text(text, persona):
        _append_validity_flag(
            state,
            "gd_panelist_ask_only_repaired",
            f"{persona.get('name') or current_speaker_id} asked a follow-up question or controlled the floor instead of contributing to the discussion.",
            severity="partial",
            speaker_id=current_speaker_id,
        )
        return _gd_safe_repair_text(
            state,
            persona,
            _assessment_repair_text(state, TaskType.GD_TEST, persona),
        )
    if gd_moderator_interview_question_text(text, persona):
        _append_validity_flag(
            state,
            "gd_moderator_interview_prompt_repaired",
            "The Moderator asked a learner-facing interview question, so the backend converted it to a discussion direction.",
            severity="partial",
            speaker_id=current_speaker_id,
        )
        return _gd_safe_repair_text(
            state,
            persona,
            _assessment_repair_text(state, TaskType.GD_TEST, persona),
        )
    if gd_panelist_formulaic_meta_text(text, persona):
        _append_validity_flag(
            state,
            "gd_panelist_formulaic_meta_repaired",
            f"{persona.get('name') or current_speaker_id} used formulaic facilitator framing instead of contributing as a panelist.",
            severity="partial",
            speaker_id=current_speaker_id,
        )
        return _gd_safe_repair_text(
            state,
            persona,
            _assessment_repair_text(state, TaskType.GD_TEST, persona),
        )
    handoff_target = (
        _detect_handoff_target(text, personas, current_speaker_id)
        if _is_moderator_persona(persona) and not isinstance(state.get("assessment_plan"), dict)
        else None
    )
    if handoff_target:
        _queue_floor_handoff(
            state,
            handoff_target,
            persona,
            "visible_handoff",
        )
    recent = _recent_assistant_tokens(state.get("messages") or [], limit=5)
    used = list(state.get("used_gd_prompts") or [])
    if not _is_repeated_probe(text, recent, used):
        used.append(text)
        state["used_gd_prompts"] = used[-12:]
        return text
    fallback = _gd_repeat_fallback_text(state, persona, recent, used)
    used.append(fallback)
    state["used_gd_prompts"] = used[-12:]
    return fallback


# ===== persona roster ========================================================
#
# A roster is fixed once per session (persisted in state["personas"]) so a
# speaker_id maps to the same voice across rounds — the UI keeps stable bubbles.
# GD participants carry a `stance` so qwen renders genuinely opposed voices in
# the single pass; the interview panel is one neutral interviewer.

# Each debater carries not just a SIDE but topic-stable grounds (what they argue
# FROM), a temperament, and a rhetorical signature, so qwen renders genuinely
# distinct voices on any motion instead of three interchangeable "agree/disagree"
# speakers. The Moderator is an explicit non-arguing facilitator (also kept out of
# the reactor pool by _reactor_pool), so it never collapses into a fourth debater.
_GD_PANEL = [
    {"speaker_id": "moderator", "name": "Moderator",
     "stance": "the neutral FACILITATOR — you never argue a side. You frame the "
               "question, keep time, draw in whoever has stayed quiet, press a "
               "vague claim for specifics, and periodically sum up where the group "
               "agrees and where it splits."},
    {"speaker_id": "gd_a", "name": "Aarav",
     "stance": "strongly IN FAVOUR of the motion. You argue from opportunity, "
               "progress and hard data; energetic and optimistic in temperament, "
               "you lead with concrete real-world examples and numbers."},
    {"speaker_id": "gd_b", "name": "Meera",
     "stance": "strongly AGAINST the motion. You argue from risk, harm and "
               "fairness to those worst affected; sharp and urgent in temperament, "
               "you expose hidden assumptions and name the worst-case consequence."},
    {"speaker_id": "gd_c", "name": "Kabir",
     "stance": "a PRAGMATIC middle ground. You argue from trade-offs and what "
               "actually works in practice; measured and diplomatic, you concede a "
               "fair point before qualifying it and keep hunting for a workable "
               "synthesis."},
]

_INTERVIEWER = [
    {"speaker_id": "interviewer", "name": "Interviewer", "role": "panel interviewer"},
]

# Per-session interviewer manner so repeat interview sessions don't feel
# identical. One interviewer, varied delivery: the manner is picked
# deterministically from the topic (stable within a session, varies across
# topics) and injected into the persona's speaking prompt by build_persona_prompt.
_INTERVIEWER_STYLES = [
    "warm and encouraging — put the candidate at ease, but still probe for substance",
    "neutral and businesslike — brisk and professional, neither warm nor cold",
    "probing and skeptical — politely press every claim for specifics and evidence",
    "rapid-fire and high-tempo — short, quick follow-ups that test composure under pace",
]


def _interviewer_style(topic: str) -> str:
    """Deterministic per-session interviewer manner from the topic string.

    crc32 (not the salted built-in hash()) so the same topic maps to the same
    manner across processes — a session's interviewer tone stays stable on
    reload, while a different topic can draw a different tone."""
    idx = zlib.crc32((topic or "").encode("utf-8")) % len(_INTERVIEWER_STYLES)
    return _INTERVIEWER_STYLES[idx]


def build_personas(task_type: TaskType, topic: str) -> list[dict]:
    """Deterministic persona roster for a test-mode simulation.

    GD returns the fixed debater panel. INTERVIEW returns the single interviewer
    with a per-session `style` (tonal manner) drawn deterministically from the
    `topic`, so repeat interviews vary in delivery without adding new personas or
    avatars; build_persona_prompt renders that style into the speaking prompt.
    """
    if task_type == TaskType.GD_TEST:
        return [dict(GD_PERSONA_LIBRARY["moderator_timekeeper"])] + [
            dict(GD_PERSONA_LIBRARY[pid]) for pid in DEFAULT_GD_PERSONAS
        ]
    if task_type == TaskType.INTERVIEW_TEST:
        persona = dict(_INTERVIEWER[0])
        persona["style"] = _interviewer_style(topic)
        return [persona]
    # non-simulation task types still get one neutral voice so the runner is total
    return [{"speaker_id": "examiner", "name": "Examiner", "role": "examiner"}]


def _sim_history(messages: list[dict], limit: int = 8) -> str:
    """Build a readable conversation history for the simulation prompt.

    Critically: label user messages as '[Learner]' so the LLM cannot confuse
    the learner's contributions with one of the named GD personas (e.g. Aarav).
    The current user turn must be included: the Director scores and routes the
    next simulation beat based on the answer that was just submitted, not the
    previous round. Assistant-side messages already carry the [Name]: prefix in
    their stored content, so they render cleanly as-is.
    """
    if not messages:
        return "(discussion just opened)"
    recent = messages[-limit:]
    lines = []
    for m in recent:
        if m.get("role") == "user":
            lines.append(f"[Learner]: {m['content']}")
        else:
            speaker = str(m.get("speaker_name") or "").strip()
            content = str(m.get("content") or "")
            lines.append(f"[{speaker}]: {content}" if speaker else content)
    return "\n".join(lines)


async def _stream_speaker_turn(
    persona,
    intent,
    transcript,
    bb,
    roster,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
    task_type: TaskType | None = None,
):
    """Stream one persona's spoken turn, guaranteeing non-empty output.

    Yields the persona's text tokens; if the model returns nothing (a backend
    hiccup) it yields a single re-prompt line so a turn never dead-ends. The
    caller accumulates the yielded tokens to recover the full text."""
    produced = False
    async for tok in stream_persona_turn(
        persona,
        intent,
        transcript,
        bb,
        roster,
        scenario_config=scenario_config,
        career_context=career_context,
        task_type=task_type,
    ):
        produced = produced or bool(tok.strip())
        yield tok
    if not produced and task_type != TaskType.GD_TEST:
        yield _EMPTY_TURN_FALLBACK


def _typed_control_payload(
    state: dict,
    *,
    task_type: TaskType,
    personas: list[dict],
    bb: dict,
) -> tuple[dict, DirectorDecision, str, dict] | None:
    action = _client_assessment_action(state)
    kind = str(action.get("kind") or "").strip()
    if kind not in {"clarify", "new_angle", "move_on"}:
        return None

    if task_type == TaskType.GD_TEST:
        persona = _moderator_persona(personas)
        topic = _active_gd_topic(state)
        topic_sentence = _as_sentence(topic)
        if kind == "clarify":
            text = (
                f"The motion remains: {topic_sentence} Take a clear position, add "
                "one concrete reason or example, then invite one active panelist "
                "to respond."
            )
            control_intent = "clarify"
        else:
            text = (
                f"Hold the motion steady: {topic_sentence} Put the stakeholder "
                "who gains the most beside the stakeholder carrying the biggest "
                "cost, then continue from that tension instead of repeating the "
                "same proof demand."
            )
            control_intent = "new_angle" if kind == "new_angle" else "move_on"
        decision = DirectorDecision(
            action="pivot_topic",
            next_speaker=str(persona.get("speaker_id") or "moderator"),
            intent=text,
            tension=max(0.2, float(bb.get("tension", 0.35)) - 0.1),
            answer_quality=float(bb.get("last_quality", 0.5)),
            should_close=False,
        )
        analysis = {
            "mode": TaskType.GD_TEST.value,
            "routing_case": "control",
            "control_intent": control_intent,
            "scorable": False,
            "client_action": action,
            "quality_score": 0.0,
        }
        return persona, decision, text, analysis

    if task_type == TaskType.INTERVIEW_TEST:
        persona = personas[0] if personas else {"speaker_id": "interviewer", "name": "Interviewer"}
        if kind == "clarify":
            prompt = str(state.get("active_interview_probe_prompt") or "").strip()
            if not prompt:
                prompt = (
                    "Tell me one specific work example: what situation you faced, "
                    "what you personally did, and what changed because of it."
                )
                _set_active_interview_probe(
                    state,
                    prompt,
                    skill_id="interview_clarified_example_structure",
                )
            text = (
                "In simpler terms, I am asking for one specific example. "
                f"{prompt}"
            )
            control_intent = "clarify"
        elif kind == "move_on":
            active_prompt = str(state.get("active_interview_probe_prompt") or "").strip()
            if active_prompt:
                used = list(state.get("used_probe_prompts") or [])
                if active_prompt not in used:
                    used.append(active_prompt)
                    state["used_probe_prompts"] = used[-12:]
            probe = _select_next_interview_probe(state)
            prompt = str(probe.get("prompt") or "").strip()
            if not prompt:
                prompt = (
                    "Tell me about a disagreement with a teammate or stakeholder. "
                    "What did you say, what changed, and what did you learn?"
                )
            _set_active_interview_probe(
                state,
                prompt,
                skill_id=probe.get("skill_id") or probe.get("id"),
                prompt_id=probe.get("prompt_id"),
            )
            used = list(state.get("used_probe_prompts") or [])
            if prompt not in used:
                used.append(prompt)
                state["used_probe_prompts"] = used[-12:]
            text = f"Let's move to a different area. {prompt}"
            control_intent = "move_on"
        else:
            return None
        decision = DirectorDecision(
            action="pivot_topic",
            next_speaker=str(persona.get("speaker_id") or "interviewer"),
            intent=text,
            tension=max(0.2, float(bb.get("tension", 0.35)) - 0.1),
            answer_quality=float(bb.get("last_quality", 0.5)),
            should_close=False,
        )
        analysis = {
            "mode": TaskType.INTERVIEW_TEST.value,
            "answer_kind": "control_request",
            "control_intent": control_intent,
            "scorable": False,
            "active_probe_id": state.get("active_interview_probe_prompt_id"),
            "client_action": action,
            "quality_score": 0.0,
        }
        return persona, decision, text, analysis

    return None


async def _stream_typed_assessment_control(
    state: dict,
    *,
    task_type: TaskType,
    personas: list[dict],
    bb: dict,
) -> AsyncIterator[object]:
    from app.services.assessment_events import append_assessment_event

    payload = _typed_control_payload(
        state,
        task_type=task_type,
        personas=personas,
        bb=bb,
    )
    if payload is None:
        return
    persona, decision, text, analysis = payload
    new_bb = apply_decision(
        bb,
        decision,
        count_quality=False,
        count_turn=False,
    )
    _settle_pending_coverage_event(
        state,
        decision,
        control_turn=True,
    )
    speaker_id = str(persona.get("speaker_id") or decision.next_speaker)
    yield Speaker(speaker_id=speaker_id, name=persona.get("name") or speaker_id)
    yield SimulationState(
        turn=new_bb["turn"],
        speaker_id=speaker_id,
        tension=new_bb["tension"],
        should_close=False,
    )
    if task_type == TaskType.INTERVIEW_TEST:
        text = _safe_interview_turn_text(state, text)
    else:
        text = _safe_gd_turn_text(state, persona, text)
    _stage_prompt_coverage_event(
        state,
        task_type,
        persona,
        decision,
        text,
        primary=True,
        blackboard=new_bb,
    )
    _record_visible_segment(state, persona, text)
    append_assessment_event(
        state,
        event_type="analysis",
        task_type=task_type.value,
        speaker_id=speaker_id,
        scorable=False,
        analysis=analysis,
        content=text,
    )
    state["blackboard"] = note_turn(new_bb, speaker_id, text)
    yield text


async def _stream_structured_assessment_round(
    state: dict,
    *,
    task_type: TaskType,
    personas: list[dict],
    bb: dict,
) -> AsyncIterator[object]:
    """Run the one-call assessment engine for a planned test session."""
    from app.services.assessment_turn import run_assessment_turn

    if _client_assessment_action_kind(state) in {"clarify", "new_angle", "move_on"}:
        async for item in _stream_typed_assessment_control(
            state,
            task_type=task_type,
            personas=personas,
            bb=bb,
        ):
            yield item
        return

    if task_type == TaskType.INTERVIEW_TEST:
        _prepare_interview_assessment_turn_context(state)
    authorized = await asyncio.wait_for(
        run_assessment_turn(state),
        timeout=ASSESSMENT_TURN_TIMEOUT_SECONDS,
    )
    from app.services.assessment_events import append_assessment_event

    decision = authorized.decision
    persona = authorized.persona
    speaker_id = str(persona.get("speaker_id") or decision.next_speaker)
    raw_text = authorized.text
    control_intent = str((authorized.analysis or {}).get("control_intent") or "none")
    if task_type == TaskType.INTERVIEW_TEST and control_intent != "none":
        _restore_interview_probe_after_control(state)
    safe_flags_start = len(state.get("assessment_validity_flags") or [])
    if task_type == TaskType.INTERVIEW_TEST and control_intent != "none":
        text = raw_text
    elif task_type == TaskType.INTERVIEW_TEST:
        text = _safe_interview_turn_text(state, raw_text)
    else:
        text = _safe_gd_turn_text(state, persona, raw_text)
    safe_flags = list(state.get("assessment_validity_flags") or [])[safe_flags_start:]
    visible_repaired = bool(safe_flags) or text != raw_text
    score_excluded_by_repair = _has_score_excluding_repair(authorized.flags)
    runtime_turn_countable = bool(authorized.scorable)
    effective_scorable = runtime_turn_countable and not score_excluded_by_repair
    event_analysis = dict(authorized.analysis or {})
    if not effective_scorable:
        event_analysis["scorable"] = False
    if score_excluded_by_repair:
        event_analysis["score_excluded_reason"] = "simulator_integrity_repair"
    if visible_repaired:
        event_analysis["visible_response_repaired"] = True
        event_analysis["visible_response_repair_codes"] = [
            str(flag.get("code") or "")
            for flag in safe_flags
            if isinstance(flag, dict) and flag.get("code")
        ] or ["visible_response_rewritten"]
    event_flags = [*list(authorized.flags or []), *safe_flags]
    append_assessment_event(
        state,
        event_type="analysis",
        task_type=task_type.value,
        speaker_id=speaker_id,
        scorable=effective_scorable,
        analysis=event_analysis,
        content=text,
        validity_flags=event_flags,
    )
    new_bb = apply_decision(
        bb,
        decision,
        count_quality=effective_scorable,
        count_turn=runtime_turn_countable,
    )
    repair_excluded = bool(score_excluded_by_repair)
    _settle_pending_coverage_event(
        state,
        decision,
        control_turn=not effective_scorable,
        skip_reason="simulator_integrity_repair" if repair_excluded else "simulation_control",
        skipped_by_user=not repair_excluded,
    )
    model_requested_close = bool(decision.should_close)
    hard_round_cap_reached = (
        new_bb["turn"] >= MAX_SIM_ROUNDS
        or (control_intent == "none" and int(bb.get("turn") or 0) >= MAX_SIM_ROUNDS - 1)
    )
    if hard_round_cap_reached and int(bb.get("turn") or 0) >= MAX_SIM_ROUNDS - 1 and new_bb["turn"] < MAX_SIM_ROUNDS:
        new_bb = {**new_bb, "turn": MAX_SIM_ROUNDS}
    should_close = model_requested_close or hard_round_cap_reached
    if model_requested_close and not hard_round_cap_reached:
        scorable_count = _scorable_turn_count_from_events(state) or 0
        min_turns = _MIN_FINAL_SCORABLE_TURNS.get(task_type, 1)
        if scorable_count < min_turns:
            _append_validity_flag(
                state,
                "early_close_suppressed",
                (
                    "The assessment model tried to close before enough scorable "
                    "learner evidence was collected, so the backend kept the test open."
                ),
                severity="partial",
                speaker_id=speaker_id,
            )
            should_close = False
    if should_close and not state.get("session_over"):
        state["session_over"] = True
        state["input_allowed"] = False
        state["block_reason"] = "session_over"
        state["session_version"] = int(state.get("session_version") or 1) + 1

    if hard_round_cap_reached:
        state["blackboard"] = new_bb
        yield SimulationState(
            turn=new_bb["turn"],
            speaker_id=speaker_id,
            tension=new_bb["tension"],
            should_close=True,
        )
        return

    yield Speaker(speaker_id=speaker_id, name=persona.get("name") or speaker_id)
    yield SimulationState(
        turn=new_bb["turn"],
        speaker_id=speaker_id,
        tension=new_bb["tension"],
        should_close=should_close,
    )

    _stage_prompt_coverage_event(
        state,
        task_type,
        persona,
        decision,
        text,
        primary=True,
        blackboard=new_bb,
    )
    _record_visible_segment(state, persona, text)
    state["blackboard"] = note_turn(new_bb, speaker_id, text)
    yield text


def _assessment_repair_text(state: dict, task_type: TaskType, persona: dict) -> str:
    if task_type == TaskType.INTERVIEW_TEST:
        selected = str(state.get("active_interview_probe_prompt") or "").strip()
        if selected:
            return selected
        role = _primary_role_label(state)
        return f"Tell me one specific example that shows ownership for {role}. What did you do, and what changed?"
    topic = _active_gd_topic(state)
    speaker_id = str(persona.get("speaker_id") or "")
    role_type = str(persona.get("role_type") or "").lower()
    return gd_persona_fallback_text(topic, speaker_id, role_type)


def _repair_persona_for_assessment_failure(
    state: dict,
    task_type: TaskType,
    personas: list[dict],
    bb: dict,
) -> tuple[dict, dict]:
    fallback_scorable, fallback_quality, fallback_points = _deterministic_fallback_assessment(state)
    quality = fallback_quality if fallback_scorable else float(bb.get("last_quality", 0.0) or 0.0)
    if task_type == TaskType.INTERVIEW_TEST:
        persona = personas[0] if personas else {"speaker_id": "interviewer", "name": "Interviewer", "role_type": "interviewer"}
        return persona, {
            "mode": task_type.value,
            "answer_kind": "answer",
            "control_intent": "none",
            "scorable": fallback_scorable,
            "active_probe_id": state.get("active_interview_probe_prompt_id") or "",
            "quality_score": quality,
            "evidence_points": fallback_points,
            "assessment_source": "deterministic_fallback",
            "repair_reason": "assessment_turn_call_failed",
        }

    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    actual_roster = {
        str(persona.get("speaker_id") or ""): persona
        for persona in personas
        if persona.get("speaker_id")
    }
    requested_id = ""
    if plan:
        from app.services.assessment_validity import explicit_requested_speaker_id, next_active_debater

        client_action = _client_assessment_action(state)
        if str(client_action.get("kind") or "") == "ask_panelist":
            requested_id = str(
                client_action.get("speaker_id")
                or client_action.get("target_speaker_id")
                or ""
            ).strip()
        if not requested_id:
            requested_id = explicit_requested_speaker_id(
                plan,
                _last_user_message(state.get("messages") or []),
            )
        if requested_id and requested_id in actual_roster:
            persona = actual_roster[requested_id]
        else:
            plan_persona = next_active_debater(plan, after=str(bb.get("last_speaker") or ""))
            persona = actual_roster.get(str(plan_persona.get("speaker_id") or "")) or _moderator_persona(personas)
    else:
        persona = _moderator_persona(personas)
    return persona, {
        "mode": task_type.value,
        "routing_case": "reply_and_request" if requested_id else "point_only",
        "control_intent": "none",
        "scorable": fallback_scorable,
        "requested_next_speaker": requested_id,
        "request_confidence": 1.0 if requested_id else 0.0,
        "quality_score": quality,
        "evidence_points": fallback_points,
        "assessment_source": "deterministic_fallback",
        "repair_reason": "assessment_turn_call_failed",
    }


async def _stream_assessment_failure_repair_round(
    state: dict,
    *,
    task_type: TaskType,
    personas: list[dict],
    bb: dict,
) -> AsyncIterator[object]:
    from app.services.assessment_events import (
        append_assessment_event,
        append_validity_flag as append_assessment_validity_flag,
    )

    persona, analysis = _repair_persona_for_assessment_failure(state, task_type, personas, bb)
    speaker_id = str(persona.get("speaker_id") or "moderator")
    fallback_answer_substantive = bool(analysis.get("scorable") is True)
    analysis["scorable"] = False
    analysis["score_excluded_reason"] = "assessment_turn_call_failed"
    fallback_scorable = False
    fallback_quality = float(analysis.get("quality_score") or 0.0)
    flag = append_assessment_validity_flag(
        state,
        "assessment_turn_call_failed",
        "The structured assessment turn call failed, so the backend used a single deterministic repair turn instead of legacy multi-speaker routing.",
        severity="partial",
        speaker_id=speaker_id,
    )
    decision = DirectorDecision(
        action="pivot_topic" if analysis.get("requested_next_speaker") else "probe_deeper",
        next_speaker=speaker_id,
        intent="Deterministic assessment repair after a failed structured turn call.",
        tension=float(bb.get("tension", 0.35)),
        answer_quality=fallback_quality if fallback_scorable else float(bb.get("last_quality", 0.5)),
        should_close=False,
    )
    hard_cap_pending = int(bb.get("turn") or 0) >= MAX_SIM_ROUNDS - 1
    new_bb = apply_decision(
        bb,
        decision,
        count_quality=fallback_scorable,
        count_turn=fallback_answer_substantive or hard_cap_pending,
    )
    _settle_pending_coverage_event_after_assessment_failure(
        state,
        score_evidence=None,
    )
    should_close = new_bb["turn"] >= MAX_SIM_ROUNDS
    if should_close and not state.get("session_over"):
        state["session_over"] = True
        state["input_allowed"] = False
        state["block_reason"] = "session_over"
        state["session_version"] = int(state.get("session_version") or 1) + 1

    if should_close:
        append_assessment_event(
            state,
            event_type="analysis",
            task_type=task_type.value,
            speaker_id=speaker_id,
            scorable=fallback_scorable,
            analysis=analysis,
            content="",
            validity_flags=[flag],
        )
        state["blackboard"] = new_bb
        yield SimulationState(
            turn=new_bb["turn"],
            speaker_id=speaker_id,
            tension=new_bb["tension"],
            should_close=True,
        )
        return

    yield Speaker(speaker_id=speaker_id, name=persona.get("name") or speaker_id)
    yield SimulationState(
        turn=new_bb["turn"],
        speaker_id=speaker_id,
        tension=new_bb["tension"],
        should_close=should_close,
    )
    text = _assessment_repair_text(state, task_type, persona)
    if task_type == TaskType.INTERVIEW_TEST:
        text = _safe_interview_turn_text(state, text)
    else:
        text = _safe_gd_turn_text(state, persona, text)
    _stage_prompt_coverage_event(
        state,
        task_type,
        persona,
        decision,
        text,
        primary=True,
        blackboard=new_bb,
    )
    _record_visible_segment(state, persona, text)
    append_assessment_event(
        state,
        event_type="analysis",
        task_type=task_type.value,
        speaker_id=speaker_id,
        scorable=fallback_scorable,
        analysis=analysis,
        content=text,
        validity_flags=[flag],
    )
    state["blackboard"] = note_turn(new_bb, speaker_id, text)
    yield text


async def stream_simulation_round(state: dict) -> AsyncIterator[object]:
    """Run one writers'-room round: Director decides, one Persona streams.

    The roster is built once and cached in `state["personas"]`; the Blackboard
    (shared group memory) is created lazily and persisted in `state["blackboard"]`.
    The Director picks WHO speaks and WHAT intent; this round yields a `Speaker`
    marker, a `SimulationState` snapshot, then that speaker's streamed text. A
    director failure falls back to a safe decision inside `decide_round`, and an
    empty persona turn falls back to a single re-prompt line so a round never
    dead-ends.
    """
    _ensure_assessment_state(state)
    messages = state.get("messages", [])
    task_type = TaskType(state["task_type"])
    personas = state.get("personas") or build_personas(
        task_type, state.get("sim_topic", "")
    )
    state["personas"] = personas
    topic = state.get("sim_topic", "")
    scenario_config = state.get("scenario_config") or {}
    career_context = state.get("career_context") or {}
    transcript = _sim_history(messages, limit=8)
    bb = state.get("blackboard") or new_blackboard(topic)

    # Phase the discussion is in BEFORE the Director moves — drives how many
    # panelists cross-talk this round (a fresh round opens single-voice).
    prev_phase = bb.get("phase", "opening")

    if isinstance(state.get("assessment_plan"), dict):
        try:
            async for item in _stream_structured_assessment_round(
                state,
                task_type=task_type,
                personas=personas,
                bb=bb,
            ):
                yield item
            return
        except Exception as exc:
            logger.warning(
                "Structured assessment turn failed for session_id=%s task_type=%s error_type=%s; using deterministic repair.",
                state.get("session_id"),
                task_type.value,
                type(exc).__name__,
                exc_info=True,
            )
            async for item in _stream_assessment_failure_repair_round(
                state,
                task_type=task_type,
                personas=personas,
                bb=bb,
            ):
                yield item
            return

    control_decision = (
        _interview_control_decision(state, personas, bb)
        or _gd_control_decision(state, personas, bb)
    )
    control_turn = control_decision is not None
    if control_decision:
        new_bb = apply_decision(
            bb,
            control_decision,
            count_quality=False,
            count_turn=False,
        )
        persona = next(
            p for p in personas
            if p["speaker_id"] == control_decision.next_speaker
        )
        decision = control_decision
    else:
        new_bb, persona, decision = await decide_round(
            bb,
            personas,
            task_type,
            transcript,
            state.get("probe_items"),
            scenario_config=scenario_config,
            career_context=career_context,
        )
    _settle_pending_coverage_event(state, decision, control_turn=control_turn)
    speaker_id = persona["speaker_id"]
    # Consume the Director's close signal (or the hard round cap). Closing a
    # simulation blocks more learner turns, but leaves status active so /end can
    # still score and persist the report.
    should_close = bool(decision.should_close) or new_bb["turn"] >= MAX_SIM_ROUNDS
    if should_close and not state.get("session_over"):
        state["session_over"] = True
        state["input_allowed"] = False
        state["block_reason"] = "session_over"
        state["session_version"] = int(state.get("session_version") or 1) + 1

    # ----- primary speaker: the Director's chosen voice + intent -----
    # One SimulationState per round (the round snapshot) is emitted here with the
    # primary speaker; reactors below add only Speaker markers + text.
    yield Speaker(speaker_id=speaker_id, name=persona["name"])
    yield SimulationState(
        turn=new_bb["turn"],
        speaker_id=speaker_id,
        tension=new_bb["tension"],
        should_close=should_close,
    )
    running_transcript = transcript
    chunks: list[str] = []
    speaker_intent = decision.intent if control_turn else _interview_probe_intent(state, decision.intent)
    if task_type == TaskType.INTERVIEW_TEST:
        async for tok in _stream_speaker_turn(
            persona,
            speaker_intent,
            running_transcript,
            new_bb,
            personas,
            scenario_config=scenario_config,
            career_context=career_context,
            task_type=task_type,
        ):
            chunks.append(tok)
        safe_text = _safe_interview_turn_text(state, "".join(chunks))
        chunks = [safe_text]
        _stage_prompt_coverage_event(
            state,
            task_type,
            persona,
            decision,
            safe_text,
            primary=True,
            blackboard=new_bb,
        )
        _record_visible_segment(state, persona, safe_text)
        yield safe_text
    else:
        async for tok in _stream_speaker_turn(
            persona,
            speaker_intent,
            running_transcript,
            new_bb,
            personas,
            scenario_config=scenario_config,
            career_context=career_context,
            task_type=task_type,
        ):
            chunks.append(tok)
        safe_text = _safe_gd_turn_text(state, persona, "".join(chunks))
        chunks = [safe_text]
        _stage_prompt_coverage_event(
            state,
            task_type,
            persona,
            decision,
            safe_text,
            primary=True,
            blackboard=new_bb,
        )
        _record_visible_segment(state, persona, safe_text)
        yield safe_text
    last_name = persona["name"]
    full_text = "".join(chunks).strip()
    new_bb = note_turn(new_bb, speaker_id, full_text)
    running_transcript = f"{running_transcript}\n[{last_name}]: {full_text}"

    # A visible moderator/panel handoff is binding: if a segment says "Devil's
    # Advocate, respond", the next visible segment must be Devil's Advocate or a
    # repair. This closes the old gap where generated prose referenced a handoff
    # but the runtime advanced back to the learner.
    handoff_consumed = False
    if task_type == TaskType.GD_TEST and state.get("floor_handoff_queue"):
        queued = list(state.get("floor_handoff_queue") or [])
        state["floor_handoff_queue"] = queued[1:]
        target_id = queued[0].get("speaker_id")
        target = next((p for p in personas if p.get("speaker_id") == target_id), None)
        if target:
            handoff_consumed = True
            yield Speaker(speaker_id=target["speaker_id"], name=target["name"])
            h_chunks: list[str] = []
            handoff_intent = (
                f"You were just explicitly given the floor by {last_name}. "
                "Respond directly to the active motion, take your own stance, "
                "and add one concrete counterpoint, metric, or synthesis move for "
                "the group. Do not interview the learner, and do not claim any "
                "other speaker made a point unless it is visible in the transcript."
            )
            async for tok in _stream_speaker_turn(
                target,
                handoff_intent,
                running_transcript,
                new_bb,
                personas,
                scenario_config=scenario_config,
                career_context=career_context,
                task_type=task_type,
            ):
                h_chunks.append(tok)
            h_text = _safe_gd_turn_text(state, target, "".join(h_chunks))
            _stage_prompt_coverage_event(
                state,
                task_type,
                target,
                decision,
                h_text,
                primary=False,
                blackboard=new_bb,
            )
            _record_visible_segment(state, target, h_text, kind="floor_handoff")
            yield h_text
            new_bb = note_turn(new_bb, target["speaker_id"], h_text)
            running_transcript = f"{running_transcript}\n[{target['name']}]: {h_text}"
            last_name = target["name"]

    # ----- reactor exchange (GD cross-talk): bounded + deterministic -----
    # Each reactor is a DIFFERENT voice (rotation off whoever just spoke), told
    # to engage the previous speaker by name. Reactors use note_turn only (no
    # apply_decision), so they don't inflate the round count that drives the cap.
    # Rotation is over the debater pool only — the Moderator facilitates as a
    # primary speaker but never jumps in as a cross-talk reactor.
    reactor_pool = _reactor_pool(personas)
    extra_speakers = 0 if control_turn or handoff_consumed else _extra_speakers(prev_phase, should_close, task_type)
    for _ in range(extra_speakers):
        reactor_id = _next_in_rotation(reactor_pool, new_bb["last_speaker"])
        reactor = next(p for p in personas if p["speaker_id"] == reactor_id)
        yield Speaker(speaker_id=reactor_id, name=reactor["name"])
        r_chunks: list[str] = []
        async for tok in _stream_speaker_turn(
            reactor,
            _reactor_intent(last_name),
            running_transcript,
            new_bb,
            personas,
            scenario_config=scenario_config,
            career_context=career_context,
            task_type=task_type,
        ):
            r_chunks.append(tok)
        r_text = _safe_gd_turn_text(state, reactor, "".join(r_chunks))
        _record_visible_segment(state, reactor, r_text)
        yield r_text
        new_bb = note_turn(new_bb, reactor_id, r_text)
        running_transcript = f"{running_transcript}\n[{reactor['name']}]: {r_text}"
        last_name = reactor["name"]

    state["blackboard"] = new_bb


_ROUND_QUALITY_WEIGHT = 0.4   # weight on the per-round director reads in the score blend
_REPEAT_SIMILARITY_THRESHOLD = 0.72
_REPEAT_COUNT_THRESHOLD = 3
_MIN_FINAL_SCORABLE_TURNS = {
    TaskType.INTERVIEW_TEST: 6,
    TaskType.GD_TEST: 5,
}
_MIN_UNIQUE_COVERAGE = {
    TaskType.INTERVIEW_TEST: 4,
    TaskType.GD_TEST: 3,
}
_NARROW_COVERAGE_SCORE_CAP = 0.72
_REPETITION_BLAME_TERMS = (
    "elaborate further",
    "repeating points",
    "repeated points",
    "repetition",
    "same prompt",
    "same question",
    "repeated prompt",
    "repeated question",
    "return to",
)
_SCORE_EXCLUDING_REPAIR_CODES = {
    "assessment_quality_score_repaired",
    "assessment_turn_call_failed",
    "interview_missing_evidence_repaired",
}
_INTERVIEW_REPORT_LEAK_TERMS = (
    "synthesize multiple viewpoints",
    "synthesize others",
    "synthesizing others",
    "synthesizing others' contributions",
    "synthesizing other contributions",
    "multiple viewpoints",
    "other participants",
    "other speakers",
    "group discussion",
    "panelist",
    "consensus",
    "claiming the floor",
    "dominant speaker",
    "quiet participant",
    "rebuttal",
    "steer discussion",
    "steering discussion",
    "build on others",
    "synthesis",
)
_TOKEN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "can", "could", "did",
    "do", "for", "from", "how", "i", "in", "is", "it", "me", "of", "on",
    "or", "that", "the", "this", "to", "was", "what", "with", "would", "you",
    "your",
}


def _normalize_round_quality_value(value: object) -> float | None:
    try:
        quality = float(value)
    except (TypeError, ValueError):
        return None
    if quality <= 0:
        return None
    if quality > 10 and quality <= 100:
        quality = quality / 100.0
    elif quality > 1 and quality <= 10:
        quality = quality / 10.0
    elif quality < 0.1:
        # Legacy Qwen/local-model turns briefly stored 0-10 scores after they
        # had already been divided by 100, e.g. 3 -> 0.03. A valid scorable turn
        # should not carry near-zero quality; zero/invalid values are handled
        # separately by assessment_quality_score_repaired.
        quality = quality * 10.0
    return round(max(0.0, min(1.0, quality)), 4)


def _normalized_round_qualities(state: dict) -> list[float]:
    raw = (state.get("blackboard") or {}).get("qualities", [])
    if not isinstance(raw, list):
        return []
    typed_events = [
        event
        for event in state.get("assessment_events") or []
        if isinstance(event, dict) and event.get("event_type") == "analysis"
    ]
    if typed_events:
        typed_qualities: list[float] = []
        scorable_count = 0
        for event in typed_events:
            if event.get("scorable") is not True:
                continue
            scorable_count += 1
            analysis = event.get("analysis") if isinstance(event.get("analysis"), dict) else {}
            quality = _normalize_round_quality_value(analysis.get("quality_score"))
            if quality is not None:
                typed_qualities.append(quality)
        if typed_qualities:
            return typed_qualities
        if len(raw) != scorable_count:
            return []
    normalized: list[float] = []
    for value in raw:
        quality = _normalize_round_quality_value(value)
        if quality is not None:
            normalized.append(quality)
    return normalized


def _tokens_for_repetition(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in _TOKEN_STOPWORDS
    }


def _token_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _repeated_assistant_prompt_count(messages: list[dict]) -> int:
    clusters: list[tuple[set[str], int]] = []
    for message in messages:
        if message.get("role") != "assistant":
            continue
        text = str(message.get("content") or "").strip()
        if len(text) < 24:
            continue
        tokens = _tokens_for_repetition(text)
        if len(tokens) < 4:
            continue
        for index, (existing, count) in enumerate(clusters):
            if _token_similarity(existing, tokens) >= _REPEAT_SIMILARITY_THRESHOLD:
                clusters[index] = (existing | tokens, count + 1)
                break
        else:
            clusters.append((tokens, 1))
    return max((count for _tokens, count in clusters), default=0)


def _repeated_unanswered_prompt_count(messages: list[dict]) -> int:
    """Count repeated assistant prompts only when no learner answer separated them."""
    max_count = 0
    clusters: list[tuple[set[str], int]] = []

    def flush() -> None:
        nonlocal max_count, clusters
        if clusters:
            repeated_counts = [count for _tokens, count in clusters if count > 1]
            max_count = max(max_count, max(repeated_counts, default=0))
        clusters = []

    for message in messages:
        role = message.get("role")
        if role == "user":
            flush()
            continue
        if role != "assistant":
            continue
        if message.get("message_kind") == "simulation_control":
            continue
        text = str(message.get("content") or "").strip()
        if len(text) < 24:
            continue
        tokens = _tokens_for_repetition(text)
        if len(tokens) < 4:
            continue
        for index, (existing, count) in enumerate(clusters):
            if _token_similarity(existing, tokens) >= _REPEAT_SIMILARITY_THRESHOLD:
                clusters[index] = (existing | tokens, count + 1)
                break
        else:
            clusters.append((tokens, 1))
    flush()
    return max_count


def _simulator_integrity_notes(state: dict, task_type: TaskType) -> list[str]:
    notes = []
    seen: set[str] = set()
    for flag in state.get("assessment_validity_flags") or []:
        if not isinstance(flag, dict):
            continue
        message = str(flag.get("message") or flag.get("code") or "").strip()
        if message and message not in seen:
            notes.append(message)
            seen.add(message)
    if task_type == TaskType.INTERVIEW_TEST:
        repeat_count = _repeated_unanswered_prompt_count(state.get("messages") or [])
        if repeat_count >= _REPEAT_COUNT_THRESHOLD:
            notes.append(
                "The interviewer repeated an unanswered prompt several times, so the simulator transcript should be treated as provisional."
            )
    return notes


def _assessment_caveats(state: dict, task_type: TaskType) -> list[str]:
    return [
        f"Simulator caveat: {message}"
        for message in _simulator_integrity_notes(state, task_type)
    ]


def _combined_caveats(learner_caveats: list[str], simulator_notes: list[str]) -> list[str]:
    combined: list[str] = []
    seen: set[str] = set()
    for caveat in learner_caveats:
        if caveat and caveat not in seen:
            combined.append(caveat)
            seen.add(caveat)
    for note in simulator_notes:
        caveat = f"Simulator caveat: {note}"
        if note and caveat not in seen:
            combined.append(caveat)
            seen.add(caveat)
    return combined


def _score_breakdown(
    *,
    model_score: float,
    round_quality_mean: float | None,
    round_quality_weight: float,
    coverage_cap: float | None,
    validity_cap: float | None,
    final_score: float,
    repeated_prompt_count: int = 0,
    excluded_turn_count: int = 0,
) -> dict:
    return {
        "model_score": round(float(model_score), 4),
        "round_quality_mean": (
            round(float(round_quality_mean), 4)
            if round_quality_mean is not None
            else None
        ),
        "round_quality_weight": round(float(round_quality_weight), 4),
        "coverage_cap": (
            round(float(coverage_cap), 4)
            if coverage_cap is not None
            else None
        ),
        "validity_cap": (
            round(float(validity_cap), 4)
            if validity_cap is not None
            else None
        ),
        "repeated_prompt_count": int(repeated_prompt_count or 0),
        "excluded_turn_count": int(excluded_turn_count or 0),
        "final_score": round(float(final_score), 4),
    }


_FINAL_SCORE_AFFECTING_REPAIR_CODES = {
    "assessment_quality_score_repaired",
    "assessment_turn_call_failed",
    "interview_missing_evidence_repaired",
}
_SAFE_REPORT_INTEGRITY_NOTE_CODES = {
    "empty_gd_visible_response_repaired",
    "gd_panelist_ask_only_repaired",
    "gd_panelist_formulaic_meta_repaired",
    "hidden_speaker_reference",
    "inactive_requested_speaker",
    "interviewer_model_answer_leak",
    "low_confidence_persona_request",
    "requested_speaker_mismatch",
    "requested_speaker_question_echo",
    "repeated_speaker_repaired",
    "self_label_or_meta_response",
    "speaker_output_mismatch",
}


def _flag_affects_final_score(flag: dict) -> bool:
    code = str(flag.get("code") or "").strip()
    if code in _SAFE_REPORT_INTEGRITY_NOTE_CODES:
        return False
    if code in _FINAL_SCORE_AFFECTING_REPAIR_CODES:
        return True
    if str(flag.get("score_excluded_reason") or "").strip():
        return True
    if str(flag.get("severity") or "").lower() == "invalid":
        return True
    return False


def _has_invalid_simulation_flags(state: dict) -> bool:
    return any(
        isinstance(flag, dict)
        and str(flag.get("severity") or "").lower() == "invalid"
        and _flag_affects_final_score(flag)
        for flag in state.get("assessment_validity_flags") or []
    )


def _invalid_simulation_report(
    state: dict,
    task_type: TaskType,
    scorable_turn_count: int,
    coverage_map: dict,
) -> SimulationReport:
    simulator_notes = _simulator_integrity_notes(state, task_type) or [
        "The assessment transcript contained invalid simulator evidence."
    ]
    caveats = _combined_caveats([], simulator_notes)
    topic_flags = [
        str(flag.get("message") or flag.get("code"))
        for flag in state.get("assessment_validity_flags") or []
        if isinstance(flag, dict) and "topic" in str(flag.get("code") or "")
    ]
    persona_warnings = [
        str(flag.get("message") or flag.get("code"))
        for flag in state.get("assessment_validity_flags") or []
        if isinstance(flag, dict) and "speaker" in str(flag.get("code") or "")
    ]
    label = "interview" if task_type == TaskType.INTERVIEW_TEST else "group discussion"
    return SimulationReport(
        score=0.0,
        summary=(
            f"This {label} run had a simulator validity problem, so it should not "
            "be treated as a learner score. Please rerun the assessment."
        ),
        strengths=[],
        improvements=["Rerun the assessment so the report is based on a valid transcript."],
        observed_skill_gaps=[],
        recommended_next_nodes=["Retry the assessment"],
        assessment_caveats=caveats,
        learner_assessment_caveats=[],
        simulator_integrity_notes=simulator_notes,
        score_breakdown=_score_breakdown(
            model_score=0.0,
            round_quality_mean=None,
            round_quality_weight=_ROUND_QUALITY_WEIGHT,
            coverage_cap=None,
            validity_cap=0.0,
            final_score=0.0,
            repeated_prompt_count=_repeated_unanswered_prompt_count(state.get("messages") or []),
            excluded_turn_count=_assessment_event_counts(state)[1],
        ),
        validity_status="invalid_simulation",
        scorable_turn_count=scorable_turn_count,
        coverage_map=coverage_map,
        topic_drift_flags=topic_flags,
        persona_warnings=persona_warnings,
        **_context_fields(state),
    )


def _remove_repetition_blame(improvements: list[str]) -> list[str]:
    return [
        item
        for item in improvements
        if not any(term in item.lower() for term in _REPETITION_BLAME_TERMS)
    ]


def _sanitize_report_improvements(task_type: TaskType, improvements: list[str]) -> list[str]:
    cleaned = _remove_repetition_blame(improvements)
    if task_type != TaskType.INTERVIEW_TEST:
        return cleaned
    replacement = (
        "Tighten answer structure by linking the situation, your action, and the measured result."
    )
    sanitized: list[str] = []
    for item in cleaned:
        normalized = " ".join(str(item or "").lower().split())
        if any(term in normalized for term in _INTERVIEW_REPORT_LEAK_TERMS):
            sanitized.append(replacement)
        else:
            sanitized.append(item)
    return list(dict.fromkeys(sanitized))


_GENERIC_REPORT_SUMMARY_RE = re.compile(
    r"\b(?:great\s+job|great\s+session|strong\s+answer|strong\s+interview\s+close|"
    r"excellent\s+work|interview[-\s]?ready|discussion[-\s]?ready|"
    r"the\s+candidate\s+gave\s+strong\s+answers|you\s+are\s+ready|you're\s+ready|"
    r"ready\s+for\s+the\s+next|mastered|try\s+saying|use\s+this\s+answer|"
    r"copy\s+this\s+answer|sample\s+answer|a\s+better\s+version\s+would\s+be)\b",
    re.I,
)


def _neutral_report_summary(
    task_type: TaskType,
    *,
    scorable_turn_count: int,
    coverage_map: dict,
    evidence_quotes: list[str] | None = None,
) -> str:
    session_label = "interview" if task_type == TaskType.INTERVIEW_TEST else "group discussion"
    covered = int(coverage_map.get("unique_covered") or 0)
    needed = int(coverage_map.get("required_unique") or 0)
    coverage_phrase = (
        f"coverage breadth ({covered}/{needed})"
        if needed > 0
        else "coverage breadth"
    )
    evidence = [
        _evidence_excerpt(sanitize_memory_text(quote), limit=120)
        for quote in (evidence_quotes or [])
        if sanitize_memory_text(quote)
    ][:2]
    evidence_sentence = (
        " Evidence used: " + "; ".join(evidence) + "."
        if evidence
        else ""
    )
    return (
        f"This {session_label} report is based on {scorable_turn_count} answered turns. "
        f"The score reflects the learner's evidence, {coverage_phrase}, answer quality, "
        f"and any simulator-validity adjustments.{evidence_sentence}"
    )


def _sanitize_report_summary(
    task_type: TaskType,
    summary: str,
    *,
    scorable_turn_count: int,
    coverage_map: dict,
    evidence_quotes: list[str] | None = None,
) -> str:
    raw = " ".join(str(summary or "").split()).strip()
    if not raw:
        return _neutral_report_summary(
            task_type,
            scorable_turn_count=scorable_turn_count,
            coverage_map=coverage_map,
            evidence_quotes=evidence_quotes,
        )
    sanitized = sanitize_memory_text(raw)
    has_mode_leak = (
        task_type == TaskType.INTERVIEW_TEST
        and any(term in raw.lower() for term in _INTERVIEW_REPORT_LEAK_TERMS)
    )
    if sanitized != raw or _GENERIC_REPORT_SUMMARY_RE.search(raw) or has_mode_leak:
        return _neutral_report_summary(
            task_type,
            scorable_turn_count=scorable_turn_count,
            coverage_map=coverage_map,
            evidence_quotes=evidence_quotes,
        )
    return raw


def sanitize_report_for_delivery(state: dict, report: dict) -> dict:
    """Revalidate persisted report text before returning it to the learner."""
    if not isinstance(report, dict):
        return report
    try:
        task_type = TaskType(str(state.get("task_type") or ""))
    except ValueError:
        return dict(report)
    sanitized = dict(report)
    improvements = _sanitize_report_improvements(
        task_type,
        list(sanitized.get("improvements") or []),
    )
    recommendations = _sanitize_report_improvements(
        task_type,
        list(sanitized.get("recommended_next_nodes") or []),
    )
    observed = _sanitize_report_improvements(
        task_type,
        list(sanitized.get("observed_skill_gaps") or []),
    )
    coverage_map = sanitized.get("coverage_map") if isinstance(sanitized.get("coverage_map"), dict) else {}
    evidence_quotes = list(dict.fromkeys([
        *_grounded_evidence_quotes(state, list(sanitized.get("evidence_quotes") or [])),
        *_assessment_evidence_quotes(state),
    ]))[:8]
    sanitized.update({
        "improvements": improvements,
        "recommended_next_nodes": recommendations,
        "observed_skill_gaps": observed or improvements[:4],
        "evidence_quotes": evidence_quotes,
        "summary": _sanitize_report_summary(
            task_type,
            str(sanitized.get("summary") or ""),
            scorable_turn_count=int(sanitized.get("scorable_turn_count") or 0),
            coverage_map=coverage_map,
            evidence_quotes=evidence_quotes,
        ),
    })
    return sanitized


def _scorable_messages(messages: list[dict]) -> list[dict]:
    return [
        message
        for message in messages
        if message.get("message_kind") != "simulation_control"
    ]


def _answered_scorable_messages(messages: list[dict]) -> list[dict]:
    """Keep only exchanges the learner actually had a chance to answer.

    Closing a simulation while the latest interviewer/panel prompt is visible
    leaves that assistant prompt at the transcript tail. The scorer must not
    treat that unanswered prompt as covered ground, otherwise reports can credit
    skills the learner never attempted.
    """
    scorable = _scorable_messages(messages)
    while scorable and scorable[-1].get("role") != "user":
        scorable.pop()
    return scorable


def _scorable_user_turn_count(messages: list[dict]) -> int:
    return sum(
        1
        for message in messages
        if message.get("role") == "user"
        and message.get("message_kind") != "simulation_control"
    )


def _assessment_analysis_events(state: dict) -> list[dict]:
    return [
        event
        for event in state.get("assessment_events") or []
        if isinstance(event, dict) and event.get("event_type") == "analysis"
    ]


def _scorable_turn_count_from_events(state: dict) -> int | None:
    events = _assessment_analysis_events(state)
    if not events:
        return None
    return sum(1 for event in events if event.get("scorable") is True)


def _model_classified_control_event(event: dict) -> bool:
    analysis = event.get("analysis") if isinstance(event.get("analysis"), dict) else {}
    control_intent = str(analysis.get("control_intent") or "none").lower()
    answer_kind = str(analysis.get("answer_kind") or "").lower()
    return control_intent not in {"", "none"} or answer_kind == "clarification_request"


def _score_excluded_answer_event(event: dict) -> bool:
    analysis = event.get("analysis") if isinstance(event.get("analysis"), dict) else {}
    reason = str(analysis.get("score_excluded_reason") or "")
    return (
        event.get("scorable") is False
        and reason in {"simulator_integrity_repair", "assessment_turn_call_failed"}
    )


def _assessment_event_counts(state: dict) -> tuple[int, int, int]:
    scorable = 0
    excluded = 0
    controls = 0
    for event in _assessment_analysis_events(state):
        if event.get("scorable") is True:
            scorable += 1
        elif _score_excluded_answer_event(event):
            excluded += 1
        else:
            controls += 1
    return scorable, excluded, controls


def _effective_scorable_turn_count(state: dict, messages: list[dict]) -> int:
    events = _assessment_analysis_events(state)
    if events:
        return sum(1 for event in events if event.get("scorable") is True)
    return _scorable_user_turn_count(messages)


def _typed_scorable_messages(messages: list[dict], events: list[dict]) -> list[dict]:
    """Project a transcript through its typed turn ledger.

    Once a typed ledger exists it is authoritative. Unmatched transcript rows are
    intentionally excluded instead of being guessed back into learner evidence.
    """
    if not events:
        return _answered_scorable_messages(messages)
    user_indices = [
        index for index, message in enumerate(messages)
        if message.get("role") == "user"
    ]
    event_by_user_index: dict[int, dict] = {}
    used_user_indices: set[int] = set()
    unbound_events: list[dict] = []
    for event in events:
        learner_turn_id = str(event.get("learner_turn_id") or "").strip()
        if not learner_turn_id:
            unbound_events.append(event)
            continue
        matched_index = next((
            index
            for index in user_indices
            if index not in used_user_indices
            and learner_turn_id == str(
                messages[index].get("turn_id")
                or messages[index].get("client_turn_id")
                or messages[index].get("message_id")
                or ""
            ).strip()
        ), None)
        if matched_index is not None:
            event_by_user_index[matched_index] = event
            used_user_indices.add(matched_index)
    available_tail = [index for index in user_indices if index not in used_user_indices]
    if unbound_events:
        available_tail = available_tail[-len(unbound_events):]
        for index, event in zip(available_tail, unbound_events):
            event_by_user_index[index] = event

    projected: list[dict] = []
    pending: list[dict] = []
    for message_index, message in enumerate(messages):
        if message.get("role") != "user":
            pending.append(message)
            continue
        event = event_by_user_index.get(message_index)
        if event is None:
            pending = []
            continue
        if event.get("scorable") is True:
            projected.extend(pending)
            projected.append(message)
        pending = []
    return projected


def _evidence_excerpt(value: str, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    trimmed = text[: max(0, limit - 3)].rstrip()
    if " " in trimmed:
        trimmed = trimmed.rsplit(" ", 1)[0].rstrip()
    return f"{trimmed.rstrip(' .')}..."


def _grounded_evidence_quotes(state: dict, candidates: list[str]) -> list[str]:
    typed_events = _assessment_analysis_events(state)
    evidence_messages = _typed_scorable_messages(
        state.get("messages") or [],
        typed_events,
    )
    learner_messages = [
        " ".join(str(message.get("content") or "").split())
        for message in evidence_messages
        if message.get("role") == "user"
        and message.get("message_kind") != "simulation_control"
        and str(message.get("content") or "").strip()
    ]
    normalized_learner_messages = [message.lower() for message in learner_messages]
    grounded: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        text = " ".join(str(candidate or "").split())
        if not text:
            continue
        match_text = text[:-3].rstrip() if text.endswith("...") else text
        normalized = match_text.lower()
        matched_source = ""
        for learner_text, normalized_learner in zip(learner_messages, normalized_learner_messages):
            match_index = normalized_learner.find(normalized)
            if match_index >= 0:
                matched_source = learner_text[match_index:]
                break
        if len(normalized) < 12 or not matched_source:
            continue
        display = _evidence_excerpt(matched_source)
        key = display.lower()
        if key in seen:
            continue
        seen.add(key)
        grounded.append(display)
    return grounded[:8]


def _assessment_evidence_quotes(state: dict) -> list[str]:
    candidates: list[str] = []
    for event in _coverage_events_from_state(state):
        text = str(event.get("learner_answer_excerpt") or "").strip()
        if text:
            candidates.append(text)

    for event in _assessment_analysis_events(state):
        if event.get("scorable") is not True:
            continue
        analysis = event.get("analysis") or {}
        if not isinstance(analysis, dict):
            continue
        for point in analysis.get("evidence_points") or []:
            text = str(point or "").strip()
            if text:
                candidates.append(text)
    return _grounded_evidence_quotes(state, candidates)


def _coverage_key(event: dict) -> str:
    for key in ("skill_id", "topic_angle", "prompt_id", "speaker_id"):
        value = str(event.get(key) or "").strip()
        if value:
            return value
    return ""


def _next_gd_focus_id(state: dict) -> str:
    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    focus_ids = [
        str(item.get("focus_id") or "").strip()
        for item in plan.get("focus_plan") or []
        if isinstance(item, dict) and str(item.get("focus_id") or "").strip()
    ]
    if not focus_ids:
        return ""
    covered = {
        str(event.get("focus_id") or "").strip()
        for event in state.get("coverage_events") or []
        if isinstance(event, dict)
        and event.get("answered") is True
        and str(event.get("focus_id") or "").strip()
    }
    pending = state.get("pending_coverage_event")
    if isinstance(pending, dict) and str(pending.get("focus_id") or "").strip():
        covered.add(str(pending["focus_id"]).strip())
    return next((focus_id for focus_id in focus_ids if focus_id not in covered), focus_ids[0])


def _coverage_events_from_state(state: dict) -> list[dict]:
    events: list[dict] = []
    for item in state.get("coverage_events") or []:
        if not isinstance(item, dict):
            continue
        if item.get("answered") is False:
            continue
        events.append(item)
    return events


def _coverage_events_from_analysis_events(state: dict) -> list[dict]:
    events: list[dict] = []
    for index, item in enumerate(_assessment_analysis_events(state)):
        if item.get("scorable") is not True:
            continue
        analysis = item.get("analysis") if isinstance(item.get("analysis"), dict) else {}
        skill_id = str(
            analysis.get("skill_id")
            or analysis.get("topic_angle")
            or analysis.get("active_probe_id")
            or analysis.get("routing_case")
            or ""
        ).strip()
        prompt_id = str(analysis.get("active_probe_id") or skill_id or f"analysis_{index}").strip()
        events.append({
            "skill_id": skill_id,
            "prompt_id": prompt_id,
            "focus_id": str(analysis.get("focus_id") or "").strip(),
            "speaker_id": item.get("speaker_id"),
            "answered": True,
            "source": "assessment_events",
        })
    return events


def _derive_coverage_from_messages(messages: list[dict]) -> list[dict]:
    """Best-effort coverage fallback for older sessions with no typed events."""
    events: list[dict] = []
    pending_prompt = ""
    prompt_index = 0
    for message in messages:
        if message.get("role") == "assistant":
            pending_prompt = str(message.get("content") or "").strip()
            continue
        if message.get("role") != "user":
            continue
        prompt_index += 1
        prompt_tokens = _tokens_for_repetition(pending_prompt)
        prompt_key = "-".join(sorted(prompt_tokens)[:6]) or f"prompt-{prompt_index}"
        events.append({
            "skill_id": prompt_key,
            "prompt_id": prompt_key,
            "answered": True,
            "source": "derived_from_transcript",
        })
    return events


def _coverage_summary(state: dict, task_type: TaskType, answered_messages: list[dict]) -> dict:
    plan = state.get("assessment_plan") if isinstance(state.get("assessment_plan"), dict) else {}
    required_unique = int(plan.get("required_unique_coverage") or _MIN_UNIQUE_COVERAGE.get(task_type, 1))
    analysis_events = _assessment_analysis_events(state)
    coverage_events = _coverage_events_from_state(state)
    analysis_coverage_events = _coverage_events_from_analysis_events(state)
    if analysis_events:
        scorable_event_count = sum(1 for event in analysis_events if event.get("scorable") is True)
        events = coverage_events[:scorable_event_count] if coverage_events else analysis_coverage_events
        answered_turn_count = scorable_event_count
    else:
        events = coverage_events
        answered_turn_count = _scorable_user_turn_count(answered_messages)
    planned_session = isinstance(plan, dict) and bool(plan)
    transcript_fallback_limit = answered_turn_count
    allow_transcript_fallback = not analysis_events and not planned_session
    if (not events or len(events) < answered_turn_count) and (
        allow_transcript_fallback and transcript_fallback_limit > 0
    ):
        derived_events = _derive_coverage_from_messages(answered_messages)
        if not coverage_events and not analysis_coverage_events:
            events = derived_events[:transcript_fallback_limit]
        elif len(events) < answered_turn_count:
            events = [*events, *derived_events[len(events):answered_turn_count]]
    keys = [key for event in events if (key := _coverage_key(event))]
    unique_keys = sorted(set(keys))
    focus_covered_ids = sorted({
        str(event.get("focus_id") or "").strip()
        for event in events
        if str(event.get("focus_id") or "").strip()
    })
    focus_required_ids = [
        str(item.get("focus_id") or "").strip()
        for item in plan.get("focus_plan") or []
        if isinstance(item, dict) and str(item.get("focus_id") or "").strip()
    ]
    repeated_prompts = _repeated_unanswered_prompt_count(state.get("messages") or [])
    used_transcript_fallback = any(
        isinstance(event, dict) and event.get("source") == "derived_from_transcript"
        for event in events
    )
    source = (
        "typed_events_with_transcript_fallback"
        if used_transcript_fallback and (planned_session or coverage_events or analysis_coverage_events)
        else "typed_events"
        if planned_session or coverage_events or analysis_coverage_events
        else "derived_from_transcript"
    )
    return {
        "required_unique": required_unique,
        "unique_covered": len(unique_keys),
        "covered_ids": unique_keys[:12],
        "focus_covered_ids": focus_covered_ids[:8],
        "focus_required_ids": focus_required_ids[:8],
        "event_count": len(events),
        "repeated_prompt_count": repeated_prompts,
        "source": source,
    }


def _latest_user_excerpt(state: dict, limit: int = 260) -> str:
    text = _last_user_message(state.get("messages") or [])
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "..."
    return text


def _event_prompt_id(text: str, fallback: str = "prompt") -> str:
    clean = " ".join((text or fallback).split())
    return f"prompt_{zlib.crc32(clean.encode('utf-8')):08x}"


def _append_coverage_event(state: dict, event: dict) -> None:
    events = list(state.get("coverage_events") or [])
    events.append(event)
    state["coverage_events"] = events[-40:]


def _settle_pending_coverage_event(
    state: dict,
    decision: DirectorDecision,
    *,
    control_turn: bool,
    skip_reason: str = "simulation_control",
    skipped_by_user: bool = True,
) -> None:
    pending = state.get("pending_coverage_event")
    if not isinstance(pending, dict):
        return
    event = dict(pending)
    event["settled_turn"] = int((state.get("blackboard") or {}).get("turn") or 0)
    if control_turn:
        event["answered"] = False
        event["skipped_by_user"] = bool(skipped_by_user)
        event["skip_reason"] = skip_reason
        event["score_evidence"] = None
    else:
        event["answered"] = True
        event["skipped_by_user"] = False
        event["skip_reason"] = None
        event["score_evidence"] = round(max(0.0, min(1.0, float(decision.answer_quality or 0.0))), 4)
        event["learner_answer_excerpt"] = _latest_user_excerpt(state)
    _append_coverage_event(state, event)
    state["pending_coverage_event"] = None


def _settle_pending_coverage_event_after_assessment_failure(
    state: dict,
    *,
    score_evidence: float | None,
) -> None:
    pending = state.get("pending_coverage_event")
    if not isinstance(pending, dict):
        return
    event = dict(pending)
    event["settled_turn"] = int((state.get("blackboard") or {}).get("turn") or 0)
    event["skipped_by_user"] = False
    event["learner_answer_excerpt"] = _latest_user_excerpt(state)
    event["integrity_note"] = "assessment_turn_call_failed"
    event["source"] = "deterministic_fallback"
    if score_evidence is None:
        event["answered"] = False
        event["skip_reason"] = "assessment_turn_call_failed"
        event["score_evidence"] = None
    else:
        event["answered"] = True
        event["skip_reason"] = None
        event["score_evidence"] = round(max(0.0, min(1.0, float(score_evidence))), 4)
    _append_coverage_event(state, event)
    state["pending_coverage_event"] = None


def _stage_prompt_coverage_event(
    state: dict,
    task_type: TaskType,
    persona: dict,
    decision: DirectorDecision,
    prompt_text: str,
    *,
    primary: bool = True,
    blackboard: dict | None = None,
) -> None:
    if not prompt_text.strip():
        return
    bb = blackboard or state.get("blackboard") or {}
    if task_type == TaskType.INTERVIEW_TEST:
        prompt_id = str(state.get("active_interview_probe_prompt_id") or _event_prompt_id(prompt_text))
        skill_id = str(state.get("active_interview_probe_skill_id") or prompt_id)
        topic_angle = decision.action
    elif task_type == TaskType.GD_TEST:
        prompt_id = _event_prompt_id(f"{decision.action}:{persona.get('speaker_id')}:{prompt_text}")
        skill_id = f"gd_{decision.action}_{persona.get('speaker_id') or 'speaker'}"
        topic_angle = str(decision.action or bb.get("phase") or "discussion")
    else:
        return
    state["pending_coverage_event"] = {
        "event_id": f"{int(bb.get('turn') or 0)}:{prompt_id}",
        "task_type": task_type.value,
        "skill_id": skill_id,
        "prompt_id": prompt_id,
        "topic_angle": topic_angle,
        "focus_id": _next_gd_focus_id(state) if task_type == TaskType.GD_TEST else "",
        "speaker_id": persona.get("speaker_id"),
        "speaker_name": persona.get("name"),
        "phase": bb.get("phase"),
        "turn": int(bb.get("turn") or 0),
        "prompt_text": prompt_text[:600],
        "answered": False,
        "primary": primary,
        "source": "runtime",
    }


def _context_fields(state: dict) -> dict:
    scenario = state.get("scenario_config") or {}
    career = state.get("career_context") or {}
    scenario_label = (
        scenario.get("topic")
        or scenario.get("resolved_topic")
        or scenario.get("target_role")
        or state.get("sim_topic", "")
    )
    return {
        "scenario_label": str(scenario_label or ""),
        "role_focus": str(scenario.get("target_role") or career.get("primary_role") or ""),
        "topic": str(scenario.get("topic") or scenario.get("resolved_topic") or state.get("sim_topic", "")),
    }


def _insufficient_evidence_report(
    state: dict,
    task_type: TaskType,
    scorable_turn_count: int,
    coverage_map: dict,
) -> SimulationReport:
    min_turns = _MIN_FINAL_SCORABLE_TURNS.get(task_type, 1)
    label = "interview" if task_type == TaskType.INTERVIEW_TEST else "group discussion"
    caveat = (
        f"Assessment caveat: not enough answered turns for a final {label} score "
        f"({scorable_turn_count}/{min_turns}). Complete more rounds before treating "
        "this as a reliable assessment."
    )
    return SimulationReport(
        score=0.0,
        summary=(
            f"This {label} session ended before there was enough scorable evidence "
            "to produce a reliable final assessment."
        ),
        strengths=[],
        improvements=["Complete more rounds so the assessment can cover enough competencies."],
        observed_skill_gaps=["insufficient_assessment_evidence"],
        recommended_next_nodes=["Complete a full simulation attempt."],
        assessment_caveats=[caveat],
        learner_assessment_caveats=[caveat],
        simulator_integrity_notes=_simulator_integrity_notes(state, task_type),
        score_breakdown=_score_breakdown(
            model_score=0.0,
            round_quality_mean=None,
            round_quality_weight=_ROUND_QUALITY_WEIGHT,
            coverage_cap=None,
            validity_cap=None,
            final_score=0.0,
            repeated_prompt_count=_repeated_unanswered_prompt_count(state.get("messages") or []),
            excluded_turn_count=_assessment_event_counts(state)[1],
        ),
        validity_status="insufficient_evidence",
        scorable_turn_count=scorable_turn_count,
        coverage_map=coverage_map,
        **_context_fields(state),
    )


def _has_unanswered_final_prompt(messages: list[dict]) -> bool:
    scorable = _scorable_messages(messages)
    return bool(scorable and scorable[-1].get("role") == "assistant")


def _completed_max_rounds(state: dict) -> bool:
    bb = state.get("blackboard") or {}
    try:
        return int(bb.get("turn") or 0) >= MAX_SIM_ROUNDS
    except (TypeError, ValueError):
        return False


def _unanswered_prompt_caveat(task_type: TaskType, state: dict) -> list[str]:
    if task_type not in {TaskType.INTERVIEW_TEST, TaskType.GD_TEST}:
        return []
    if _completed_max_rounds(state):
        return []
    if not _has_unanswered_final_prompt(state.get("messages") or []):
        return []
    return [
        "Assessment caveat: the session ended before the latest interviewer or panel prompt was answered, so the score reflects only completed learner turns."
    ]


_INSUFFICIENT_TURN_CAVEAT_TERMS = (
    "insufficient answered turn",
    "not enough answered turn",
    "not enough scorable",
    "complete more answered round",
    "complete more round",
)
_INSUFFICIENT_COVERAGE_CAVEAT_TERMS = (
    "not cover enough",
    "coverage was too narrow",
    "narrow competency coverage",
    "cover enough competencies",
)


def _filter_contradicted_learner_caveats(
    caveats: list[str],
    *,
    scorable_turn_count: int,
    min_turns: int,
    coverage_map: dict,
) -> list[str]:
    """Drop model-written learner caveats that backend counters disprove."""
    enough_turns = scorable_turn_count >= min_turns
    enough_coverage = int(coverage_map.get("unique_covered") or 0) >= int(
        coverage_map.get("required_unique") or 0
    )
    filtered: list[str] = []
    for caveat in caveats:
        normalized = " ".join(str(caveat or "").lower().split())
        if enough_turns and any(term in normalized for term in _INSUFFICIENT_TURN_CAVEAT_TERMS):
            continue
        if enough_coverage and any(term in normalized for term in _INSUFFICIENT_COVERAGE_CAVEAT_TERMS):
            continue
        filtered.append(caveat)
    return list(dict.fromkeys(filtered))


def assessment_progress_snapshot(state: dict) -> dict:
    """Backend-owned evidence counters for live assessment UI."""
    try:
        task_type = TaskType(state["task_type"])
    except Exception:
        return {}
    if task_type not in {TaskType.INTERVIEW_TEST, TaskType.GD_TEST}:
        return {}
    answered_messages = _answered_scorable_messages(state.get("messages", []))
    scorable_turn_count = _effective_scorable_turn_count(state, answered_messages)
    _event_scorable, excluded_turn_count, control_turn_count = _assessment_event_counts(state)
    if not _assessment_analysis_events(state):
        control_turn_count += sum(
            1
            for message in state.get("messages") or []
            if message.get("role") == "user"
            and message.get("message_kind") == "simulation_control"
        )
    return {
        "scorable_turn_count": scorable_turn_count,
        "min_scorable_turns": _MIN_FINAL_SCORABLE_TURNS.get(task_type, 1),
        "control_turn_count": control_turn_count,
        "excluded_turn_count": excluded_turn_count,
        "round_count": int(
            state.get("simulation_round")
            or (state.get("blackboard") or {}).get("turn")
            or 0
        ),
        "coverage_map": _coverage_summary(state, task_type, answered_messages),
    }


def _explain_score_adjustments(
    report: SimulationReport,
    task_type: TaskType,
    *,
    coverage_map: dict,
    qualities: list[float],
) -> SimulationReport:
    explanations = dict(getattr(report, "score_explanations", {}) or {})
    caveats = list(report.assessment_caveats)
    if task_type == TaskType.INTERVIEW_TEST:
        visible_dims = [
            value
            for value in (float(report.clarity_score or 0.0), float(report.confidence_score or 0.0))
            if value > 0
        ]
        if visible_dims:
            visible_avg = sum(visible_dims) / len(visible_dims)
            explanations.setdefault(
                "Overall",
                "Overall also reflects answer depth, evidence specificity, role relevance, coverage breadth, and backend validity adjustments.",
            )
            if abs(visible_avg - float(report.score)) >= 0.18:
                caveat = (
                    "Overall score differs from the visible rubric bars because hidden assessment factors "
                    "such as evidence depth, competency coverage, repeated prompts, and per-round answer quality adjusted the final score."
                )
                if caveat not in caveats:
                    caveats.append(caveat)
        if qualities:
            explanations.setdefault(
                "Round evidence",
                "Per-round answer quality is blended into the final score so a short scoring transcript tail cannot override the full session.",
            )
        if coverage_map.get("unique_covered", 0) < coverage_map.get("required_unique", 0):
            explanations.setdefault(
                "Coverage",
                "Coverage penalties apply when the session does not cover enough distinct interview competencies.",
            )
    elif task_type == TaskType.GD_TEST:
        explanations.setdefault(
            "Overall",
            "Overall reflects contribution quality, relevance, language, coverage breadth, and simulator-validity adjustments.",
        )
    return report.model_copy(update={
        "score_explanations": explanations,
        "assessment_caveats": caveats,
    })


async def score_session(state: dict) -> SimulationReport:
    """Score a finished TEST simulation over its whole transcript.

    Called at session end (never mid-stream): delegates to the AI boundary's
    evaluate_simulation with the task's strict behavior pack, then GROUNDS that
    single end-of-session pass in the Director's per-round reads of the learner.

    The holistic pass sees only a truncated TAIL of the transcript and is a single
    high-variance sample; the blackboard's `qualities` series carries one
    answer_quality per round across the WHOLE session. We blend LLM-primary
    (weight 1 - _ROUND_QUALITY_WEIGHT) so the rubric-aware score still leads and the
    round mean only corrects truncation/variance — and only when rounds actually
    ran. A fallback-only session (no director rounds) keeps the LLM score alone.
    Only the top-line `score` is blended; the rubric sub-scores stay as scored."""
    task_type = TaskType(state["task_type"])
    all_messages = state.get("messages", [])
    answered_messages = _answered_scorable_messages(all_messages)
    analysis_events = _assessment_analysis_events(state)
    scoring_messages = _typed_scorable_messages(all_messages, analysis_events)
    scorable_turn_count = _effective_scorable_turn_count(state, answered_messages)
    _event_scorable, excluded_turn_count, _control_turn_count = _assessment_event_counts(state)
    coverage_map = _coverage_summary(state, task_type, scoring_messages)
    min_turns = _MIN_FINAL_SCORABLE_TURNS.get(task_type, 1)
    if _has_invalid_simulation_flags(state) or (excluded_turn_count > 0 and scorable_turn_count == 0):
        return _invalid_simulation_report(
            state,
            task_type,
            scorable_turn_count,
            coverage_map,
        )
    if scorable_turn_count < min_turns:
        return _insufficient_evidence_report(
            state,
            task_type,
            scorable_turn_count,
            coverage_map,
        )
    report = await evaluate_simulation(
        task_type,
        state.get("sim_topic", ""),
        scoring_messages,
        scenario_config=state.get("scenario_config") or {},
        career_context=state.get("career_context") or {},
    )
    model_score = float(report.score)
    sanitized_recommendations = (
        _sanitize_report_improvements(task_type, list(report.recommended_next_nodes or []))
        if report.recommended_next_nodes
        else []
    )
    report = report.model_copy(update={
        "improvements": _sanitize_report_improvements(task_type, list(report.improvements)),
        "recommended_next_nodes": sanitized_recommendations,
        "observed_skill_gaps": _sanitize_report_improvements(
            task_type,
            list(report.observed_skill_gaps or []),
        ),
    })
    report = report.model_copy(update={
        "scenario_label": report.scenario_label or _context_fields(state)["scenario_label"],
        "role_focus": report.role_focus or _context_fields(state)["role_focus"],
        "topic": report.topic or _context_fields(state)["topic"],
        "observed_skill_gaps": report.observed_skill_gaps or list(report.improvements[:4]),
        "scorable_turn_count": scorable_turn_count,
        "coverage_map": coverage_map,
        "evidence_quotes": list(dict.fromkeys([
            *_grounded_evidence_quotes(state, list(report.evidence_quotes or [])),
            *_assessment_evidence_quotes(state),
        ]))[:8],
        "validity_status": report.validity_status or "final",
    })
    learner_caveats = [
        *list(report.learner_assessment_caveats or []),
        *list(report.assessment_caveats or []),
        *_unanswered_prompt_caveat(task_type, state),
    ]
    learner_caveats = _filter_contradicted_learner_caveats(
        learner_caveats,
        scorable_turn_count=scorable_turn_count,
        min_turns=min_turns,
        coverage_map=coverage_map,
    )
    simulator_notes = [
        *list(report.simulator_integrity_notes or []),
        *_simulator_integrity_notes(state, task_type),
    ]
    has_partial_integrity_flags = excluded_turn_count > 0 or any(
        isinstance(flag, dict)
        and str(flag.get("severity") or "").lower() == "partial"
        and _flag_affects_final_score(flag)
        for flag in state.get("assessment_validity_flags") or []
    )
    coverage_cap = None
    validity_cap = None
    if coverage_map["unique_covered"] < coverage_map["required_unique"]:
        learner_caveats.append(
            "Assessment caveat: competency coverage was too narrow for a fully reliable final score."
        )
        coverage_cap = _NARROW_COVERAGE_SCORE_CAP
        report = report.model_copy(update={
            "validity_status": "partial",
            "score": min(float(report.score), _NARROW_COVERAGE_SCORE_CAP),
        })
    if has_partial_integrity_flags and report.validity_status == "final":
        validity_cap = _NARROW_COVERAGE_SCORE_CAP
        report = report.model_copy(update={"validity_status": "partial"})
    if learner_caveats or simulator_notes:
        report = report.model_copy(update={
            "assessment_caveats": _combined_caveats(learner_caveats, simulator_notes),
            "learner_assessment_caveats": list(dict.fromkeys(learner_caveats)),
            "simulator_integrity_notes": list(dict.fromkeys(simulator_notes)),
            "improvements": _sanitize_report_improvements(task_type, list(report.improvements)),
        })
    if not report.recommended_next_nodes:
        report = report.model_copy(update={
            "recommended_next_nodes": list(report.improvements[:3]),
        })
    qualities = _normalized_round_qualities(state)
    round_mean = None
    if qualities:
        round_mean = sum(qualities) / len(qualities)
        blended = round(
            (1 - _ROUND_QUALITY_WEIGHT) * report.score
            + _ROUND_QUALITY_WEIGHT * round_mean,
            4,
        )
        report = report.model_copy(update={"score": blended})
    if report.validity_status == "partial":
        report = report.model_copy(update={
            "score": min(float(report.score), _NARROW_COVERAGE_SCORE_CAP),
        })
    report = _explain_score_adjustments(
        report,
        task_type,
        coverage_map=coverage_map,
        qualities=qualities,
    )
    learner_caveats = list(report.learner_assessment_caveats or [])
    for caveat in report.assessment_caveats:
        if caveat.startswith("Simulator caveat:"):
            continue
        if caveat not in learner_caveats:
            learner_caveats.append(caveat)
    learner_caveats = _filter_contradicted_learner_caveats(
        learner_caveats,
        scorable_turn_count=scorable_turn_count,
        min_turns=min_turns,
        coverage_map=coverage_map,
    )
    simulator_notes = list(dict.fromkeys(report.simulator_integrity_notes or []))
    report = report.model_copy(update={
        "summary": _sanitize_report_summary(
            task_type,
            report.summary,
            scorable_turn_count=scorable_turn_count,
            coverage_map=coverage_map,
            evidence_quotes=list(report.evidence_quotes or []),
        ),
        "learner_assessment_caveats": learner_caveats,
        "simulator_integrity_notes": simulator_notes,
        "assessment_caveats": _combined_caveats(learner_caveats, simulator_notes),
        "score_breakdown": _score_breakdown(
            model_score=model_score,
            round_quality_mean=round_mean,
            round_quality_weight=_ROUND_QUALITY_WEIGHT,
            coverage_cap=coverage_cap,
            validity_cap=validity_cap,
            final_score=float(report.score),
            repeated_prompt_count=_repeated_unanswered_prompt_count(state.get("messages") or []),
            excluded_turn_count=excluded_turn_count,
        ),
    })
    return report
