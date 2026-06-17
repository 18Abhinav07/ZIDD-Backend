"""Phase 1.3 wiring — the service resolves a TaskType and threads its
BehaviorPack into every rendered prompt.

Two seams are proven here, both offline (the AI boundary is patched to capture
the rendered prompt instead of calling a model):

  1. start_session stores the TaskType *value* (task_type_of), not the bare
     module id — so an interview session keys storage on "interview_prep", and
     the pack lookup has something total to resolve.
  2. The opening prompt AND the per-turn pedagogy prompt both carry the pack's
     persona, so voice follows task type all the way to the wire.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.behaviors import behavior_for  # noqa: E402
from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio

INT_NODE = "int_01_elevator_pitch"


class _Capture:
    """Patched stream_generation: record each spec.prompt, emit fixed tokens."""

    def __init__(self):
        self.prompts: list[str] = []

    async def __call__(self, spec):
        self.prompts.append(spec.prompt)
        for tok in ("ok", " ", "done"):
            yield tok


@pytest.fixture(autouse=True)
def _patch_ai(monkeypatch):
    cap = _Capture()
    monkeypatch.setattr("app.services.session_service.stream_generation", cap)

    async def _fake_eval(node, messages, user_input):
        return DiagnosisEval(
            score=0.9, understanding="x", errors=[], strengths=["s"],
            next_focus="n", on_task=True, english=True, affect="neutral",
        )

    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer", _fake_eval, raising=False
    )
    monkeypatch.setattr("app.services.session_service._capture", cap, raising=False)
    yield cap
    svc.SessionStore.clear()


async def _drain(agen):
    async for _ in agen:
        pass


async def test_start_session_stores_task_type_value(_patch_ai):
    # interview node -> prep TaskType value, not the bare module id "interview".
    _sid, state = await svc.start_session("u_int", INT_NODE)
    assert state["task_type"] == TaskType.INTERVIEW_PREP.value


async def test_opening_prompt_carries_behavior(_patch_ai):
    cap = _patch_ai
    sid, _state = await svc.start_session("u_int2", INT_NODE)
    await _drain(svc.stream_opening(sid))
    persona = behavior_for(TaskType.INTERVIEW_PREP).persona
    assert any(persona in p for p in cap.prompts)


async def test_turn_pedagogy_prompt_carries_behavior(_patch_ai):
    cap = _patch_ai
    sid, state = await svc.start_session("u_int3", INT_NODE)
    state["turn_count"] = 1  # skip opening; next message is a scored turn
    cap.prompts.clear()
    await _drain(svc.run_turn(sid, "Here is my elevator pitch."))
    persona = behavior_for(TaskType.INTERVIEW_PREP).persona
    assert any(persona in p for p in cap.prompts)


# ----- Phase 2.4: prior weaknesses thread into the rendered prompt -----

_WEAK = [{"skill_id": "FILLER_WORDS", "hit_count": 3, "last_raw": "um, like, you know"}]


async def test_opening_prompt_carries_weakness(_patch_ai):
    cap = _patch_ai
    sid, state = await svc.start_session("u_w1", INT_NODE)
    state["weakness_context"] = list(_WEAK)
    cap.prompts.clear()
    await _drain(svc.stream_opening(sid))
    assert any("FILLER_WORDS" in p for p in cap.prompts)


async def test_turn_pedagogy_prompt_carries_weakness(_patch_ai):
    cap = _patch_ai
    sid, state = await svc.start_session("u_w2", INT_NODE)
    state["turn_count"] = 1  # skip opening; next message is a scored turn
    state["weakness_context"] = list(_WEAK)
    cap.prompts.clear()
    await _drain(svc.run_turn(sid, "Here is my elevator pitch."))
    assert any("FILLER_WORDS" in p for p in cap.prompts)
