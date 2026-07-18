import pytest
from sqlalchemy.engine import make_url

from app.config import Settings, get_jwt_secret, get_settings
from scripts import apply_migrations
from scripts import preflight_school_migrations


def _settings(**overrides) -> Settings:
    values = {
        "data_region": "india",
        "supabase_pooler_url": "postgresql://legacy:old@legacy.example:6543/postgres",
        "supabase_db_password": "old",
        "supabase_transaction_pooler_url_ind": (
            "postgresql://postgres.project:placeholder@pool.india.example:6543/postgres"
        ),
        "supabase_direct_url_ind": (
            "postgresql://postgres:placeholder@db.india.example:5432/postgres"
        ),
        "supabase_db_password_ind": "p@ss:/?# with spaces",
    }
    values.update(overrides)
    return Settings(**values)


def test_india_runtime_uses_transaction_pooler_and_separate_password():
    settings = _settings()

    url = make_url(settings.async_database_url)

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "pool.india.example"
    assert url.port == 6543
    assert url.username == "postgres.project"
    assert url.password == "p@ss:/?# with spaces"
    assert url.database == "postgres"
    assert "ssl" not in url.query


def test_india_migrations_use_direct_endpoint_with_same_safe_password():
    settings = _settings()

    url = make_url(settings.migration_async_database_url)

    assert url.drivername == "postgresql+asyncpg"
    assert url.host == "db.india.example"
    assert url.port == 5432
    assert url.username == "postgres"
    assert url.password == "p@ss:/?# with spaces"
    assert url.database == "postgres"
    assert "ssl" not in url.query


def test_default_region_preserves_legacy_runtime_and_migration_endpoint():
    settings = _settings(data_region="default")

    runtime = make_url(settings.async_database_url)
    migration = make_url(settings.migration_async_database_url)

    assert runtime.host == "legacy.example"
    assert migration.host == "legacy.example"
    assert runtime.password == "old"
    assert migration.password == "old"


def test_india_configuration_fails_closed_when_required_endpoint_missing():
    settings = _settings(supabase_transaction_pooler_url_ind="")

    assert settings.runtime_database_configured is False
    assert settings.migration_database_configured is True


def test_india_runtime_uses_its_dedicated_jwt_secret(monkeypatch):
    monkeypatch.setenv("DATA_REGION", "india")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ZIDD_JWT_SECRET", "")
    monkeypatch.setenv("ZIDD_JWT_SECRET_IND", "i" * 48)
    get_settings.cache_clear()
    get_jwt_secret.cache_clear()

    try:
        assert get_jwt_secret() == "i" * 48
    finally:
        get_settings.cache_clear()
        get_jwt_secret.cache_clear()


def test_india_runtime_rejects_a_short_dedicated_jwt_secret(monkeypatch):
    monkeypatch.setenv("DATA_REGION", "india")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("ZIDD_JWT_SECRET", "")
    monkeypatch.setenv("ZIDD_JWT_SECRET_IND", "too-short")
    get_settings.cache_clear()
    get_jwt_secret.cache_clear()

    try:
        with pytest.raises(RuntimeError, match="ZIDD_JWT_SECRET_IND must be at least 32"):
            get_jwt_secret()
    finally:
        get_settings.cache_clear()
        get_jwt_secret.cache_clear()


@pytest.mark.asyncio
async def test_direct_preflight_passes_tls_as_driver_option_not_server_parameter(
    monkeypatch,
):
    captured = {}

    class Transaction:
        async def start(self):
            return None

        async def rollback(self):
            return None

    class Connection:
        def transaction(self, **kwargs):
            captured["transaction"] = kwargs
            return Transaction()

        async def close(self):
            captured["closed"] = True

    async def fake_connect(dsn, *, statement_cache_size, ssl):
        captured.update(
            dsn=dsn,
            statement_cache_size=statement_cache_size,
            ssl=ssl,
        )
        return Connection()

    async def fake_collect(connection, database_url):
        return {"ok": True, "database": database_url}

    monkeypatch.setattr(preflight_school_migrations.asyncpg, "connect", fake_connect)
    monkeypatch.setattr(
        preflight_school_migrations,
        "collect_preflight",
        fake_collect,
    )

    result = await preflight_school_migrations.run_preflight(
        "postgresql+asyncpg://user:secret@db.example:5432/postgres"
        "?ssl=require"
    )

    assert result["ok"] is True
    assert "ssl=" not in captured["dsn"]
    assert captured["ssl"] == "require"
    assert captured["statement_cache_size"] == 0
    assert captured["closed"] is True


@pytest.mark.asyncio
async def test_fresh_database_bootstrap_does_not_replay_historical_bodies(
    monkeypatch,
    tmp_path,
):
    events = []

    class Connection:
        async def execute(self, statement, parameters=None):
            events.append("lock")

        async def exec_driver_sql(self, statement):
            events.append("historical_body")

    class Context:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *args):
            return None

    class Engine:
        def begin(self):
            return Context()

        async def dispose(self):
            events.append("disposed")

    class MigrationSettings:
        migration_database_configured = True
        migration_async_database_url = "postgresql+asyncpg://redacted"
        supabase_pooler_url = "postgresql://redacted"

    async def classify(connection):
        return "fresh"

    async def final_schema(connection):
        events.append("final_schema")

    async def canonical(connection, snapshot):
        events.append(f"canonical:{snapshot.path.name}")

    async def validate(connection):
        events.append("validated")

    async def mark(connection, snapshots, **kwargs):
        events.append(f"marked:{kwargs.get('include_canonical', False)}")

    async def preflight(connection, database_url):
        return {"ok": True}

    monkeypatch.setattr(apply_migrations, "get_settings", lambda: MigrationSettings())
    monkeypatch.setattr(apply_migrations, "get_migration_engine", lambda: Engine())
    monkeypatch.setattr(apply_migrations, "_classify_predecessor", classify)
    monkeypatch.setattr(apply_migrations, "_apply_final_schema", final_schema)
    monkeypatch.setattr(apply_migrations, "_apply_canonical_migration", canonical)
    monkeypatch.setattr(apply_migrations, "validate_runtime_schema", validate)
    monkeypatch.setattr(
        apply_migrations,
        "_mark_reconciled_school_migrations",
        mark,
    )
    monkeypatch.setattr(
        apply_migrations,
        "collect_preflight_on_connection",
        preflight,
    )
    monkeypatch.setattr(apply_migrations, "write_preflight_output", lambda *args: None)

    await apply_migrations.apply(
        apply_migrations.DEFAULT_MIGRATIONS,
        preflight_output=tmp_path / "preflight.json",
        reconcile_predecessor=True,
    )

    assert "final_schema" in events
    assert "historical_body" not in events
    assert not any(event.startswith("canonical:") for event in events)
    assert "marked:True" in events
