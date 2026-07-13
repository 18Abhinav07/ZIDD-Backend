CREATE TABLE IF NOT EXISTS school_placement_reports (
    report_id                      UUID PRIMARY KEY,
    user_id                        TEXT NOT NULL REFERENCES learner_profiles(user_id),
    profile_version_id             UUID NOT NULL REFERENCES school_profile_versions(profile_version_id),
    placement_session_id           UUID NOT NULL REFERENCES school_sessions(session_id),
    placement_status               TEXT NOT NULL,
    subject_id                     TEXT NOT NULL,
    target_class_no                INTEGER NOT NULL,
    evaluated_class_no             INTEGER NOT NULL,
    active_learning_class_no       INTEGER NOT NULL,
    unlock_state                   TEXT NOT NULL,
    blocking_skills_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
    watchlist_skills_json          JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_summary_json          JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_recap_modules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    learner_summary                TEXT NOT NULL DEFAULT '',
    parent_summary                 TEXT NOT NULL DEFAULT '',
    allowed_next_actions_json      JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, placement_session_id)
);

CREATE INDEX IF NOT EXISTS idx_school_placement_reports_user_updated
    ON school_placement_reports(user_id, updated_at DESC);

ALTER TABLE school_placement_reports ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_placement_reports FROM anon;
REVOKE ALL ON TABLE public.school_placement_reports FROM authenticated;
REVOKE ALL ON TABLE public.school_placement_reports FROM PUBLIC;
