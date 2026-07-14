CREATE TABLE IF NOT EXISTS public.school_v2_practice_sessions (
    practice_session_id TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    subject_id          TEXT NOT NULL,
    target_class_no     INTEGER NOT NULL,
    skill_id            TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'in_progress',
    state_json          JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_school_v2_practice_user_status_updated
    ON public.school_v2_practice_sessions(user_id, status, updated_at DESC);

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_v2_one_active_practice
    ON public.school_v2_practice_sessions(user_id, subject_id, target_class_no, skill_id)
    WHERE status = 'in_progress';

ALTER TABLE public.school_v2_practice_sessions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM anon;
REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM PUBLIC;
