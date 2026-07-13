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


_PITCH_ROLE_TERMS = (
    "engineer",
    "developer",
    "manager",
    "sales",
    "recruiter",
    "recruiting",
    "hr",
    "human resources",
    "finance",
    "accountant",
    "consultant",
    "analyst",
    "data scientist",
    "designer",
    "student",
    "marketer",
    "marketing",
    "operator",
    "operations",
    "teacher",
    "educator",
    "nurse",
    "doctor",
    "clinician",
    "therapist",
    "writer",
    "researcher",
    "tester",
    "qa",
    "intern",
    "founder",
    "engineering",
)
_PITCH_PROOF_TERMS = (
    "built",
    "created",
    "improved",
    "reduced",
    "increased",
    "led",
    "owned",
    "traced",
    "added",
    "launched",
    "delivered",
    "resolved",
    "using",
    "focused on",
    "specialize in",
    "specialise in",
    "worked on",
    "work on",
    "experience with",
    "managed",
    "analyzed",
    "analysed",
    "coordinated",
    "negotiated",
    "closed",
    "sold",
    "recruited",
    "hired",
    "screened",
    "forecasted",
    "designed",
    "shipped",
    "debugged",
)
_PITCH_PROOF_DETAIL_TERMS = (
    "api",
    "apis",
    "fastapi",
    "django",
    "python",
    "typescript",
    "react",
    "database",
    "databases",
    "checkout",
    "payment",
    "payments",
    "service",
    "services",
    "incident",
    "incidents",
    "latency",
    "retries",
    "retry",
    "idempotency",
    "logging",
    "observability",
    "debugging",
    "migration",
    "release",
    "launch",
    "dashboard",
    "dashboards",
    "customer",
    "customers",
    "support",
    "tickets",
    "users",
    "revenue",
    "transaction",
    "transactions",
    "distributed system",
    "distributed systems",
    "production",
    "renewal",
    "renewals",
    "churn",
    "enterprise",
    "account",
    "accounts",
    "quota",
    "pipeline",
    "hiring",
    "candidate",
    "candidates",
    "onboarding",
    "payroll",
    "budget",
    "finance",
    "forecast",
    "forecasts",
    "campaign",
    "campaigns",
    "conversion",
    "conversions",
    "retention",
    "process",
    "processes",
    "inventory",
    "vendor",
    "vendors",
    "medication",
    "medicine",
    "patient",
    "patients",
    "ward",
    "handoff",
    "handoffs",
    "checklist",
    "checklists",
    "safety",
    "errors",
)
_PITCH_DIRECTION_TERMS = (
    "next goal",
    "next role",
    "next step",
    "next i want",
    "i want to",
    "i aim to",
    "i'm aiming",
    "i am aiming",
    "moving toward",
    "want to own",
    "grow into",
    "looking to",
)
_WEAKNESS_REAL_TERMS = (
    "weakness",
    "tended",
    "used to",
    "earlier",
    "previously",
    "struggle",
    "under pressure",
    "sometimes",
    "over-explain",
    "jumping straight",
    "technical implementation before business impact",
    "technical details before business impact",
)
_WEAKNESS_REAL_REQUIRED_TERMS = (
    "weakness",
    "struggle",
    "over-explain",
    "jumping straight",
    "tend to jump",
    "tend to explain",
    "jump straight into implementation",
    "jump straight into technical",
    "implementation before explaining business impact",
    "before explaining business impact",
    "before making business impact",
    "technical implementation before business impact",
    "technical details before business impact",
    "technical trade-off before",
    "technical trade-offs before",
    "technical tradeoff before",
    "technical tradeoffs before",
    "technical details before",
    "technical detail before",
)
_WEAKNESS_MITIGATION_TERMS = (
    "i now",
    "now i",
    "changed that",
    "corrected that",
    "manage it",
    "mitigate",
    "habit",
    "start with",
    "lead with",
    "decision criteria",
    "plain language",
    "compare options",
)
_WEAKNESS_PROGRESS_TERMS = (
    "recently",
    "in a ",
    "in the ",
    "that meant",
    "that helped",
    "instead of",
    "helped",
    "caught",
    "catching",
    "avoided",
    "avoiding",
    "reduced",
    "improved",
    "increased",
    "finished",
    "saved",
    "rollback",
    "support",
    "revenue",
    "product",
    "week",
    "meeting",
)
_WEAKNESS_PROGRESS_OUTCOME_TERMS = (
    "caught",
    "catching",
    "avoided",
    "avoiding",
    "reduced",
    "improved",
    "increased",
    "finished",
    "finish",
    "saved",
    "meant",
    "helped",
    "protected",
    "resolved",
    "prevented",
)
_WEAKNESS_PROGRESS_DETAIL_TERMS = (
    "payment",
    "rollout",
    "rollback",
    "retry",
    "revenue",
    "support",
    "product review",
    "product",
    "email thread",
    "email threads",
    "handoff",
    "customer",
    "client",
    "incident",
    "migration",
    "transaction",
    "latency",
    "defect",
    "bug",
    "mismatch",
    "metric",
    "metrics",
    "stakeholder",
)
_WEAKNESS_PROGRESS_CONTEXT_TERMS = (
    "recently",
    "that meant",
    "in a ",
    "in the ",
    "during ",
    "after ",
    "when ",
    "last ",
    "this week",
    "week one",
    "rollout",
    "incident",
    "migration",
    "launch",
    "review",
    "meeting",
    "email thread",
    "customer call",
    "support ticket",
    "escalation",
)


