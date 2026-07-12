"""Immutable per-session assessment plans for Interview Test and GD Test."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.content.task_types import TaskType
from app.services.interview_probes import build_interview_probe_plan

MAX_ASSESSMENT_ROUNDS = 10
MAX_GD_FOCUS_ITEMS = 4


class GDFocusItem(BaseModel):
    model_config = ConfigDict(frozen=True)

    focus_id: str = Field(max_length=128)
    skill_id: str = Field(max_length=128)
    status: Literal["active_gap", "improving"]
    gap: str = Field(max_length=240)
    repeat_count: int = Field(ge=0, le=999)
    latest_evidence: str = Field(max_length=320)


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
    focus_plan: tuple[GDFocusItem, ...] = Field(default_factory=tuple, max_length=MAX_GD_FOCUS_ITEMS)
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


def _bounded_focus_text(value: Any, *, limit: int) -> str:
    return " ".join(str(value or "").split()).strip()[:limit]


def _bounded_repeat_count(value: Any) -> int:
    try:
        return max(0, min(999, int(value or 0)))
    except (TypeError, ValueError):
        return 0


def _is_gd_focus(item: dict[str, Any], skill_id: str) -> bool:
    module_id = str(item.get("module_id") or "").strip()
    task_type = str(item.get("task_type") or "").strip()
    if module_id and module_id != "group_discussion":
        return False
    if task_type and task_type not in {"gd_test", "gd_prep"}:
        return False
    return (
        module_id == "group_discussion"
        or task_type in {"gd_test", "gd_prep"}
        or skill_id.lower().startswith("gd_")
    )


def _build_gd_focus_plan(career_context: dict[str, Any]) -> tuple[GDFocusItem, ...]:
    memory = career_context.get("career_memory_context")
    if not isinstance(memory, dict):
        return ()

    candidates: list[tuple[int, int, int, GDFocusItem]] = []
    source_index = 0
    for priority, (bucket, status) in enumerate((
        ("active_gaps", "active_gap"),
        ("improving_gaps", "improving"),
    )):
        rows = memory.get(bucket)
        if not isinstance(rows, list):
            continue
        for raw_item in rows:
            source_index += 1
            if not isinstance(raw_item, dict):
                continue
            skill_id = _bounded_focus_text(raw_item.get("skill_id"), limit=128)
            focus_id = _bounded_focus_text(raw_item.get("focus_id") or skill_id, limit=128)
            if not focus_id or not _is_gd_focus(raw_item, skill_id):
                continue
            repeat_count = _bounded_repeat_count(raw_item.get("repeat_count"))
            candidates.append((
                priority,
                -repeat_count,
                source_index,
                GDFocusItem(
                    focus_id=focus_id,
                    skill_id=skill_id,
                    status=status,
                    gap=_bounded_focus_text(raw_item.get("gap"), limit=240),
                    repeat_count=repeat_count,
                    latest_evidence=_bounded_focus_text(raw_item.get("latest_evidence"), limit=320),
                ),
            ))

    selected: list[GDFocusItem] = []
    seen_identities: set[str] = set()
    for _, _, _, item in sorted(candidates, key=lambda candidate: candidate[:3]):
        identities = {f"focus:{item.focus_id.lower()}"}
        if item.skill_id:
            identities.add(f"skill:{item.skill_id.lower()}")
        if identities & seen_identities:
            continue
        seen_identities.update(identities)
        selected.append(item)
        if len(selected) == MAX_GD_FOCUS_ITEMS:
            break
    return tuple(selected)


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
            focus_plan=_build_gd_focus_plan(career),
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
