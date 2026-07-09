ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS career_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS scenario_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS persona_roster JSONB NOT NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS context_hash TEXT NOT NULL DEFAULT 'default';

ALTER TABLE test_items
    ADD COLUMN IF NOT EXISTS context_hash TEXT NOT NULL DEFAULT 'default';

ALTER TABLE test_items DROP CONSTRAINT IF EXISTS test_items_pkey;

ALTER TABLE test_items
    ADD PRIMARY KEY (user_id, task_type, context_hash);

CREATE INDEX IF NOT EXISTS idx_sessions_user_context
    ON sessions(user_id, task_type, context_hash, last_seen_at DESC);
