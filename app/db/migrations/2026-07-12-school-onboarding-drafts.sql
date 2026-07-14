ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS current_step INTEGER NOT NULL DEFAULT 0 CHECK (current_step BETWEEN 0 AND 4);

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS draft_revision INTEGER NOT NULL DEFAULT 1 CHECK (draft_revision >= 1);

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS last_save_request_id UUID;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS last_save_payload_hash TEXT;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS source_profile_version_id UUID;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS activation_request_id UUID;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS activation_payload_hash TEXT;

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS activation_result_profile_version_id UUID;

ALTER TABLE public.school_profile_versions
    ALTER COLUMN display_name DROP NOT NULL,
    ALTER COLUMN display_name DROP DEFAULT,
    ALTER COLUMN school_name DROP NOT NULL,
    ALTER COLUMN board_id DROP NOT NULL,
    ALTER COLUMN target_class_no DROP NOT NULL,
    ALTER COLUMN subject_ids DROP NOT NULL,
    ALTER COLUMN subject_ids DROP DEFAULT,
    ALTER COLUMN preferred_teaching_language DROP NOT NULL,
    ALTER COLUMN english_comfort DROP NOT NULL,
    ALTER COLUMN learner_goal DROP NOT NULL,
    ALTER COLUMN learner_goal DROP DEFAULT,
    ALTER COLUMN parent_goal DROP NOT NULL,
    ALTER COLUMN parent_goal DROP DEFAULT,
    ALTER COLUMN prior_difficulty_signals DROP NOT NULL,
    ALTER COLUMN prior_difficulty_signals DROP DEFAULT;

ALTER TABLE public.school_profile_versions
    DROP CONSTRAINT IF EXISTS school_profile_versions_source_profile_version_id_fkey;

ALTER TABLE public.school_profile_versions
    ADD CONSTRAINT school_profile_versions_source_profile_version_id_fkey
    FOREIGN KEY (source_profile_version_id)
    REFERENCES public.school_profile_versions(profile_version_id);

ALTER TABLE public.school_profile_versions
    DROP CONSTRAINT IF EXISTS school_profile_versions_activation_result_profile_version_id_fkey;

ALTER TABLE public.school_profile_versions
    ADD CONSTRAINT school_profile_versions_activation_result_profile_version_id_fkey
    FOREIGN KEY (activation_result_profile_version_id)
    REFERENCES public.school_profile_versions(profile_version_id);

UPDATE public.school_profile_versions
SET activated_at = NULL,
    archived_at = NULL,
    updated_at = COALESCE(updated_at, created_at, now())
WHERE status = 'draft'
  AND (activated_at IS NOT NULL OR archived_at IS NOT NULL);

UPDATE public.school_profile_versions
SET activated_at = COALESCE(activated_at, updated_at, created_at, now()),
    archived_at = NULL,
    updated_at = COALESCE(updated_at, created_at, now())
WHERE status = 'active'
  AND (activated_at IS NULL OR archived_at IS NOT NULL);

UPDATE public.school_profile_versions
SET archived_at = COALESCE(archived_at, updated_at, created_at, now()),
    updated_at = COALESCE(updated_at, created_at, now())
WHERE status = 'archived'
  AND archived_at IS NULL;

WITH invalid_active_profiles AS (
    SELECT profile_version_id, user_id
    FROM public.school_profile_versions
    WHERE status = 'active'
      AND NOT (
          display_name IS NOT NULL
          AND school_name IS NOT NULL
          AND char_length(btrim(display_name)) >= 2
          AND char_length(btrim(school_name)) >= 2
          AND board_id IN ('cbse', 'ncert')
          AND target_class_no BETWEEN 2 AND 5
          AND subject_ids IS NOT NULL
          AND jsonb_typeof(subject_ids) = 'array'
          AND CASE
              WHEN jsonb_typeof(subject_ids) = 'array'
              THEN jsonb_array_length(subject_ids) > 0
              ELSE FALSE
          END
          AND subject_ids <@ '["english"]'::jsonb
          AND preferred_teaching_language IN ('en', 'hi', 'hi_en')
          AND english_comfort IN ('low', 'medium', 'high')
          AND learner_goal IS NOT NULL
          AND parent_goal IS NOT NULL
          AND (
              NULLIF(btrim(learner_goal), '') IS NOT NULL
              OR NULLIF(btrim(parent_goal), '') IS NOT NULL
          )
          AND prior_difficulty_signals IS NOT NULL
          AND jsonb_typeof(prior_difficulty_signals) = 'array'
          AND prior_difficulty_signals <@ '["reading", "vocabulary", "grammar", "writing", "chapter_answers"]'::jsonb
      )
),
archived_invalid_profiles AS (
    UPDATE public.school_profile_versions AS profile
    SET status = 'archived', archived_at = now(), updated_at = now()
    FROM invalid_active_profiles AS invalid
    WHERE profile.profile_version_id = invalid.profile_version_id
    RETURNING profile.profile_version_id, profile.user_id
)
UPDATE public.school_sessions AS school_session
SET status = 'expired',
    updated_at = now(),
    completed_at = COALESCE(school_session.completed_at, now())
