#!/usr/bin/env python3
"""Launch the local India beta with one explicit, reproducible environment."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Mapping

from dotenv import dotenv_values


DEFAULT_CORS_ALLOWED_ORIGINS = "http://localhost:3000,http://localhost:3001"
DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite"
DEFAULT_GEMINI_FALLBACK_MODEL = "gemini-3.1-flash-lite"
DEFAULT_BETA_CREDIT_EXPIRY = "2026-08-31T23:59:59+05:30"


def _configured_or_default(values: Mapping[str, str], key: str, default: str) -> str:
    return str(values.get(key) or default)


def build_runtime_env(
    *,
    environ: Mapping[str, str],
    env_file: Path | None,
) -> dict[str, str]:
    """Apply an optional beta env file before launcher defaults.

    The file wins over ordinary inherited values so a linked worktree cannot
    accidentally retain another worktree's local provider configuration.
    `ZIDD_AI_BACKEND` remains an explicit launcher override for local Qwen QA.
    """

    original = dict(environ)
    values = dict(original)
    if env_file is not None:
        values.update(
            {
                key: value
                for key, value in dotenv_values(env_file).items()
                if value is not None
            }
        )

    requested_backend = original.get("ZIDD_AI_BACKEND") or values.get(
        "ZIDD_AI_BACKEND"
    )
    values["APP_ENV"] = _configured_or_default(values, "APP_ENV", "dev")
    values["DATA_REGION"] = "india"
    values["AI_BACKEND"] = requested_backend or _configured_or_default(
        values, "AI_BACKEND", "gemini"
    )
    # Beta uses the same wallet/debit gates as launch. New accounts receive a
    # fixed, expiring beta grant instead of bypassing billing entirely, so the
    # pricing and entitlement paths receive real-world coverage before sale.
    values["BILLING_MODE"] = "enabled"
    values["BILLING_POLICY"] = "journey"
    values["BETA_CREDIT_GRANT_ENABLED"] = "true"
    values["BETA_CREDIT_GRANT_CREDITS"] = "300"
    values["BETA_CREDIT_GRANT_EXPIRES_AT"] = _configured_or_default(
        values,
        "BETA_CREDIT_GRANT_EXPIRES_AT",
        DEFAULT_BETA_CREDIT_EXPIRY,
    )
    values["CREDIT_PURCHASES_ENABLED"] = "false"
    values["WELCOME_CREDITS"] = "0"
    values["DB_POOL_PRE_PING"] = _configured_or_default(
        values, "DB_POOL_PRE_PING", "false"
    )
    values["CORS_ALLOWED_ORIGINS"] = _configured_or_default(
        values, "CORS_ALLOWED_ORIGINS", DEFAULT_CORS_ALLOWED_ORIGINS
    )
    values["GEMINI_TEXT_MODEL"] = _configured_or_default(
        values, "GEMINI_TEXT_MODEL", DEFAULT_GEMINI_MODEL
    )
    values["GEMINI_STRUCTURED_MODEL"] = _configured_or_default(
        values, "GEMINI_STRUCTURED_MODEL", DEFAULT_GEMINI_MODEL
    )
    values["GEMINI_TEXT_FALLBACK_MODEL"] = _configured_or_default(
        values, "GEMINI_TEXT_FALLBACK_MODEL", DEFAULT_GEMINI_FALLBACK_MODEL
    )
    values["GEMINI_STRUCTURED_FALLBACK_MODEL"] = _configured_or_default(
        values,
        "GEMINI_STRUCTURED_FALLBACK_MODEL",
        DEFAULT_GEMINI_FALLBACK_MODEL,
    )
    return values


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args(argv)

    runtime_env = build_runtime_env(environ=os.environ, env_file=args.env_file)
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host",
        args.host,
        "--port",
        str(args.port),
    ]
    os.execvpe(command[0], command, runtime_env)


if __name__ == "__main__":
    main()
