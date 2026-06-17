"""Phase 1.2 — BehaviorPack: per-TaskType persona / pedagogy / rubric knobs.

A BehaviorPack carries the differences the engine must apply per task type:
persona voice, pedagogy stance, what the rubric emphasises, how strict the
language gate is, and the output style. `behavior_for(task_type)` returns the
right pack; every TaskType must have one (no KeyError, no silent fallback that
hides a missing pack).
"""
import pytest

from app.ai.behaviors import BehaviorPack, behavior_for
from app.content.task_types import TaskType


@pytest.mark.parametrize("tt", list(TaskType))
def test_every_task_type_has_a_pack(tt):
    pack = behavior_for(tt)
    assert isinstance(pack, BehaviorPack)
    # all rendered fields are non-empty prose the prompt can inject.
    assert pack.persona.strip()
    assert pack.pedagogy.strip()
    assert pack.rubric_emphasis.strip()
    assert pack.output_style.strip()


def test_school_is_gentle_and_low_strictness():
    pack = behavior_for(TaskType.SCHOOL_ENGLISH)
    text = (pack.persona + pack.pedagogy).lower()
    assert "child" in text or "gentle" in text or "young" in text
    assert pack.language_strictness == "lenient"


def test_test_modes_are_strict_graders():
    for tt in (TaskType.INTERVIEW_TEST, TaskType.GD_TEST):
        pack = behavior_for(tt)
        assert pack.language_strictness == "strict"
        # a grader does not coach mid-answer.
        assert "assess" in pack.pedagogy.lower() or "evaluat" in pack.pedagogy.lower()


def test_prep_modes_coach():
    for tt in (TaskType.INTERVIEW_PREP, TaskType.GD_PREP):
        pack = behavior_for(tt)
        assert pack.language_strictness in ("standard", "strict")
        assert "coach" in pack.pedagogy.lower() or "teach" in pack.pedagogy.lower()
