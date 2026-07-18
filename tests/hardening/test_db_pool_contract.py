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


def test_migration_engine_uses_the_dedicated_migration_url(monkeypatch):
    class FakeSettings:
        async_database_url = (
            "postgresql+asyncpg://runtime:secret@pool.example:6543/postgres?ssl=require"
        )
        migration_async_database_url = (
            "postgresql+asyncpg://migrator:secret@db.example:5432/postgres?ssl=require"
        )
        db_pool_size = 5
        db_max_overflow = 0
        effective_db_pool_pre_ping = False

    monkeypatch.setattr(engine, "get_settings", lambda: FakeSettings())
    engine._migration_engine = None
    try:
        migration_engine = engine.get_migration_engine()
        assert migration_engine.url.host == "db.example"
        assert migration_engine.url.port == 5432
        assert migration_engine.url.username == "migrator"
    finally:
        engine._migration_engine = None
