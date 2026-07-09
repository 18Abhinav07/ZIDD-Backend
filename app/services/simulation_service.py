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
import zlib
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.calls import evaluate_simulation
from app.ai.schemas import DirectorDecision, SimulationReport
from app.content.task_types import TaskType
from app.services.simulation.blackboard import apply_decision, new_blackboard, note_turn
from app.services.simulation.director import _next_in_rotation, decide_round
from app.services.simulation.persona import stream_persona_turn
from app.services.simulation_config import DEFAULT_GD_PERSONAS, GD_PERSONA_LIBRARY


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
    "another topic",
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
    return [
        {"prompt": prompt.format(role=role), "aim": "answer with a specific example and clear ownership"}
        for prompt in _INTERVIEW_DEFAULT_PROBES
    ]


def _last_user_message(messages: list[dict]) -> str:
    for message in reversed(messages or []):
        if message.get("role") == "user":
            return str(message.get("content") or "")
    return ""


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
        if _token_similarity(candidate, tokens) >= _REPEAT_SIMILARITY_THRESHOLD:
            return True
    for previous in used[-8:]:
        prev_tokens = _tokens_for_repetition(previous)
        if _token_similarity(candidate, prev_tokens) >= _REPEAT_SIMILARITY_THRESHOLD:
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
        role_type = str(persona.get("role_type") or "").lower()
        speaker_id = str(persona.get("speaker_id") or "").lower()
        name = str(persona.get("name") or "").lower()
        if role_type == "moderator" or "moderator" in speaker_id or "moderator" in name:
            return persona
    return personas[0]


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
            r"can|could|please)\b",
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
        return DirectorDecision(
            action="pivot_topic",
            next_speaker=requested["speaker_id"],
            intent=(
                f"{name}, the learner explicitly asked to hear from you. "
                "Give your view directly, connect it to the current topic, and "
                "ask the learner one clear follow-up."
            ),
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
                "to pick one of those voices or answer the current topic directly, "
                "then ask one simple continuation question. Do not pretend the "
                "missing persona spoke."
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
                "one panelist to respond. Then ask one easy next question about "
                "the current topic. Do not demand case-study evidence yet."
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
                "repeated thread, shift the group to one new angle on the same topic, "
                "and ask the learner one clear next question. Do not demand the same "
                "case-study or evidence example again."
            ),
            tension=max(0.25, float(bb.get("tension", 0.3)) - 0.1),
            answer_quality=bb.get("last_quality", 0.5),
            should_close=False,
        )
    return None


def is_simulation_control_input(task_type_value: str, text: str) -> bool:
    """True when a TEST-mode learner turn is a runtime command, not an answer.

    These turns should steer the simulation and be excluded from scoring. The
    scoring layer already ignores messages marked ``simulation_control``; this
    helper keeps the classification consistent between persistence and routing.
    """
    lower = (text or "").lower()
    if not lower.strip():
        return False
    if task_type_value == TaskType.INTERVIEW_TEST.value:
        return _has_confusion_control_intent(lower) or any(
            term in lower for term in _MOVE_ON_TERMS
        )
    if task_type_value == TaskType.GD_TEST.value:
        return (
            _has_confusion_control_intent(lower)
            or any(term in lower for term in _MOVE_ON_TERMS)
            or _has_gd_persona_control_request(lower)
        )
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

    authored = [
        p for p in (state.get("probe_items") or [])
        if (p.get("prompt") or "").strip()
    ]
    probes = authored + _default_interview_probes(state)
    cursor = int(state.get("probe_cursor") or 0)
    used = list(state.get("used_probe_prompts") or [])
    recent = _recent_assistant_tokens(state.get("messages") or [])

    for offset in range(len(probes)):
        index = (cursor + offset) % len(probes)
        candidate = probes[index]
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
    return text


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


_GD_MODERATOR_REPEAT_FALLBACKS = (
    "Let's shift to a new angle on {topic}. Which stakeholder is most affected here, and what trade-off should the group weigh next?",
    "Let's move from proof to feasibility. What safeguard would make a position on {topic} stronger in practice?",
    "Let's pull this toward synthesis. What is the strongest argument on each side of {topic}, and where can the group agree?",
)