FROM archived_invalid_profiles AS archived
WHERE school_session.user_id = archived.user_id
  AND school_session.profile_version_id = archived.profile_version_id
  AND school_session.status IN ('active', 'paused_for_masterclass');

WITH ranked_legacy_drafts AS (
    SELECT profile_version_id,
           row_number() OVER (
               PARTITION BY user_id
               ORDER BY updated_at DESC, profile_version_id DESC
           ) AS draft_rank
    FROM public.school_profile_versions
    WHERE status = 'draft'
)
UPDATE public.school_profile_versions AS profile
SET status = 'archived', archived_at = now(), updated_at = now()
FROM ranked_legacy_drafts AS ranked
WHERE profile.profile_version_id = ranked.profile_version_id
  AND ranked.draft_rank > 1;

ALTER TABLE public.school_profile_versions
    DROP CONSTRAINT IF EXISTS school_profile_versions_complete_non_drafts;

ALTER TABLE public.school_profile_versions
    ADD CONSTRAINT school_profile_versions_complete_non_drafts CHECK (
        status <> 'active'
        OR (
            display_name IS NOT NULL
            AND school_name IS NOT NULL
            AND char_length(btrim(display_name)) >= 2
            AND char_length(btrim(school_name)) >= 2
            AND board_id IN ('cbse', 'ncert')
            AND target_class_no BETWEEN 2 AND 5
            AND subject_ids IS NOT NULL
            AND jsonb_typeof(subject_ids) = 'array'
            AND CASE
                WHEN jsonb_typeof(subject_ids) = 'array'
                THEN jsonb_array_length(subject_ids) > 0
                ELSE FALSE
            END
            AND subject_ids <@ '["english"]'::jsonb
            AND preferred_teaching_language IN ('en', 'hi', 'hi_en')
            AND english_comfort IN ('low', 'medium', 'high')
            AND learner_goal IS NOT NULL
            AND parent_goal IS NOT NULL
            AND (
                NULLIF(btrim(learner_goal), '') IS NOT NULL
                OR NULLIF(btrim(parent_goal), '') IS NOT NULL
            )
            AND prior_difficulty_signals IS NOT NULL
            AND jsonb_typeof(prior_difficulty_signals) = 'array'
            AND prior_difficulty_signals <@ '["reading", "vocabulary", "grammar", "writing", "chapter_answers"]'::jsonb
        )
    );

ALTER TABLE public.school_profile_versions
    DROP CONSTRAINT IF EXISTS school_profile_versions_lifecycle;

ALTER TABLE public.school_profile_versions
    ADD CONSTRAINT school_profile_versions_lifecycle CHECK (
        (status = 'draft' AND activated_at IS NULL AND archived_at IS NULL)
        OR (status = 'active' AND activated_at IS NOT NULL AND archived_at IS NULL)
        OR (status = 'archived' AND archived_at IS NOT NULL)
    );

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_draft
    ON public.school_profile_versions(user_id)
    WHERE status = 'draft';

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_activation_request
    ON public.school_profile_versions(user_id, activation_request_id)
    WHERE activation_request_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS public.school_profile_draft_requests (
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    request_id UUID NOT NULL,
    profile_version_id UUID NOT NULL
        REFERENCES public.school_profile_versions(profile_version_id),
    payload_hash TEXT NOT NULL,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, request_id)
);

ALTER TABLE public.school_profile_draft_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM anon;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM PUBLIC;
