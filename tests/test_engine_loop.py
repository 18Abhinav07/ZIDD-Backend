"""Layer-A engine mechanics — no network, no DB.

Monkeypatches the AI boundary (evaluate + stream) so the full decision loop
runs offline. Asserts routing, EMA mastery, the bridge 3-attempt cap, node
advance on mastery, and the <50% clean pass-rate remediation flag.
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
from app.services import session_service as svc  # noqa: E402

pytestmark = pytest.mark.asyncio


# ---------- fakes ----------

class _Scores:
    """Hands back scripted scores to the patched evaluator, in order.

    Optional parallel sequences for the new diagnosis fields (on_task, english,
    affect) let a test script off-task / non-English / mood turns. Each defaults
    to a clean on-task English answer so existing tests are unaffected."""

    def __init__(self, scores, on_task=None, english=None, affect=None):
        self._it = iter(scores)
        self._on_task = iter(on_task) if on_task is not None else None
        self._english = iter(english) if english is not None else None
        self._affect = iter(affect) if affect is not None else None

    async def __call__(self, node, messages, user_input):
        score = next(self._it)
        return DiagnosisEval(
            score=score,
            understanding="x",
            errors=[] if score >= 0.6 else ["e"],
            strengths=["s"] if score >= 0.6 else [],
            next_focus="n",
            on_task=next(self._on_task) if self._on_task is not None else True,
            english=next(self._english) if self._english is not None else True,
            affect=next(self._affect) if self._affect is not None else "neutral",
        )


async def _fake_stream(spec):
    # Ignore the real provider; emit deterministic tokens.
    for tok in ("ok", " ", "done"):
        yield tok


@pytest.fixture(autouse=True)
def _patch_ai(monkeypatch):
    # evaluate_answer is bound into the evaluate node module at import time.
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer", None, raising=False
    )
    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)

    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr("app.services.session_service.summarize_session", _fake_summary)
    yield
    svc.SessionStore.clear()


def _set_eval(monkeypatch, scores, on_task=None, english=None, affect=None):
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores(scores, on_task=on_task, english=english, affect=affect),
    )


async def _drain(agen):
    async for _ in agen:
        pass


# ---------- tests ----------

async def test_bridge_three_attempt_cap(monkeypatch):
    # Sub-0.4 every turn: bridge until the 3-cap, then re-anchor on teach
    # (NOT strengthen — a sub-0.4 answer contradicts "skill present-but-shaky").
    _set_eval(monkeypatch, [0.3, 0.3, 0.3, 0.3])
    _sid, state = await svc.start_session("u1", "comm_01_self_intro")
    state["turn_count"] = 1  # skip opening; go straight to scored turns

    routes = []
    for _ in range(4):
        await _drain(svc.run_turn(_sid, "answer"))
        routes.append(state["last_route"])

    assert routes == ["bridge", "bridge", "bridge", "teach"]
    assert state["bridge_attempts"] == 3  # capped, did not reach 4


async def test_strengthen_cap_escapes_plateau(monkeypatch):
    # Stuck in the 0.4-0.6 dead zone: strengthen twice, then scaffold DOWN to
    # bridge instead of looping strengthen forever (council fix #1).
    _set_eval(monkeypatch, [0.5, 0.5, 0.5])
    _sid, state = await svc.start_session("u1b", "comm_01_self_intro")
    state["turn_count"] = 1

    routes = []
    for _ in range(3):
        await _drain(svc.run_turn(_sid, "half answer"))
        routes.append(state["last_route"])

    assert routes == ["strengthen", "strengthen", "bridge"]
    assert state["strengthen_attempts"] == 2  # not reset (no pass), capped escape


async def test_strengthen_attempts_reset_on_pass(monkeypatch):
    # A clean pass clears the plateau counter so the next stall starts fresh.
    _set_eval(monkeypatch, [0.5, 0.5, 0.9])
    _sid, state = await svc.start_session("u1c", "comm_01_self_intro")
    state["turn_count"] = 1

    for _ in range(3):
        await _drain(svc.run_turn(_sid, "answer"))

    assert state["strengthen_attempts"] == 0  # reset by the passing answer


async def test_ema_mastery_no_spike(monkeypatch):
    _set_eval(monkeypatch, [1.0])
    _sid, state = await svc.start_session("u2", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "great answer"))
    # EMA from 0 with alpha 0.3: one perfect answer -> 0.3, not 1.0
    assert state["current_mastery"] == pytest.approx(0.3)


async def test_mastery_flat_below_floor(monkeypatch):
    # Sub-floor (0.5) answers must NOT inch the EMA up and fake progress.
    _set_eval(monkeypatch, [0.5, 0.5, 0.5])
    _sid, state = await svc.start_session("u2b", "comm_01_self_intro")
    state["turn_count"] = 1

    for _ in range(3):
        await _drain(svc.run_turn(_sid, "half answer"))

    assert state["current_mastery"] == pytest.approx(0.0)  # never raised


async def test_node_advance_on_clean_streak(monkeypatch):
    # Advance is gated on a 2-pass clean streak, NOT EMA mastery.
    _set_eval(monkeypatch, [1.0, 1.0])
    _sid, state = await svc.start_session("u3", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "pass one"))
    assert state["competency_node"] == "comm_01_self_intro"  # one pass != advance

    await _drain(svc.run_turn(_sid, "pass two"))
    assert state["competency_node"] == "comm_02_describe_routine"
    assert state["current_mastery"] == 0.0      # reset for the new node
    assert state["bridge_attempts"] == 0
    assert state["strengthen_attempts"] == 0
    assert "comm_01_self_intro" in state["node_history"]


async def test_advance_streams_new_node_opening(monkeypatch):
    # Desync fix #5: advancing mid-turn streams an opening for the NEW node so
    # the tutor text matches the post-advance snapshot. The advance turn appends
    # two assistant messages (old-node pedagogy + new-node opening).
    _set_eval(monkeypatch, [1.0, 1.0])
    _sid, state = await svc.start_session("u3b", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "pass one"))
    before = len(state["messages"])
    await _drain(svc.run_turn(_sid, "pass two"))  # this advances

    # user + pedagogy(assistant) + opening(assistant) = 3 new messages
    assert len(state["messages"]) == before + 3
    assert state["messages"][-1]["role"] == "assistant"
    assert state["messages"][-2]["role"] == "assistant"


async def test_clean_pass_no_remediation(monkeypatch):
    _set_eval(monkeypatch, [1.0, 1.0])  # 2 clean passes, attempts==2 -> clean
    _sid, state = await svc.start_session("u4", "comm_01_self_intro")
    state["turn_count"] = 1

    for _ in range(2):
        await _drain(svc.run_turn(_sid, "mastered"))

    assert state["node_history"]["comm_01_self_intro"]["clean"] is True
    assert state["remediation"] is False


async def test_low_passrate_flags_remediation(monkeypatch):
    # A broken streak pushes attempts past the clean cap (>2) before advance,
    # so the node is logged not-clean and the module flags remediation.
    _set_eval(monkeypatch, [1.0, 0.5, 1.0, 1.0])
    _sid, state = await svc.start_session("u5", "comm_01_self_intro")
    state["turn_count"] = 1

    for _ in range(4):
        if state["module_done"] or state["competency_node"] != "comm_01_self_intro":
            break
        await _drain(svc.run_turn(_sid, "answer"))

    hist = state["node_history"]["comm_01_self_intro"]
    assert hist["attempts"] == 4
    assert hist["clean"] is False          # took >2 attempts
    assert state["remediation"] is True    # 0/1 clean < 0.5 floor


# ---------- fix #1/#6: on_task/english split + redirect ----------

async def test_fluent_offtask_routes_redirect(monkeypatch):
    # Competent English but answering a different question: scores 0.0 by the
    # ruthless rubric, but must NOT be treated as a struggling learner. Route to
    # redirect (point them back at the skill), not bridge (scaffold down).
    _set_eval(monkeypatch, [0.0], on_task=[False], english=[True])
    _sid, state = await svc.start_session("o1", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "I completely disagree with your premise"))
    assert state["last_route"] == "redirect"


async def test_nonenglish_nonanswer_still_bridges(monkeypatch):
    # Off-task AND not real English (gibberish / other language) is a genuine
    # non-answer — keep the existing scaffold-down to bridge.
    _set_eval(monkeypatch, [0.0], on_task=[False], english=[False])
    _sid, state = await svc.start_session("o2", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "asdkjfh qwiueh"))
    assert state["last_route"] == "bridge"


async def test_offtask_does_not_scaffold_or_break_streak(monkeypatch):
    # Repeated fluent off-task answers must not corrupt struggle bookkeeping:
    # no scaffold, no level_fails, clean_streak untouched.
    _set_eval(
        monkeypatch,
        [0.0, 0.0, 0.0],
        on_task=[False, False, False],
        english=[True, True, True],
    )
    _sid, state = await svc.start_session("o3", "comm_01_self_intro")
    state["turn_count"] = 1

    for _ in range(3):
        await _drain(svc.run_turn(_sid, "off topic but fluent"))

    assert state["scaffold"] == 0
    assert state["level_fails"] == 0
    assert state["clean_streak"] == 0
    assert state["last_route"] == "redirect"


# ---------- fix #2: ceiling escape ----------

async def test_first_try_high_score_routes_challenge(monkeypatch):
    # A near-perfect FIRST answer should not be re-taught — stretch immediately.
    _set_eval(monkeypatch, [0.9])
    _sid, state = await svc.start_session("c1", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(_sid, "fully fluent first attempt"))
    assert state["last_route"] == "challenge"


# ---------- fix #3: bridge dead-end -> graceful ease ----------

async def test_bridge_giveup_offers_ease(monkeypatch):
    # Stuck hard-failing past the bridge cap AND the give-up threshold: stop
    # drilling, offer an easing off-ramp instead of teaching forever.
    _set_eval(monkeypatch, [0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
    _sid, state = await svc.start_session("e1", "comm_01_self_intro")
    state["turn_count"] = 1

    routes = []
    for _ in range(6):
        await _drain(svc.run_turn(_sid, "still failing"))
        routes.append(state["last_route"])

    assert routes[:3] == ["bridge", "bridge", "bridge"]
    assert routes[-1] == "ease"
