# Zidd Engine

The backend for **Zidd**, an AI English coach for learners in India. It runs two products on one engine:

- **School**: NCERT-aligned English for Classes 2–5 (47 chapters), with placement, teaching, recap, and parent/teacher-facing reports.
- **Career**: communication practice, mock interviews and group-discussion simulations for job-seekers.

Learners answer in their own words. The engine scores each answer, picks the next teaching move, and streams the reply token by token.

| | |
|---|---|
| **Live API** | https://zidd-api.onrender.com (`/health` for status) |
| **Frontend** | [ZIDD-Frontend](https://github.com/18Abhinav07/ZIDD-Frontend), live at https://zidd.onrender.com |
| **Stack** | Python 3.11 · FastAPI · LangGraph · SQLAlchemy (async) · asyncpg · Postgres + pgvector (Supabase) · Gemini · Groq · Ollama · Razorpay |

> The free Render tier sleeps when idle. The first request after a quiet period can take about a minute while the service wakes.

---

## At a glance

| | |
|---|---|
| Application code | ~84k lines of engine code plus ~96k lines of authored curriculum manifests |
| HTTP routes | 60+ endpoints across 9 mounted routers |
| Database | 36 idempotent SQL migrations, checksummed by a migration runner |
| Tests | 112 test files, 2,300+ test functions (`tests/hardening`, `tests/integration`) |
| Curriculum | 47 NCERT English chapters (Class 2: 13, Class 3: 12, Class 4: 12, Class 5: 10) plus communication, interview and group-discussion modules |
| Architecture docs | [`docs/`](docs): SSE protocol, School rebuild architecture contract, QA reports, migration notes |

---

## How a learner turn works

```
 client ──POST /session/turn──▶ JWT auth ─▶ rate limit ─▶ session service
                                                              │
                              ┌───────────────────────────────┘
                              ▼
                      LangGraph decision graph
        evaluate ─▶ route ─┬─▶ teach        (new idea, worked example)
                           ├─▶ bridge       (score < 0.4: scaffold down, capped at 3)
                           ├─▶ strengthen   (0.4–0.6: reinforce, capped at 2)
                           ├─▶ challenge    (mastered: stretch)
                           ├─▶ redirect     (fluent but off-task)
                           └─▶ ease         (long failure run: graceful off-ramp)
                              │
                              ▼
              AI provider boundary (Gemini key pool · Groq · Ollama)
                              │
          SSE: token frames ─▶ progress_update ─▶ done (state snapshot)
```

- **The graph is a pure decision layer.** It evaluates the answer and builds a prompt but never calls a provider. The service layer streams the generation, so the whole loop is testable offline by swapping a single boundary.
- **Progression uses a clean-pass streak, not an EMA.** A moving average converging on a steady 0.8 never crosses a strict `> 0.8` gate and soft-locks a correct learner. The streak is reachable and a truer signal of readiness. Mastery EMA (`α = 0.3`) ignores sub-0.6 answers, so a run of mediocre answers cannot fake progress.
- **Loops are bounded everywhere.** Bridge (3), strengthen (2) and give-up (5 consecutive hard fails) all have caps that escalate to a different move, so a learner can't be drilled forever.
- **Fluent-but-off-task answers aren't treated as failure.** A language gate (`langdetect`) separates "wrong language" from "right language, wrong question". The second routes to `redirect` and leaves the streak and scaffold counters alone.
- **The stream contract is documented.** [`docs/sse-protocol.md`](docs/sse-protocol.md) defines token, `progress_update` and `done` frames.

---

## Engineering decisions

### Reliability

- **Fail-closed boot.** The lifespan refuses to start unless the JWT secret is set, the database is writable (5 probes with exponential backoff to absorb pooler handshake blips), and the runtime schema passes `validate_runtime_schema`. A bad deploy fails at boot, not on a learner's first request.
- **Durable evaluation jobs.** Open-answer grading for School runs through a Postgres-backed job queue with retry scheduling, attempt caps, stall timeouts, atomic completion and request metadata (see `app/services/school/evaluation_jobs.py` and migrations `2026-07-18/19-*`). A crash mid-grade resumes rather than losing the answer.
- **Idempotency on money and state.** Session start, answer submission and attempt charges all carry idempotency keys with claim generations (`2026-07-06/11-*` migrations), so a client retry never double-charges or double-starts.
- **Provider resilience.** `app/ai/provider.py` classifies upstream errors (auth, rate-limit, transient, model-unavailable, non-retryable) and reacts per class. `GeminiCredentialManager` runs a pool of numbered keys (`GEMINI_API_KEY_1…N`) with per-quota-scope health, rotating on 429s. Model fallback chains are configurable. A startup probe makes a real bounded call, because a configured key can still lack access to the chosen model.
- **LLM concurrency control.** A global semaphore caps concurrent model calls; one slot is reserved for Career's request path so queued School grading can't starve interactive sessions.

### Security

- **Auth.** Google ID-token verification server-side, then a backend-minted HS256 JWT. Auth middleware gates everything except `/auth`, `/health` and the signed Razorpay webhook.
- **Secrets discipline.** `ZIDD_JWT_SECRET` is mandatory, with a ≥32-character check in `prod`. A separate signing key is used for the India data region. The test-auth bypass needs two explicit opt-ins and is hard-blocked in `prod`.
- **Abuse limits.** Per-IP auth throttling, per-user daily turn caps, per-user active-session caps, input length caps.
- **CORS.** Explicit allow-list only, no wildcard, mounted outermost so preflights are answered before auth and rate-limit logic.
- **Database.** Row-level security enabled on all tables, so a leaked anon key reads nothing. Runtime and migration connections are separate.
- **History hygiene.** No credentials in the tree or in any commit on any branch.

### Data and payments

- **Postgres on Supabase transaction pooler.** `NullPool`, `statement_cache_size=0` and unique prepared-statement names, all required to avoid asyncpg/pgbouncer collisions. The reasons are documented in `app/db/engine.py`.
- **pgvector memory.** Session summaries are embedded (768-dim) and recalled per learner and competency node for continuity across sessions.
- **Data residency switch.** `DATA_REGION=india` selects a separate database, pooler and signing key.
- **Credit wallet.** Lot-based ledger where expiring grants are spent before purchased credit. Allocation is a pure, independently tested function. Razorpay orders and a signature-verified webhook feed it. `BILLING_MODE=disabled` turns the whole surface into 404s for free or beta deployments.

### Content engineering

- **Authored, validated curriculum.** Each chapter ships as a JSON bundle with a Python manifest, and audit scripts (`scripts/audit_school_*`, `validate_school_v3_content.py`) check structure, source provenance, instruction parity and semantic quality. Contract tests pin the result.
- **Grading that resists gaming.** Deterministic answer matching runs first, an LLM judge handles open answers, and adversarial tests probe the grader (`test_school_semantic_grading_adversarial.py`).
- **Placement and reports.** A scheduled placement diagnostic builds an evidence-scoped growth report; recap and support flows unlock from it.

---

## Repository layout

```
app/
  main.py              Lifespan, middleware stack, router wiring
  config.py            Typed settings (pydantic-settings), region and billing switches
  api/                 auth · health · me · onboarding · session · billing · school_* routers
  middleware/          JWT auth · rate limiting · LLM concurrency lanes
  graph/               LangGraph decision graph: evaluate, route, 7 pedagogy nodes
  ai/                  Provider boundary, Gemini key pool, structured output, prompts, Ollama
  services/            Session engine, assessment, rubrics, simulation, School rebuild services
  billing/             Wallet lots, pricing, Razorpay client, gating
  db/                  Async engine, repo, schema guard, migrations/
  storage/             Postgres store (jobs, sessions)
  content/             Curriculum JSON, manifests, NCERT source maps
scripts/               Migration runner, content audits, load and persona harnesses
tests/                 hardening/ (unit and contract) · integration/ (opt-in, disposable DB)
docs/                  SSE protocol, architecture contracts, QA reports
```

---

## Run locally

Requires Python 3.11 and a Postgres database (a free Supabase project works).

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env            # fill in the values below
python scripts/apply_migrations.py   # idempotent; safe to re-run

uvicorn app.main:app --reload --port 8080
curl localhost:8080/health
```

For zero-quota development, set `AI_BACKEND=local` and run [Ollama](https://ollama.com) with `qwen2.5:14b`. For cloud models, set `AI_BACKEND=cloud` and provide Gemini and Groq keys.

### Configuration

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_POOLER_URL` | yes | Transaction-pooler URL (port 6543); the code adds the asyncpg driver and SSL |
| `ZIDD_JWT_SECRET` | yes | HS256 signing secret (≥32 chars when `APP_ENV=prod`) |
| `GOOGLE_CLIENT_ID` | yes | Audience for verifying Google ID tokens |
| `CORS_ALLOWED_ORIGINS` | yes | Comma-separated frontend origins |
| `AI_BACKEND` | yes | `local` (Ollama) or `cloud` (Gemini + Groq) |
| `GEMINI_API_KEY` / `GEMINI_API_KEY_1…N` | cloud | One key or a rotating pool |
| `GROQ_API_KEY` | cloud | Groq models |
| `APP_ENV` | no | `dev` · `test` · `prod` |
| `BILLING_MODE` | no | `enabled` or `disabled` |
| `RAZORPAY_KEY_ID` / `_KEY_SECRET` / `_WEBHOOK_SECRET` | if billing | Payments |
| `SESSION_TTL_SECONDS`, `MAX_ACTIVE_SESSIONS_PER_USER`, `SESSION_TURN_LIMIT_PER_DAY`, `AUTH_GOOGLE_LIMIT_PER_MINUTE` | no | Abuse limits |
| `DATA_REGION` | no | `default` or `india` |

### Tests

```bash
pytest -q tests                      # hardening and contract suite; no external services
pytest -m integration tests/integration   # opt-in; needs a disposable Postgres
```

`conftest.py` sets the test-only auth opt-ins so the suite boots without credentials.

---

## Deploy

The included `Dockerfile` builds a Python 3.11 image that binds to `$PORT` (default 8080), so it runs unchanged on Render, Cloud Run or Fly. The live deployment is a Render web service built from this repo.

1. Create a Supabase project and run `python scripts/apply_migrations.py` with `SUPABASE_POOLER_URL` set.
2. Create the web service from this repo and set the variables above, with `APP_ENV=prod`.
3. Set `CORS_ALLOWED_ORIGINS` to the frontend's origin.
4. Check `GET /health` (service, DB and AI readiness) before sending traffic.

---

## Related

- Frontend: [ZIDD-Frontend](https://github.com/18Abhinav07/ZIDD-Frontend)
- Protocol: [`docs/sse-protocol.md`](docs/sse-protocol.md)
- School architecture: [`docs/school-prep-rebuild-architecture-contract.md`](docs/school-prep-rebuild-architecture-contract.md)
