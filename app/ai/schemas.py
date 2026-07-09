"""Structured-output schemas for the engine's AI calls.

Council rule (structured.py): Flash-Lite ignores schema `description` fields,
so instructions live in the prompt, not here. Keep string fields short.
"""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class DiagnosisEval(BaseModel):
    """Flash-Lite structured read of one learner answer.

    `score` drives routing (route_node). The text fields feed the next
    pedagogy prompt so the tutor references the learner's actual answer.
    """

    score: float = Field(ge=0.0, le=1.0)
    understanding: str          # one-line read of what the learner grasped
    errors: list[str]           # concrete mistakes (empty if none)
    strengths: list[str]        # what they did well (empty if none)
    next_focus: str             # the single thing to work on next
    # Routing split (council fix #1/#6): an off-task answer scores 0.0 by the
    # rubric, but a fluent off-task answer (on_task=False, english=True) needs a
    # REDIRECT, while a genuine non-answer (english=False) needs a bridge. Affect
    # (#5) lets a frustrated/discouraged read flip support without regex. Defaults
    # keep old callers/back-compat decodes valid.
    on_task: bool = True        # did the answer attempt the assessed skill?
    english: bool = True        # competent English (vs empty/gibberish/non-English)?
    affect: Literal["neutral", "frustrated", "confident", "confused"] = "neutral"
    goodbye: bool = False       # learner is ending the session (natural farewell)


class CriterionEval(BaseModel):
    """LLM judgment for one explicit prep-rubric criterion.

    The model judges semantics; backend code validates required evidence and
    applies score caps. `evidence_quote` must be copied from the learner answer
    for required criteria, not inferred from the rubric text.
    """

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "id" not in out and "criterion_id" in out:
            out["id"] = out["criterion_id"]
        if "reason" not in out and "rationale" in out:
            out["reason"] = out["rationale"]
        if "quality" not in out and "score" in out:
            out["quality"] = out["score"]
        return out

    id: str
    met: bool = False
    evidence_quote: str = ""
    reason: str = ""
    quality: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def criterion_id(self) -> str:
        return self.id

    @property
    def rationale(self) -> str:
        return self.reason

    @property
    def score(self) -> float:
        return self.quality


