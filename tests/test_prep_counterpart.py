"""Phase 3.3 — prep/test pairing helper.

A TEST session (gd_test, interview_test) is never coached per-skill, so it logs
no weaknesses of its own. To seed its simulation from what the learner actually
struggled with, start_session must read the PREP sibling's weaknesses. That
sibling is resolved by `prep_counterpart`: test values map to their prep value,
prep and single-mode values map to themselves (a harmless no-op).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

# Referenced via the module (tt.test_counterpart) so pytest does not collect the
# prep->test helper as a test just because its name starts with "test_".
from app.content import task_types as tt  # noqa: E402
from app.content.task_types import TaskType, prep_counterpart  # noqa: E402


def test_test_values_map_to_prep_sibling():
    assert prep_counterpart(TaskType.GD_TEST.value) == TaskType.GD_PREP.value
    assert prep_counterpart(TaskType.INTERVIEW_TEST.value) == \
        TaskType.INTERVIEW_PREP.value


def test_prep_and_single_mode_values_map_to_themselves():
    assert prep_counterpart(TaskType.GD_PREP.value) == TaskType.GD_PREP.value
    assert prep_counterpart(TaskType.COMMUNICATION.value) == \
        TaskType.COMMUNICATION.value
    assert prep_counterpart(TaskType.SCHOOL_ENGLISH.value) == \
        TaskType.SCHOOL_ENGLISH.value


def test_unknown_value_maps_to_itself():
    assert prep_counterpart("nonsense") == "nonsense"


# --- Phase 4 Layer B: reverse pairing for precache (prep -> test sibling) ---


def test_prep_values_map_to_test_sibling():
    assert tt.test_counterpart(TaskType.GD_PREP.value) == TaskType.GD_TEST.value
    assert tt.test_counterpart(TaskType.INTERVIEW_PREP.value) == \
        TaskType.INTERVIEW_TEST.value


def test_single_mode_prep_has_no_distinct_test_sibling():
    # No assessment variant -> maps to itself, so the caller can skip precache.
    assert tt.test_counterpart(TaskType.COMMUNICATION.value) == \
        TaskType.COMMUNICATION.value
    assert tt.test_counterpart(TaskType.SCHOOL_ENGLISH.value) == \
        TaskType.SCHOOL_ENGLISH.value


def test_test_and_unknown_values_map_to_themselves():
    assert tt.test_counterpart(TaskType.GD_TEST.value) == TaskType.GD_TEST.value
    assert tt.test_counterpart("nonsense") == "nonsense"
