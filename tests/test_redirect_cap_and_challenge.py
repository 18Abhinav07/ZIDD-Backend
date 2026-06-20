"""P0-6 — redirect soft-lock escape + reachable challenge route.

Two engine defects this pins:

  1. `redirect` had NO attempt cap. A fluent-but-off-task learner routed to
     redirect forever (redirect_node touches no progression counters and
     _update_progress early-returns on on_task=False), an infinite soft-lock.
     After REDIRECT_ATTEMPT_CAP steer-backs the router must escape to `teach`.

  2. `challenge` was effectively unreachable. The old gate `mastery > 0.8` can
     never be crossed (the EMA asymptotes to the score), and the ceiling escape
     keyed on lifetime `attempts` which a returning learner loads >1 from disk.
     Challenge must now fire on a clean streak and on an early session ceiling
     answer regardless of lifetime attempts.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.graph import route  # noqa: E402
from app.graph.route import route_node  # noqa: E402


# ---------- pure route_node unit tests ----------

def _state(**over) -> dict:
    base = {
        "last_eval_score": 0.0,
        "current_mastery": 0.0,
        "last_diagnosis": {"on_task": True, "english": True},
        "clean_streak": 0,
        "attempts": 0,
        "session_attempts": 0,
        "redirect_attempts": 0,
        "bridge_attempts": 0,
        "strengthen_attempts": 0,
        "clarify_attempts": 0,
        "level_fails": 0,
    }
    base.update(over)
    return base


def _offtask(**over):
    d = {"on_task": False, "english": True}
    return _state(last_diagnosis=d, last_eval_score=0.0, **over)


def test_redirect_fires_below_cap():
    assert route_node(_offtask(redirect_attempts=0)) == "redirect"
    assert route_node(_offtask(redirect_attempts=route.REDIRECT_ATTEMPT_CAP - 1)) == "redirect"


def test_redirect_escapes_to_teach_at_cap():
    # Soft-lock broken: once the cap is reached, stop steering and deliver content.
    assert route_node(_offtask(redirect_attempts=route.REDIRECT_ATTEMPT_CAP)) == "teach"
    assert route_node(_offtask(redirect_attempts=route.REDIRECT_ATTEMPT_CAP + 3)) == "teach"


def test_challenge_reachable_on_clean_streak():
    # A solid answer with at least one clean pass behind it stretches, not re-teaches.
    assert route_node(_state(last_eval_score=0.75, clean_streak=1)) == "challenge"


def test_no_challenge_without_streak_or_ceiling():
    # A solid answer with no streak and not near-perfect is taught, not challenged.
    assert route_node(_state(last_eval_score=0.72, clean_streak=0, session_attempts=4)) == "teach"


def test_ceiling_escape_uses_session_attempts_for_returning_learner():
    # The decisive fix: a returning learner has high lifetime `attempts`, but their
    # FIRST strong answer this session (session_attempts==1) must still ceiling-escape.
    st = _state(last_eval_score=0.9, attempts=7, session_attempts=1, clean_streak=0)
    assert route_node(st) == "challenge"


def test_ceiling_escape_does_not_fire_after_grinding_this_session():
    st = _state(last_eval_score=0.9, attempts=7, session_attempts=5, clean_streak=0)
    assert route_node(st) == "teach"


def test_old_mastery_gate_no_longer_required():
    # Even with mastery stuck below the old unreachable >0.8 gate, a streak answer
    # still reaches challenge — the whole point of the fix.
    st = _state(last_eval_score=0.8, current_mastery=0.4, clean_streak=1)
    assert route_node(st) == "challenge"


# ---------- end-to-end through run_turn ----------

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.services import session_service as svc  # noqa: E402


class _Scores:
    def __init__(self, scores, on_task=None, english=None):
        self._it = iter(scores)
        self._on_task = iter(on_task) if on_task is not None else None
        self._english = iter(english) if english is not None else None

    async def __call__(self, node, messages, user_input, behavior=None):
        score = next(self._it)
        return DiagnosisEval(
            score=score, understanding="x",
            errors=[] if score >= 0.6 else ["e"],
            strengths=["s"] if score >= 0.6 else [],
            next_focus="n",
            on_task=next(self._on_task) if self._on_task is not None else True,
            english=next(self._english) if self._english is not None else True,
        )


async def _fake_stream(spec):
    for tok in ("ok", " ", "done"):
        yield tok


@pytest.fixture(autouse=True)
def _patch_ai(monkeypatch):
    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)
    # Bypass the deterministic langdetect pre-gate: it runs BEFORE the (faked)
    # evaluator and short-text langdetect is unreliable, so it would otherwise
    # misroute our English off-task probes to clarify. We are testing the routing
    # cap, so let the fake eval's english/on_task flags drive the route.
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.fails_language_gate", lambda *a, **k: False
    )

    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr("app.services.session_service.summarize_session", _fake_summary)
    yield
    svc.SessionStore.clear()


async def _drain(agen):
    async for _ in agen:
        pass


@pytest.mark.asyncio
async def test_fluent_offtask_eventually_escapes_redirect(monkeypatch):
    # Four consecutive fluent-off-task answers: redirect three times, then escape.
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores([0.0, 0.0, 0.0, 0.0], on_task=[False] * 4, english=[True] * 4),
    )
    sid, state = await svc.start_session("rc1", "comm_01_self_intro")
    state["turn_count"] = 1

    routes = []
    for _ in range(4):
        await _drain(svc.run_turn(sid, "fluent but about pizza"))
        routes.append(state["last_route"])

    assert routes == ["redirect", "redirect", "redirect", "teach"]


@pytest.mark.asyncio
async def test_redirect_counter_refunded_after_on_task_recovery(monkeypatch):
    # off-task, off-task (redirect_attempts climbs), then a clean on-task pass
    # refunds the counter to 0, so the next stray is treated as a fresh first stray.
    monkeypatch.setattr(
        "app.graph.nodes.evaluate.evaluate_answer",
        _Scores(
            [0.0, 0.0, 0.9, 0.0],
            on_task=[False, False, True, False],
            english=[True, True, True, True],
        ),
    )
    sid, state = await svc.start_session("rc2", "comm_01_self_intro")
    state["turn_count"] = 1

    await _drain(svc.run_turn(sid, "off 1"))
    await _drain(svc.run_turn(sid, "off 2"))
    assert state["redirect_attempts"] == 2
    await _drain(svc.run_turn(sid, "a strong on-task self introduction"))
    assert state["redirect_attempts"] == 0   # refunded on recovery
    await _drain(svc.run_turn(sid, "off again"))
    assert state["redirect_attempts"] == 1   # counts from a clean slate
    assert state["last_route"] == "redirect"