class PrepRubricEval(BaseModel):
    """Structured career-prep evaluation over explicit node criteria.

    Keeps the DiagnosisEval surface (understanding/errors/strengths/next_focus
    plus routing flags) while carrying criterion-level proof and backend-applied
    eligibility. Non-career modules continue to use DiagnosisEval.
    """

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_aliases(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        out = dict(data)
        if "raw_score" not in out and "score" in out:
            out["raw_score"] = out["score"]
        if "required_missing" not in out and "missing_required_criteria" in out:
            out["required_missing"] = out["missing_required_criteria"]
        return out

    raw_score: float = Field(ge=0.0, le=1.0)
    effective_score: float = Field(default=0.0, ge=0.0, le=1.0)
    understanding: str = ""
    errors: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    next_focus: str
    criteria: list[CriterionEval] = Field(default_factory=list)
    pass_eligible: bool = False
    mastery_eligible: bool = False
    required_missing: list[str] = Field(default_factory=list)
    on_task: bool = True
    english: bool = True
    affect: Literal["neutral", "frustrated", "confident", "confused"] = "neutral"
    goodbye: bool = False

    @property
    def score(self) -> float:
        return self.raw_score

    @property
    def missing_required_criteria(self) -> list[str]:
        return self.required_missing


class SimulationReport(BaseModel):
    """End-of-session score for a TEST-mode simulation (interview_test / gd_test).

    Test sessions are scored, not coached mid-stream: the round runner streams
    persona turns with no feedback, and this report is produced once at the end.
    `score` (0-1) gates progression like DiagnosisEval.score; the text fields are
    the deferred feedback shown to the learner after the session closes.

    GD rubric sub-scores (0-1, default 0.0 for non-GD sessions):
      participation_score — claimed the floor, interjected, held space.
      relevance_score     — stayed on topic, built coherent arguments.
      language_score      — fluency, grammar, vocabulary under pressure.
    """

    score: float = Field(ge=0.0, le=1.0)
    summary: str                # one-paragraph read of the whole performance
    strengths: list[str]        # what landed (empty if none)
    improvements: list[str]     # the few things to work on next
    # GD rubric dimensions — 0.0 default keeps old callers (interview_test) valid
    participation_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    language_score: float = Field(default=0.0, ge=0.0, le=1.0)
    # Interview rubric dimensions — 0.0 default keeps GD callers valid
    clarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    scenario_label: str = ""
    role_focus: str = ""
    topic: str = ""
    observed_skill_gaps: list[str] = Field(default_factory=list)
    recommended_next_nodes: list[str] = Field(default_factory=list)
    assessment_caveats: list[str] = Field(default_factory=list)
    learner_assessment_caveats: list[str] = Field(default_factory=list)
    simulator_integrity_notes: list[str] = Field(default_factory=list)
    score_breakdown: dict[str, Any] = Field(default_factory=dict)
    score_explanations: dict[str, str] = Field(default_factory=dict)
    read_observations: list[str] = Field(default_factory=list)
    validity_status: Literal["final", "partial", "insufficient_evidence", "invalid_simulation"] = "final"
    scorable_turn_count: int = 0
    coverage_map: dict[str, Any] = Field(default_factory=dict)
    evidence_quotes: list[str] = Field(default_factory=list)
    repeated_answer_flags: list[str] = Field(default_factory=list)
    topic_drift_flags: list[str] = Field(default_factory=list)
    persona_warnings: list[str] = Field(default_factory=list)


class ProbeItem(BaseModel):
    """One probe item for a TEST-mode assessment (gd_test / interview_test).

    Generated up front (not mid-stream) so the persona panel / interviewer has a
    ready bank to press the learner with. `skill_id` ties the item back to a
    SkillID the learner was weak on in prep, so the test concentrates there.
    """

    skill_id: str               # SkillID value the item probes (ties to a weakness)
    prompt: str                 # the question / debate motion / scenario shown
    aim: str                    # one line: what a strong answer demonstrates


class ProbeSet(BaseModel):
    """Wrapper so the structured call returns a single model (a list of items)."""

    items: list[ProbeItem]


class FillBlankGame(BaseModel):
    """Gamified teach item for scaffold turns (scaffold >= 1).

    Rendered by the client as an interactive fill-in-the-blank widget. The
    learner's fill is submitted as the next turn answer and scored normally —
    the graph stays intact. `answer_key` stays server-side (not sent to client).
    """

    sentence: str       # one natural sentence with exactly one ___ gap
    hint: str           # short grammar/vocab category label — NOT the answer
    answer_key: str     # correct fill, shown only after the learner submits
    context: str        # one line: why this gap targets the current teaching focus


class PlacementEval(BaseModel):
    """Flash-Lite read of an onboarding writing sample -> CEFR estimate.

    Drives placement: `cefr` maps (in the registry) to the learner's STARTING
    node so an advanced learner skips trivial early levels. `rationale` is shown
    to the learner so the placement feels transparent, not arbitrary.
    """

    cefr: str = Field(pattern="^(A1|A2|B1|B2|C1|C2)$")
    rationale: str              # one-line justification shown to the learner


class DirectorDecision(BaseModel):
    """Writers'-room Director output: who speaks next and with what intent.

    Produced once per round; drives blackboard updates and persona selection.
    `tension` and `answer_quality` are plain float (no Field bounds) so a
    slightly out-of-range LLM value doesn't crash the turn — clamping happens
    downstream in apply_decision.
    """

    action: Literal["probe_deeper", "pivot_topic", "escalate_pressure", "wind_down"]
    next_speaker: str           # speaker_id from roster
    intent: str                 # concrete instruction to the persona, cites the transcript
    tension: float              # 0.0-1.0 target after this turn
    answer_quality: float       # director's read of the learner's last answer (0-1)
    should_close: bool          # signal the simulation should wrap


class AssessmentAnalysis(BaseModel):
    """Superset analysis schema for provider-compatible structured output."""

    mode: Literal["gd_test", "interview_test"] = "gd_test"
    routing_case: Literal[
        "reply_only",
        "reply_and_request",
        "point_only",
        "request_only",
        "clarification_request",
        "move_on",
    ] = "point_only"
    answer_kind: Literal[
        "answer",
        "clarification_request",
        "move_on_request",
        "dodge",
        "end_request",
    ] = "answer"
    control_intent: Literal["none", "clarify", "move_on", "end"] = "none"
    scorable: bool = True
    addressed_personas: list[str] = Field(default_factory=list)
    addressed_event_ids: list[str] = Field(default_factory=list)
    requested_next_speaker: str = ""
    request_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    question_to_requested_speaker: str = ""
    stance: str = ""
    evidence_points: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    active_probe_id: str = ""
    criteria_met: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    follow_up_focus: str = ""
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("request_confidence", "quality_score", mode="before", check_fields=False)
    @classmethod
    def _normalize_percent_scale_scores(cls, value: Any) -> Any:
        if value in (None, ""):
            return value
        try:
            number = float(value)
        except (TypeError, ValueError):
            return value
        if 1.0 < number <= 10.0:
            return round(number / 10.0, 4)
        if 10.0 < number <= 100.0:
            return round(number / 100.0, 4)
        return value


class GDAnalysis(AssessmentAnalysis):
    """One-turn semantic read for a scored group-discussion assessment."""

    mode: Literal["gd_test"] = "gd_test"
    routing_case: Literal[
        "reply_only",
        "reply_and_request",
        "point_only",
        "request_only",
        "clarification_request",
        "move_on",
    ] = "point_only"
    scorable: bool = True
    addressed_personas: list[str] = Field(default_factory=list)
    addressed_event_ids: list[str] = Field(default_factory=list)
    requested_next_speaker: str = ""
    request_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    question_to_requested_speaker: str = ""
    stance: str = ""
    evidence_points: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    control_intent: Literal["none", "clarify", "move_on", "end"] = "none"


class InterviewAnalysis(AssessmentAnalysis):
    """One-turn semantic read for a scored interview assessment."""

    mode: Literal["interview_test"] = "interview_test"
    answer_kind: Literal[
        "answer",
        "clarification_request",
        "move_on_request",
        "dodge",
        "end_request",
    ] = "answer"
    control_intent: Literal["none", "clarify", "move_on", "end"] = "none"
    scorable: bool = True
    active_probe_id: str = ""
    criteria_met: list[str] = Field(default_factory=list)
    missing_criteria: list[str] = Field(default_factory=list)
    evidence_points: list[str] = Field(default_factory=list)
    follow_up_focus: str = ""
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)


