#!/usr/bin/env bash
set -euo pipefail

# Local beta runtime only. The Python launcher reads the selected dotenv file
# before applying safe beta defaults, so a linked worktree cannot inherit a
# different worktree's provider or CORS configuration by accident.
# DATA_REGION=india also selects ZIDD_JWT_SECRET_IND in app.config.

ENV_FILE="${ZIDD_ENV_FILE:-.env}"
if [[ -n "${ZIDD_ENV_FILE:-}" && ! -f "$ENV_FILE" ]]; then
  echo "ZIDD_ENV_FILE does not exist: $ENV_FILE" >&2
  exit 2
fi

LAUNCHER_ARGS=(scripts/run_india_beta.py --host 127.0.0.1 --port "${PORT:-8088}")
if [[ -f "$ENV_FILE" ]]; then
  LAUNCHER_ARGS+=(--env-file "$ENV_FILE")
fi

exec python3 "${LAUNCHER_ARGS[@]}"
