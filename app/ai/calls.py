"""The AI execution boundary.

Every real model call goes through here. Graph nodes build a `GenSpec`
(which model, what prompt) but never call a provider directly — so tests
monkeypatch the three functions below and exercise the full loop offline.

Model routing (architecture-v3 §59 routing table):
  evaluate   -> Gemini Flash-Lite (structured JSON)
  teach      -> Groq 70B
  bridge     -> Gemini Flash
  strengthen -> Gemini Flash
  redirect   -> Gemini Flash   (fluent-but-off-task steer-back)
  ease       -> Gemini Flash   (graceful off-ramp after long fail run)
  challenge  -> Groq 70B
  summary    -> Groq 70B
"""
from collections.abc import AsyncIterator
from dataclasses import dataclass

from app.ai.clients import get_gemini_client, get_groq_client
from app.ai.local import ollama_complete, ollama_stream, ollama_structured
from app.ai.behaviors import BehaviorPack, behavior_for
from app.ai.prompts import (
    build_assessment_turn_prompt,
    build_director_prompt,
    build_eval_prompt,
    build_prep_eval_prompt,
    build_placement_prompt,
    build_selector_prompt,
    build_simulation_score_prompt,
    build_summary_prompt,
    build_teach_game_prompt,
)
from app.ai.schemas import (
    AssessmentTurnCall,
    CriterionEval,
    DiagnosisEval,
    DirectorDecision,
    FillBlankGame,
    PlacementEval,
    PrepRubricEval,
    SelectionDecision,
    SimulationReport,
)
from app.ai.structured import call_with_structured_output
from app.config import get_settings
from app.content.schema import Concept
from app.content.task_types import TaskType
from app.services.rubric_engine import (
    RubricResult,
    apply_caps,
    build_evaluation_packet,
    invalid_required_evidence_ids,
)
from app.services.school.open_answer_ai import evaluate_school_open_answer
from app.services.rubrics import get_rubric

GROQ_70B = "llama-3.3-70b-versatile"
GROQ_8B = "llama-3.1-8b-instant"
GEMINI_FLASH = "gemini-flash-latest"  # 2.0-flash free tier zeroed; 2.5-flash stream 503s (2026)


def _local() -> bool:
    """True when the local Ollama backend is active (dev/build)."""
    return get_settings().ai_backend == "local"


@dataclass(frozen=True)
class GenSpec:
    """A pending streamed generation the service will execute."""

    provider: str   # "groq" | "gemini"
    model: str
    prompt: str
    kind: str       # opening | teach | bridge | strengthen | redirect | ease | challenge


class PrepEvaluationRetryRequired(RuntimeError):
    def __init__(self, criterion_ids: list[str]):
        self.criterion_ids = list(dict.fromkeys(criterion_ids))
        super().__init__(
            "prep_evaluation_retry_required: " + ", ".join(self.criterion_ids)
        )


_DETERMINISTIC_PREP_REPAIR_NODES = frozenset({
    "int_07_clarify_before_answering",
    "int_08_quantify_impact",
    "int_09_diplomatic_pushback",
    "gd_01_stake_position",
    "gd_02_support_with_evidence",
    "gd_03_take_the_floor",
    "gd_04_build_on_others",
    "gd_05_disagree_respectfully",
})


from app.middleware.rate_limit import llm_semaphore


def _expected_criterion_ids(packet) -> list[str]:
    """The prompt contract requires exactly one row for every packet criterion."""
    return list(dict.fromkeys(str(criterion["id"]) for criterion in packet.criteria))


def _structurally_invalid_criterion_ids(packet, raw: PrepRubricEval) -> list[str]:
    counts: dict[str, int] = {}
    for row in raw.criteria:
        criterion_id = str(row.id)
        counts[criterion_id] = counts.get(criterion_id, 0) + 1
    structural = [
        criterion_id
        for criterion_id in _expected_criterion_ids(packet)
        if counts.get(criterion_id, 0) != 1
    ]
    return list(dict.fromkeys([
        *structural,
        *invalid_required_evidence_ids(packet, raw),
    ]))


