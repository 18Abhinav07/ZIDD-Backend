"""Immutable per-session assessment plans for Interview Test and GD Test."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.content.task_types import TaskType
from app.services.interview_probes import build_interview_probe_plan

MAX_ASSESSMENT_ROUNDS = 10


class AssessmentPersona(BaseModel):
    model_config = ConfigDict(extra="allow")

    speaker_id: str
    name: str
    role_type: str = ""
    role: str = ""
    stance: str = ""
    style: str = ""


class GDPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: Literal["gd_test"] = "gd_test"
    topic: str
    environment: str = ""
    active_personas: list[dict[str, Any]] = Field(default_factory=list)
    max_rounds: int = MAX_ASSESSMENT_ROUNDS
    required_unique_coverage: int = 3
    rubric: list[str] = Field(default_factory=lambda: [
        "clear stance",
        "specific evidence",
        "active listening",
        "rebuttal quality",
        "collaborative synthesis",
    ])


class InterviewPlan(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: Literal["interview_test"] = "interview_test"
    role: str
    interview_type: str = ""
    pressure_level: str = "standard"
    active_personas: list[dict[str, Any]] = Field(default_factory=list)
    probe_plan: list[dict[str, Any]] = Field(default_factory=list)
    max_rounds: int = MAX_ASSESSMENT_ROUNDS
    required_unique_coverage: int = 4
    rubric: list[str] = Field(default_factory=lambda: [
        "specific example",
        "personal ownership",
        "trade-off or decision quality",
        "result or impact",
        "clear structure",
    ])


def _public_persona(persona: dict[str, Any]) -> dict[str, Any]:
    return {
        key: persona.get(key)
        for key in ("speaker_id", "name", "role_type", "role", "stance", "style")
        if persona.get(key) is not None
    }


def build_assessment_plan(state: dict[str, Any]) -> GDPlan | InterviewPlan | None:
    """Build the canonical test contract from resolved session state."""
    task_type = str(state.get("task_type") or "")
    scenario = state.get("scenario_config") or {}
    career = state.get("career_context") or {}
    personas = [
        _public_persona(persona)
        for persona in (state.get("personas") or [])
        if isinstance(persona, dict) and persona.get("speaker_id")
    ]
    if task_type == TaskType.GD_TEST.value:
        topic = (
            str(scenario.get("topic") or scenario.get("resolved_topic") or state.get("sim_topic") or "").strip()
            or "the active GD motion"
        )
        return GDPlan(
            topic=topic,
            environment=str(scenario.get("environment") or ""),
            active_personas=personas,
        )
    if task_type == TaskType.INTERVIEW_TEST.value:
        role = (
            str(scenario.get("target_role") or career.get("primary_role") or "").strip()
            or "the target role"
        )
        return InterviewPlan(
            role=role,
            interview_type=str(scenario.get("interview_type") or ""),
            pressure_level=str(scenario.get("pressure_level") or "standard"),
            active_personas=personas,
            probe_plan=build_interview_probe_plan(state),
        )
    return None


def ensure_assessment_plan(state: dict[str, Any]) -> dict[str, Any] | None:
    """Return the persisted plan, creating it once for test-mode sessions."""
    existing = state.get("assessment_plan")
    if isinstance(existing, dict):
        if existing.get("mode") == TaskType.INTERVIEW_TEST.value and not existing.get("probe_plan"):
            refreshed = dict(existing)
            refreshed["probe_plan"] = build_interview_probe_plan(state)
            state["assessment_plan"] = refreshed
            return refreshed
        return existing
    plan = build_assessment_plan(state)
    if plan is None:
        return None
    dumped = plan.model_dump()
    state["assessment_plan"] = dumped
    return dumped
