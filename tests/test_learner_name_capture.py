"""Learner display name: captured at registration, sourced into every session.

The coach could never address the learner by name because register stored
name="" and start_session never sourced a name (learner_name defaulted to "").
Now register persists an optional display name on the profile, and start_session
reads it back so coach_view can personalise the directives.

Offline: a dedicated LocalStore is injected; no AI or network.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from fastapi.testclient import TestClient  # noqa: E402

import app.api.auth as auth_mod  # noqa: E402
from app.main import app  # noqa: E402
from app.services import session_service as svc  # noqa: E402
from app.storage.local_store import LocalStore  # noqa: E402

pytestmark = pytest.mark.asyncio

NODE = "comm_00_greetings"  # a PREP node -> start_session stays fully offline


async def test_register_persists_trimmed_display_name(tmp_path, monkeypatch):
    store = LocalStore(str(tmp_path / "reg.db"))
    monkeypatch.setattr(auth_mod, "get_storage", lambda: store)

    client = TestClient(app)
    r = client.post(
        "/auth/register",
        json={"user_id": "newbie", "password": "pw", "name": "  Asha  "},
    )
    assert r.status_code == 200

    prof = await store.get_profile("newbie")
    assert prof is not None
    assert prof["name"] == "Asha"  # trimmed


async def test_register_without_name_stays_blank(tmp_path, monkeypatch):
    store = LocalStore(str(tmp_path / "reg2.db"))
    monkeypatch.setattr(auth_mod, "get_storage", lambda: store)

    client = TestClient(app)
    r = client.post("/auth/register", json={"user_id": "anon", "password": "pw"})
    assert r.status_code == 200

    prof = await store.get_profile("anon")
    assert prof["name"] == ""


async def test_start_session_sources_name_from_profile(tmp_path, monkeypatch):
    store = LocalStore(str(tmp_path / "named.db"))
    await store.ensure_profile("learner_x", name="Asha", password_hash="x")
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    sid, state = await svc.start_session("learner_x", NODE)
    try:
        assert state["learner_name"] == "Asha"
    finally:
        svc.SessionStore.pop(sid, None)


async def test_start_session_blank_name_when_profile_unnamed(tmp_path, monkeypatch):
    store = LocalStore(str(tmp_path / "unnamed.db"))
    await store.ensure_profile("learner_y", name="", password_hash="x")
    monkeypatch.setattr(svc, "get_storage", lambda: store)

    sid, state = await svc.start_session("learner_y", NODE)
    try:
        assert state["learner_name"] == ""
    finally:
        svc.SessionStore.pop(sid, None)
