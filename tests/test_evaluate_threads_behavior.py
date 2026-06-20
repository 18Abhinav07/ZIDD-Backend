"""P0-2 — the evaluator receives the per-TaskType grading stance.

evaluate_node previously called evaluate_answer WITHOUT a behavior pack, so
build_eval_prompt's `_strictness_gate`/`_persona` were dead code: an
assessment-sim answer ("strict, hold a high bar") and a young learner's phonics
("lenient, reward effort") were graded on the identical bar. This pins that the
behavior now threads from state.task_type all the way into evaluate_answer.

Offline: evaluate_answer is patched to capture the behavior arg; no model runs.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.graph.nodes import evaluate as ev  # noqa: E402

pytestmark = pytest.mark.asyncio

# An English answer so the deterministic language pre-gate does not short-circuit
# before the (patched) evaluate_answer call we are inspecting.
ENGLISH_ANSWER = "I am a backend engineer and I build payment systems."


def _state(task_type: str) -> dict:
    return {
        "competency_node": "comm_01_self_intro",
        "task_type": task_type,
        "user_input": ENGLISH_ANSWER,
        "messages": [{"role": "user", "content": ENGLISH_ANSWER}],
        "current_mastery": 0.0,
        "last_eval_score": None,
        "attempts": 0,
    }


@pytest.fixture
def captured(monkeypatch):
    box = {}

    async def _fake_eval(node, messages, user_input, behavior=None):
        box["behavior"] = behavior
        return DiagnosisEval(
            score=0.7,
            understanding="ok",
            errors=[],
            strengths=[],
            next_focus="keep going",
        )

    monkeypatch.setattr(ev, "evaluate_answer", _fake_eval)
    return box


async def test_interview_test_grades_strict(captured):
    await ev.evaluate_node(_state(TaskType.INTERVIEW_TEST.value))
    assert captured["behavior"] is not None
    assert captured["behavior"].language_strictness == "strict"


async def test_gd_test_grades_strict(captured):
    await ev.evaluate_node(_state(TaskType.GD_TEST.value))
    assert captured["behavior"] is not None
    assert captured["behavior"].language_strictness == "strict"


async def test_school_english_grades_lenient(captured):
    await ev.evaluate_node(_state(TaskType.SCHOOL_ENGLISH.value))
    assert captured["behavior"] is not None
    assert captured["behavior"].language_strictness == "lenient"


async def test_communication_grades_standard(captured):
    await ev.evaluate_node(_state(TaskType.COMMUNICATION.value))
    assert captured["behavior"] is not None
    assert captured["behavior"].language_strictness == "standard"


async def test_unknown_task_type_degrades_to_no_pack(captured):
    """An empty/legacy task_type yields None so the eval keeps the standard rubric."""
    await ev.evaluate_node(_state(""))
    assert captured["behavior"] is None
