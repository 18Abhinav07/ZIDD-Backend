import asyncio
from types import SimpleNamespace

from app.api import school_rebuild_routes


def test_school_open_answer_uses_configured_cloud_budget_but_keeps_local_unbounded(
    monkeypatch,
):
    monkeypatch.setattr(
        school_rebuild_routes,
        "get_settings",
        lambda: SimpleNamespace(
            ai_backend="gemini",
            school_open_answer_timeout_seconds=21.5,
        ),
    )
    assert school_rebuild_routes._school_open_answer_timeout_seconds() == 21.5

    monkeypatch.setattr(
        school_rebuild_routes,
        "get_settings",
        lambda: SimpleNamespace(
            ai_backend="local",
            school_open_answer_timeout_seconds=21.5,
        ),
    )
    assert school_rebuild_routes._school_open_answer_timeout_seconds() is None


def test_explicit_school_worker_budget_reaches_only_the_school_evaluator(monkeypatch):
    captured: list[float | None] = []

    async def evaluator(_activity, _answer, *, timeout_seconds=None):
        captured.append(timeout_seconds)
        return {"score": 0.9}

    monkeypatch.setattr(
        school_rebuild_routes,
        "evaluate_school_open_answer",
        evaluator,
    )

    result = asyncio.run(
        school_rebuild_routes._evaluate_school_open_answer_with_runtime_policy(
            {"activity_id": "worker-item"},
            "A saved learner answer.",
            timeout_seconds=30.0,
        )
    )

    assert result == {"score": 0.9}
    assert captured == [30.0]
