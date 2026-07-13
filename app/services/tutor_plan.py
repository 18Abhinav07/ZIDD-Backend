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


def _hot_repeat_count(state: dict | None, focus: str) -> int:
    if not state or not focus:
        return 0
    delta = state.get("session_learning_delta")
    if not isinstance(delta, dict):
        return 0
    repeated = delta.get("repeated_issue_counts")
    if not isinstance(repeated, dict):
        return 0
    exact = repeated.get(focus)
    if exact is not None:
        try:
            return int(exact)
        except (TypeError, ValueError):
            return 0
    focus_key = focus.strip().lower()
    for key, value in repeated.items():
        if str(key or "").strip().lower() != focus_key:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
    return 0


def _missing_criterion_repeat_count(state: dict | None, required_missing: list[Any]) -> int:
    counts: list[int] = []
    for criterion in required_missing:
        criterion_id = str(criterion or "").strip()
        if criterion_id:
            counts.append(_hot_repeat_count(state, f"criterion:{criterion_id}"))
    return max(counts) if counts else 0


def build_tutor_turn_plan(result: Any, state: dict | None = None, *, scaffolded: bool = False) -> TutorTurnPlan:
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
        focus = _get(result, "next_focus", "") or "fix the missing required criterion"
        prior_repeats = max(
            _hot_repeat_count(state, str(focus)),
            _missing_criterion_repeat_count(state, required_missing),
        )
        if prior_repeats >= 1:
            return TutorTurnPlan(
                verdict="repeat_gap",
                next_action="micro_drill_then_rewrite",
                tone_policy="direct_no_praise_supportive",
                allowed_praise=False,
                focus=f"{focus} (repeated {prior_repeats + 1}x this session)",
                stage="adaptive_repair",
            )
        return TutorTurnPlan(
            verdict="partial",
            next_action="rewrite",
            tone_policy="direct_no_praise",
            allowed_praise=False,
            focus=focus,
            stage="guided_revision",
        )
    if scaffolded and _get(result, "pass_eligible", False):
        return TutorTurnPlan(
            verdict="guided_success",
            next_action="retry_without_scaffold",
            tone_policy="warm_but_not_mastery",
            allowed_praise=False,
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
            tone_policy="measured_no_celebration",
            allowed_praise=False,
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
