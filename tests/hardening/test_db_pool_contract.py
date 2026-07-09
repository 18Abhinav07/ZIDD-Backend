from app.config import get_settings
from app.db import engine


def test_sessionmaker_is_reused_with_single_engine():
    engine._engine = None
    engine._sessionmaker = None
    get_settings.cache_clear()
    try:
        first = engine.get_sessionmaker()
        second = engine.get_sessionmaker()
        assert first is second
        assert engine.get_engine() is engine.get_engine()
    finally:
        engine._engine = None
        engine._sessionmaker = None
        get_settings.cache_clear()


def test_pool_pre_ping_is_disabled_by_default():
    assert get_settings().db_pool_pre_ping is False


def test_pool_pre_ping_is_enabled_effectively_in_production(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("DB_POOL_PRE_PING", raising=False)
    try:
        assert get_settings().effective_db_pool_pre_ping is True
    finally:
        get_settings.cache_clear()