def _answer_has_any(answer: str, terms: tuple[str, ...]) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    return any(term in lowered for term in terms)


def _criterion_evidence(answer: str, terms: tuple[str, ...]) -> str:
    lowered = str(answer or "").lower()
    for term in terms:
        index = lowered.find(term)
        if index < 0:
            continue
        start = max(0, index - 40)
        end = min(len(answer), index + max(len(term), 1) + 90)
        return " ".join(answer[start:end].strip(" .,;:-").split())
    return ""


def _has_concrete_weakness_progress(answer: str) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    if not lowered:
        return False
    if any(
        phrase in lowered
        for phrase in (
            "not named a real case",
            "no real case",
            "no concrete",
            "don't have a concrete",
            "do not have a concrete",
            "no example",
            "not have an example",
            "haven't named",
            "have not named",
            "without a real case",
            "should be better outcomes",
            "would be better outcomes",
        )
    ):
        return False
    outcome_hits = sum(1 for term in _WEAKNESS_PROGRESS_OUTCOME_TERMS if term in lowered)
    strong_outcome_hits = sum(
        1
        for term in _WEAKNESS_PROGRESS_OUTCOME_TERMS
        if term not in {"helped", "improved", "meant"} and term in lowered
    )
    has_work_detail = _answer_has_any(lowered, _WEAKNESS_PROGRESS_DETAIL_TERMS)
    has_number = bool(re.search(r"\b\d+\b", lowered)) or _answer_has_any(
        lowered,
        (" one ", " two ", " three ", " four ", " five "),
    )
    has_before_after = _answer_has_any(
        lowered,
        ("instead of", "before they", "before it", "rather than"),
    )
    has_event_context = _answer_has_any(lowered, _WEAKNESS_PROGRESS_CONTEXT_TERMS)
    return (
        has_work_detail
        and has_event_context
        and outcome_hits >= 1
        and (strong_outcome_hits >= 1 or has_number or has_before_after)
    )


def _has_number_or_metric(text: str) -> bool:
    lowered = " ".join(str(text or "").lower().split())
    return bool(re.search(r"\b\d+(?:\.\d+)?%?\b", lowered)) or _answer_has_any(
        lowered,
        (
            " one ",
            " two ",
            " three ",
            " four ",
            " five ",
            "p95",
            "p99",
            "sla",
            "slas",
            "kpi",
            "kpis",
            "metric",
            "metrics",
        ),
    )


def _pitch_term_appears(answer: str, term: str) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    normalized_term = " ".join(str(term or "").lower().split())
    if not normalized_term:
        return False
    if " " in normalized_term:
        return normalized_term in lowered
    return bool(re.search(rf"\b{re.escape(normalized_term)}\b", lowered))


def _has_pitch_term(answer: str, terms: tuple[str, ...]) -> bool:
    return any(_pitch_term_appears(answer, term) for term in terms)


def _before_pitch_future_direction(answer: str) -> str:
    lowered = " ".join(str(answer or "").lower().split())
    markers = (
        "next goal",
        "next role",
        "next step",
        "i want to",
        "want to",
        "i aim to",
        "i'm aiming",
        "i am aiming",
        "moving toward",
        "want to own",
        "grow into",
        "grow as",
        "looking to",
        "become",
    )
    indexes = [lowered.find(marker) for marker in markers if lowered.find(marker) >= 0]
    if not indexes:
        return lowered
    return lowered[: min(indexes)].strip(" .,;:-")


