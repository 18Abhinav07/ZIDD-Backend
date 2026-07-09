"""Deterministic tutor planning from the latest enforced rubric result."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class TutorTurnPlan:
    verdict: str
    next_action: str
    tone_policy: str
    allowed_praise: bool
    focus: str
    stage: str

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


def _get(result: Any, key: str, default: Any = None) -> Any:
    if isinstance(result, dict):
        if key == "required_missing":
            return result.get("required_missing", result.get("missing_required_criteria", default))
        return result.get(key, default)
    return getattr(result, key, default)


def build_tutor_turn_plan(result: Any, state: dict | None = None, *, scaffolded: bool = False) -> TutorTurnPlan:
    del state  # reserved for learner-history-aware planning in the next phase
    if not _get(result, "english", True):
        return TutorTurnPlan(
            verdict="clarify_language",
            next_action="ask_for_english_retry",
            tone_policy="supportive_direct",
            allowed_praise=False,
            focus="answer in English",
            stage="repair",
        )
    if not _get(result, "on_task", True):
        return TutorTurnPlan(
            verdict="redirect",
            next_action="bring_back_to_task",
            tone_policy="neutral_corrective",
            allowed_praise=False,
            focus=_get(result, "next_focus", "") or "answer the active prompt",
            stage="redirect",
        )
    required_missing = list(_get(result, "required_missing", []) or [])
    if required_missing:
        return TutorTurnPlan(
            verdict="partial",
            next_action="rewrite",
            tone_policy="direct_no_praise",
            allowed_praise=False,
            focus=_get(result, "next_focus", "") or "fix the missing required criterion",
            stage="guided_revision",
        )
    if scaffolded and _get(result, "pass_eligible", False):
        return TutorTurnPlan(
            verdict="guided_success",
            next_action="retry_without_scaffold",
            tone_policy="warm_but_not_mastery",
            allowed_praise=True,
            focus=_get(result, "next_focus", "") or "repeat independently",
            stage="scaffold",
        )
    if _get(result, "mastery_eligible", False):
        return TutorTurnPlan(
            verdict="independent_pass",
            next_action="raise_transfer_or_pressure",
            tone_policy="stretch",
            allowed_praise=True,
            focus=_get(result, "next_focus", "") or "prove transfer",
            stage="challenge",
        )
    if _get(result, "pass_eligible", False):
        return TutorTurnPlan(
            verdict="independent_pass",
            next_action="tighten_one_gap",
            tone_policy="measured",
            allowed_praise=True,
            focus=_get(result, "next_focus", "") or "make the answer more concrete",
            stage="practice",
        )
    return TutorTurnPlan(
        verdict="not_yet",
        next_action="reteach_required_gap",
        tone_policy="corrective_supportive",
        allowed_praise=False,
        focus=_get(result, "next_focus", "") or "meet the required rubric criterion",
        stage="repair",
    )