_GD_PANEL_REPEAT_FALLBACKS = (
    "I'll shift the angle. The key trade-off on {topic} is between speed and safeguards; which side should get priority, and why?",
    "Let me take this from a feasibility angle. What would have to be true for this idea to work responsibly in the real world?",
    "I'll move this toward conclusion. What is one point you would keep, one point you would qualify, and why?",
)

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
    if is_moderator:
        return (
            f"Let's keep the discussion grounded in {topic}. Ryuk, name one concrete "
            "risk or example, then invite one panelist to respond."
        )
    return (
        f"I'll stay with the actual motion: {topic}. Ryuk, your point needs one "
        "visible example or metric so the group can test whether it holds."
    )


def _record_visible_segment(
    state: dict,
    persona: dict,
    text: str,
    *,
    kind: str = "simulation_segment",
) -> None:
    _ensure_assessment_state(state)
    segment = {
        "event_id": f"seg_{len(state.get('visible_event_ledger') or []) + 1}",
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
    templates = _GD_MODERATOR_REPEAT_FALLBACKS if is_moderator else _GD_PANEL_REPEAT_FALLBACKS
    cursor = int(state.get("gd_repeat_fallback_cursor") or 0)
    for offset in range(len(templates)):
        candidate = templates[(cursor + offset) % len(templates)].format(topic=topic)
        if not _is_repeated_probe(candidate, recent, used):
            state["gd_repeat_fallback_cursor"] = cursor + offset + 1
            return candidate
    state["gd_repeat_fallback_cursor"] = cursor + 1
    return templates[cursor % len(templates)].format(topic=topic)


def _safe_gd_turn_text(state: dict, persona: dict, generated: str) -> str:
    """Validate GD panel text before it becomes visible to the learner."""
    _ensure_assessment_state(state)
    text = (generated or "").strip()
    if not text:
        return _EMPTY_TURN_FALLBACK
    personas = state.get("personas") or []
    current_speaker_id = str(persona.get("speaker_id") or "").strip()
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
        return _gd_integrity_fallback(state, persona)
    handoff_target = _detect_handoff_target(text, personas, current_speaker_id)
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
    if not produced:
        yield _EMPTY_TURN_FALLBACK


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
                "and ask the learner one clear follow-up. Do not claim any other "
                "speaker made a point unless it is visible in the transcript."
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
    "same prompt",
    "same question",
    "repeated prompt",
    "repeated question",
    "return to",
)
_TOKEN_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "can", "could", "did",
    "do", "for", "from", "how", "i", "in", "is", "it", "me", "of", "on",
    "or", "that", "the", "this", "to", "was", "what", "with", "would", "you",
    "your",
}


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


def _assessment_caveats(state: dict, task_type: TaskType) -> list[str]:
    caveats = []
    for flag in state.get("assessment_validity_flags") or []:
        if not isinstance(flag, dict):
            continue
        message = str(flag.get("message") or flag.get("code") or "").strip()
        if message:
            caveats.append(f"Simulator caveat: {message}")
    if task_type == TaskType.INTERVIEW_TEST:
        repeat_count = _repeated_assistant_prompt_count(state.get("messages") or [])
        if repeat_count >= _REPEAT_COUNT_THRESHOLD:
            caveats.append(
                "Assessment caveat: the interviewer repeated a prompt several times, so treat this score as provisional and rerun the assessment."
            )
    return caveats


def _has_invalid_simulation_flags(state: dict) -> bool:
    return any(
        isinstance(flag, dict) and str(flag.get("severity") or "").lower() == "invalid"
        for flag in state.get("assessment_validity_flags") or []
    )


def _invalid_simulation_report(
    state: dict,
    task_type: TaskType,
    scorable_turn_count: int,
    coverage_map: dict,
) -> SimulationReport:
    caveats = _assessment_caveats(state, task_type) or [
        "Simulator caveat: the assessment transcript contained invalid simulator evidence."
    ]
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
    return sum(1 for message in messages if message.get("role") == "user")


def _coverage_key(event: dict) -> str:
    for key in ("skill_id", "topic_angle", "prompt_id", "speaker_id"):
        value = str(event.get(key) or "").strip()
        if value:
            return value
    return ""


