"""Finding #11 — placement AI failure must log + fall back, not swallow silently."""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from fastapi.testclient import TestClient

from app.content.registry import COMM_ID, get_module
from app.main import app
from app.services import session_service as svc

AUTH = {"Authorization": "Bearer test_token"}


def test_placement_ai_failure_logs_and_falls_back(monkeypatch, caplog):
    async def _boom(module_id, writing_sample, self_report, grade):
        raise RuntimeError("ollama down")

    monkeypatch.setattr(svc, "place_user", _boom)

    client = TestClient(app)
    with caplog.at_level("WARNING", logger="app.api.routes"):
        r = client.post(
            "/onboarding/placement", json={"module_id": COMM_ID}, headers=AUTH
        )
    assert r.status_code == 200
    first_node = get_module(COMM_ID).nodes[0].id
    assert r.json() == {"node_id": first_node, "cefr_estimate": "A1"}
    # The failure must be observable, not silent.
    assert any("placement failed" in rec.getMessage() for rec in caplog.records)


def test_placement_unknown_module_is_404(monkeypatch):
    # The narrow KeyError path is unchanged: a genuinely unknown module is a 404.
    async def _missing(module_id, writing_sample, self_report, grade):
        raise KeyError(module_id)

    monkeypatch.setattr(svc, "place_user", _missing)
    client = TestClient(app)
    r = client.post(
        "/onboarding/placement", json={"module_id": COMM_ID}, headers=AUTH
    )
    assert r.status_code == 404