def _rows_by_id(raw: PrepRubricEval) -> dict[str, list]:
    rows: dict[str, list] = {}
    for row in raw.criteria:
        rows.setdefault(str(row.id), []).append(row)
    return rows


def _allows_deterministic_prep_repair(packet) -> bool:
    if packet.node_id == "int_09_diplomatic_pushback":
        return packet.attempt_type in {"independent", "transfer", "pressure"}
    return packet.node_id in _DETERMINISTIC_PREP_REPAIR_NODES


def _ordered_valid_first_response(packet, raw: PrepRubricEval) -> PrepRubricEval:
    rows = _rows_by_id(raw)
    ordered = [rows[criterion_id][0] for criterion_id in _expected_criterion_ids(packet)]
    return raw.model_copy(update={"criteria": ordered})


def _merge_structural_repair(
    packet,
    first: PrepRubricEval,
    repair: PrepRubricEval,
    target_ids: list[str],
) -> PrepRubricEval:
    first_rows = _rows_by_id(first)
    repair_rows = _rows_by_id(repair)
    invalid_repair_targets = [
        criterion_id
        for criterion_id in target_ids
        if len(repair_rows.get(criterion_id, [])) != 1
    ]
    if invalid_repair_targets:
        raise PrepEvaluationRetryRequired(invalid_repair_targets)

    targets = set(target_ids)
    ordered = [
        repair_rows[criterion_id][0]
        if criterion_id in targets
        else first_rows[criterion_id][0]
        for criterion_id in _expected_criterion_ids(packet)
    ]
    repaired_met = {
        criterion_id
        for criterion_id in targets
        if repair_rows[criterion_id][0].met
    }
    required_missing = [
        criterion_id
        for criterion_id in (first.required_missing or [])
        if str(criterion_id) not in repaired_met
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {str(row.id) for row in ordered if row.met}
    pass_eligible = bool(
        not required_missing
        and required_ids.issubset(met_ids)
        and first.on_task
        and first.english
        and float(first.effective_score or first.raw_score) >= float(packet.pass_score)
    )
    return first.model_copy(update={
        "criteria": ordered,
        "required_missing": required_missing,
        "pass_eligible": pass_eligible,
        "mastery_eligible": bool(first.mastery_eligible and pass_eligible),
    })


def _merge_structural_fallback(
    packet,
    first: PrepRubricEval,
    target_ids: list[str],
) -> PrepRubricEval:
    """Preserve valid first-call rows and mark unresolved repair targets unmet."""
    first_rows = _rows_by_id(first)
    targets = set(target_ids)
    ordered = []
    for criterion_id in _expected_criterion_ids(packet):
        rows = first_rows.get(criterion_id, [])
        if criterion_id not in targets and len(rows) == 1:
            ordered.append(rows[0])
            continue
        ordered.append(CriterionEval(
            id=criterion_id,
            met=False,
            quality=0.0,
            evidence_quote="",
            reason="criterion missing from evaluator output",
        ))
    required_missing = list(dict.fromkeys([
        *(first.required_missing or []),
        *[
            criterion_id
            for criterion_id in target_ids
            if any(
                str(criterion.get("id") or "") == criterion_id
                and bool(criterion.get("required"))
                for criterion in packet.criteria
            )
        ],
    ]))
    return first.model_copy(update={
        "criteria": ordered,
        "required_missing": required_missing,
        "pass_eligible": False,
        "mastery_eligible": False,
    })


def _prep_repair_prompt(
    original_prompt: str,
    raw: PrepRubricEval,
    invalid_ids: list[str],
) -> str:
    return (
        f"{original_prompt}\n\n"
        "REPAIR ONLY: the previous structured response omitted, duplicated, or used an invalid evidence_quote for expected criterion IDs. "
        "Preserve every non-target field and criterion judgment exactly. Return one row for each invalid ID. "
        "For a met target, evidence_quote must be one short contiguous verbatim quote copied from the learner answer; "
        "if no exact quote proves it, mark that target not met. Return one complete PrepRubricEval JSON object. "
        "Do not improve scores or change non-target judgments.\n"
        f"Structurally invalid expected IDs: {', '.join(invalid_ids)}\n"
        f"Previous structured response: {raw.model_dump_json()}"
    )


async def _call_prep_structured(prompt: str) -> PrepRubricEval:
    if _local():
        return await ollama_structured(prompt, PrepRubricEval)
    client = get_gemini_client()
    return await call_with_structured_output(client, prompt, PrepRubricEval)


async def evaluate_answer(
    node: Concept,
    messages: list[dict],
    user_input: str,
    behavior: BehaviorPack | None = None,
    career_context: dict | None = None,
) -> DiagnosisEval:
    """Structured assessment of the latest learner answer.

    `behavior` carries the per-TaskType grading stance (strict for assessment
    sims, lenient for a young SCHOOL_ENGLISH learner, standard otherwise). It was
    previously never threaded here, so `_strictness_gate`/`_persona` in
    build_eval_prompt were dead code and a child's phonics and a mock interview
    were graded on the identical bar. None preserves the legacy standard rubric."""
    prompt = build_eval_prompt(
        node,
        messages,
        user_input,
        behavior=behavior,
        career_context=career_context,
    )
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, DiagnosisEval)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, DiagnosisEval)


