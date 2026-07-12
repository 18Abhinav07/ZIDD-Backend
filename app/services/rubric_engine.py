"""Backend enforcement for career-prep rubric evaluations.

The LLM performs the semantic judgment. This layer makes that judgment
auditable: every required criterion needs proof, configured blockers cap the
score, and eligibility is derived from the enforced result rather than from a
single broad model score.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import logging
import re
from typing import Any

from app.ai.schemas import CriterionEval, PrepRubricEval
from app.content.schema import Concept
from app.services.career_task_contract import CareerTaskContract
from app.services.rubrics import PrepRubric, get_rubric


logger = logging.getLogger("zidd.rubric_engine")

_GD09_DIRECTED_ATTACK_RE = re.compile(
    r"\b(?:shut\s+up|stop\s+talking|you\s+talk\s+too\s+much|"
    r"your\s+(?:selfish\s+)?rambling|you(?:'ve|\s+have)\s+wasted|"
    r"you(?:'re|\s+are|\s+keep)\s+(?:selfish|rude|stupid|monopoli[sz]ing)|"
    r"let\s+others\s+speak\s+for\s+once)\b",
    re.IGNORECASE,
)


def gd_has_directed_attack(answer: str) -> bool:
    """Detect an actual attack while ignoring quoted or explicitly rejected wording."""
    text = str(answer or "")
    for match in _GD09_DIRECTED_ATTACK_RE.finditer(text):
        prefix = text[max(0, match.start() - 72):match.start()].lower()
        suffix = text[match.end():min(len(text), match.end() + 72)].lower()
        if re.search(
            r"(?:never|would\s+not|wouldn't|should\s+not|shouldn't|do\s+not|don't|"
            r"avoid|without|instead\s+of\s+(?:saying|telling|using))\b[^.!?]{0,48}$",
            prefix,
        ):
            continue
        if re.search(r"\b(?:inappropriate|unacceptable|wrong|rude|harmful|not\s+what\s+i\s+would\s+say)\b", suffix):
            continue
        return True
    return False


@dataclass(frozen=True)
class EvaluationPacket:
    node_id: str
    node_title: str
    teach_focus: str
    active_role: str
    active_topic: str
    task_contract: dict[str, Any]
    attempt_type: str
    core_qualified: bool
    core_qualification_turn_id: str
    core_qualification_evidence: dict[str, Any]
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
        if (
            str(message.get("role") or "") == "assistant"
            and (
                str(message.get("message_kind") or "") == "evaluation_retry"
                or "couldn't review that answer reliably" in content.lower()
            )
        ):
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


def normalize_gd_whether_topic(clause: str) -> str:
    """Turn prose after "whether" into a clean GD motion."""
    topic = " ".join(str(clause or "").strip().rstrip("?.!").split())
    topic = re.split(
        r"\s+and\s+(?:(?:the\s+)?(?:discussion|conversation|group)\s+)?"
        r"(?:shifted|drifted|moved|turned)\b",
        topic,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    if not topic:
        return ""
    if topic.lower().startswith("should "):
        return f"{topic[0].upper()}{topic[1:]}?"
    subject_predicate = re.fullmatch(r"(.+?)\s+should\s+(.+)", topic, re.IGNORECASE)
    if subject_predicate:
        subject, predicate = subject_predicate.groups()
        return f"Should {subject.strip()} {predicate.strip()}?"
    return f"Should {topic}?"


def infer_gd_topic_from_messages(messages: list[dict] | None) -> str:
    for message in reversed(messages or []):
        if str(message.get("role") or "") != "assistant":
            continue
        content = " ".join(str(message.get("content") or "").split())
        transfer_match = re.search(
            r'\bTransfer task on\s+["“]([^"”]+)',
            content,
            re.IGNORECASE,
        )
        motion_match = re.search(r'\bMotion:\s*["“]([^"”]+)', content, re.IGNORECASE)
        whether_match = re.search(r"\bdiscussing whether\s+([^.!?]+)", content, re.IGNORECASE)
        inferred = transfer_match or motion_match or whether_match
        if inferred:
            topic = inferred.group(1).strip()
            return normalize_gd_whether_topic(topic) if whether_match else topic
        lowered = content.lower()
        if "ai" in lowered and "hiring" in lowered:
            return "Should companies use AI in hiring?"
        if "remote work" in lowered:
            return "Should remote work be the default?"
        if "four-day" in lowered or "four day work" in lowered:
            return "Should four-day workweeks become the standard?"
        if "social media" in lowered and ("verify" in lowered or "identity" in lowered):
            return "Should social-media platforms verify every user identity?"
        if "digital payment" in lowered:
            return "Should digital payments become the default?"
    return ""


def infer_initial_gd_topic(messages: list[dict] | None, node_id: str = "") -> str:
    rows = list(messages or [])
    if node_id:
        node_rows = [
            message for message in rows
            if str(message.get("node_id") or "") == node_id
        ]
        legacy_rows = [message for message in rows if not message.get("node_id")]
        rows = node_rows or legacy_rows
    for message in rows:
        topic = infer_gd_topic_from_messages([message])
        if topic:
            return topic
    return ""


def gd_topic_family(topic: str) -> str:
    lowered = _normalize(topic)
    if "ai" in lowered and "hiring" in lowered:
        return "ai_hiring"
    if "remote" in lowered and "work" in lowered:
        return "remote_work"
    if "four day" in lowered and "work" in lowered:
        return "four_day_workweek"
    if "social media" in lowered and ("identity" in lowered or "verify" in lowered):
        return "social_identity"
    if "digital payment" in lowered:
        return "digital_payments"
    return lowered


def configured_gd_topic(state: dict) -> str:
    career_context = state.get("career_context") or {}
    scenario = state.get("scenario_config") or {}
    topics = career_context.get("gd_topics") or career_context.get("custom_gd_topics") or []
    if isinstance(topics, list) and topics:
        configured = str(topics[0] or "").strip()
        if configured:
            return configured
    return str(
        career_context.get("gd_topic")
        or scenario.get("resolved_topic")
        or scenario.get("topic")
        or ""
    ).strip()


def resolve_prompt_gd_topic(state: dict) -> str:
    """Return the exact structured motion for the currently visible GD task."""
    active = str(state.get("active_gd_prompt_topic") or "").strip()
    configured = configured_gd_topic(state)
    if active:
        attempt_type = str(state.get("active_prompt_attempt_type") or "")
        if attempt_type in {"transfer", "pressure"}:
            node_id = str(state.get("competency_node") or "")
            for message in reversed(state.get("messages") or []):
                if str(message.get("role") or "") != "assistant":
                    continue
                if node_id and str(message.get("node_id") or "") != node_id:
                    continue
                message_kind = str(message.get("message_kind") or "")
                content = " ".join(str(message.get("content") or "").split())
                if message_kind:
                    if message_kind not in {"coach_response", "coach_fallback"}:
                        continue
                elif not re.match(r"^(?:Transfer\s+(?:task|motion)|Pressure\s+(?:check|motion))\b", content, re.IGNORECASE):
                    continue
                explicit = re.search(
                    r'\b(?:Transfer\s+(?:task|motion)|Pressure\s+(?:check|motion))(?:\s+on)?\s*:?\s*["“]([^"”]+)',
                    content,
                    re.IGNORECASE,
                )
                if explicit:
                    visible_topic = explicit.group(1).strip()
                    if visible_topic and visible_topic != active:
                        return visible_topic
                # Only the latest node-scoped prompt can redefine the active motion.
                # Older quoted transfer prompts must never leak back into a later turn.
                break
        return active
    if configured:
        return configured
    return infer_gd_topic_from_messages(state.get("messages") or [])


def resolve_core_gd_topic(state: dict, node_id: str = "") -> str:
    """Return the exact topic persisted with GD core qualification evidence."""
    if not state.get("core_qualified"):
        return ""
    evidence = state.get("core_qualification_evidence")
    if not isinstance(evidence, dict):
        return ""
    return str(evidence.get("active_topic") or "").strip()


def _state_topic(state: dict) -> str:
    return resolve_prompt_gd_topic(state)


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
        active_contract = CareerTaskContract.from_state(state)
        active_topic = (
            active_contract.active_topic
            if active_contract and active_contract.active_topic
            else _state_topic(state)
        )
        active_role = (
            active_contract.active_role
            if active_contract and active_contract.active_role
            else str(
                (state.get("career_context") or {}).get("primary_role")
                or (state.get("scenario_config") or {}).get("target_role")
                or ""
            ).strip()
        )
        task_contract = active_contract.model_dump() if active_contract else {}
        attempt_type = _attempt_type(state)
    else:
        state = {}
        node = state_or_node
        messages = node_or_messages if isinstance(node_or_messages, list) else []
        active_topic = ""
        active_role = ""
        task_contract = {}
        attempt_type = "independent"
    if not isinstance(node, Concept):
        raise TypeError("build_evaluation_packet requires a Concept node")
    rubric = rubric or get_rubric(node.id)
    core_qualification_turn_id = str(state.get("core_qualification_turn_id") or "")
    parent = (
        dict(state.get("core_qualification_evidence") or {})
        if isinstance(state.get("core_qualification_evidence"), dict)
        else {}
    )
    core_qualified = bool(
        state.get("core_qualified")
        and core_qualification_turn_id
        and parent.get("evaluation_id") == core_qualification_turn_id
        and parent.get("user_id") == state.get("user_id")
        and parent.get("node_id") == node.id
        and parent.get("attempt_type") == "independent"
        and parent.get("pass_eligible") is True
        and bool(str(parent.get("learner_answer") or "").strip())
        and (not node.id.startswith("gd_") or bool(str(parent.get("active_topic") or "").strip()))
        and not parent.get("blockers")
    )
    criteria = [
        {
            "id": c.id,
            "label": c.label,
            "required": c.required,
            "missing_cap": c.missing_cap,
            "proof_required": c.proof_required,
        }
        for c in rubric.criteria
    ]
    if attempt_type == "transfer":
        criteria = [
            *criteria,
            {
                "id": "transfer_context",
                "label": "Applies the qualified skill in a meaningfully different realistic context",
                "required": True,
                "missing_cap": 0.62,
                "proof_required": True,
            },
        ]
    elif attempt_type == "pressure":
        if node.id in {
            "int_09_diplomatic_pushback",
            "int_10_close_strong",
            "int_11_salary_negotiation",
            "int_12_explain_a_gap",
            "gd_06_balanced_view",
            "gd_07_steer_back",
            "gd_08_include_quiet",
            "gd_09_manage_dominator",
            "gd_10_drive_consensus",
        }:
            criteria = [
                {**criterion, "required": True}
                for criterion in criteria
            ] + [{
                "id": "core_consistency",
                "label": "Keeps the harder response consistent with the qualified core answer",
                "required": True,
                "missing_cap": 0.65,
                "proof_required": True,
            }]
        else:
            criteria = [
            {
                "id": "pressure_response",
                "label": "Directly answers the interviewer or panel pushback",
                "required": True,
                "missing_cap": 0.62,
                "proof_required": True,
            },
            {
                "id": "evidence_defense",
                "label": "Defends the decision with learner-owned evidence or a concrete reason",
                "required": True,
                "missing_cap": 0.65,
                "proof_required": True,
            },
            {
                "id": "core_consistency",
                "label": "Keeps the defense consistent with the qualified core answer",
                "required": True,
                "missing_cap": 0.65,
                "proof_required": True,
            },
            ]
    return EvaluationPacket(
        node_id=node.id,
        node_title=node.title,
        teach_focus=node.teach_focus,
        active_role=active_role,
        active_topic=active_topic,
        task_contract=task_contract,
        attempt_type=attempt_type,
        core_qualified=core_qualified,
        core_qualification_turn_id=core_qualification_turn_id,
        core_qualification_evidence=parent if core_qualified else {},
        learner_answer=user_input,
        pass_score=rubric.pass_score,
        mastery_score=rubric.mastery_score,
        criteria=criteria,
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


def invalid_required_evidence_ids(
    packet: EvaluationPacket,
    raw: PrepRubricEval,
) -> list[str]:
    """Return proof-bearing met criteria whose claimed quote is not learner-verbatim."""
    rows_by_id: dict[str, list[CriterionEval]] = {}
    for row in raw.criteria:
        rows_by_id.setdefault(str(row.id), []).append(row)
    invalid: list[str] = []
    for criterion in packet.criteria:
        if not criterion.get("proof_required"):
            continue
        criterion_id = str(criterion.get("id") or "")
        rows = rows_by_id.get(criterion_id, [])
        if len(rows) != 1 or not rows[0].met:
            continue
        if not _quote_appears(packet.learner_answer, rows[0].evidence_quote):
            invalid.append(criterion_id)
    return invalid


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
_PITCH_MECHANISM_TERMS = (
    "fastapi",
    "django",
    "python",
    "typescript",
    "react",
    "database",
    "databases",
    "checkout",
    "latency",
    "retry",
    "retries",
    "idempotency",
    "logging",
    "observability",
    "transaction",
    "transactions",
    "dashboard",
    "dashboards",
    "checklist",
    "checklists",
)
_PITCH_MECHANISM_CHANGE_ACTION_PATTERN = (
    r"(?:build(?:s|ing)?|built|creat(?:e|es|ed|ing)|us(?:e|es|ed|ing)|"
    r"implement(?:s|ed|ing)?|introduc(?:e|es|ed|ing)|automat(?:e|es|ed|ing)|"
    r"migrat(?:e|es|ed|ing)|fix(?:es|ed|ing)?|add(?:s|ed|ing)?|"
    r"(?:re)?design(?:s|ed|ing)?|ship(?:s|ped|ping)?|debug(?:s|ged|ging)?|"
    r"trac(?:e|es|ed|ing))"
)
_PITCH_SPECIFIC_COMPLETED_ACTION_PATTERN = (
    rf"(?:{_PITCH_MECHANISM_CHANGE_ACTION_PATTERN}|lead(?:s|ing)?|led|"
    r"launch(?:es|ed|ing)?|deliver(?:s|ed|ing)?|resolv(?:e|es|ed|ing)|"
    r"clos(?:e|es|ed|ing))"
)
_PITCH_SCOPED_WORK_EXAMPLES = (
    "renewal process",
    "payment api",
    "payment apis",
    "payment service",
    "payments migration",
    "payment migration",
    "migration",
    "rollout",
    "checkout",
    "incident",
    "release",
    "launch",
    "dashboard",
    "handoff",
    "checklist",
    "onboarding process",
    "hiring pipeline",
)
_PITCH_OUTCOME_ACTION_PATTERN = (
    r"(?:reduc(?:e|es|ed|ing)|increas(?:e|es|ed|ing)|improv(?:e|es|ed|ing)|"
    r"cut(?:s|ting)?|sav(?:e|es|ed|ing)|prevent(?:s|ed|ing)?|"
    r"avoid(?:s|ed|ing)?|resolv(?:e|es|ed|ing)|protect(?:s|ed|ing)?)"
)
_PITCH_ANY_PROOF_ACTION_PATTERN = (
    rf"(?:{_PITCH_SPECIFIC_COMPLETED_ACTION_PATTERN}|{_PITCH_OUTCOME_ACTION_PATTERN}|"
    r"work(?:s|ed|ing)?|manag(?:e|es|ed|ing)|own(?:s|ed|ing)?)"
)
_PITCH_EXPLICIT_OUTCOME_TARGETS = (
    "churn",
    "latency",
    "duplicate writes",
    "error",
    "errors",
    "incident",
    "incidents",
    "failure",
    "failures",
    "conversion",
    "conversions",
    "retention",
    "revenue",
    "uptime",
    "throughput",
    "turnaround",
    "rollback",
    "risk",
    "risks",
    "cost",
    "costs",
    "time",
    "defect",
    "defects",
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
    outcome_verbs = "|".join(
        re.escape(term)
        for term in _WEAKNESS_PROGRESS_OUTCOME_TERMS
        if " " not in term
    )
    has_learner_action = bool(
        re.search(
            r"\b(?:i|we)\b[^.!?]{0,180}\b(?:changed|change|started|start|used|use|"
            r"chose|choose|implemented|apply|applied|lead|led|open|opened|manage|managed)\b",
            lowered,
        )
    )
    owned_completed_result = False
    for sentence in re.split(r"[.!?;]+", lowered):
        if not re.search(rf"\b(?:{outcome_verbs})\b", sentence):
            continue
        if re.search(
            r"\b(?:according\s+to|as\s+(?:reported|stated|claimed)\s+by)\b|"
            r"\b(?:i|we)\s+(?:was|were)\s+(?:told|informed|advised|notified)\b|"
            r"\b(?:i|we)\s+(?:heard|learned|observed)\s+that\b|"
            r"\b(?:i|we)\s+watched\s+while\b|"
            r"\b(?:my|our|the)\s+(?:manager|lead|colleague|teammate|stakeholder|"
            r"client|customer)\s+(?:told|informed|said|reported|claimed|noted)\b",
            sentence,
        ):
            continue
        if re.search(
            r"\b(?:would|could|should|might|may|expected|expect|hoped|hope|"
            r"planned|plan|believed|believe)\b",
            sentence,
        ):
            continue
        if re.search(
            rf"\b(?:would|could|should|might|may)\s+(?:have\s+)?(?:{outcome_verbs})\b",
            sentence,
        ):
            continue
        if re.search(
            rf"\b(?:did\s+not|didn't|never|not)\b[^.!?]{{0,40}}\b(?:{outcome_verbs})\b",
            sentence,
        ):
            continue
        if re.search(r"\bthe\s+team\b", sentence):
            if not (has_learner_action and "that helped the team" in sentence):
                continue
        if re.search(
            r"\b(?:i|we|my|our)\b|\b(?:that|this|the)\s+"
            r"(?:approach|change|habit|decision|rollout|fix)\b",
            sentence,
        ) or (
            has_learner_action
            and ("that meant" in sentence or "that helped" in sentence)
        ):
            owned_completed_result = True
            break
    return (
        has_work_detail
        and has_event_context
        and outcome_hits >= 1
        and (strong_outcome_hits >= 1 or has_number or has_before_after)
        and owned_completed_result
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


def _has_pitch_action_form(answer: str, pattern: str) -> bool:
    return bool(re.search(rf"\b{pattern}\b", str(answer or "").lower()))


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
    lowered = " ".join(_before_pitch_future_direction(answer).lower().split())
    if not lowered:
        return False
    if re.search(
        rf"\b(?:haven't|have not|hasn't|has not|didn't|did not|don't|do not|never)\b.{{0,50}}"
        rf"\b{_PITCH_ANY_PROOF_ACTION_PATTERN}\b",
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
    has_specific_mechanism_change = (
        _has_pitch_action_form(lowered, _PITCH_MECHANISM_CHANGE_ACTION_PATTERN)
        and _has_pitch_term(lowered, _PITCH_MECHANISM_TERMS)
    )
    has_scoped_completed_work = (
        _has_pitch_action_form(lowered, _PITCH_SPECIFIC_COMPLETED_ACTION_PATTERN)
        and _has_pitch_term(lowered, _PITCH_SCOPED_WORK_EXAMPLES)
    )
    has_outcome_action = _has_pitch_action_form(lowered, _PITCH_OUTCOME_ACTION_PATTERN)
    has_measurable_outcome = has_outcome_action and _has_number_or_metric(lowered)
    has_explicit_outcome = (
        has_outcome_action
        and _has_pitch_term(lowered, _PITCH_EXPLICIT_OUTCOME_TARGETS)
    )
    return (
        has_specific_mechanism_change
        or has_scoped_completed_work
        or has_measurable_outcome
        or has_explicit_outcome
    )


def _has_real_weakness_signal(answer: str) -> bool:
    return _answer_has_any(answer, _WEAKNESS_REAL_REQUIRED_TERMS)


def _has_complete_weakness_shape(packet: EvaluationPacket) -> bool:
    if packet.node_id != "int_03_weakness_framing" or packet.attempt_type != "independent":
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
        if row is not None:
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
            "transition",
            "linking",
            "linkage",
            "overlap",
            "redundan",
        )
    ):
        next_focus = (
            "Pressure-test the answer against one follow-up about stakeholder "
            "pushback or what changed after the rollout."
        )
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item
        for item in (result.required_missing or [])
        if str(item) not in evidence_by_id
    ]
    errors = [
        item
        for item in (result.errors or [])
        if not (
            "missing required rubric proof" in str(item).lower()
            and any(key in str(item) for key in evidence_by_id)
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
    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    proven_ids: set[str] = set()
    role_quote = _criterion_evidence(answer, _PITCH_ROLE_TERMS) or answer[:180]
    proof_quote = (
        _criterion_evidence(answer, _PITCH_PROOF_TERMS)
        or _criterion_evidence(answer, _PITCH_PROOF_DETAIL_TERMS)
        or answer[:180]
    )
    direction_quote = _criterion_evidence(answer, _PITCH_DIRECTION_TERMS) or answer[:180]
    evidence_by_id = {
        "answers_question": (
            has_role,
            role_quote,
            0.7,
            "backend detected an explicit role or professional identity in learner answer",
        ),
        "specific_detail": (
            has_proof,
            proof_quote,
            0.72,
            "backend detected concrete role-relevant proof in learner answer",
        ),
        "pitch_structure": (
            has_role and has_proof and has_direction,
            answer[:240],
            0.7,
            "backend detected role, proof, and direction in the pitch",
        ),
        "future_goal": (
            has_direction,
            direction_quote,
            0.72,
            "backend detected explicit future-direction language in learner answer",
        ),
    }
    for criterion_id, (proven, evidence, quality_floor, reason) in evidence_by_id.items():
        if not proven:
            continue
        proven_ids.add(criterion_id)
        row = rows_by_id.get(criterion_id)
        if row is not None and not row.met:
            updates[criterion_id] = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), quality_floor),
                "evidence_quote": evidence,
                "reason": reason,
            })

    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item
        for item in (result.required_missing or [])
        if str(item) not in proven_ids
    ]
    errors = [
        item
        for item in (result.errors or [])
        if not (
            "missing required rubric proof" in str(item).lower()
            and any(key in str(item) for key in proven_ids)
        )
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
    })


def _reconcile_failure_pressure_response(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    """Repair only an unmistakably direct int06 pushback answer mislabeled by the model."""
    if (
        packet.node_id != "int_06_own_a_failure"
        or packet.attempt_type != "pressure"
        or not packet.core_qualified
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    if not re.search(
        r"\b(?:you\s+(?:should|can)\s+trust\s+my\s+judg(?:e)?ment|"
        r"my\s+judg(?:e)?ment\s+is\s+trustworthy)\b[^.!?]*\bbecause\b",
        first_sentence,
        re.IGNORECASE,
    ):
        return result
    rows = {row.id: row for row in result.criteria}
    pressure_row = rows.get("pressure_response")
    if pressure_row is None or pressure_row.met:
        return result
    repaired = pressure_row.model_copy(update={
        "met": True,
        "quality": max(float(pressure_row.quality or 0.0), 0.8),
        "evidence_quote": first_sentence[:320],
        "reason": "backend detected an explicit direct answer to the judgment-trust pushback",
    })
    criteria = [repaired if row.id == "pressure_response" else row for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) != "pressure_response"
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = [
        item for item in (result.errors or [])
        if "pressure_response" not in str(item)
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_clarification_evidence(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if packet.node_id != "int_07_clarify_before_answering" or packet.attempt_type == "pressure":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    question_match = re.search(r"(?:^|(?<=[.!]))\s*([^?]{12,320}\?)", answer)
    if not question_match:
        return result
    question = question_match.group(1).strip()
    lowered_question = question.lower()
    active_prompt = ""
    for message in reversed(packet.recent_messages or []):
        if (
            str(message.get("role") or "") == "assistant"
            and str(message.get("message_kind") or "") != "evaluation_retry"
            and "couldn't review that answer reliably" not in str(message.get("content") or "").lower()
        ):
            active_prompt = str(message.get("content") or "")
            break
    lowered_prompt = active_prompt.lower()
    prompt_allows_clarification = bool(
        active_prompt
        and not any(
            marker in lowered_prompt
            for marker in (
                "focus specifically",
                "specifically on",
                "focus only on",
                "answer specifically",
                "the exact incident",
                "the checkout outage on",
            )
        )
    )
    leadership_terms = ("leadership", "people management", "technical direction", "manager", "manage people")
    product_terms = ("product", "onboarding", "retention", "user", "customer")
    technical_terms = (
        "technical", "system", "systems", "design", "incident", "response", "diagnosis", "decision",
        "architecture", "reliability", "latency", "cost", "performance",
    )
    has_term = lambda text, term: bool(re.search(rf"\b{re.escape(term)}\b", text))
    if any(has_term(lowered_question, term) for term in leadership_terms):
        clarifier_domain = "leadership"
        grounded = any(has_term(lowered_prompt, term) for term in ("leadership", "lead", "team", "manager"))
    elif any(has_term(lowered_question, term) for term in product_terms):
        clarifier_domain = "product"
        grounded = any(has_term(lowered_prompt, term) for term in product_terms)
    elif any(has_term(lowered_question, term) for term in technical_terms):
        clarifier_domain = "technical"
        grounded = any(has_term(lowered_prompt, term) for term in technical_terms)
    else:
        clarifier_domain = "generic"
        prompt_tokens = {
            token for token in _normalize(active_prompt).split()
            if len(token) >= 5 and token not in {"about", "would", "could", "interviewer", "question"}
        }
        question_tokens = set(_normalize(question).split())
        grounded = bool(active_prompt and len(prompt_tokens & question_tokens) >= 2)
    narrows_scope = (
        prompt_allows_clarification
        and grounded
        and " or " in lowered_question
        and any(
            marker in lowered_question
            for marker in (
                "do you mean",
                "would you like",
                "are you asking",
                "should i focus",
                "should i emphasize",
                "more interested in",
                "which aspect",
                "what aspect",
                "which part",
                "what part",
                "could you clarify whether",
                "would you clarify whether",
                "can you clarify whether",
            )
        )
    )
    remainder = answer[question_match.end():].strip()
    answer_prefix = bool(
        len(re.findall(r"[a-z0-9']+", remainder.lower())) >= 8
        and re.match(
            r"(?:if|for|assuming|in that case|i would|i'd|i will|i'll|my answer)\b",
            remainder,
            re.IGNORECASE,
        )
    )
    answer_body = re.sub(
        r"^(?:if|for|assuming)\s+[^,:]{1,100}[,:]\s*",
        "",
        remainder,
        count=1,
        flags=re.IGNORECASE,
    )
    answer_body = re.sub(
        r"^(?:i(?:'ll| will| would|\'d)\s+(?:focus on|choose|take)\s+[^,:]{1,80}[,:])\s*",
        "",
        answer_body,
        count=1,
        flags=re.IGNORECASE,
    )
    lowered_body = answer_body.lower()
    if clarifier_domain == "technical":
        unmistakable_signals = (
            "architecture", "database", " api", "idempot", "latency", "rollback", "rollout",
            "deploy", "debug",
        )
        technical_anchors = (
            "diagnos", "trace", "incident", "outage", "service", "retry", "reliability",
            "design", "system", "failure", "trade-off", "tradeoff", "decision",
        )
        technical_actions = (
            "monitor", "alert", "test", "compare", "constraint", "option", "document",
            "launch", "traffic", "restore", "pause",
        )
        design_reasoning_signals = (
            "compare", "option", "constraint", "team", "document", "launch", "trade-off",
            "tradeoff", "decision",
        )
        anchor_hits = sum(term in lowered_body for term in technical_anchors)
        body_grounded = bool(
            any(term in lowered_body for term in unmistakable_signals)
            or anchor_hits >= 2
            or (anchor_hits >= 1 and any(term in lowered_body for term in technical_actions))
            or sum(term in lowered_body for term in design_reasoning_signals) >= 3
        )
    elif clarifier_domain == "leadership":
        strong_signals = (
            "mentor", "coach", "delegate", "align", "conflict", "stakeholder", "feedback",
        )
        weak_signals = ("team", "people", "manager", "decision", "direction", "architecture")
        body_grounded = bool(
            any(term in lowered_body for term in strong_signals)
            or sum(term in lowered_body for term in weak_signals) >= 2
        )
    elif clarifier_domain == "product":
        strong_signals = (
            "onboarding", "retention", "metric", "experiment", "adoption", "churn", "conversion",
        )
        weak_signals = ("product", "reliability", "user", "customer", "feedback")
        body_grounded = bool(
            any(term in lowered_body for term in strong_signals)
            or sum(term in lowered_body for term in weak_signals) >= 2
        )
    else:
        grounding_tokens = {
            token
            for token in _normalize(f"{active_prompt} {question}").split()
            if len(token) >= 4
            and token not in {
                "before", "answer", "would", "could", "should", "whether", "interviewer",
                "question", "clarify", "asking", "prefer", "default", "focus",
            }
        }
        body_grounded = len(grounding_tokens & set(_normalize(answer_body).split())) >= 2
    answer_frame = bool(answer_prefix and body_grounded)
    proof: dict[str, str] = {}
    if narrows_scope:
        alternative_match = re.search(r"\b[^?]{0,90}\bor\b[^?]{0,90}", question, re.IGNORECASE)
        proof["recognizes_ambiguity"] = (
            alternative_match.group(0).strip() if alternative_match else question
        )[:320]
        proof["asks_targeted_question"] = question[:320]
    if answer_frame:
        first_answer_sentence = re.split(r"(?<=[.!?])\s+", remainder, maxsplit=1)[0].strip()
        proof["states_answer_frame"] = first_answer_sentence[:320]
    if not proof:
        return result

    rows = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.8),
            "evidence_quote": evidence,
            "reason": "backend detected a scope-narrowing clarifier and its focused answer frame",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = [
        item for item in (result.errors or [])
        if not any(criterion_id in str(item) for criterion_id in proof)
    ]
    if complete_required:
        next_focus = "Apply the clarify-then-answer structure to a different ambiguous interview question."
    elif "states_answer_frame" in required_missing:
        next_focus = "Add a focused answer to the interpretation selected by the clarifier."
    elif "asks_targeted_question" in required_missing or "recognizes_ambiguity" in required_missing:
        next_focus = "Ask one concise question that distinguishes two plausible interpretations."
    else:
        next_focus = result.next_focus
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_int07_pressure_response(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        packet.node_id != "int_07_clarify_before_answering"
        or packet.attempt_type != "pressure"
        or not packet.core_qualified
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    assumption_match = re.match(
        r"(?P<proof>(?:i will assume|i'll assume|i am assuming|i'm assuming)\s+[^,.!?]{3,120})",
        answer,
        re.IGNORECASE,
    )
    if not assumption_match:
        return result
    rows = {row.id: row for row in result.criteria}
    row = rows.get("pressure_response")
    if row is None or row.met:
        return result
    proof = assumption_match.group("proof").strip()
    repaired = row.model_copy(update={
        "met": True,
        "quality": max(float(row.quality or 0.0), 0.8),
        "evidence_quote": proof,
        "reason": "backend detected an explicit assumption in response to the no-clarification pushback",
    })
    criteria = [repaired if item.id == "pressure_response" else item for item in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) != "pressure_response"
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {item.id for item in criteria if item.met}
    complete_required = required_ids.issubset(met_ids)
    errors = [
        item for item in (result.errors or [])
        if "pressure_response" not in str(item)
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_int08_quantified_impact(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if packet.node_id != "int_08_quantify_impact":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    prompt_candidates: list[str] = []
    for message in reversed(packet.recent_messages or []):
        if (
            str(message.get("role") or "") == "assistant"
            and str(message.get("message_kind") or "") != "evaluation_retry"
            and "couldn't review that answer reliably" not in str(message.get("content") or "").lower()
        ):
            active_prompt = str(message.get("content") or "")
            break
    stopwords = {
        "about", "after", "before", "could", "would", "provide", "specific", "example",
        "comparison", "numerical", "previous", "role", "those", "their", "there",
    }

    def normalized_token(token: str) -> str:
        if token.endswith("ies") and len(token) > 5:
            return f"{token[:-3]}y"
        if token.endswith("s") and len(token) > 4 and not token.endswith(("ss", "us", "is")):
            return token[:-1]
        return token

    prompt_tokens = {
        normalized_token(token)
        for token in _normalize(active_prompt).split()
        if len(token) >= 4 and token not in stopwords
    }
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", answer)
        if sentence.strip()
    ]
    content_stopwords = stopwords | {
        "from", "into", "over", "under", "using", "with", "that", "this", "then",
        "introduced", "implemented", "increased", "decreased", "dropped", "reduced",
    }

    def content_tokens(text: str) -> set[str]:
        return {
            normalized_token(token) for token in _normalize(text).split()
            if len(token) >= 4 and token not in content_stopwords
        }

    grounded_sentences = [
        sentence
        for sentence in sentences
        if len(prompt_tokens & content_tokens(sentence)) >= 2
    ]
    metrics = re.findall(
        r"\b\d+(?:\.\d+)?(?:\s*%|\s*(?:seconds?|minutes?|hours?|days?|weeks?|months?|"
        r"users?|tickets?|transactions?|requests?|customers?))?\b",
        answer,
        re.IGNORECASE,
    )
    action_pattern = re.compile(
        r"\bI\s+(?:introduced|implemented|built|created|designed|led|changed|automated|"
        r"reduced|cut|optimized|migrated|added|removed|reworked|launched)\b[^.;!?]{0,220}",
        re.IGNORECASE,
    )
    action_sentence = next((sentence for sentence in sentences if action_pattern.search(sentence)), "")
    action_match = action_pattern.search(action_sentence)
    outcome_markers = (
        "fell", "dropped", "decreased", "reduced", "cut", "improved", "increased",
        "grew", "saved", "from ", " to ",
    )
    impact_sentence = next(
        (
            sentence for sentence in sentences
            if any(marker in sentence.lower() for marker in outcome_markers)
            and re.search(r"\d", sentence)
        ),
        "",
    )
    impact_linked_to_prompt = bool(
        impact_sentence
        and (
            impact_sentence in grounded_sentences
            or any(
                len(content_tokens(impact_sentence) & content_tokens(sentence)) >= 2
                for sentence in grounded_sentences
            )
        )
    )
    contribution_linked = bool(
        action_match
        and impact_sentence
        and (
            action_sentence == impact_sentence
            or len(content_tokens(action_sentence) & content_tokens(impact_sentence)) >= 2
        )
    )
    has_impact = bool(
        grounded_sentences
        and impact_linked_to_prompt
        and len(metrics) >= 2
    )
    proof: dict[str, str] = {}
    if has_impact:
        proof["impact_claim"] = impact_sentence
        proof["quantified_before_after"] = impact_sentence
    if has_impact and contribution_linked and action_match:
        proof["learner_contribution"] = action_match.group(0).strip()
    if has_impact and any(
        term in answer.lower()
        for term in (
            "user", "customer", "support", "ticket", "revenue", "cost", "completion",
            "latency", "time", "transaction", "reliability",
        )
    ):
        proof["business_or_user_value"] = impact_sentence
    if not proof:
        return result

    rows = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.8),
            "evidence_quote": evidence[:320],
            "reason": "backend detected prompt-grounded before/after metrics tied to the learner's action",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = [
        item for item in (result.errors or [])
        if not any(criterion_id in str(item) for criterion_id in proof)
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": (
            "Apply the same action-to-metric structure to a different achievement."
            if complete_required
            else result.next_focus
        ),
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_int09_diplomatic_pushback(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    """Repair only explicit, prompt-grounded independent diplomatic pushback."""
    if (
        packet.node_id != "int_09_diplomatic_pushback"
        or packet.attempt_type not in {"independent", "transfer", "pressure"}
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if len(_normalize(answer).split()) < 18 or _INT09_DIRECTED_ATTACK_RE.search(answer):
        return result
    prompt_candidates: list[str] = []
    for message in reversed(packet.recent_messages or []):
        if (
            str(message.get("role") or "") == "assistant"
            and str(message.get("message_kind") or "") != "evaluation_retry"
            and "couldn't review that answer reliably" not in str(message.get("content") or "").lower()
        ):
            prompt_candidates.append(str(message.get("content") or ""))
    if not prompt_candidates:
        return result

    stopwords = {
        "about", "against", "answer", "could", "interviewer", "more", "point",
        "respond", "response", "should", "their", "there", "these", "they",
        "this", "those", "what", "while", "with", "would", "your",
    }

    def tokens(text: str) -> set[str]:
        out: set[str] = set()
        for token in _normalize(text).split():
            if len(token) < 4 or token in stopwords:
                continue
            if token.endswith("ies") and len(token) > 5:
                token = f"{token[:-3]}y"
            elif token.endswith("s") and len(token) > 4 and not token.endswith(("ss", "us", "is")):
                token = token[:-1]
            out.add(token)
        return out

    answer_tokens = tokens(answer)
    active_prompt = max(
        prompt_candidates,
        key=lambda candidate: len(tokens(candidate) & answer_tokens),
    )
    prompt_tokens = tokens(active_prompt)
    if len(prompt_tokens & answer_tokens) < 2:
        return result
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?;])\s+", answer)
        if part.strip()
    ]
    acknowledgement = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:i\s+(?:see|hear|understand|agree)|i\s+can\s+see\s+why|"
            r"that(?:'s|\s+is)\s+(?:fair|valid)|you\s+make\s+a\s+fair\s+point)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    counter = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:however|though|but|still|yet|i\s+would\s+not|i'd\s+argue|"
            r"i\s+would\s+argue|i\s+disagree|my\s+(?:view|position)\s+is)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    reason = next((
        sentence for sentence in sentences
        if re.search(r"\b(?:because|since|given|so\s+that|depends\s+on)\b", sentence, re.IGNORECASE)
        and re.search(
            r"\b(?:risk|reliability|safety|quality|cost|deadline|compliance|scope|"
            r"customer|maintainability|invariant|consistency|failure|regression|idempotency)\w*\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    collaborative = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:choose|reserve|keep|where\s+needed|when\s+needed|depending|"
            r"rather\s+than|not\s+(?:a|the)\s+universal|hybrid)\b",
            sentence,
            re.IGNORECASE,
        )
    ), acknowledgement if acknowledgement and counter else "")
    proof = {
        criterion_id: quote[:320]
        for criterion_id, quote in {
            "acknowledges_view": acknowledgement,
            "clear_counterposition": counter,
            "requirement_based_reasoning": reason,
            "collaborative_tone": collaborative,
        }.items()
        if quote
    }
    if packet.attempt_type == "transfer":
        if not packet.core_qualified:
            return result
        core_tokens = tokens(str(packet.core_qualification_evidence.get("learner_answer") or ""))
        distinct_prompt_tokens = prompt_tokens - core_tokens
        if len(distinct_prompt_tokens & answer_tokens) < 2:
            return result
        proof["transfer_context"] = (acknowledgement or counter)[:320]
    if packet.attempt_type == "pressure":
        if not packet.core_qualified:
            return result
        core_tokens = tokens(str(packet.core_qualification_evidence.get("learner_answer") or ""))
        if len(core_tokens & answer_tokens) < 2:
            return result
        proof["core_consistency"] = (counter or reason)[:320]
    expected_proof_count = 5 if packet.attempt_type in {"transfer", "pressure"} else 4
    if len(proof) != expected_proof_count:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    criteria = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote,
                "reason": "backend verified explicit prompt-grounded diplomatic pushback",
            })
        criteria.append(row)
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete = required_ids.issubset(met_ids)
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    errors = list(result.errors or [])
    if complete:
        errors = [
            item for item in errors
            if not any(criterion_id in str(item) for criterion_id in required_ids)
        ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": (
            "Use the same diplomatic structure on a different interviewer premise."
            if complete else result.next_focus
        ),
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete else result.effective_score,
        "pass_eligible": True if complete else result.pass_eligible,
    })


_INT11_BACKPEDAL_RE = re.compile(
    r"\b(?:sorry|i\s+apologi[sz]e|i\s+do\s+not\s+want\s+to\s+be\s+difficult|"
    r"i\s+don't\s+want\s+to\s+be\s+difficult|whatever\s+you\s+think\s+is\s+fair|"
    r"whatever\s+the\s+standard\s+band\s+is|if\s+that\s+is\s+too\s+high|"
    r"if\s+that's\s+too\s+high|i\s+can\s+(?:come|go)\s+down|"
    r"i(?:'m|\s+am)\s+fine\s+with\s+less|happy\s+with\s+whatever)\b",
    re.IGNORECASE,
)

_INT11_EXPLICIT_CONCESSION_RE = re.compile(
    r"\b(?:(?:i\s+would|i'd|i\s+can|i\s+could|i(?:'m|\s+am)\s+willing\s+to|"
    r"i(?:'m|\s+am)\s+happy\s+to)\s+(?:accept|take|settle\s+for)|"
    r"(?:lower|reduce)\s+(?:my\s+)?(?:ask|anchor|range|target)(?:\s+to)?)\s+"
    r"(?:[$€£₹]\s*)?\d+(?:[,.]\d+)?\s*(?:k|thousand|lakh|lakhs|lpa|usd|inr)?\b",
    re.IGNORECASE,
)


def _reconcile_int11_salary_negotiation(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    """Verify a complete negotiation without treating courtesy as apology."""
    if (
        packet.node_id != "int_11_salary_negotiation"
        or packet.attempt_type not in {"independent", "transfer", "pressure"}
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if (
        len(_normalize(answer).split()) < 18
        or _INT11_BACKPEDAL_RE.search(answer)
        or _INT11_EXPLICIT_CONCESSION_RE.search(answer)
    ):
        return result
    sentences = [
        part.strip()
        for part in re.split(r"(?<=[.!?;])\s+", answer)
        if part.strip()
    ]
    anchor = next((
        sentence for sentence in sentences
        if re.search(
            r"(?:[$€£₹]\s*\d[\d,.]*|\b\d+(?:\.\d+)?\s*(?:k|thousand|"
            r"lakh|lakhs|lpa|usd|inr)\b)",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    reason = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:market|scope|experience|value|delivered|improved|reduced|built|"
            r"shipped|operated|reliability|latency|observability|ownership)\w*\b",
            sentence,
            re.IGNORECASE,
        )
        and sentence != anchor
    ), "")
    if not reason and anchor and re.search(
        r"\b(?:market|scope|experience|value|delivered|improved|reduced|built|"
        r"shipped|operated|reliability|latency|observability|ownership)\w*\b",
        anchor,
        re.IGNORECASE,
    ):
        reason = anchor
    flexibility = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:flexible|open\s+to|discuss|explore|consider|trade[- ]?off)\w*\b",
            sentence,
            re.IGNORECASE,
        )
        and re.search(
            r"\b(?:package|total\s+comp(?:ensation)?|bonus|equity|benefits?|"
            r"signing|scope|title|start\s+date|leave|remote)\w*\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    proof = {
        criterion_id: quote[:320]
        for criterion_id, quote in {
            "clear_anchor": anchor,
            "market_or_value_reason": reason,
            "collaborative_flexibility": flexibility,
            "calm_tone": anchor if anchor else reason,
        }.items()
        if quote
    }
    if packet.attempt_type == "transfer":
        if not packet.core_qualified or not flexibility:
            return result
        proof["transfer_context"] = flexibility[:320]
    if packet.attempt_type == "pressure":
        if not packet.core_qualified:
            return result
        core_answer = _normalize(str(packet.core_qualification_evidence.get("learner_answer") or ""))
        evidence_terms = {
            term for term in (
                "market", "scope", "experience", "value", "latency", "reliability",
                "observability", "payments", "payment", "ownership",
            )
            if term in core_answer and term in _normalize(answer)
        }
        if not evidence_terms:
            return result
        proof["core_consistency"] = (reason or anchor)[:320]

    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    if not required_ids.issubset(proof):
        return result
    criteria: list[CriterionEval] = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote,
                "reason": "backend verified a specific, justified anchor with bounded flexibility and no concession",
            })
        criteria.append(row)
    errors = [
        item for item in (result.errors or [])
        if not any(criterion_id in str(item) for criterion_id in required_ids)
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": [
            item for item in (result.required_missing or [])
            if str(item) not in proof
        ],
        "errors": errors,
        "next_focus": "Apply the same anchored negotiation to a different compensation constraint.",
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score),
        "pass_eligible": True,
    })


_GD_STANCE_HEDGES = (
    "maybe",
    "perhaps",
    "not sure",
    "hard to say",
    "both sides",
    "it depends",
    "depends on",
    "i guess",
    "could go either way",
)
_GD_TOPIC_STOPWORDS = {
    "should", "would", "could", "the", "this", "that", "with", "from",
    "have", "being", "companies", "company", "default",
}

_GD_EVIDENCE_MARKERS = (
    "in our ", "on my ", "on our ", "my team", "our team", "pilot", "case study",
    "survey", "audit", "we tracked", "we measured", "the data", "for example",
)
_GD_EVIDENCE_OUTCOMES = (
    "reduced", "increased", "fell", "rose", "cut", "improved", "caught", "missed",
    "excluded", "excluding", "exposed", "prevented", "saved", "grew", "declined",
    "participation", "attrition", "latency", "time", "rate", "qualified candidates",
)
_GD_REBUTTAL_TERMS = (
    "but", "however", "cannot", "can't", "does not", "doesn't", "still", "even if",
    "not enough", "not guarantee", "only", "while",
)
_GD_EVIDENCE_LINK_TERMS = (
    "that evidence", "this evidence", "this shows", "this demonstrates", "this supports",
    "therefore", "which means", "because", "so ", "supports", "shows why",
)
_GD_EVIDENCE_TOKEN_STOPWORDS = _GD_TOPIC_STOPWORDS | {
    "about", "after", "again", "against", "among", "answer", "because", "before",
    "clearly", "discussion", "evidence", "everyone", "final", "human", "necessary",
    "people", "position", "review", "still", "their", "there", "these", "those",
    "using", "while",
}


def _gd_meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in _normalize(text).split()
        if len(token) >= 4 and token not in _GD_EVIDENCE_TOKEN_STOPWORDS
    }


_GD_TOPIC_SIGNAL_GROUPS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "ai_hiring": (
        ("ai", "artificial intelligence", "algorithm", "automated", "automation", "model", "machine learning"),
        ("hiring", "hire", "recruit", "recruiter", "recruiters", "candidate", "candidates", "screening", "shortlist", "selection"),
    ),
    "remote_work": (
        ("remote", "distributed", "virtual", "work from home", "home based"),
        ("work", "worker", "employee", "team", "teams", "office", "workplace", "onboarding"),
    ),
    "four_day_workweek": (
        ("four day", "4 day", "shorter week", "shorter workweek", "compressed week"),
        ("workweek", "work week", "schedule", "shift", "coverage", "working week"),
    ),
    "social_identity": (
        ("social media", "platform", "platforms", "network", "account"),
        ("identity", "verify", "verification", "anonymous", "anonymity", "pseudonym"),
    ),
    "digital_payments": (
        ("digital", "cashless", "online", "mobile", "electronic"),
        ("payment", "payments", "transaction", "transactions", "cash", "wallet"),
    ),
}


def _gd_contains_signal(normalized_text: str, signal: str) -> bool:
    normalized_signal = _normalize(signal)
    return bool(
        normalized_signal
        and f" {normalized_signal} " in f" {normalized_text} "
    )


def _gd_topic_grounded(answer: str, topic: str) -> bool:
    """Require enough semantic topic evidence for deterministic GD credit."""
    if not str(topic or "").strip():
        return False
    family = gd_topic_family(topic)
    normalized_answer = _normalize(answer)
    signal_groups = _GD_TOPIC_SIGNAL_GROUPS.get(family)
    if signal_groups:
        return all(
            any(_gd_contains_signal(normalized_answer, signal) for signal in group)
            for group in signal_groups
        )
    return len(_gd_meaningful_tokens(answer) & _gd_meaningful_tokens(topic)) >= 2


def gd_answer_is_topic_grounded(answer: str, topic: str) -> bool:
    """Public topic-grounding contract shared by graph and rubric gates."""
    return _gd_topic_grounded(answer, topic)


def _gd_topic_partially_grounded(answer: str, topic: str) -> bool:
    """Allow a counter-clause to inherit context only when it retains a topic signal."""
    family = gd_topic_family(topic)
    normalized_answer = _normalize(answer)
    signal_groups = _GD_TOPIC_SIGNAL_GROUPS.get(family)
    if signal_groups:
        return any(
            _gd_contains_signal(normalized_answer, signal)
            for group in signal_groups
            for signal in group
        )
    return bool(_gd_meaningful_tokens(answer) & _gd_meaningful_tokens(topic))


def _gd_topic_is_verifiable(topic: str) -> bool:
    if not str(topic or "").strip():
        return False
    if gd_topic_family(topic) in _GD_TOPIC_SIGNAL_GROUPS:
        return True
    return len(_gd_meaningful_tokens(topic)) >= 2


def _gd_sentence_evidence(answer: str, terms: tuple[str, ...]) -> str:
    for sentence in re.split(r"(?<=[.!?;])\s+", str(answer or "")):
        lowered = sentence.lower()
        if any(term in lowered for term in terms):
            return " ".join(sentence.strip().split())[:320]
    return " ".join(str(answer or "").strip().split())[:320]


def _gd_has_concrete_evidence(answer: str) -> bool:
    lowered = " ".join(str(answer or "").lower().split())
    has_number = bool(re.search(r"\b\d+(?:\.\d+)?%?\b", lowered))
    has_context = any(marker in lowered for marker in _GD_EVIDENCE_MARKERS)
    has_outcome = any(outcome in lowered for outcome in _GD_EVIDENCE_OUTCOMES)
    return has_outcome and (has_number or has_context)


def _reconcile_gd_balanced_view(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        packet.node_id != "gd_06_balanced_view"
        or packet.attempt_type not in {"independent", "transfer", "scaffolded"}
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    lowered = answer.lower()
    topic = packet.active_topic or infer_gd_topic_from_messages(packet.recent_messages)
    if len(_normalize(answer).split()) < 24 or not _gd_topic_grounded(answer, topic):
        return result
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?;])\s+", answer)
        if sentence.strip()
    ]
    supporting = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:benefit|advantage|strongest\s+case\s+for|case\s+for|support|"
            r"improve|broader|access|flexibility|speed|efficiency)\w*\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    opposing = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:concern|risk|strongest\s+case\s+against|case\s+against|opposing|"
            r"drawback|cost|exclude|weaken|slower|riskier|outage)\w*\b",
            sentence,
            re.IGNORECASE,
        )
        and sentence != supporting
    ), "")
    if (
        not opposing
        and supporting
        and re.search(r"\b(?:but|while|whereas|however)\b", supporting, re.IGNORECASE)
        and re.search(
            r"\b(?:concern|risk|drawback|cost|exclude|weaken|slower|riskier|outage)\w*\b",
            supporting,
            re.IGNORECASE,
        )
    ):
        opposing = supporting
    tradeoff = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:trade[- ]?off|on\s+balance|decisive|outweigh|weighing|"
            r"matters\s+more|priority)\w*\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    position = next((
        sentence for sentence in reversed(sentences)
        if re.search(
            r"\b(?:recommend|should|my\s+position|i\s+(?:therefore\s+)?(?:support|oppose|reject)|"
            r"on\s+balance|default\s+only)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    both_sides = " ".join(part for part in (supporting, opposing) if part)
    proof = {
        criterion_id: quote[:320]
        for criterion_id, quote in {
            "names_both_sides": both_sides if supporting and opposing else "",
            "weighs_tradeoff": tradeoff,
            "returns_to_position": position,
            "topic_relevance": supporting or position,
        }.items()
        if quote
    }
    required_base = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required")) and str(criterion["id"]) != "transfer_context"
    }
    existing_met = {row.id for row in result.criteria if row.met}
    if not required_base.issubset(existing_met | set(proof)):
        return result
    criteria: list[CriterionEval] = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote,
                "reason": "backend verified both sides, the decisive trade-off, and a topic-grounded recommendation",
            })
        criteria.append(row)
    met_ids = {row.id for row in criteria if row.met}
    complete = required_base.issubset(met_ids)
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": [
            item for item in (result.required_missing or [])
            if str(item) not in proof
        ],
        "errors": [
            item for item in (result.errors or [])
            if not any(criterion_id in str(item) for criterion_id in required_base)
        ],
        "next_focus": "Apply the same balanced reasoning to a distinct motion.",
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete else result.effective_score,
        "pass_eligible": True if complete else result.pass_eligible,
    })


def _gd_latest_assistant_prompt(packet: EvaluationPacket) -> str:
    for message in reversed(packet.recent_messages or []):
        if str(message.get("role") or "") != "assistant":
            continue
        if packet.node_id and str(message.get("node_id") or "") != packet.node_id:
            continue
        content = " ".join(str(message.get("content") or "").split())
        message_kind = str(message.get("message_kind") or "")
        if message_kind in {"coach_response", "coach_fallback"}:
            return content
        if not message_kind and re.match(
            r"^(?:Transfer\s+(?:task|motion)|Pressure\s+(?:check|motion))\b",
            content,
            re.IGNORECASE,
        ):
            return content
    return ""


def _reconcile_gd_steer_back(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    """Stabilize explicit, topic-grounded GD redirects across evaluator variance."""
    if (
        packet.node_id != "gd_07_steer_back"
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if len(_normalize(answer).split()) < 14 or not _gd_topic_grounded(answer, packet.active_topic):
        return result
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?;])\s+", answer)
        if sentence.strip()
    ]
    drift = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:drifted|off[-\s]?topic|away\s+from|return\s+to|back\s+to|"
            r"actual\s+motion|decision\s+before\s+us)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    redirect = next((
        sentence for sentence in sentences
        if _gd_topic_grounded(sentence, packet.active_topic)
        and re.search(
            r"\b(?:motion|decision|question|topic|return|refocus)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    next_step = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:ask|assess|compare|decide|evidence|examine|identify|measure|test|what|which)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    respectful = "" if re.search(
        r"\b(?:shut\s+up|stop\s+talking|irrelevant|stupid|nonsense|you\s+are\s+wrong)\b",
        answer,
        re.IGNORECASE,
    ) else (redirect or drift)
    proof = {
        criterion_id: quote[:320]
        for criterion_id, quote in {
            "identifies_derailment": drift,
            "redirects_to_topic": redirect,
            "gives_next_step": next_step,
            "non_controlling_tone": respectful,
        }.items()
        if quote
    }
    required_base = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
        and str(criterion["id"]) not in {"transfer_context", "core_consistency"}
    }
    if not required_base.issubset(set(proof)):
        return result
    criteria = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote,
                "reason": "backend verified an explicit topic-grounded redirect and next step",
            })
        criteria.append(row)
    met_ids = {row.id for row in criteria if row.met}
    complete = required_base.issubset(met_ids)
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": [
            item for item in (result.required_missing or [])
            if str(item) not in proof
        ],
        "errors": [
            item for item in (result.errors or [])
            if not any(criterion_id in str(item) for criterion_id in required_base)
        ] if complete else list(result.errors or []),
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete else result.effective_score,
        "pass_eligible": True if complete else result.pass_eligible,
    })


def _reconcile_gd_include_quiet(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    """Stabilize explicit, topic-linked invitations to a quieter participant."""
    if (
        packet.node_id != "gd_08_include_quiet"
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if len(_normalize(answer).split()) < 12 or not _gd_topic_grounded(answer, packet.active_topic):
        return result
    invitation = gd_invitation_clause(
        answer,
        gd_prompt_participant_names(_gd_latest_assistant_prompt(packet)),
    )
    addressed = invitation
    topic_link = invitation if _gd_topic_grounded(invitation, packet.active_topic) else ""
    floor_give = invitation if re.search(
            r"\b(?:share|add|view|take|perspective|thoughts?|hear\s+from|give\s+you\s+the\s+floor)\b",
            invitation,
            re.IGNORECASE,
        ) else ""
    non_pressuring = invitation if re.search(
            r"\b(?:if\s+you(?:'d|\s+would)\s+like|if\s+you\s+want|when\s+you(?:'re|\s+are)\s+ready|"
            r"no\s+pressure|feel\s+free|could\s+you|would\s+you)\b",
            invitation,
            re.IGNORECASE,
        ) else ""
    proof = {
        criterion_id: quote[:320]
        for criterion_id, quote in {
            "names_quiet_participant": addressed,
            "topic_linked_invite": topic_link,
            "respectful_floor_give": floor_give,
            "non_pressuring_tone": non_pressuring,
        }.items()
        if quote
    }
    required_base = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
        and str(criterion["id"]) not in {"transfer_context", "core_consistency"}
    }
    if not required_base.issubset(set(proof)):
        return result
    criteria = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote,
                "reason": "backend verified a direct topic-linked and low-pressure invitation",
            })
        criteria.append(row)
    met_ids = {row.id for row in criteria if row.met}
    complete = required_base.issubset(met_ids)
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": [
            item for item in (result.required_missing or [])
            if str(item) not in proof
        ],
        "errors": [
            item for item in (result.errors or [])
            if not any(criterion_id in str(item) for criterion_id in required_base)
            and not (
                "invitation" in str(item).lower()
                and any(term in str(item).lower() for term in ("topic", "generic", "link"))
            )
        ] if complete else list(result.errors or []),
        "next_focus": (
            "Apply the same topic-linked invitation in a different GD scenario."
            if complete else result.next_focus
        ),
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete else result.effective_score,
        "pass_eligible": True if complete else result.pass_eligible,
    })


_GD_NON_NAME_ADDRESSEE_WORDS = {
    "also", "additionally", "but", "finally", "first", "however", "instead",
    "meanwhile", "next", "perhaps", "please", "second", "still", "therefore",
    "though", "well", "actually", "clearly", "conversely", "generally", "importantly",
    "moreover", "nevertheless", "discussion", "group", "motion", "remote", "topic", "work",
}

_GD_DIRECT_ADDRESSEE_RE = re.compile(
    r"\b((?:[A-Z]\.[A-Z]\.|[^\W\d_][\w'’.-]{1,24}))\s*,",
    re.UNICODE,
)


def gd_prompt_participant_names(prompt: str) -> set[str]:
    return {
        match.group(1).casefold()
        for match in re.finditer(
            r"\b([^\W\d_][\w'’.-]{1,24})\b\s+(?:has\s+not|hasn't|did\s+not|"
            r"says?|argues?|believes?|supports?|opposes?|rejects?|accepts?)\b",
            str(prompt or ""),
            re.UNICODE | re.IGNORECASE,
        )
        if match.group(1)[0].isupper()
    }


def gd_invitation_clause(answer: str, expected_names: set[str] | None = None) -> str:
    for clause in re.split(r"(?<=[.!?;])\s+", str(answer or "")):
        for match in _GD_DIRECT_ADDRESSEE_RE.finditer(clause):
            candidate = match.group(1).strip(".")
            first_letter = next((char for char in candidate if char.isalpha()), "")
            if (
                first_letter.isupper()
                and candidate.casefold() not in _GD_NON_NAME_ADDRESSEE_WORDS
                and (not expected_names or candidate.casefold() in expected_names)
            ):
                return clause.strip()
    return ""


def gd_has_direct_addressee(answer: str) -> bool:
    """Require a real named participant, not a sentence-initial discourse word."""
    return bool(gd_invitation_clause(answer))


def _apply_verified_gd_move(
    packet: EvaluationPacket,
    result: PrepRubricEval,
    proof: dict[str, str],
    *,
    reason: str,
    next_focus: str,
) -> PrepRubricEval:
    required_base = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
        and str(criterion["id"]) not in {"transfer_context", "core_consistency"}
    }
    if not required_base.issubset(set(proof)):
        return result
    criteria = []
    for row in result.criteria:
        quote = proof.get(row.id)
        if quote and not row.met:
            row = row.model_copy(update={
                "met": True,
                "quality": max(float(row.quality or 0.0), 0.76),
                "evidence_quote": quote[:320],
                "reason": reason,
            })
        criteria.append(row)
    met_ids = {row.id for row in criteria if row.met}
    complete = required_base.issubset(met_ids)
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": [
            item for item in (result.required_missing or [])
            if str(item) not in proof
        ],
        "errors": [
            item for item in (result.errors or [])
            if not any(criterion_id in str(item) for criterion_id in required_base)
        ] if complete else list(result.errors or []),
        "next_focus": next_focus if complete else result.next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete else result.effective_score,
        "pass_eligible": True if complete else result.pass_eligible,
    })


def _reconcile_gd_manage_dominator(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        packet.node_id != "gd_09_manage_dominator"
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if len(_normalize(answer).split()) < 14 or not _gd_topic_grounded(answer, packet.active_topic):
        return result
    if gd_has_directed_attack(answer):
        return result
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?;])\s+", answer)
        if sentence.strip()
    ]
    acknowledgement = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:strong|useful|fair|valid|important|appreciate|thank\s+you|good)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    redistribution = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:hear\s+from|bring\s+in|open\s+the\s+floor|another\s+(?:view|voice|participant)|"
            r"other\s+(?:views|voices|participants)|make\s+room|give\s+.+\s+the\s+floor|"
            r"(?:maya|neha|dev|sara|aman|leena|rohit)\s*,?\s*(?:please\s+)?take\s+the\s+floor|"
            r"hear\s+(?:from\s+)?(?:maya|neha|dev|sara|aman|leena|rohit)(?:'s|’s)?\s+(?:view|perspective)|"
            r"give\s+us\s+(?:your|their)\s+(?:view|perspective))\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    topic_link = next((
        sentence for sentence in sentences
        if _gd_topic_grounded(sentence, packet.active_topic)
    ), "")
    proof = {
        criterion_id: quote
        for criterion_id, quote in {
            "acknowledges_contribution": acknowledgement,
            "redistributes_floor": redistribution,
            "topic_link": topic_link,
        }.items()
        if quote
    }
    return _apply_verified_gd_move(
        packet,
        result,
        proof,
        reason="backend verified acknowledgement, a respectful boundary, topic grounding, and floor redistribution",
        next_focus="Apply the same respectful floor-redistribution move under a different GD pressure.",
    )


def _reconcile_gd_drive_consensus(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        packet.node_id != "gd_10_drive_consensus"
        or not result.on_task
        or not result.english
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if len(_normalize(answer).split()) < 18 or not _gd_topic_grounded(answer, packet.active_topic):
        return result
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?;])\s+", answer)
        if sentence.strip()
    ]
    position_sentences = [
        sentence for sentence in sentences
        if re.search(
            r"\b(?:maya|dev|one\s+side|another\s+side|support|oppose|mixed|qualif|"
            r"benefit|risk|case\s+for|case\s+against)\w*\b",
            sentence,
            re.IGNORECASE,
        )
    ]
    has_two_positions = _gd10_has_distinct_positions(
        answer,
        _gd_latest_assistant_prompt(packet),
    )
    summary = " ".join(position_sentences[:2]) if has_two_positions else ""
    common_ground = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:common\s+ground|both\s+(?:agree|need|want)|shared|we\s+agree|"
            r"reliable\s+evidence|decision\s+standard)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    next_step = next((
        sentence for sentence in sentences
        if re.search(
            r"\b(?:propose|recommend|should|let(?:'s|\s+us)|next\s+step|decision\s+rule|"
            r"threshold|pilot|test|measure|review)\b",
            sentence,
            re.IGNORECASE,
        )
    ), "")
    balanced = answer if has_two_positions and re.search(
        r"\b(?:maya|dev|group|both|we|one\s+side|other)\b",
        answer,
        re.IGNORECASE,
    ) else ""
    proof = {
        criterion_id: quote
        for criterion_id, quote in {
            "summarizes_key_points": summary,
            "identifies_common_ground": common_ground,
            "proposes_next_step": next_step,
            "balanced_credit": balanced,
        }.items()
        if quote
    }
    return _apply_verified_gd_move(
        packet,
        result,
        proof,
        reason="backend verified two credited positions, common ground, and a concrete consensus move",
        next_focus="Apply the same evidence-led synthesis to a different GD motion.",
    )


def _reconcile_shared_gd_transfer(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        not packet.node_id.startswith("gd_")
        or packet.attempt_type != "transfer"
        or not packet.core_qualified
    ):
        return result
    core_topic = str(packet.core_qualification_evidence.get("active_topic") or "")
    active_topic = str(packet.active_topic or "")
    if (
        not core_topic
        or not active_topic
        or gd_topic_family(core_topic) == gd_topic_family(active_topic)
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not _gd_topic_grounded(answer, active_topic):
        return result
    rows_by_id = {row.id: row for row in result.criteria}
    transfer_row = rows_by_id.get("transfer_context")
    if transfer_row is None or transfer_row.met:
        return result
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    updated_row = transfer_row.model_copy(update={
        "met": True,
        "quality": max(float(transfer_row.quality or 0.0), 0.75),
        "evidence_quote": first_sentence[:320],
        "reason": "backend verified a different GD topic family with explicit active-topic content",
    })
    criteria = [
        updated_row if row.id == "transfer_context" else row
        for row in result.criteria
    ]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) != "transfer_context"
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = [
        item for item in (result.errors or [])
        if "transfer_context" not in str(item)
    ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_shared_gd_pressure(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if (
        not packet.node_id.startswith("gd_")
        or packet.node_id == "gd_02_support_with_evidence"
        or packet.attempt_type != "pressure"
        or not packet.core_qualified
    ):
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    lowered = answer.lower()
    prompt = _gd_latest_assistant_prompt(packet)
    prompt_overlap = _gd_meaningful_tokens(answer) & _gd_meaningful_tokens(prompt)
    direct_marker = any(marker in lowered for marker in (
        "you are right",
        "you're right",
        "the new implication",
        "the distinction",
        "to answer that",
        "i used your point",
        "i agree that",
        "but ",
        "however",
    ))
    direct_response = direct_marker and len(prompt_overlap) >= 1
    causal = any(marker in lowered for marker in (
        " because ",
        " unless ",
        " so ",
        " therefore",
        " which ",
        " those safeguards",
        " that means",
    ))
    concrete_reason = (
        len(_normalize(answer).split()) >= 24
        and causal
        and (
            "," in answer
            or any(marker in lowered for marker in (
                "audit",
                "onboarding",
                "ownership",
                "threshold",
                "appeal",
                "safeguard",
                "mitigation",
                "review",
                "decision",
            ))
        )
    )
    qualified_answer = str(packet.core_qualification_evidence.get("learner_answer") or "")
    core_overlap = _gd_meaningful_tokens(answer) & _gd_meaningful_tokens(qualified_answer)
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    proof: dict[str, str] = {}
    if direct_response:
        proof["pressure_response"] = first_sentence[:320]
    if concrete_reason:
        proof["evidence_defense"] = _gd_sentence_evidence(
            answer,
            ("because", "unless", "so ", "therefore", "which", "safeguard"),
        )
    if not proof:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected a direct GD pressure response with a concrete, core-consistent reason",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = list(result.errors or [])
    if complete_required:
        errors = [
            item for item in errors
            if not any(criterion_id in str(item) for criterion_id in required_ids)
        ]
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_gd_evidence(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    if packet.node_id != "gd_02_support_with_evidence":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    lowered = answer.lower()
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0]
    stance = bool(re.search(
        r"(?:\bi\s+(?:support|oppose|believe|agree|disagree)\b|\bshould\b|\bmust\b|"
        r"\bonly\s+as\b|\bnever\s+as\b|\bcannot\b|\bcan't\b)",
        lowered,
    ))
    evidence_sentence = _gd_sentence_evidence(
        answer,
        _GD_EVIDENCE_MARKERS + _GD_EVIDENCE_OUTCOMES,
    )
    concrete = _gd_has_concrete_evidence(answer)
    linked = any(term in lowered for term in _GD_EVIDENCE_LINK_TERMS)
    prompt = _gd_latest_assistant_prompt(packet)
    topic_reference = packet.active_topic or prompt
    evidence_topic = topic_reference
    if packet.attempt_type == "pressure" and packet.core_qualified:
        qualified_topic = str(packet.core_qualification_evidence.get("active_topic") or "")
        evidence_topic = qualified_topic
        topic_relevant = bool(
            _gd_topic_is_verifiable(qualified_topic)
            and _gd_topic_grounded(answer, qualified_topic)
        )
    else:
        topic_relevant = _gd_topic_grounded(answer, topic_reference)
    concrete = bool(concrete and _gd_topic_grounded(evidence_sentence, evidence_topic))
    proof: dict[str, str] = {}

    if packet.attempt_type == "pressure" and packet.core_qualified:
        direct_rebuttal = any(term in lowered for term in _GD_REBUTTAL_TERMS)
        prompt_lower = _normalize(prompt)
        if "correlation" in prompt_lower or "causation" in prompt_lower:
            pressure_grounded = bool(re.search(
                r"\b(?:caus|correlat|mechanism|confound|control\s+group|before\s+and\s+after|"
                r"comparison|counterfactual)\w*\b",
                answer,
                re.IGNORECASE,
            ))
        else:
            challenge_tokens = (
                _gd_meaningful_tokens(prompt)
                - _gd_meaningful_tokens(packet.active_topic)
            )
            pressure_grounded = False
        if direct_rebuttal and topic_relevant and pressure_grounded:
            proof["pressure_response"] = first_sentence[:320]
        if concrete and linked:
            proof["evidence_defense"] = _gd_sentence_evidence(
                answer,
                _GD_EVIDENCE_MARKERS + _GD_EVIDENCE_OUTCOMES,
            )
    else:
        if stance:
            proof["clear_stance"] = first_sentence[:320]
        if concrete:
            proof["concrete_evidence"] = evidence_sentence
        if topic_relevant:
            proof["topic_relevance"] = first_sentence[:320]
        if concrete and linked:
            proof["evidence_link"] = _gd_sentence_evidence(answer, _GD_EVIDENCE_LINK_TERMS)

    if not proof:
        return result
    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected explicit learner-owned GD evidence and claim linkage",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or []) if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = list(result.errors or [])
    next_focus = result.next_focus
    if complete_required:
        errors = [
            item for item in errors
            if "missing required rubric proof" not in str(item).lower()
        ]
        if any(term in str(next_focus or "").lower() for term in ("explain the link", "link between", "evidence link")):
            next_focus = "Defend the same evidence against one new counterargument without changing the claim."
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


_GD_ENTRY_OPENERS = (
    "building on ",
    "to build on ",
    "adding to ",
    "to add to ",
    "picking up on ",
    "following that point",
    "just to add",
    "if i may add",
    "i'd like to add",
    "i would like to add",
)

_GD_AGGRESSIVE_ENTRY_MARKERS = (
    "shut up",
    "let me finish",
    "you're wrong",
    "you are wrong",
    "that is nonsense",
    "obviously you",
)


def _reconcile_gd_take_floor(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    if packet.node_id != "gd_03_take_the_floor":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    lowered = answer.lower()
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    polite_entry = any(lowered.startswith(opener) for opener in _GD_ENTRY_OPENERS)
    prompt = _gd_latest_assistant_prompt(packet)
    prior_overlap = _gd_meaningful_tokens(answer) & _gd_meaningful_tokens(prompt)
    links_prior = polite_entry and len(prior_overlap) >= 2
    extension_text = answer.split(",", 1)[1].strip() if polite_entry and "," in answer else answer
    topic_reference = packet.active_topic or prompt
    extension_grounded = _gd_topic_grounded(extension_text, topic_reference)
    word_count = len(_normalize(answer).split())
    adds_value = (
        word_count >= 18
        and extension_grounded
        and any(marker in lowered for marker in (
            " because ",
            " that matters",
            " which means",
            " improves ",
            " lets ",
            " risk ",
            " only if ",
        ))
    )
    assertive_not_rude = (
        polite_entry
        and adds_value
        and not any(marker in lowered for marker in _GD_AGGRESSIVE_ENTRY_MARKERS)
        and not lowered.endswith("can i speak?")
    )
    proof: dict[str, str] = {}
    if polite_entry:
        proof["polite_entry_phrase"] = first_sentence[:320]
    if links_prior:
        proof["links_prior_point"] = first_sentence[:320]
    if adds_value:
        proof["adds_new_value"] = _gd_sentence_evidence(
            answer,
            ("because", "that matters", "which means", "improves", "lets", "only if"),
        )
    if assertive_not_rude:
        proof["assertive_not_rude"] = first_sentence[:320]
    if not proof:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected a linked, substantive, non-aggressive GD entry",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = list(result.errors or [])
    next_focus = result.next_focus
    if complete_required:
        errors = [
            item for item in errors
            if not any(term in str(item).lower() for term in (
                "assertive",
                "claiming space",
                "entry phrase",
                "prior point",
            ))
        ]
        next_focus = (
            "Enter a second discussion by linking a different prior point and adding one new implication."
        )
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_gd_build_on(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    if packet.node_id != "gd_04_build_on_others":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    lowered = answer.lower()
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    credits_prior = bool(re.match(
        r"(?:building on|adding to|to build on|picking up on|following)\s+(?:your|that|the)\s+"
        r"(?:point|idea|concern)|as\s+.{1,50}\s+(?:said|mentioned)|"
        r"i agree with\s+(?:your|that|the)\s+(?:point|idea)",
        lowered,
    ))
    prompt = _gd_latest_assistant_prompt(packet)
    topic_reference = packet.active_topic or prompt
    extension_text = answer.split(",", 1)[1].strip() if credits_prior and "," in answer else answer
    extension_grounded = _gd_topic_grounded(extension_text, topic_reference)
    word_count = len(_normalize(answer).split())
    extends_idea = (
        word_count >= 20
        and extension_grounded
        and any(marker in lowered for marker in (
            "i would add",
            "i'd add",
            "it also",
            "another implication",
            "which can",
            "which means",
            "but ",
            "so ",
        ))
    )
    topic_reference = prompt or packet.active_topic
    topic_overlap = _gd_meaningful_tokens(answer) & _gd_meaningful_tokens(topic_reference)
    topic_relevant = len(topic_overlap) >= 2 if topic_reference else False
    collaborative = (
        credits_prior
        and not any(marker in lowered for marker in _GD_AGGRESSIVE_ENTRY_MARKERS)
    )
    proof: dict[str, str] = {}
    if credits_prior:
        proof["credits_prior_speaker"] = first_sentence[:320]
    if extends_idea:
        proof["extends_idea"] = _gd_sentence_evidence(
            answer,
            ("i would add", "i'd add", "it also", "another implication", "which", "but", "so"),
        )
    if topic_relevant:
        proof["topic_relevance"] = first_sentence[:320]
    if collaborative:
        proof["collaborative_tone"] = first_sentence[:320]
    if not proof:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected explicit prior-point credit and a distinct collaborative extension",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = list(result.errors or [])
    next_focus = result.next_focus
    if complete_required:
        errors = [
            item for item in errors
            if not any(term in str(item).lower() for term in (
                "credits_prior_speaker",
                "prior speaker",
                "prior point",
                "extend",
            ))
        ]
        next_focus = "Credit and extend a different participant's point under transfer or pressure."
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _reconcile_gd_respectful_disagreement(
    packet: EvaluationPacket,
    result: PrepRubricEval,
) -> PrepRubricEval:
    if packet.node_id != "gd_05_disagree_respectfully":
        return result
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return result
    prompt = _gd_latest_assistant_prompt(packet)
    topic_reference = packet.active_topic or prompt
    if not _gd_topic_grounded(answer, topic_reference):
        return result
    lowered = answer.lower()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip()]
    first_sentence = sentences[0] if sentences else answer
    counter_match = re.search(
        r"\b(?:however|but|yet|i do not think|i don't think|i disagree|that does not|that doesn't)\b[,:]?\s*(.+)",
        answer,
        re.IGNORECASE,
    )
    counter_sentence = (
        counter_match.group(1).strip()
        if counter_match
        else sentences[1]
        if len(sentences) > 1
        else answer
    )
    counter_grounded = bool(
        _gd_topic_grounded(counter_sentence, topic_reference)
        or (
            _gd_topic_grounded(answer, topic_reference)
            and _gd_topic_partially_grounded(counter_sentence, topic_reference)
            and re.search(r"\b(?:it|that|this|they|these|those)\b", counter_sentence, re.IGNORECASE)
        )
    )
    acknowledges = any(marker in lowered for marker in (
        "i agree that",
        "i agree with",
        "i understand that",
        "it is fair that",
        "that's a valid",
        "that is a valid",
        "has merit",
        "is a real benefit",
        "can help",
    ))
    clear_counter = bool(counter_match and counter_grounded)
    reasoned = (
        clear_counter
        and any(marker in lowered for marker in (
            " because ",
            " since ",
            " so ",
            "can encode",
            "at scale",
            "historical",
            "which means",
        ))
        and len(_normalize(answer).split()) >= 20
    )
    personal_attack = any(marker in lowered for marker in (
        "you are wrong",
        "you're wrong",
        "your idea is stupid",
        "that idea is nonsense",
        "only an idiot",
        "shut up",
    ))
    civil = acknowledges and clear_counter and not personal_attack
    proof: dict[str, str] = {}
    if acknowledges:
        proof["acknowledges_valid_point"] = first_sentence[:320]
    if clear_counter:
        proof["clear_counter"] = counter_sentence[:320]
    if reasoned:
        proof["reasoned_basis"] = _gd_sentence_evidence(
            answer,
            ("because", "since", "so ", "can encode", "at scale", "historical", "which means"),
        )
    if civil:
        proof["civil_tone"] = first_sentence[:320]
    if not proof:
        return result

    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected an explicit concession, clear counterpoint, and civil topic-based reason",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    required_ids = {
        str(criterion["id"])
        for criterion in packet.criteria
        if bool(criterion.get("required"))
    }
    met_ids = {row.id for row in criteria if row.met}
    complete_required = required_ids.issubset(met_ids)
    errors = list(result.errors or [])
    next_focus = result.next_focus
    if complete_required:
        errors = [
            item for item in errors
            if not any(criterion_id in str(item) for criterion_id in required_ids)
        ]
        next_focus = "Disagree respectfully on a different motion, then handle one pressure response."
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
        "effective_score": max(float(result.effective_score or result.raw_score), packet.pass_score)
        if complete_required
        else result.effective_score,
        "pass_eligible": True if complete_required else result.pass_eligible,
    })


def _gd_stance_proof(packet: EvaluationPacket) -> dict[str, str]:
    if packet.node_id != "gd_01_stake_position":
        return {}
    answer = " ".join(str(packet.learner_answer or "").split()).strip()
    if not answer:
        return {}
    first_sentence = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0].strip()
    first_lower = first_sentence.lower()
    commitment = bool(re.search(
        r"(?:\bi\s+(?:firmly\s+)?(?:support|oppose|believe|agree|disagree)\b|"
        r"\bmy position is\b|\b(?:should|must|need to)\b)",
        first_lower,
    ))
    hedged = any(phrase in answer.lower() for phrase in _GD_STANCE_HEDGES)
    starts_with_hedge = any(
        first_lower.startswith(prefix)
        for prefix in ("maybe ", "perhaps ", "i am not sure", "i'm not sure", "it depends")
    )
    clear_commitment = commitment and not starts_with_hedge
    topic_relevant = _gd_topic_grounded(answer, packet.active_topic)
    sentence_count = len([part for part in re.split(r"[.!?]+", answer) if part.strip()])
    concise = clear_commitment and sentence_count <= 2 and len(answer.split()) <= 80
    proof: dict[str, str] = {}
    if clear_commitment:
        proof["clear_stance"] = first_sentence
    if topic_relevant:
        proof["topic_relevance"] = first_sentence
    if clear_commitment and not hedged:
        proof["low_hedging"] = first_sentence
    if concise:
        proof["concise_opening"] = first_sentence
    return proof


def _reconcile_gd_stance_evidence(packet: EvaluationPacket, result: PrepRubricEval) -> PrepRubricEval:
    proof = _gd_stance_proof(packet)
    if not proof:
        return result
    rows_by_id = {row.id: row for row in result.criteria}
    updates: dict[str, CriterionEval] = {}
    for criterion_id, evidence in proof.items():
        row = rows_by_id.get(criterion_id)
        if row is None or row.met:
            continue
        updates[criterion_id] = row.model_copy(update={
            "met": True,
            "quality": max(float(row.quality or 0.0), 0.75),
            "evidence_quote": evidence,
            "reason": "backend detected a position-first stance without actual hedging language",
        })
    criteria = [updates.get(row.id, row) for row in result.criteria]
    required_missing = [
        item for item in (result.required_missing or [])
        if str(item) not in proof
    ]
    complete_required = {"clear_stance", "topic_relevance", "low_hedging"}.issubset(proof)
    errors = list(result.errors or [])
    next_focus = result.next_focus
    if complete_required:
        errors = [
            item for item in errors
            if not any(term in str(item).lower() for term in ("hedg", "caveat", "avoid but", "clear stance"))
        ]
        if any(term in str(next_focus or "").lower() for term in ("hedg", "caveat", "avoid but", "state the position again")):
            next_focus = "Pressure-test the same position against one concrete objection without changing sides."
    return result.model_copy(update={
        "criteria": criteria,
        "required_missing": required_missing,
        "errors": errors,
        "next_focus": next_focus,
    })


def _has_complete_gd_stance_shape(packet: EvaluationPacket) -> bool:
    return {"clear_stance", "topic_relevance", "low_hedging"}.issubset(_gd_stance_proof(packet))


def _has_complete_pitch_shape(packet: EvaluationPacket) -> bool:
    if packet.node_id != "int_01_elevator_pitch":
        return False
    answer = str(packet.learner_answer or "")
    return (
        _has_pitch_identity(answer)
        and _has_concrete_pitch_detail(answer)
        and _answer_has_any(answer, _PITCH_DIRECTION_TERMS)
    )


_INT09_DIRECTED_ATTACK_RE = re.compile(
    r"\b(?:you(?:\s+do\s+not|\s+don't)\s+understand|you\s+are\s+wrong|you're\s+wrong|"
    r"your\s+idea\s+is\s+(?:stupid|ridiculous)|that\s+is\s+(?:nonsense|ridiculous)|"
    r"only\s+an?\s+idiot|shut\s+up|anyone\s+who\s+thinks\s+otherwise\s+is\s+reckless)\b",
    re.IGNORECASE,
)


def _answers_near_duplicate(first: str, second: str) -> bool:
    first_tokens = set(_normalize(first).split())
    second_tokens = set(_normalize(second).split())
    if not first_tokens or not second_tokens:
        return False
    overlap = len(first_tokens & second_tokens) / max(1, len(first_tokens | second_tokens))
    containment = len(first_tokens & second_tokens) / max(1, min(len(first_tokens), len(second_tokens)))
    return overlap >= 0.8 or containment >= 0.9


def _int10_closing_missing(answer: str, active_role: str = "") -> dict[str, str]:
    role_tokens = {
        token
        for token in _normalize(active_role).split()
        if len(token) >= 4 and token not in {"role", "engineer", "manager"}
    }
    role_pattern = "|".join(re.escape(token) for token in sorted(role_tokens))
    question_context = r"\b(?:role|team|position)\b"
    if role_pattern:
        question_context = rf"(?:{question_context}|\b(?:{role_pattern})\b)"
    questions = [part.strip() for part in re.findall(r"[^?]+\?", answer) if part.strip()]
    specific_question = next((
        question for question in questions
        if re.search(
            r"\b(?:success|priorit|time|first\s+(?:90|ninety)\s+days|"
            r"first\s+six\s+months|challenge|ownership|collaboration|reliability)\w*\b",
            question,
            re.IGNORECASE,
        )
        and re.search(question_context, question, re.IGNORECASE)
        and not re.search(r"\b(?:benefits?|vacation|leave\s+policy|feedback\s+for\s+me)\b", question, re.IGNORECASE)
    ), "")
    statements = [part.strip() for part in re.split(r"(?<=[.!?])\s+", answer) if part.strip() and "?" not in part]
    fit_statement = next((
        statement for statement in statements
        if re.search(r"\bI\b", statement)
        and re.search(r"\b(?:bring|contribute|add|built|led|improved|delivered|owned|reduced|designed)\w*\b", statement, re.IGNORECASE)
        and re.search(
            r"\b(?:backend|platform|production|reliability|incident|systems?|api|data|"
            r"security|scal|automation|delivery|collaboration|customer|latency|"
            r"quota|revenue|enterprise|sales|operations|strategy|leadership)\w*\b"
            + (rf"|\b(?:{role_pattern})\b" if role_pattern else ""),
            statement,
            re.IGNORECASE,
        )
    ), "")
    missing: dict[str, str] = {}
    if not specific_question:
        missing["specific_closing_question"] = "minimum gate requires one substantive role, team, success, or priorities question"
        missing["role_relevance"] = "minimum gate requires a role-relevant closing question"
        missing["non_generic"] = "minimum gate rejects feedback-only, benefits-only, or generic closing questions"
    if not fit_statement:
        missing["role_fit_evidence"] = "minimum gate requires a separate first-person statement of specific value"
        missing["professional_close"] = "minimum gate requires both the substantive question and a specific fit statement"
    return missing


_INTERVIEW_TRANSFER_MARKER_GROUPS: dict[str, tuple[tuple[str, ...], ...]] = {
    "int_02_strength_with_evidence": (("stakeholder", "client", "partner"), ("communicat", "explain", "align")),
    "int_03_weakness_framing": (("estimat", "forecast"), ("ambigu", "uncertain", "unknown")),
    "int_05_why_this_role": (("company", "product", "engineering", "strategy"), ("contribut", "fit", "experience", "work")),
    "int_06_own_a_failure": (("constraint", "limited", "without", "unavailable", "deadline", "access", "budget", "time"), ("response", "workaround", "adjust", "priorit", "scope")),
    "int_07_clarify_ambiguous": (("onboarding", "reliability", "retention"), ("product", "improv")),
    "int_08_quantify_impact": (("customer", "operational", "team"), ("baseline", "metric", "result", "outcome")),
    "int_09_diplomatic_pushback": (("alone", "individual"), ("team", "collaborat")),
    "int_10_close_strong": (("platform",), ("reliability",)),
    "int_11_salary_negotiation": (("bonus", "equity"), ("fixed", "package", "total value")),
    "int_12_explain_a_gap": (("plateau", "stagnat"), ("growth", "learn", "next")),
}


def _has_assigned_interview_transfer_context(node_id: str, answer: str) -> bool:
    groups = _INTERVIEW_TRANSFER_MARKER_GROUPS.get(node_id)
    if not groups:
        return True
    lowered = _normalize(answer)
    return all(any(marker in lowered for marker in group) for group in groups)


def _gd_stance_polarity(text: str) -> str:
    lowered = " ".join(str(text or "").lower().split())
    negative = bool(re.search(r"\b(?:oppose|against|should\s+(?:not|never)|must\s+not|reject)\b", lowered))
    positive = bool(re.search(r"\b(?:support|in\s+favou?r|should\s+be|must\s+be|agree\s+with)\b", lowered))
    if positive and not negative:
        return "positive"
    if negative and not positive:
        return "negative"
    return ""


def _gd08_invite_missing(answer: str, active_topic: str, prompt: str = "") -> dict[str, str]:
    invitation = gd_invitation_clause(answer, gd_prompt_participant_names(prompt))
    addressed = bool(invitation)
    floor_give = bool(re.search(
        r"\b(?:share|add|view|take|perspective|thoughts?|hear\s+from|give\s+you\s+the\s+floor)\b",
        invitation,
        re.IGNORECASE,
    ))
    optional = bool(re.search(
        r"\b(?:if\s+you(?:'d|\s+would)?\s*(?:like|want|feel\s+comfortable)|"
        r"if\s+you\s+are\s+comfortable|when\s+you(?:'re|\s+are)\s+ready|"
        r"feel\s+free|could\s+you|would\s+you)\b",
        invitation,
        re.IGNORECASE,
    ))
    coercive = bool(re.search(
        r"\b(?:must|have\s+to|right\s+now|everyone\s+needs\s+to)\b",
        invitation,
        re.IGNORECASE,
    ))
    missing: dict[str, str] = {}
    if not addressed:
        missing["names_quiet_participant"] = "minimum gate requires directly addressing one quiet participant"
    if not _gd_topic_grounded(invitation, active_topic):
        missing["topic_linked_invite"] = "minimum gate requires linking the invitation to the active motion"
    if not floor_give:
        missing["respectful_floor_give"] = "minimum gate requires a clear invitation or floor handoff"
    if not optional or coercive:
        missing["non_pressuring_tone"] = "minimum gate requires an optional, non-coercive invitation"
    return missing


def _gd10_has_distinct_positions(answer: str, prompt: str = "") -> bool:
    expected_names = gd_prompt_participant_names(prompt)
    affirmative_re = re.compile(
        r"\b(?:support|in\s+favou?r|benefit|advantage|case\s+for|accept|adopt(?:\s+now)?)\w*\b",
        re.IGNORECASE,
    )
    counter_re = re.compile(
        r"\b(?:oppose|against|risk\s+(?:remains|outweighs)|concern\s+remains|"
        r"mixed|too\s+mixed|qualif|case\s+against|reject|do(?:es)?\s+not\s+support|"
        r"wait\s+for|stronger\s+evidence)\w*\b",
        re.IGNORECASE,
    )
    clauses = [
        clause.strip(" ,")
        for clause in re.split(
            r"(?<=[.!?;])\s+|\b(?:while|whereas|but|however)\b",
            answer,
            flags=re.IGNORECASE,
        )
        if clause.strip(" ,")
    ]
    rows: list[tuple[str, str]] = []
    generic_speaker_re = re.compile(
        r"\b(?:one\s+side|one\s+participant|the\s+other\s+side|another\s+participant)\b",
        re.IGNORECASE,
    )
    excluded_names = {"I", "We", "The", "This", "That", "However", "While", "Whereas", "But"}
    for clause in clauses:
        generic = generic_speaker_re.search(clause)
        if generic:
            speaker = _normalize(generic.group(0))
        else:
            named = re.search(
                r"\b([^\W\d_][\w'’.-]{1,24})\b\s+(?:argues?|says?|believes?|supports?|"
                r"opposes?|accepts?|rejects?|would\s+(?:adopt|wait|accept|reject))\b",
                clause,
                re.UNICODE | re.IGNORECASE,
            )
            if not named or not named.group(1)[0].isupper() or named.group(1) in excluded_names:
                continue
            speaker = named.group(1).casefold()
            if expected_names and speaker not in expected_names:
                continue
            if not expected_names and speaker not in {"maya", "dev"}:
                continue
        rows.append((speaker, clause))
    support_rows = [(speaker, row) for speaker, row in rows if affirmative_re.search(row)]
    counter_rows = [
        (speaker, row) for speaker, row in rows
        if counter_re.search(row) and not affirmative_re.search(row)
    ]
    return any(
        support_speaker != counter_speaker
        for support_speaker, _ in support_rows
        for counter_speaker, _ in counter_rows
    )


def _minimum_gate_missing(packet: EvaluationPacket) -> dict[str, str]:
    answer = str(packet.learner_answer or "")
    tone_missing = (
        {
            "collaborative_tone": (
                "diplomatic pushback cannot include a directed personal attack"
            )
        }
        if packet.node_id == "int_09_diplomatic_pushback"
        and _INT09_DIRECTED_ATTACK_RE.search(answer)
        else {}
    )
    if packet.node_id == "int_10_close_strong":
        tone_missing.update(_int10_closing_missing(answer, packet.active_topic))
    if packet.node_id == "gd_08_include_quiet":
        tone_missing.update(_gd08_invite_missing(
            answer,
            packet.active_topic,
            _gd_latest_assistant_prompt(packet),
        ))
    if packet.node_id == "gd_09_manage_dominator" and gd_has_directed_attack(answer):
        tone_missing["respectful_boundary"] = "minimum gate rejects a directed personal attack"
    if packet.node_id == "gd_10_drive_consensus" and not _gd10_has_distinct_positions(
        answer,
        _gd_latest_assistant_prompt(packet),
    ):
        tone_missing["summarizes_key_points"] = "minimum gate requires two genuinely different positions"
    if packet.attempt_type == "transfer":
        if (
            not packet.core_qualified
            or not str(packet.core_qualification_evidence.get("learner_answer") or "").strip()
        ):
            return {
                **tone_missing,
                "transfer_context": (
                    "transfer requires the actual qualified independent learner answer"
                )
            }
        if not packet.node_id.startswith("gd_"):
            core_answer = str(packet.core_qualification_evidence.get("learner_answer") or "")
            if _answers_near_duplicate(core_answer, answer):
                return {
                    **tone_missing,
                    "transfer_context": "transfer requires a meaningfully different answer for the newly assigned context",
                }
            if not _has_assigned_interview_transfer_context(packet.node_id, answer):
                return {
                    **tone_missing,
                    "transfer_context": "transfer answer does not address the newly assigned scenario",
                }
            return tone_missing
        core_topic = str(packet.core_qualification_evidence.get("active_topic") or "")
        if (
            not _gd_topic_is_verifiable(core_topic)
            or not _gd_topic_is_verifiable(packet.active_topic)
            or gd_topic_family(core_topic) == gd_topic_family(packet.active_topic)
        ):
            logger.warning(
                "rejecting GD transfer topic evidence node=%s core=%r core_family=%s active=%r active_family=%s",
                packet.node_id,
                core_topic,
                gd_topic_family(core_topic),
                packet.active_topic,
                gd_topic_family(packet.active_topic),
            )
            return {
                **tone_missing,
                "transfer_context": (
                    "transfer requires verifiable, meaningfully different GD topic families for the core and active prompts"
                )
            }
        return tone_missing
    if packet.attempt_type == "pressure" and not packet.core_qualified:
        return {
            **tone_missing,
            "core_consistency": (
                "pressure requires a valid qualified independent learner answer"
            )
        }
    if (
        packet.attempt_type == "pressure"
        and not str(packet.core_qualification_evidence.get("learner_answer") or "").strip()
    ):
        return {
            **tone_missing,
            "core_consistency": (
                "pressure consistency requires the actual qualified independent learner answer"
            )
        }
    if packet.attempt_type == "pressure":
        core_answer = str(packet.core_qualification_evidence.get("learner_answer") or "")
        if (
            packet.node_id.startswith("gd_")
            and _gd_stance_polarity(core_answer)
            and _gd_stance_polarity(answer)
            and _gd_stance_polarity(core_answer) != _gd_stance_polarity(answer)
        ):
            return {
                **tone_missing,
                "core_consistency": "pressure response explicitly reverses the qualified stance",
            }
        return tone_missing
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
    return tone_missing


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


def _is_evaluator_omission(row: CriterionEval | None) -> bool:
    return bool(
        row is not None
        and not row.met
        and row.reason == "criterion missing from evaluator output"
    )


def _pitch_next_focus(required_missing: list[str]) -> str:
    focus_by_criterion = {
        "answers_question": "State the current role or professional identity directly.",
        "specific_detail": "Add one concrete role-relevant proof detail.",
        "pitch_structure": "Complete the role, proof, and future-direction structure.",
        "future_goal": "State the future direction for the role.",
    }
    for criterion_id in required_missing:
        if criterion_id in focus_by_criterion:
            return focus_by_criterion[criterion_id]
    return "Pressure-test delivery with a concise follow-up or transfer version of the pitch."


def apply_caps(packet: EvaluationPacket, raw: PrepRubricEval | RubricResult | dict) -> RubricResult:
    """Apply configured caps and eligibility rules to a semantic LLM eval."""
    normalized = _reconcile_gd_evidence(
        packet,
        _reconcile_shared_gd_transfer(
            packet,
            _reconcile_shared_gd_pressure(
                packet,
                _reconcile_gd_drive_consensus(
                    packet,
                    _reconcile_gd_manage_dominator(
                        packet,
                        _reconcile_gd_include_quiet(
                            packet,
                            _reconcile_gd_steer_back(
                                packet,
                                _reconcile_gd_respectful_disagreement(
                                    packet,
                                    _reconcile_gd_balanced_view(
                                        packet,
                                        _reconcile_gd_build_on(
                                            packet,
                                            _reconcile_gd_take_floor(
                                                packet,
                                                _reconcile_gd_stance_evidence(
                                                    packet,
                                                    _reconcile_clarification_evidence(
                                                        packet,
                                                        _reconcile_int07_pressure_response(
                                                            packet,
                                                            _reconcile_failure_pressure_response(
                                                                packet,
                                                                _reconcile_weakness_evidence(
                                                                    packet,
                                                                    _reconcile_pitch_evidence(
                                                                        packet,
                                                                        _reconcile_int08_quantified_impact(
                                                                            packet,
                                                                            _reconcile_int09_diplomatic_pushback(
                                                                                packet,
                                                                                _reconcile_int11_salary_negotiation(
                                                                                    packet,
                                                                                    validate_llm_eval(raw, packet),
                                                                                ),
                                                                            ),
                                                                        ),
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    minimum_missing = _minimum_gate_missing(packet)
    normalized = _apply_minimum_gate_to_rows(normalized, minimum_missing)
    effective = float(normalized.effective_score or normalized.raw_score)
    required_missing: list[str] = []
    evaluator_incomplete: list[str] = []
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

        if required and missing and _is_evaluator_omission(row):
            evaluator_incomplete.append(criterion_id)
            cap = float(criterion.get("missing_cap") or packet.pass_score)
            effective = min(effective, cap)
            blockers.append(f"evaluator_incomplete:{criterion_id}")
            continue

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
    if evaluator_incomplete:
        errors = [
            item
            for item in errors
            if not (
                "missing required rubric proof" in str(item).lower()
                and any(key in str(item) for key in evaluator_incomplete)
            )
        ]
        errors.append(
            "evaluator incomplete for required rubric criteria: "
            + ", ".join(evaluator_incomplete)
        )

    complete_pitch_shape = _has_complete_pitch_shape(packet) and not required_missing
    complete_weakness_shape = _has_complete_weakness_shape(packet) and not required_missing
    complete_gd_stance_shape = _has_complete_gd_stance_shape(packet) and not required_missing
    if complete_pitch_shape:
        effective = max(effective, packet.pass_score)
    if complete_weakness_shape:
        effective = max(effective, packet.pass_score)
    if complete_gd_stance_shape:
        effective = max(effective, packet.pass_score)

    effective = round(max(0.0, min(1.0, effective)), 4)
    pass_eligible = (
        (
            bool(normalized.pass_eligible)
            or complete_pitch_shape
            or complete_weakness_shape
            or complete_gd_stance_shape
        )
        and not required_missing
        and not evaluator_incomplete
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
    next_focus = normalized.next_focus
    if evaluator_incomplete:
        next_focus = ""
    elif packet.node_id == "int_01_elevator_pitch":
        next_focus = _pitch_next_focus(required_missing)
    return RubricResult(
        raw_score=float(normalized.raw_score),
        effective_score=effective,
        understanding=normalized.understanding,
        criteria=list(normalized.criteria),
        required_missing=required_missing,
        blockers=blockers,
        strengths=list(normalized.strengths or []),
        errors=errors,
        next_focus=next_focus,
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

    # Readiness and mastery represent independently demonstrated evidence, not
    # time spent retrying. Failed and scaffolded turns remain useful for tutor
    # adaptation but must never accelerate progression.
    if pass_eligible and not scaffolded:
        out["meaningful_attempts"] = int(out.get("meaningful_attempts") or 0) + 1
    if pass_eligible and scaffolded:
        out["scaffold_successes"] = int(out["scaffold_successes"]) + 1
    elif pass_eligible:
        if transfer:
            out["transfer_passes"] = int(out["transfer_passes"]) + 1
        elif pressure:
            out["pressure_passes"] = int(out["pressure_passes"]) + 1
        else:
            out["independent_passes"] = int(out["independent_passes"]) + 1
            out["best_independent_score"] = max(
                float(out["best_independent_score"] or 0.0),
                effective_score,
            )

    if next_focus:
        out["last_gap"] = next_focus
    bounded_score = round(max(0.0, min(1.0, effective_score)), 4)
    out["readiness_score"] = (
        bounded_score
        if pass_eligible
        else min(float(out.get("readiness_score") or 0.0), bounded_score)
    )

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
        # Two core passes qualify the skill; the third is the final
        # consolidation after distinct transfer and pressure evidence.
        and independent_passes >= 3
        and transfer_passes >= 1
        and pressure_passes >= 1
    ):
        out["display_status"] = "ready_to_advance"
    elif not out.get("node_mastered"):
        out["display_status"] = "in_progress"

    if out.get("display_status") in {"ready_to_advance", "mastered"}:
        out["last_gap"] = ""

    return out
