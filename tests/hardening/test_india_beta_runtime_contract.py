import os
from pathlib import Path

from scripts.run_india_beta import build_runtime_env


ROOT = Path(__file__).resolve().parents[2]


def test_india_beta_runtime_keeps_dev_pool_pre_ping_opt_in() -> None:
    values = build_runtime_env(environ={}, env_file=None)

    assert values["DB_POOL_PRE_PING"] == "false"


def test_india_beta_runtime_accepts_an_explicit_external_env_file() -> None:
    script = (ROOT / "scripts" / "run_india_beta.sh").read_text(encoding="utf-8")

    assert 'ENV_FILE="${ZIDD_ENV_FILE:-.env}"' in script
    assert '"${ZIDD_ENV_FILE:-}"' in script
    assert 'LAUNCHER_ARGS+=(--env-file "$ENV_FILE")' in script


def test_explicit_india_beta_env_file_overrides_launcher_defaults(tmp_path: Path) -> None:
    env_file = tmp_path / "india-beta.env"
    env_file.write_text(
        "\n".join(
            (
                "APP_ENV=qa",
                "AI_BACKEND=gemini",
                "CORS_ALLOWED_ORIGINS=https://beta.example.test",
                "GEMINI_TEXT_MODEL=from-file-text",
                "GEMINI_STRUCTURED_MODEL=from-file-structured",
            )
        ) + "\n",
        encoding="utf-8",
    )
    values = build_runtime_env(
        environ={"PATH": os.environ["PATH"]},
        env_file=env_file,
    )

    assert values["APP_ENV"] == "qa"
    assert values["DATA_REGION"] == "india"
    assert values["AI_BACKEND"] == "gemini"
    assert values["CORS_ALLOWED_ORIGINS"] == "https://beta.example.test"
    assert values["GEMINI_TEXT_MODEL"] == "from-file-text"
    assert values["GEMINI_STRUCTURED_MODEL"] == "from-file-structured"
    assert values["BILLING_MODE"] == "enabled"
    assert values["BILLING_POLICY"] == "journey"
    assert values["BETA_CREDIT_GRANT_ENABLED"] == "true"
    assert values["BETA_CREDIT_GRANT_CREDITS"] == "300"
    assert values["CREDIT_PURCHASES_ENABLED"] == "false"
    assert values["WELCOME_CREDITS"] == "0"


def test_explicit_zidd_backend_override_wins_over_beta_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / "india-beta.env"
    env_file.write_text("AI_BACKEND=gemini\n", encoding="utf-8")

    values = build_runtime_env(
        environ={"ZIDD_AI_BACKEND": "local"},
        env_file=env_file,
    )

    assert values["AI_BACKEND"] == "local"


def test_empty_runtime_values_still_receive_safe_beta_defaults() -> None:
    values = build_runtime_env(
        environ={
            "APP_ENV": "",
            "AI_BACKEND": "",
            "DB_POOL_PRE_PING": "",
            "CORS_ALLOWED_ORIGINS": "",
            "GEMINI_TEXT_MODEL": "",
        },
        env_file=None,
    )

    assert values["APP_ENV"] == "dev"
    assert values["AI_BACKEND"] == "gemini"
    assert values["DB_POOL_PRE_PING"] == "false"
    assert values["CORS_ALLOWED_ORIGINS"] == "http://localhost:3000,http://localhost:3001"
    assert values["GEMINI_TEXT_MODEL"] == "gemini-3.1-flash-lite"
