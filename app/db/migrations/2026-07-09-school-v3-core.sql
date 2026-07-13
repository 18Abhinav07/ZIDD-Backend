-- School V3 shared session core.

CREATE TABLE IF NOT EXISTS school_sessions (
    session_id        UUID PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES learner_profiles(user_id),
    api_version       TEXT NOT NULL,
    flow_type         TEXT NOT NULL,
    subject_id        TEXT NOT NULL,
    class_no          INTEGER NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active',
    current_stage     TEXT NOT NULL DEFAULT '',
    linked_session_id UUID REFERENCES school_sessions(session_id),
    state_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at      TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_school_sessions_user_status_updated
    ON school_sessions(user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_school_sessions_linked_session
    ON school_sessions(linked_session_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_sessions_one_active_flow
    ON school_sessions(user_id, flow_type, subject_id, class_no)
    WHERE status IN ('active', 'paused_for_masterclass');

CREATE TABLE IF NOT EXISTS school_language_confidence (
    user_id                  TEXT PRIMARY KEY REFERENCES learner_profiles(user_id),
    en_production_confidence REAL NOT NULL DEFAULT 0.0,
    total_signals            INTEGER NOT NULL DEFAULT 0,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE school_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_language_confidence ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_sessions FROM anon;
REVOKE ALL ON TABLE public.school_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_language_confidence FROM anon;
REVOKE ALL ON TABLE public.school_language_confidence FROM authenticated;
REVOKE ALL ON TABLE public.school_language_confidence FROM PUBLIC;