async def evaluate_prep_answer(
    node: Concept,
    messages: list[dict],
    user_input: str,
    behavior: BehaviorPack | None = None,
    career_context: dict | None = None,
    state: dict | None = None,
) -> RubricResult:
    """Structured rubric assessment for interview/GD prep nodes."""
    packet_state = dict(state or {})
    packet_state.setdefault("messages", messages)
    packet_state.setdefault("career_context", career_context or {})
    rubric = get_rubric(node.id)
    packet = build_evaluation_packet(packet_state, node, user_input, rubric)
    prompt = build_prep_eval_prompt(packet.model_dump(), career_context=career_context)
    async with llm_semaphore:
        first = await _call_prep_structured(prompt)
        invalid_ids = _structurally_invalid_criterion_ids(packet, first)
        if invalid_ids:
            repair_prompt = _prep_repair_prompt(prompt, first, invalid_ids)
            try:
                repair = await _call_prep_structured(repair_prompt)
            except Exception as exc:
                if not _allows_deterministic_prep_repair(packet):
                    raise PrepEvaluationRetryRequired(invalid_ids) from exc
                raw = _merge_structural_fallback(packet, first, invalid_ids)
            else:
                try:
                    raw = _merge_structural_repair(packet, first, repair, invalid_ids)
                except PrepEvaluationRetryRequired:
                    if not _allows_deterministic_prep_repair(packet):
                        raise
                    raw = _merge_structural_fallback(packet, first, invalid_ids)
                else:
                    invalid_repair_ids = _structurally_invalid_criterion_ids(packet, raw)
                    if invalid_repair_ids:
                        if not _allows_deterministic_prep_repair(packet):
                            raise PrepEvaluationRetryRequired(invalid_repair_ids)
                        raw = _merge_structural_fallback(packet, raw, invalid_repair_ids)
        else:
            raw = _ordered_valid_first_response(packet, first)
    result = apply_caps(packet, raw)
    unresolved_ids = [
        str(blocker).split(":", 1)[1]
        for blocker in result.blockers
        if str(blocker).startswith(("evaluator_incomplete:", "invalid_proof:"))
    ]
    if unresolved_ids:
        raise PrepEvaluationRetryRequired(unresolved_ids)
    return result


async def evaluate_placement(module_title: str, writing_sample: str) -> PlacementEval:
    """Structured CEFR estimate from an onboarding writing sample."""
    prompt = build_placement_prompt(module_title, writing_sample)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, PlacementEval)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, PlacementEval)


async def evaluate_simulation(
    task_type: TaskType,
    topic: str,
    messages: list[dict],
    scenario_config: dict | None = None,
    career_context: dict | None = None,
) -> SimulationReport:
    """Structured end-of-session score for a TEST-mode simulation.

    Test sessions are scored, not coached mid-stream; this runs once at the end
    over the whole transcript with the task's (strict) behavior pack."""
    prompt = build_simulation_score_prompt(
        behavior_for(task_type),
        topic,
        messages,
        scenario_config=scenario_config,
        career_context=career_context,
        task_type=task_type,
    )
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, SimulationReport)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, SimulationReport)