class NextAction(BaseModel):
    """Model-proposed next assessment action. Backend policy must authorize it."""

    speaker_id: str
    action_type: str
    intent: str
    should_close: bool = False


class VisibleResponse(BaseModel):
    """The learner-visible turn text drafted by the structured assessment call."""

    speaker_id: str
    text: str


class AssessmentTurnCall(BaseModel):
    """Single structured model call for a normal test-mode learner turn."""

    analysis: AssessmentAnalysis
    next_action: NextAction
    visible_response: VisibleResponse


class AssessmentEvent(BaseModel):
    """Durable typed event used by reports and learning-profile projection."""

    event_id: str
    event_type: Literal["learner_turn", "analysis", "visible_response"]
    task_type: str
    speaker_id: str = ""
    scorable: bool = True
    analysis: dict[str, Any] = Field(default_factory=dict)
    content: str = ""
    validity_flags: list[dict[str, Any]] = Field(default_factory=list)


class SelectionDecision(BaseModel):
    """Spec B selector output: which content node the learner moves to next.

    Produced (or synthesized) at the advance boundary. The selector is a
    two-stage hybrid: deterministic rules narrow the valid candidates, then a
    single LLM call (only when >1 candidate) picks one. All instruction lives in
    the prompt text (council rule); the schema fields carry none.
    """

    action: Literal["ADVANCE", "REMEDIATE", "REPEAT", "SKIP"]
    next_ref: str
    band: Literal["foundational", "standard", "stretch"] = "standard"
    rationale: str
