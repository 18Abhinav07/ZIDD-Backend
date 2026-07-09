"""Backend enforcement for career-prep rubric evaluations.

The LLM performs the semantic judgment. This layer makes that judgment
auditable: every required criterion needs proof, configured blockers cap the
score, and eligibility is derived from the enforced result rather than from a
single broad model score.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.content.schema import Concept
from app.services.rubrics import PrepRubric, get_rubric


@dataclass(frozen=True)
class EvaluationPacket:
    node_id: str
    node_title: str
    teach_focus: str
    active_topic: str
    attempt_type: str
    learner_answer: str
    pass_score: float
    mastery_score: float
    criteria: list[dict[str, Any]]
    recent_messages: list[dict[str, Any]]

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RubricResult:
    raw_score: float
    effective_score: float
    understanding: str
    criteria: list[CriterionEval]
    required_missing: list[str]
    blockers: list[str]
    strengths: list[str]
    errors: list[str]
    next_focus: str
    on_task: bool
    english: bool
    affect: str
    goodbye: bool
    pass_eligible: bool
    mastery_eligible: bool
    attempt_type: str

    @property
    def score(self) -> float:
        return self.raw_score

    @property
    def missing_required_criteria(self) -> list[str]:
        return self.required_missing

    def model_dump(self) -> dict[str, Any]:
        out = asdict(self)
        out["criteria"] = [row.model_dump() for row in self.criteria]
        return out


def _state_messages(state: dict) -> list[dict]:
    messages = state.get("messages") or []
    if not isinstance(messages, list):
        return []
    sanitized: list[dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        row: dict[str, str] = {
            "role": str(message.get("role") or ""),
            "content": content[:1200],
        }
        for key in ("message_kind", "speaker_name", "speaker_id", "node_id"):
            value = message.get(key)
            if value is not None:
                row[key] = str(value)
        sanitized.append(row)
    return sanitized


def _state_topic(state: dict) -> str:
    career_context = state.get("career_context") or {}
    scenario = state.get("scenario_config") or {}
    topics = career_context.get("gd_topics") or career_context.get("custom_gd_topics") or []
    if isinstance(topics, list) and topics:
        return str(topics[0])
    return str(
        career_context.get("gd_topic")
        or scenario.get("resolved_topic")
        or scenario.get("topic")
        or ""
    )


def _attempt_type(state: dict) -> str:
    active_prompt_attempt_type = str(state.get("active_prompt_attempt_type") or "")
    if active_prompt_attempt_type:
        return active_prompt_attempt_type
    if state.get("pending_answer_key"):
        return "scaffolded"
    if state.get("tester_level") or state.get("last_route") == "challenge":
        return "pressure"
    if state.get("last_route") in {"strengthen", "redirect"}:
        return "transfer"
    return "independent"


def build_evaluation_packet(
    state_or_node: dict | Concept,
    node_or_messages: Concept | list[dict],
    user_input: str,
    rubric: PrepRubric | None = None,
) -> EvaluationPacket:
    """Build the compact packet rendered into the structured eval prompt.

    Preferred call shape is ``build_evaluation_packet(state, node, answer)``.
    The older ``(node, messages, answer, rubric)`` shape is accepted so current
    callers can be migrated without breaking unrelated tests.
    """
    if isinstance(state_or_node, dict):
        state = state_or_node
        node = node_or_messages  # type: ignore[assignment]
        messages = _state_messages(state)
        active_topic = _state_topic(state)
        attempt_type = _attempt_type(state)
    else:
        state = {}
        node = state_or_node
        messages = node_or_messages if isinstance(node_or_messages, list) else []
        active_topic = ""
        attempt_type = "independent"
    if not isinstance(node, Concept):
        raise TypeError("build_evaluation_packet requires a Concept node")
    rubric = rubric or get_rubric(node.id)
    return EvaluationPacket(
        node_id=node.id,
        node_title=node.title,
        teach_focus=node.teach_focus,
        active_topic=active_topic,
        attempt_type=attempt_type,
        learner_answer=user_input,
        pass_score=rubric.pass_score,
        mastery_score=rubric.mastery_score,
        criteria=[
            {
                "id": c.id,
                "label": c.label,
                "required": c.required,
                "missing_cap": c.missing_cap,
                "proof_required": c.proof_required,
            }
            for c in rubric.criteria
        ],
        recent_messages=messages[-8:],
    )


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", (text or "").lower())).strip()


def _quote_appears(answer: str, quote: str) -> bool:
    quote = (quote or "").strip()
    if not quote:
        return False
    answer_norm = _normalize(answer)
    quote_norm = _normalize(quote)
    if not quote_norm:
        return False
    return quote_norm in answer_norm


def validate_llm_eval(raw: PrepRubricEval | RubricResult | dict, packet: EvaluationPacket) -> PrepRubricEval:
    """Normalize model output so every rubric criterion has one judgment row."""
    if isinstance(raw, RubricResult):
        raw = {
            "raw_score": raw.raw_score,
            "effective_score": raw.effective_score,
            "understanding": raw.understanding,
            "errors": raw.errors,
            "strengths": raw.strengths,
            "next_focus": raw.next_focus,
            "criteria": raw.criteria,
            "required_missing": raw.required_missing,
            "pass_eligible": raw.pass_eligible,
            "mastery_eligible": raw.mastery_eligible,
            "on_task": raw.on_task,
            "english": raw.english,
            "affect": raw.affect,
            "goodbye": raw.goodbye,
        }
    result = raw if isinstance(raw, PrepRubricEval) else PrepRubricEval.model_validate(raw)
    by_id = {row.id: row for row in result.criteria}
    criteria: list[CriterionEval] = []
    for criterion in packet.criteria:
        row = by_id.get(str(criterion["id"]))
        if row is None:
            row = CriterionEval(
                id=str(criterion["id"]),
                met=False,
                evidence_quote="",
                reason="criterion missing from evaluator output",
                quality=0.0,
            )
        criteria.append(row)
    return result.model_copy(update={"criteria": criteria})


def apply_caps(packet: EvaluationPacket, raw: PrepRubricEval | RubricResult | dict) -> RubricResult:
    """Apply configured caps and eligibility rules to a semantic LLM eval."""
    normalized = validate_llm_eval(raw, packet)
    effective = float(normalized.effective_score or normalized.raw_score)
    required_missing: list[str] = []
    blockers: list[str] = []
    errors = list(normalized.errors or [])

    raw_required_missing = {str(item) for item in (normalized.required_missing or [])}
    rows_by_id = {row.id: row for row in normalized.criteria}
    for criterion in packet.criteria:
        criterion_id = str(criterion["id"])
        row = rows_by_id.get(criterion_id)
        required = bool(criterion.get("required"))
        proof_required = bool(criterion.get("proof_required"))
        missing = criterion_id in raw_required_missing or row is None or not bool(row.met)
        invalid_proof = False
        if row is not None and required and proof_required and row.met:
            invalid_proof = not _quote_appears(packet.learner_answer, row.evidence_quote)

        if required and (missing or invalid_proof):
            if criterion_id not in required_missing:
                required_missing.append(criterion_id)
            cap = float(criterion.get("missing_cap") or packet.pass_score)
            effective = min(effective, cap)
            blocker = (
                f"invalid_proof:{criterion_id}"
                if invalid_proof and not missing
                else f"missing_required:{criterion_id}"
            )
            if blocker not in blockers:
                blockers.append(blocker)

    if required_missing:
        msg = "missing required rubric proof: " + ", ".join(required_missing)
        if msg not in errors:
            errors.append(msg)

    effective = round(max(0.0, min(1.0, effective)), 4)
    pass_eligible = (
        bool(normalized.pass_eligible)
        and not required_missing
        and bool(normalized.on_task)
        and bool(normalized.english)
        and effective >= packet.pass_score
    )
    mastery_eligible = (
        bool(normalized.mastery_eligible)
        and pass_eligible
        and effective >= packet.mastery_score
        and packet.attempt_type != "scaffolded"
    )
    return RubricResult(
        raw_score=float(normalized.raw_score),
        effective_score=effective,
        understanding=normalized.understanding,
        criteria=list(normalized.criteria),
        required_missing=required_missing,
        blockers=blockers,
        strengths=list(normalized.strengths or []),
        errors=errors,
        next_focus=normalized.next_focus,
        on_task=bool(normalized.on_task),
        english=bool(normalized.english),
        affect=normalized.affect,
        goodbye=bool(normalized.goodbye),
        pass_eligible=pass_eligible,
        mastery_eligible=mastery_eligible,
        attempt_type=packet.attempt_type,
    )


def _result_value(result: RubricResult | PrepRubricEval | dict, key: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        if key == "raw_score":
            return result.get("raw_score", result.get("score", default))
        if key == "required_missing":
            return result.get("required_missing", result.get("missing_required_criteria", default))
        return result.get(key, default)
    return getattr(result, key, default)


def compute_attempt_credit(
    previous: dict | None,
    result: RubricResult | PrepRubricEval | dict,
    *,
    scaffolded: bool = False,
    transfer: bool = False,
    pressure: bool = False,
    min_mastery_independent_passes: int = 3,
) -> dict:
    """Fold one rubric result into durable prep-progress counters.

    A scaffolded success can be useful, but it is not independent mastery. A
    mastered node requires repeated independent passes plus harder evidence
    contexts, so two borderline passes cannot mark mastery.
    """
    out = dict(previous or {})
    out.setdefault("node_mastered", False)
    out.setdefault("display_status", "in_progress")
    out.setdefault("best_independent_score", 0.0)
    out.setdefault("independent_passes", 0)
    out.setdefault("transfer_passes", 0)
    out.setdefault("pressure_passes", 0)
    out.setdefault("scaffold_successes", 0)
    out.setdefault("meaningful_attempts", 0)
    out.setdefault("last_gap", "")
    out.setdefault("mastery_evidence", [])
    out.setdefault("readiness_score", 0.0)

    pass_eligible = bool(_result_value(result, "pass_eligible", False))
    mastery_eligible = bool(_result_value(result, "mastery_eligible", False))
    effective_score = float(_result_value(result, "effective_score", _result_value(result, "score", 0.0)) or 0.0)
    next_focus = str(_result_value(result, "next_focus", "") or "")
    attempt_type = str(_result_value(result, "attempt_type", "") or "")
    scaffolded = scaffolded or attempt_type == "scaffolded"
    transfer = transfer or attempt_type == "transfer"
    pressure = pressure or attempt_type == "pressure"

    out["meaningful_attempts"] = int(out.get("meaningful_attempts") or 0) + 1
    if pass_eligible and scaffolded:
        out["scaffold_successes"] = int(out["scaffold_successes"]) + 1
    elif pass_eligible:
        out["independent_passes"] = int(out["independent_passes"]) + 1
        out["best_independent_score"] = max(
            float(out["best_independent_score"] or 0.0),
            effective_score,
        )
        if transfer:
            out["transfer_passes"] = int(out["transfer_passes"]) + 1
        if pressure:
            out["pressure_passes"] = int(out["pressure_passes"]) + 1

    if next_focus:
        out["last_gap"] = next_focus
    out["readiness_score"] = round(max(0.0, min(1.0, effective_score)), 4)

    independent_passes = int(out["independent_passes"])
    transfer_passes = int(out["transfer_passes"])
    pressure_passes = int(out["pressure_passes"])
    meaningful_attempts = int(out.get("meaningful_attempts") or 0)
    repeated = independent_passes >= min_mastery_independent_passes
    harder_evidence = transfer_passes >= 2 and pressure_passes >= 1
    strong = mastery_eligible and float(out["best_independent_score"] or 0.0) >= 0.85
    if meaningful_attempts >= 8 and repeated and strong and harder_evidence:
        out["node_mastered"] = True
        out["display_status"] = "mastered"
        evidence = list(out.get("mastery_evidence") or [])
        attempt_evidence = {
            "attempt_type": "pressure" if pressure else "transfer" if transfer else "scaffolded" if scaffolded else "independent",
            "score": effective_score,
            "criteria": [
                row.model_dump() if hasattr(row, "model_dump") else dict(row)
                for row in (_result_value(result, "criteria", []) or [])
            ],
        }
        if attempt_evidence not in evidence:
            evidence.append(attempt_evidence)
        out["mastery_evidence"] = evidence
    elif (
        pass_eligible
        and effective_score >= 0.8
        and meaningful_attempts >= 5
        and independent_passes >= 2
        and (transfer_passes + pressure_passes) >= 1
    ):
        out["display_status"] = "ready_to_advance"
    elif not out.get("node_mastered"):
        out["display_status"] = "in_progress"

    return out
