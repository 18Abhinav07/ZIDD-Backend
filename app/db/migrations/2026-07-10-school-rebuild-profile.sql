CREATE TABLE IF NOT EXISTS public.school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    display_name TEXT NOT NULL DEFAULT '',
    school_name TEXT NOT NULL,
    board_id TEXT NOT NULL,
    target_class_no INTEGER NOT NULL CHECK (target_class_no BETWEEN 2 AND 5),
    subject_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    preferred_teaching_language TEXT NOT NULL CHECK (preferred_teaching_language IN ('en', 'hi', 'hi_en')),
    english_comfort TEXT NOT NULL CHECK (english_comfort IN ('low', 'medium', 'high')),
    learner_goal TEXT NOT NULL DEFAULT '',
    parent_goal TEXT NOT NULL DEFAULT '',
    prior_difficulty_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_active
    ON public.school_profile_versions(user_id)
    WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_school_profile_versions_user_status_updated
    ON public.school_profile_versions(user_id, status, updated_at DESC);

ALTER TABLE public.school_profile_versions ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_profile_versions FROM anon;
REVOKE ALL ON TABLE public.school_profile_versions FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_versions FROM PUBLIC;
