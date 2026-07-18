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