async def direct_simulation(
    bb,
    personas,
    task_type,
    transcript,
    probe_items=None,
    scenario_config: dict | None = None,
    career_context: dict | None = None,
) -> DirectorDecision:
    """Director's structured decision for one writers'-room round (the deliberate
    'thinking' beat). Non-streamed: returns a DirectorDecision. This is the LLM
    boundary — the only place the director model is called.

    `probe_items` is the prep-weakness probe bank; it is rendered into the prompt
    so the director presses the learner's known weak spots (previously generated
    then never consumed)."""
    prompt = build_director_prompt(
        bb,
        personas,
        task_type,
        transcript,
        probe_items,
        scenario_config=scenario_config,
        career_context=career_context,
    )
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, DirectorDecision)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, DirectorDecision)


async def evaluate_assessment_turn(
    *,
    plan: dict,
    visible_ledger: list[dict],
    transcript: str,
    learner_turn: str,
    turn_context: dict | None = None,
) -> AssessmentTurnCall:
    """Single structured model call for one test-mode learner turn."""
    prompt = build_assessment_turn_prompt(
        plan=plan,
        visible_ledger=visible_ledger,
        transcript=transcript,
        learner_turn=learner_turn,
        turn_context=turn_context,
    )
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, AssessmentTurnCall)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, AssessmentTurnCall)


async def select_next_content(
    snapshot: dict, candidates: list[dict]
) -> SelectionDecision:
    """Spec B Stage 2: pick the next content node from >1 valid candidate.

    Single structured call — same boundary pattern as direct_simulation. Only
    invoked when the deterministic stage left more than one candidate; the
    single-candidate fast path synthesizes its decision without touching the
    model. The caller validates/backstops the returned decision."""
    prompt = build_selector_prompt(snapshot, candidates)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, SelectionDecision)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, SelectionDecision)


async def generate_game_item(
    node: Concept,
    diagnosis: dict,
    coach: dict | None = None,
    career_context: dict | None = None,
) -> FillBlankGame:
    """Gamified fill-blank for scaffold turns (scaffold >= 1).

    Structured call — same pattern as evaluate_answer. Returns FillBlankGame;
    teach_node stores it as pending_game in state (no pending/stream GenSpec)."""
    prompt = build_teach_game_prompt(node, diagnosis, coach, career_context=career_context)
    async with llm_semaphore:
        if _local():
            return await ollama_structured(prompt, FillBlankGame)
        client = get_gemini_client()
        return await call_with_structured_output(client, prompt, FillBlankGame)


async def stream_generation(spec: GenSpec) -> AsyncIterator[str]:
    """Stream a pedagogy generation token-by-token from the chosen provider."""
    async with llm_semaphore:
        if _local():
            async for chunk in ollama_stream(spec.prompt):
                yield chunk
            return
        if spec.provider == "groq":
            async for chunk in _stream_groq(spec.model, spec.prompt):
                yield chunk
        elif spec.provider == "gemini":
            async for chunk in _stream_gemini(spec.model, spec.prompt):
                yield chunk
        else:  # pragma: no cover - guard
            raise ValueError(f"unknown provider: {spec.provider}")


async def _stream_groq(model: str, prompt: str) -> AsyncIterator[str]:
    client = get_groq_client()
    stream = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


async def _stream_gemini(model: str, prompt: str) -> AsyncIterator[str]:
    client = get_gemini_client()
    stream = await client.aio.models.generate_content_stream(
        model=model, contents=prompt
    )
    async for chunk in stream:
        if chunk.text:
            yield chunk.text


async def summarize_session(node: Concept, messages: list[dict]) -> str:
    """Writes the <=200-token memory summary at session end."""
    prompt = build_summary_prompt(node, messages)
    async with llm_semaphore:
        if _local():
            return await ollama_complete(prompt)
        client = get_groq_client()
        resp = await client.chat.completions.create(
            model=GROQ_70B,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return resp.choices[0].message.content or ""
