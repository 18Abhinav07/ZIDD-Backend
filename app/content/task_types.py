"""TaskType — the pedagogy axis a BehaviorPack keys on.

A TaskType is coarser than a module_id in one direction and finer in another:
the interview and group_discussion modules each host BOTH a coaching ("prep")
and an assessment ("test") behavior, while communication and school_english
have a single mode. Resolving a node to a TaskType lets the prompt layer pick a
behavior pack without hardcoding module strings or a prep/test branch at every
call site.

`task_type_of(node_id, test_mode=...)` is the single resolver: it reads the
owning module via the registry, then applies the prep/test split only for the
modules that have one. Keep the enum values stable — they are used as join keys
in storage (sessions.task_type, weaknesses.task_type).
"""
from enum import Enum

from app.content.registry import module_of


class TaskType(str, Enum):
    COMMUNICATION = "communication"
    INTERVIEW_PREP = "interview_prep"
    INTERVIEW_TEST = "interview_test"
    GD_PREP = "gd_prep"
    GD_TEST = "gd_test"
    SCHOOL_ENGLISH = "school_english"


# module_id (registry) -> (prep TaskType, test TaskType). Single-mode modules
# repeat the same TaskType so test_mode is a harmless no-op for them.
_MODULE_TASK_TYPES: dict[str, tuple[TaskType, TaskType]] = {
    "communication": (TaskType.COMMUNICATION, TaskType.COMMUNICATION),
    "interview": (TaskType.INTERVIEW_PREP, TaskType.INTERVIEW_TEST),
    "group_discussion": (TaskType.GD_PREP, TaskType.GD_TEST),
    "school_english": (TaskType.SCHOOL_ENGLISH, TaskType.SCHOOL_ENGLISH),
}


# test TaskType value -> its prep counterpart value. Built from _MODULE_TASK_TYPES
# so the pairing stays in one place; single-mode modules map their value to
# itself (prep == test), making prep_counterpart a no-op for them.
_TEST_TO_PREP: dict[str, str] = {
    test.value: prep.value for prep, test in _MODULE_TASK_TYPES.values()
}


# prep TaskType value -> its DISTINCT test counterpart value. Only the modules
# that actually have a separate assessment variant appear; single-mode modules
# (prep == test) are excluded, so test_counterpart returns them unchanged and the
# precache wiring can detect "no test sibling -> skip" by value equality.
_PREP_TO_TEST: dict[str, str] = {
    prep.value: test.value
    for prep, test in _MODULE_TASK_TYPES.values()
    if prep.value != test.value
}


def prep_counterpart(task_type_value: str) -> str:
    """The prep TaskType value paired with a given task_type value.

    Test variants resolve to their prep sibling (gd_test -> gd_prep); prep,
    single-mode, and unknown values map to themselves. Lets a TEST session read
    the prep weaknesses logged while the learner coached the same module.
    """
    return _TEST_TO_PREP.get(task_type_value, task_type_value)


def test_counterpart(task_type_value: str) -> str:
    """The TEST TaskType value paired with a given prep task_type value.

    Reverse of prep_counterpart: prep variants resolve to their test sibling
    (gd_prep -> gd_test). Single-mode, test, and unknown values map to
    themselves, so a caller can treat value-equality as "no distinct test
    sibling exists" and skip precaching. Used at PREP end_session to know which
    TEST task type to precompute probe items for.
    """
    return _PREP_TO_TEST.get(task_type_value, task_type_value)


def task_type_of(node_id: str, test_mode: bool = False) -> TaskType:
    """Resolve a node to its TaskType.

    `test_mode=True` selects the assessment variant for modules that have one
    (interview, group_discussion); it is ignored for single-mode modules.
    Raises KeyError if the node id is unknown (mirrors registry.module_of).
    """
    module_id = module_of(node_id)
    pair = _MODULE_TASK_TYPES.get(module_id)
    if pair is None:
        # NCERT school chapter modules (a chapter IS a module, id like c2_ch01_*)
        # are all the single school_english task type. Identify them by their
        # chapter metadata rather than hardcoding ids.
        from app.content.registry import get_module
        if get_module(module_id).class_no is not None:
            return TaskType.SCHOOL_ENGLISH
        raise KeyError(module_id)
    prep, test = pair
    return test if test_mode else prep
