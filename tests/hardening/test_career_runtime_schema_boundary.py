from types import SimpleNamespace

import pytest

import app.main as main_module


class _WritableStorage:
    async def ping_writable(self) -> bool:
        return True


class _Engine:
    async def dispose(self) -> None:
        return None


def _install_lifespan_dependencies(monkeypatch, observed_schema_flags: list[bool]) -> None:
    settings = SimpleNamespace(
        app_env="dev",
        runtime_database_configured=True,
    )

    async def validate_schema(*, school_runtime_enabled: bool) -> None:
        observed_schema_flags.append(school_runtime_enabled)

    monkeypatch.setattr(main_module, "get_settings", lambda: settings)
    monkeypatch.setattr(main_module, "get_jwt_secret", lambda: "test-secret")
    monkeypatch.setattr(main_module, "get_storage", lambda: _WritableStorage())
    monkeypatch.setattr(main_module, "validate_runtime_schema", validate_schema)
    monkeypatch.setattr(main_module, "load_sessions", lambda: None)
    monkeypatch.setattr(main_module, "save_sessions", lambda: None)
    monkeypatch.setattr(main_module, "get_engine", lambda: _Engine())


@pytest.mark.asyncio
@pytest.mark.parametrize("school_runtime_enabled", [False, True])
async def test_lifespan_passes_the_school_runtime_state_to_schema_guard(
    monkeypatch,
    school_runtime_enabled,
):
    observed_schema_flags: list[bool] = []
    _install_lifespan_dependencies(monkeypatch, observed_schema_flags)
    monkeypatch.setattr(
        main_module,
        "_school_runtime_enabled",
        school_runtime_enabled,
    )

    if school_runtime_enabled:
        async def worker(**_kwargs) -> None:
            return None

        monkeypatch.setattr(main_module, "run_school_evaluation_worker", worker)
        monkeypatch.setattr(main_module, "notify_school_evaluation_job_enqueued", lambda: None)
        monkeypatch.setattr(
            main_module,
            "school_evaluation_policy",
            lambda _settings: SimpleNamespace(
                max_worker_attempts=1,
                worker_stall_timeout_seconds=1,
            ),
        )

    async with main_module.lifespan(main_module.app):
        pass

    assert observed_schema_flags == [school_runtime_enabled]


@pytest.mark.asyncio
async def test_lifespan_retries_a_transient_storage_probe_before_refusing_boot(
    monkeypatch,
):
    observed_schema_flags: list[bool] = []
    _install_lifespan_dependencies(monkeypatch, observed_schema_flags)
    monkeypatch.setattr(main_module, "_school_runtime_enabled", False)

    class FlakyStorage:
        calls = 0

        async def ping_writable(self) -> bool:
            self.calls += 1
            return self.calls >= 2

    storage = FlakyStorage()
    sleeps: list[float] = []

    async def record_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(main_module, "get_storage", lambda: storage)
    monkeypatch.setattr(main_module.asyncio, "sleep", record_sleep)

    async with main_module.lifespan(main_module.app):
        pass

    assert storage.calls == 2
    assert sleeps == [0.5]
