-- Zidd engine schema (architecture-v3 §408). Run once against Supabase.
-- Text + vectors only. NEVER store raw audio/files here (3GB free-tier rule).

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- learners ----------
CREATE TABLE IF NOT EXISTS learner_profiles (
    user_id         TEXT PRIMARY KEY,
    display_name    TEXT,
    preferences     JSONB NOT NULL DEFAULT '{}'::jsonb,
    primary_motive  TEXT,
    onboarding_completed_at TIMESTAMPTZ,
    school_profile  JSONB NOT NULL DEFAULT '{}'::jsonb,
    career_profile  JSONB NOT NULL DEFAULT '{}'::jsonb,
    onboarding_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Present only for Google-linked or email-known accounts; both UNIQUE so
    -- login-by-email/login-by-google_sub lookups resolve to at most one row.
    email           TEXT UNIQUE,
    google_sub      TEXT UNIQUE,
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
    status          TEXT NOT NULL DEFAULT 'active',
    module_id       TEXT,
    task_type       TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    test_mode       BOOLEAN NOT NULL DEFAULT FALSE,
    reattempt_of_session_id TEXT,
    career_context  JSONB NOT NULL DEFAULT '{}'::jsonb,
    scenario_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    persona_roster  JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_hash    TEXT NOT NULL DEFAULT 'default',
    turn_count      INTEGER NOT NULL DEFAULT 0,
    final_mastery   REAL,
    summary         TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- ---------- durable live session runtime ----------
CREATE TABLE IF NOT EXISTS session_runtime (
    session_id        TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id           TEXT NOT NULL REFERENCES learner_profiles(user_id),
    current_node      TEXT NOT NULL,
    module_id         TEXT,
    task_type         TEXT,
    test_mode         BOOLEAN NOT NULL DEFAULT FALSE,
    status            TEXT NOT NULL DEFAULT 'active',
    state_snapshot    JSONB NOT NULL DEFAULT '{}'::jsonb,
    pending_transition JSONB,
    session_version   INTEGER NOT NULL DEFAULT 1,
    active_turn_id    TEXT,
    active_opening_id TEXT,
    last_error        JSONB,
    lease_expires_at  TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_runtime_user_status
    ON session_runtime(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS session_messages (
    message_id     TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    sequence_index INTEGER NOT NULL DEFAULT 0,
    turn_id        TEXT,
    transition_id  TEXT,
    node_id        TEXT,
    role           TEXT NOT NULL,
    content        TEXT NOT NULL DEFAULT '',
    speaker_name   TEXT,
    speaker_id     TEXT,
    message_kind   TEXT,
    status         TEXT NOT NULL DEFAULT 'committed',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_messages_session_sequence
    ON session_messages(session_id, sequence_index);

CREATE TABLE IF NOT EXISTS session_turn_requests (
    session_id       TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    client_turn_id   TEXT NOT NULL,
    request_hash     TEXT NOT NULL,
    expected_version INTEGER,
    status           TEXT NOT NULL DEFAULT 'in_progress',
    transcript_delta JSONB NOT NULL DEFAULT '[]'::jsonb,
    done_snapshot    JSONB,
    error_code       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, client_turn_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_turn_requests_session_version
    ON session_turn_requests(session_id, expected_version)
    WHERE expected_version IS NOT NULL AND status IN ('in_progress', 'completed');

CREATE TABLE IF NOT EXISTS session_start_requests (
    user_id              TEXT NOT NULL REFERENCES learner_profiles(user_id),
    client_start_id      TEXT NOT NULL,
    request_hash         TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'in_progress',
    session_id           TEXT,
    response_json        JSONB,
    error_code           TEXT,
    source_session_id    TEXT,
    source_transition_id TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, client_start_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_start_requests_source_transition
    ON session_start_requests(source_session_id, source_transition_id)
    WHERE source_session_id IS NOT NULL
      AND source_transition_id IS NOT NULL
      AND status IN ('in_progress', 'completed');

CREATE TABLE IF NOT EXISTS session_opening_requests (
    session_id     TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    transition_id  TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'in_progress',
    message_id     TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    last_error     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, transition_id)
);

CREATE TABLE IF NOT EXISTS session_end_requests (
    session_id     TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'in_progress',
    response_json  JSONB,
    error_code     TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- turns ----------
CREATE TABLE IF NOT EXISTS turns (
    id              BIGSERIAL PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(session_id),
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    node_id         TEXT NOT NULL,
    score           REAL,
    on_task         BOOLEAN NOT NULL DEFAULT TRUE,
    english         BOOLEAN NOT NULL DEFAULT TRUE,
    affect          TEXT NOT NULL DEFAULT 'neutral',
    ts              DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, id);

CREATE TABLE IF NOT EXISTS turn_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    user_id       TEXT NOT NULL REFERENCES learner_profiles(user_id),
    node_id       TEXT NOT NULL,
    turn_id       TEXT,
    attempt_index INTEGER NOT NULL,
    attempt_type  TEXT NOT NULL,
    user_answer   TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    raw_score     REAL NOT NULL,
    effective_score REAL NOT NULL,
    criteria_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers      JSONB NOT NULL DEFAULT '[]'::jsonb,
    pass_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    advance_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    mastery_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    tutor_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_name    TEXT,
    prompt_version TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_turn_evaluations_session
    ON turn_evaluations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_turn_evaluations_user_node
    ON turn_evaluations(user_id, node_id, created_at DESC);

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
    best_mastery    REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    clean_pass      BOOLEAN NOT NULL DEFAULT FALSE,   -- passed in <=2 attempts
    node_completed  BOOLEAN NOT NULL DEFAULT FALSE,   -- user advanced past this node
    node_mastered   BOOLEAN NOT NULL DEFAULT FALSE,   -- stricter career-prep mastery
    display_status  TEXT NOT NULL DEFAULT 'active',
    best_independent_score REAL NOT NULL DEFAULT 0.0,
    independent_passes INTEGER NOT NULL DEFAULT 0,
    transfer_passes INTEGER NOT NULL DEFAULT 0,
    pressure_passes INTEGER NOT NULL DEFAULT 0,
    scaffold_successes INTEGER NOT NULL DEFAULT 0,
    last_gap        TEXT NOT NULL DEFAULT '',
    mastery_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    completed_at    TIMESTAMPTZ,
    completion_count INTEGER NOT NULL DEFAULT 0,
    last_completed_session_id TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, competency_node)
);

CREATE TABLE IF NOT EXISTS node_attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    starting_mastery REAL NOT NULL DEFAULT 0.0,
    ending_mastery REAL NOT NULL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_node_attempts_user_node
    ON node_attempts(user_id, competency_node, started_at DESC);

-- ---------- weaknesses ----------
CREATE TABLE IF NOT EXISTS weaknesses (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    task_type       TEXT NOT NULL,
    skill_id        TEXT NOT NULL,
    hit_count       INTEGER NOT NULL DEFAULT 0,
    last_score      REAL,
    last_seen       DOUBLE PRECISION NOT NULL,
    last_raw        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, task_type, skill_id)
);
CREATE INDEX IF NOT EXISTS idx_weaknesses_user_task_seen
    ON weaknesses(user_id, task_type, last_seen DESC);

-- ---------- global learner evidence/profile ----------
CREATE TABLE IF NOT EXISTS learning_events (
    event_id         BIGSERIAL PRIMARY KEY,
    source_event_key TEXT NOT NULL UNIQUE,
    user_id          TEXT NOT NULL REFERENCES learner_profiles(user_id),
    domain           TEXT NOT NULL,
    task_type        TEXT NOT NULL,
    module_id        TEXT NOT NULL DEFAULT '',
    session_id       TEXT,
    node_id          TEXT NOT NULL DEFAULT '',
    skill_id         TEXT NOT NULL,
    source           TEXT NOT NULL,
    attempt_type     TEXT NOT NULL DEFAULT '',
    score            REAL NOT NULL DEFAULT 0.0,
    confidence       REAL NOT NULL DEFAULT 0.0,
    criteria_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    blockers         JSONB NOT NULL DEFAULT '[]'::jsonb,
    gap              TEXT NOT NULL DEFAULT '',
    scenario_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    caveats          JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_name       TEXT,
    prompt_version   TEXT,
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_time
    ON learning_events(user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_domain_skill_time
    ON learning_events(user_id, domain, skill_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_session
    ON learning_events(session_id);

CREATE TABLE IF NOT EXISTS session_reports (
    report_id       TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL UNIQUE REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    report_type     TEXT NOT NULL,
    task_type       TEXT NOT NULL,
    module_id       TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL,
    score           REAL NOT NULL DEFAULT 0.0,
    readiness_score REAL NOT NULL DEFAULT 0.0,
    summary         TEXT NOT NULL DEFAULT '',
    strengths_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_actions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    validity_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    public_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_reports_user_type_time
    ON session_reports(user_id, report_type, created_at DESC);

CREATE TABLE IF NOT EXISTS learner_skill_profiles (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    domain          TEXT NOT NULL,
    skill_id        TEXT NOT NULL,
    module_id       TEXT NOT NULL DEFAULT '',
    task_type       TEXT NOT NULL DEFAULT '',
    mastery         REAL NOT NULL DEFAULT 0.0,
    readiness       REAL NOT NULL DEFAULT 0.0,
    confidence      REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    strengths_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_next_action TEXT NOT NULL DEFAULT '',
    source_summary  TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, domain, skill_id)
);
CREATE INDEX IF NOT EXISTS idx_learner_skill_profiles_user_domain_mastery_seen
    ON learner_skill_profiles(user_id, domain, mastery, last_seen_at DESC);

-- ---------- school progress ----------
CREATE TABLE IF NOT EXISTS school_skill_mastery (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    skill           TEXT NOT NULL,
    ema             REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_seen       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, skill)
);

CREATE TABLE IF NOT EXISTS school_results (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    test_id         TEXT NOT NULL,
    class_no        INTEGER NOT NULL,
    kind            TEXT NOT NULL,
    score           REAL NOT NULL,
    passed          BOOLEAN NOT NULL DEFAULT FALSE,
    by_skill        JSONB NOT NULL DEFAULT '[]'::jsonb,
    weak_skills     JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at      DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, test_id)
);

-- ---------- test-item cache ----------
CREATE TABLE IF NOT EXISTS test_items (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    task_type       TEXT NOT NULL,
    context_hash    TEXT NOT NULL DEFAULT 'default',
    items           JSONB NOT NULL DEFAULT '[]'::jsonb,
    cached_at       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, task_type, context_hash)
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

-- ---------- content unlocks + purchases ----------
CREATE TABLE IF NOT EXISTS content_unlocks (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    scope           TEXT NOT NULL,
    ref_id          TEXT NOT NULL,
    credits_spent   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, scope, ref_id)
);
CREATE INDEX IF NOT EXISTS idx_unlocks_user ON content_unlocks(user_id);

CREATE TABLE IF NOT EXISTS purchases (
    order_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    pack_id         TEXT NOT NULL,
    credits         INTEGER NOT NULL,
    amount_paise    INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'created',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);

-- ---------- row-level security ----------
-- Lock every table to superuser / service_role only. No policies are defined,
-- so anon + authenticated keys get ZERO access. The backend connects via the
-- transaction pooler as the `postgres` role, which bypasses RLS, so the engine
-- is unaffected. Defense-in-depth for the XPRIZE public submission: a leaked
-- anon key cannot read learner data.
ALTER TABLE learner_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_runtime     ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_messages    ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_turn_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_start_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_opening_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_end_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE turns               ENABLE ROW LEVEL SECURITY;
ALTER TABLE turn_evaluations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_entries      ENABLE ROW LEVEL SECURITY;
ALTER TABLE competency_nodes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE weaknesses          ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_events     ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_reports     ENABLE ROW LEVEL SECURITY;
ALTER TABLE learner_skill_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_skill_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_items          ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_unlocks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.node_attempts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.session_runtime FROM anon;
REVOKE ALL ON TABLE public.session_runtime FROM authenticated;
REVOKE ALL ON TABLE public.session_runtime FROM PUBLIC;
REVOKE ALL ON TABLE public.session_messages FROM anon;
REVOKE ALL ON TABLE public.session_messages FROM authenticated;
REVOKE ALL ON TABLE public.session_messages FROM PUBLIC;
REVOKE ALL ON TABLE public.session_turn_requests FROM anon;
REVOKE ALL ON TABLE public.session_turn_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_turn_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_start_requests FROM anon;
REVOKE ALL ON TABLE public.session_start_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_start_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_opening_requests FROM anon;
REVOKE ALL ON TABLE public.session_opening_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_opening_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_end_requests FROM anon;
REVOKE ALL ON TABLE public.session_end_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_end_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.turn_evaluations FROM anon;
REVOKE ALL ON TABLE public.turn_evaluations FROM authenticated;
REVOKE ALL ON TABLE public.turn_evaluations FROM PUBLIC;
REVOKE ALL ON TABLE public.learning_events FROM anon;
REVOKE ALL ON TABLE public.learning_events FROM authenticated;
REVOKE ALL ON TABLE public.learning_events FROM PUBLIC;
REVOKE ALL ON TABLE public.session_reports FROM anon;
REVOKE ALL ON TABLE public.session_reports FROM authenticated;
REVOKE ALL ON TABLE public.session_reports FROM PUBLIC;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM anon;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM authenticated;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM PUBLIC;
REVOKE ALL ON TABLE public.node_attempts FROM anon;
REVOKE ALL ON TABLE public.node_attempts FROM authenticated;
REVOKE ALL ON TABLE public.node_attempts FROM PUBLIC;
