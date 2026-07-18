#!/usr/bin/env bash
set -euo pipefail

# Local beta runtime only. It always uses the separate India Supabase project;
# use ZIDD_AI_BACKEND=local when deliberately checking the local Qwen path.
# DATA_REGION=india also selects ZIDD_JWT_SECRET_IND in app.config.
export APP_ENV="${APP_ENV:-dev}"
export DATA_REGION="india"
export AI_BACKEND="${ZIDD_AI_BACKEND:-gemini}"
export BILLING_MODE="disabled"
export CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-http://localhost:3000,http://localhost:3001}"
export GEMINI_TEXT_MODEL="${GEMINI_TEXT_MODEL:-gemini-2.5-flash-lite}"
export GEMINI_STRUCTURED_MODEL="${GEMINI_STRUCTURED_MODEL:-gemini-2.5-flash-lite}"
export GEMINI_TEXT_FALLBACK_MODEL="${GEMINI_TEXT_FALLBACK_MODEL:-gemini-3.1-flash-lite}"
export GEMINI_STRUCTURED_FALLBACK_MODEL="${GEMINI_STRUCTURED_FALLBACK_MODEL:-gemini-3.1-flash-lite}"

exec python3 -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8088}"