def _has_pitch_identity(answer: str) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    identity_scope = _before_pitch_future_direction(answer)
    if not identity_scope:
        return False
    identity_patterns = (
        r"\b(?:i am|i'm)\s+(?:a|an)\s+(?P<role>[a-z][a-z0-9+#/ -]{1,80})",
        r"\b(?:i work as|i currently work as|my role is)\s+(?:a|an)?\s*(?P<role>[a-z][a-z0-9+#/ -]{1,80})",
        r"\b(?:currently a|currently an|as a|as an)\s+(?P<role>[a-z][a-z0-9+#/ -]{1,80})",
    )
    for pattern in identity_patterns:
        match = re.search(pattern, identity_scope)
        if match and _has_pitch_term(match.group("role"), _PITCH_ROLE_TERMS):
            return True
    if re.search(
        r"\b(?:is my next role|is the role i want|role i want|next role)\b",
        lowered[:180],
    ):
        return False
    opening = re.sub(r"[^a-z0-9+#/ ]", " ", identity_scope[:120])
    opening_tokens = opening.split()[:6]
    for term in _PITCH_ROLE_TERMS:
        normalized_term = " ".join(str(term or "").lower().split())
        if not normalized_term:
            continue
        if " " in normalized_term:
            if normalized_term in " ".join(opening_tokens):
                return True
            continue
        if normalized_term in opening_tokens:
            return True
    return False


def _has_concrete_pitch_detail(answer: str) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    if not lowered:
        return False
    if re.search(
        r"\b(?:haven't|have not|hasn't|has not|didn't|did not|don't|do not|never)\b.{0,50}"
        r"\b(?:built|build|created|create|worked|work|used|use|using|led|lead|owned|own|delivered|deliver|managed|manage|reduced|reduce|increased|increase|launched|launch|shipped|ship|debugged|debug|traced|trace|added|add)\b",
        lowered,
    ) or any(
        phrase in lowered
        for phrase in (
            "not yet built",
            "yet to build",
            "no experience with",
            "without experience",
            "do not have experience",
            "don't have experience",
        )
    ):
        return False
    if any(
        phrase in lowered
        for phrase in (
            "improved things",
            "improve things",
            "made things better",
            "worked on things",
            "did stuff",
            "larger systems",
        )
    ):
        return False
    has_detail = _has_pitch_term(lowered, _PITCH_PROOF_DETAIL_TERMS)
    has_action = _has_pitch_term(lowered, _PITCH_PROOF_TERMS)
    return has_action and (has_detail or _has_number_or_metric(lowered))


def _has_real_weakness_signal(answer: str) -> bool:
    return _answer_has_any(answer, _WEAKNESS_REAL_REQUIRED_TERMS)


def _has_complete_weakness_shape(packet: EvaluationPacket) -> bool:
    if packet.node_id != "int_03_weakness_framing":
        return False
    answer = str(packet.learner_answer or "")
    return (
        _has_real_weakness_signal(answer)
        and _answer_has_any(answer, _WEAKNESS_MITIGATION_TERMS)
        and _answer_has_any(answer, _WEAKNESS_PROGRESS_TERMS)
        and _has_concrete_weakness_progress(answer)
    )


def _reconcile_weakness_evidence(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    if not _has_complete_weakness_shape(packet):
        return result
    answer = str(packet.learner_answer or "")
    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    evidence_by_id = {
        "real_weakness": _criterion_evidence(answer, _WEAKNESS_REAL_TERMS) or answer[:180],
        "mitigation_habit": _criterion_evidence(answer, _WEAKNESS_MITIGATION_TERMS) or answer[:180],
        "progress_evidence": _criterion_evidence(answer, _WEAKNESS_PROGRESS_TERMS) or answer[:180],
    }
    for criterion_id, evidence in evidence_by_id.items():
        row = rows_by_id.get(criterion_id)
        if row is not None and not row.met:
            updates[criterion_id] = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.72),
                "evidence_quote": evidence,
                "reason": "backend detected weakness, corrective habit, and concrete progress evidence in learner answer",
            })
    next_focus = result.next_focus
    if any(
        phrase in str(next_focus or "").lower()
        for phrase in (
            "corrective habit",
            "mitigation habit",
            "progress evidence",
            "concrete progress",
            "evidence of progress",
            "real weakness",
            "three-part weakness answer",
            "practise delivering",
            "practice delivering",
        )
    ):
        next_focus = (
            "Pressure-test the answer against one follow-up about stakeholder "
            "pushback or what changed after the rollout."
        )
    if not updates:
        if next_focus != result.next_focus:
            return result.model_copy(update={"next_focus": next_focus})
        return result
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item
        for item in (result.required_missing or [])
        if str(item) not in updates
    ]
    errors = [
        item
        for item in (result.errors or [])
        if not (
            "missing required rubric proof" in str(item).lower()
            and any(key in str(item) for key in updates)
        )
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
    })