def _coverage_events_from_state(state: dict) -> list[dict]:
    events: list[dict] = []
    for item in state.get("coverage_events") or []:
        if not isinstance(item, dict):
            continue
        if item.get("answered") is False:
            continue
        events.append(item)
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
    required_unique = _MIN_UNIQUE_COVERAGE.get(task_type, 1)
    events = _coverage_events_from_state(state)
    if not events:
        events = _derive_coverage_from_messages(answered_messages)
    keys = [key for event in events if (key := _coverage_key(event))]
    unique_keys = sorted(set(keys))
    repeated_prompts = max(0, len(keys) - len(unique_keys))
    return {
        "required_unique": required_unique,
        "unique_covered": len(unique_keys),
        "covered_ids": unique_keys[:12],
        "event_count": len(events),
        "repeated_prompt_count": repeated_prompts,
        "source": "typed_events" if _coverage_events_from_state(state) else "derived_from_transcript",
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
) -> None:
    pending = state.get("pending_coverage_event")
    if not isinstance(pending, dict):
        return
    event = dict(pending)
    event["settled_turn"] = int((state.get("blackboard") or {}).get("turn") or 0)
    if control_turn:
        event["answered"] = False
        event["skipped_by_user"] = True
        event["skip_reason"] = "simulation_control"
        event["score_evidence"] = None
    else:
        event["answered"] = True
        event["skipped_by_user"] = False
        event["score_evidence"] = round(max(0.0, min(1.0, float(decision.answer_quality or 0.0))), 4)
        event["learner_answer_excerpt"] = _latest_user_excerpt(state)
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
        validity_status="insufficient_evidence",
        scorable_turn_count=scorable_turn_count,
        coverage_map=coverage_map,
        **_context_fields(state),
    )


def _has_unanswered_final_prompt(messages: list[dict]) -> bool:
    scorable = _scorable_messages(messages)
    return bool(scorable and scorable[-1].get("role") == "assistant")


def _unanswered_prompt_caveat(task_type: TaskType, messages: list[dict]) -> list[str]:
    if task_type not in {TaskType.INTERVIEW_TEST, TaskType.GD_TEST}:
        return []
    if not _has_unanswered_final_prompt(messages):
        return []
    return [
        "Assessment caveat: the session ended before the latest interviewer or panel prompt was answered, so the score reflects only completed learner turns."
    ]


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
    answered_messages = _answered_scorable_messages(state.get("messages", []))
    scorable_turn_count = _scorable_user_turn_count(answered_messages)
    coverage_map = _coverage_summary(state, task_type, answered_messages)
    min_turns = _MIN_FINAL_SCORABLE_TURNS.get(task_type, 1)
    if scorable_turn_count < min_turns:
        return _insufficient_evidence_report(
            state,
            task_type,
            scorable_turn_count,
            coverage_map,
        )
    if _has_invalid_simulation_flags(state):
        return _invalid_simulation_report(
            state,
            task_type,
            scorable_turn_count,
            coverage_map,
        )

    report = await evaluate_simulation(
        task_type,
        state.get("sim_topic", ""),
        answered_messages,
        scenario_config=state.get("scenario_config") or {},
        career_context=state.get("career_context") or {},
    )
    report = report.model_copy(update={
        "scenario_label": report.scenario_label or _context_fields(state)["scenario_label"],
        "role_focus": report.role_focus or _context_fields(state)["role_focus"],
        "topic": report.topic or _context_fields(state)["topic"],
        "observed_skill_gaps": report.observed_skill_gaps or list(report.improvements[:4]),
        "scorable_turn_count": scorable_turn_count,
        "coverage_map": coverage_map,
        "validity_status": report.validity_status or "final",
    })
    caveats = [
        *_unanswered_prompt_caveat(task_type, state.get("messages") or []),
        *_assessment_caveats(state, task_type),
    ]
    if coverage_map["unique_covered"] < coverage_map["required_unique"]:
        caveats.append(
            "Assessment caveat: competency coverage was too narrow for a fully reliable final score."
        )
        report = report.model_copy(update={
            "validity_status": "partial",
            "score": min(float(report.score), _NARROW_COVERAGE_SCORE_CAP),
        })
    if caveats:
        report = report.model_copy(update={
            "assessment_caveats": list(report.assessment_caveats) + caveats,
            "improvements": _remove_repetition_blame(list(report.improvements)),
        })
    if not report.recommended_next_nodes:
        report = report.model_copy(update={
            "recommended_next_nodes": list(report.improvements[:3]),
        })
    qualities = (state.get("blackboard") or {}).get("qualities", [])
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
    return report
