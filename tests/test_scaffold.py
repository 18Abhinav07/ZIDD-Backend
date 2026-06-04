"""Scaffold smoke tests — no network, no real keys required."""
import os

import pytest

# Inject dummy env so Settings() loads without a real .env in CI.
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)


def test_health(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_async_url_driver_swap():
    from app.config import Settings

    s = Settings()
    url = s.async_database_url
    assert url.startswith("postgresql+asyncpg://")
    assert ":6543/" in url
    assert "ssl=require" in url


def test_route_node_bridge_guard():
    """Council fix: 3 failed bridges must escalate out of bridge loop."""
    from app.graph.route import route_node

    base = {"current_mastery": 0.2}
    looping = {**base, "last_eval_score": 0.3, "bridge_attempts": 3}
    assert route_node(looping) != "bridge"  # escalated, not infinite loop

    fresh = {**base, "last_eval_score": 0.3, "bridge_attempts": 0}
    assert route_node(fresh) == "bridge"