def _reconcile_pitch_evidence(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    if packet.node_id != "int_01_elevator_pitch":
        return result
    answer = str(packet.learner_answer or "")
    has_role = _has_pitch_identity(answer)
    has_proof = _has_concrete_pitch_detail(answer)
    has_direction = _answer_has_any(answer, _PITCH_DIRECTION_TERMS)
    if not has_direction:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    direction_quote = _criterion_evidence(answer, _PITCH_DIRECTION_TERMS) or answer[:180]
    future_goal = rows_by_id.get("future_goal")
    if future_goal is not None and not future_goal.met:
        updates["future_goal"] = future_goal.model_copy(update={
            "met": True,
            "quality": max(float(future_goal.quality or 0.0), 0.72),
            "evidence_quote": direction_quote,
            "reason": "backend detected explicit future-direction language in learner answer",
        })
    pitch_structure = rows_by_id.get("pitch_structure")
    if pitch_structure is not None and not pitch_structure.met and has_role and has_proof:
        updates["pitch_structure"] = pitch_structure.model_copy(update={
            "met": True,
            "quality": max(float(pitch_structure.quality or 0.0), 0.7),
            "evidence_quote": direction_quote,
            "reason": "backend detected role, proof, and direction in the pitch",
        })
    if not updates:
        return result

    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item
        for item in (result.required_missing or [])
        if str(item) not in updates
    ]
    errors = [
        item
        for item in (result.errors or [])
        if not (
            "missing required rubric proof" in str(item).lower()
            and any(key in str(item) for key in updates)
        )
    ]
    next_focus = result.next_focus
    if any(
        phrase in str(next_focus or "").lower()
        for phrase in (
            "future goal",
            "future direction",
            "missing direction",
            "clear future",
            "next goal",
        )
    ):
        next_focus = "Tighten the pitch with one measurable impact or sharper role fit."
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
    })


def _has_complete_pitch_shape(packet: EvaluationPacket) -> bool:
    if packet.node_id != "int_01_elevator_pitch":
        return False
    answer = str(packet.learner_answer or "")
    return (
        _has_pitch_identity(answer)
        and _has_concrete_pitch_detail(answer)
        and _answer_has_any(answer, _PITCH_DIRECTION_TERMS)
    )


def _minimum_gate_missing(packet: EvaluationPacket) -> dict[str, str]:
    answer = str(packet.learner_answer or "")
    if packet.node_id == "int_03_weakness_framing":
        missing: dict[str, str] = {}
        if not _has_real_weakness_signal(answer):
            missing["real_weakness"] = "minimum gate requires a real weakness signal in the learner answer"
        if not _answer_has_any(answer, _WEAKNESS_MITIGATION_TERMS):
            missing["mitigation_habit"] = "minimum gate requires a concrete mitigation habit in the learner answer"
        if not _has_concrete_weakness_progress(answer):
            missing["progress_evidence"] = "minimum gate requires concrete progress evidence, not a generic improvement claim"
        return missing
    if packet.node_id == "int_01_elevator_pitch":
        has_role = _has_pitch_identity(answer)
        has_concrete_detail = _has_concrete_pitch_detail(answer)
        has_direction = _answer_has_any(answer, _PITCH_DIRECTION_TERMS)
        missing = {}
        if not has_role:
            missing["answers_question"] = "minimum gate requires a role or identity signal"
        if not has_concrete_detail:
            missing["specific_detail"] = "minimum gate requires a concrete role-relevant proof detail"
        if not (has_role and has_concrete_detail and has_direction):
            missing["pitch_structure"] = "minimum gate requires role, concrete proof detail, and future direction"
        return missing
    return {}


def _apply_minimum_gate_to_rows(result: PrepRubricEval, minimum_missing: dict[str, str]) -> PrepRubricEval:
    if not minimum_missing:
        return result
    criteria = [
        row.model_copy(update={
            "met": False,
            "quality": min(float(row.quality or 0.0), 0.35),
            "evidence_quote": "",
            "reason": minimum_missing[row.id],
        })
        if row.id in minimum_missing
        else row
        for row in result.criteria
    ]
    required_missing = list(result.required_missing or [])
    for criterion_id in minimum_missing:
        if criterion_id not in required_missing:
            required_missing.append(criterion_id)
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "pass_eligible": False,
        "mastery_eligible": False,
    })


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
    normalized = _reconcile_weakness_evidence(
        packet,
        _reconcile_pitch_evidence(packet, validate_llm_eval(raw, packet)),
    )
    minimum_missing = _minimum_gate_missing(packet)
    normalized = _apply_minimum_gate_to_rows(normalized, minimum_missing)
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
                f"minimum_gate:{criterion_id}"
                if criterion_id in minimum_missing
                else
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

    complete_pitch_shape = _has_complete_pitch_shape(packet) and not required_missing
    complete_weakness_shape = _has_complete_weakness_shape(packet) and not required_missing
    if complete_pitch_shape:
        effective = max(effective, packet.pass_score)
    if complete_weakness_shape:
        effective = max(effective, packet.pass_score)

    effective = round(max(0.0, min(1.0, effective)), 4)
    pass_eligible = (
        (bool(normalized.pass_eligible) or complete_pitch_shape or complete_weakness_shape)
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
