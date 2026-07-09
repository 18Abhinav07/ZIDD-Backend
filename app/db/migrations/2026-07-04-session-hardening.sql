ALTER TABLE learner_profiles
    DROP COLUMN IF EXISTS password_hash,
    ADD COLUMN IF NOT EXISTS preferences JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS module_id TEXT,
    ADD COLUMN IF NOT EXISTS task_type TEXT,
    ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS test_mode BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS reattempt_of_session_id TEXT;

ALTER TABLE competency_nodes
    ADD COLUMN IF NOT EXISTS best_mastery REAL NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS node_completed BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS completion_count INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_completed_session_id TEXT;

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

CREATE INDEX IF NOT EXISTS idx_sessions_user_status
    ON sessions(user_id, status, last_seen_at);

CREATE INDEX IF NOT EXISTS idx_node_attempts_user_node
    ON node_attempts(user_id, competency_node, started_at DESC);

ALTER TABLE public.node_attempts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.node_attempts FROM anon;
REVOKE ALL ON TABLE public.node_attempts FROM authenticated;
REVOKE ALL ON TABLE public.node_attempts FROM PUBLIC;
