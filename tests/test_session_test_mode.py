"""Phase 3.2 — session start selects the assessment ("test") TaskType variant.

A learner can enter an interview/GD node in either coaching ("prep") mode or
assessment ("test") mode. start_session threads a `test_mode` flag into
task_type_of so the stored task_type — which keys behavior pack, memory, and
weaknesses — is the strict assessment variant when the learner is being tested.

Offline: no AI or storage is exercised; only the resolved task_type is asserted.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

INT_NODE = "int_01_elevator_pitch"
GD_NODE = "gd_01_stake_position"
COMM_NODE = "comm_02_describe_routine"


@pytest.fixture(autouse=True)
def _clear():
    yield
    svc.SessionStore.clear()


async def test_interview_test_mode_selects_assessment_variant():
    _sid, state = await svc.start_session("u_t1", INT_NODE, test_mode=True)
    assert state["task_type"] == TaskType.INTERVIEW_TEST.value


async def test_gd_test_mode_selects_assessment_variant():
    _sid, state = await svc.start_session("u_t2", GD_NODE, test_mode=True)
    assert state["task_type"] == TaskType.GD_TEST.value


async def test_default_is_prep_variant():
    _sid, state = await svc.start_session("u_t3", INT_NODE)
    assert state["task_type"] == TaskType.INTERVIEW_PREP.value


async def test_test_mode_ignored_for_modules_without_assessment_variant():
    # communication has no prep/test split — test_mode is a no-op there.
    _sid, state = await svc.start_session("u_t4", COMM_NODE, test_mode=True)
    assert state["task_type"] == TaskType.COMMUNICATION.value
