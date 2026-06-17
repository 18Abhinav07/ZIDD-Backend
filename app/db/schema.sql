-- Zidd engine schema (architecture-v3 §408). Run once against Supabase.
-- Text + vectors only. NEVER store raw audio/files here (3GB free-tier rule).

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- learners ----------
CREATE TABLE IF NOT EXISTS learner_profiles (
    user_id         TEXT PRIMARY KEY,
    display_name    TEXT,
    password_hash   TEXT,
    credits         INTEGER NOT NULL DEFAULT 0,
    -- Judge/demo bypass (architecture-v3 §621): when true, credit-deduction
    -- middleware skips ALL paywalls. NON-NEGOTIABLE for XPRIZE judging.
    demo_unlimited  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- sessions ----------
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    ended_at        TIMESTAMPTZ,
    turn_count      INTEGER NOT NULL DEFAULT 0,
    final_mastery   REAL,
    summary         TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- ---------- long-term memory (pgvector) ----------
CREATE TABLE IF NOT EXISTS memory_entries (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    session_id      TEXT,
    competency_node TEXT NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(768),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_memory_user_node
    ON memory_entries(user_id, competency_node);
-- NOTE: no IVFFlat index until >10K rows (architecture-v3 §408). Exact scan
-- is faster and recall-perfect below that threshold.

-- ---------- per-node mastery ----------
CREATE TABLE IF NOT EXISTS competency_nodes (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    mastery         REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    clean_pass      BOOLEAN NOT NULL DEFAULT FALSE,  -- passed in <=2 attempts
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, competency_node)
);

-- ---------- credit ledger ----------
CREATE TABLE IF NOT EXISTS credit_transactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES learner_profiles(user_id),
    delta       INTEGER NOT NULL,        -- negative = spend, positive = grant
    reason      TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_credit_user ON credit_transactions(user_id);

-- ---------- row-level security ----------
-- Lock every table to superuser / service_role only. No policies are defined,
-- so anon + authenticated keys get ZERO access. The backend connects via the
-- transaction pooler as the `postgres` role, which bypasses RLS, so the engine
-- is unaffected. Defense-in-depth for the XPRIZE public submission: a leaked
-- anon key cannot read learner data.
ALTER TABLE learner_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_entries      ENABLE ROW LEVEL SECURITY;
ALTER TABLE competency_nodes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
