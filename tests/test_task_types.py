"""Phase 1.1 — TaskType taxonomy and module->TaskType resolution.

TaskType is the pedagogy axis: it is what a BehaviorPack keys on. It is coarser
than module_id in one direction (interview_prep/interview_test both live in the
interview module) and identical in another (communication -> COMMUNICATION).
`task_type_of(node_id, test_mode=...)` resolves a node to its TaskType so the
service can pick the right behavior pack without hardcoding module strings.
"""
from app.content.task_types import TaskType, task_type_of


def test_task_type_is_closed_string_enum():
    # join-key stability: values are stable strings.
    assert TaskType.COMMUNICATION.value == "communication"
    assert TaskType.INTERVIEW_PREP.value == "interview_prep"
    assert TaskType.INTERVIEW_TEST.value == "interview_test"
    assert TaskType.GD_PREP.value == "gd_prep"
    assert TaskType.GD_TEST.value == "gd_test"
    assert TaskType.SCHOOL_ENGLISH.value == "school_english"


def test_communication_node_maps_to_communication():
    assert task_type_of("comm_01_self_intro") is TaskType.COMMUNICATION


def test_interview_node_defaults_to_prep():
    assert task_type_of("int_01_elevator_pitch") is TaskType.INTERVIEW_PREP


def test_interview_node_test_mode_maps_to_test():
    assert (
        task_type_of("int_01_elevator_pitch", test_mode=True)
        is TaskType.INTERVIEW_TEST
    )


def test_gd_node_defaults_to_prep_and_test_mode_flips():
    assert task_type_of("gd_01_stake_position") is TaskType.GD_PREP
    assert task_type_of("gd_01_stake_position", test_mode=True) is TaskType.GD_TEST


def test_school_node_ignores_test_mode():
    # school_english has no test variant; test_mode is a no-op there.
    assert task_type_of("c2_alphabet_sounds") is TaskType.SCHOOL_ENGLISH
    assert task_type_of("c2_alphabet_sounds", test_mode=True) is TaskType.SCHOOL_ENGLISH
