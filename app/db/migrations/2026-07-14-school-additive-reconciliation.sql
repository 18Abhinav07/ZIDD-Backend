-- Bring every valid historical School migration prefix to the canonical shape.
-- Only deterministic lineage and lifecycle fields are backfilled. Incompatible
-- rows fail validation and leave the transaction unchanged; historical
-- archive/expiry/status/link repairs are not replayed.

CREATE TABLE IF NOT EXISTS public.school_migration_markers (
    migration_key TEXT PRIMARY KEY,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.school_migration_markers
    ADD COLUMN IF NOT EXISTS file_sha256 TEXT,
    ADD COLUMN IF NOT EXISTS applied_at TIMESTAMPTZ;

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_migration_markers'::regclass
          AND conname = 'school_migration_markers_file_sha256'
    ) THEN
        ALTER TABLE public.school_migration_markers
            ADD CONSTRAINT school_migration_markers_file_sha256
            CHECK (
                file_sha256 IS NULL
                OR file_sha256 ~ '^[0-9a-f]{64}$'
            ) NOT VALID;
    END IF;
END;
$migration$;

ALTER TABLE public.school_migration_markers
    VALIDATE CONSTRAINT school_migration_markers_file_sha256;

CREATE TABLE IF NOT EXISTS public.school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    display_name TEXT,
    school_name TEXT,
    board_id TEXT CHECK (board_id IN ('cbse', 'ncert')),
    target_class_no INTEGER CHECK (target_class_no BETWEEN 2 AND 5),
    subject_ids JSONB,
    preferred_teaching_language TEXT
        CHECK (preferred_teaching_language IN ('en', 'hi', 'hi_en')),
    english_comfort TEXT CHECK (english_comfort IN ('low', 'medium', 'high')),
    learner_goal TEXT,
    parent_goal TEXT,
    prior_difficulty_signals JSONB,
    current_step INTEGER NOT NULL DEFAULT 0
        CHECK (current_step BETWEEN 0 AND 4),
    draft_revision INTEGER NOT NULL DEFAULT 1 CHECK (draft_revision >= 1),
    last_save_request_id UUID,
    last_save_payload_hash TEXT,
    source_profile_version_id UUID,
    activation_request_id UUID,
    activation_payload_hash TEXT,
    activation_result_profile_version_id UUID,
    coach_avatar_id TEXT,
    coach_palette_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ
);

ALTER TABLE public.school_profile_versions
    ADD COLUMN IF NOT EXISTS current_step INTEGER NOT NULL DEFAULT 0
        CHECK (current_step BETWEEN 0 AND 4),
    ADD COLUMN IF NOT EXISTS draft_revision INTEGER NOT NULL DEFAULT 1
        CHECK (draft_revision >= 1),
    ADD COLUMN IF NOT EXISTS last_save_request_id UUID,
    ADD COLUMN IF NOT EXISTS last_save_payload_hash TEXT,
    ADD COLUMN IF NOT EXISTS source_profile_version_id UUID,
    ADD COLUMN IF NOT EXISTS activation_request_id UUID,
    ADD COLUMN IF NOT EXISTS activation_payload_hash TEXT,
    ADD COLUMN IF NOT EXISTS activation_result_profile_version_id UUID,
    ADD COLUMN IF NOT EXISTS coach_avatar_id TEXT,
    ADD COLUMN IF NOT EXISTS coach_palette_id TEXT;

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

-- Historical profiles predate the lifecycle check. Normalize timestamps while
-- preserving the learner-selected status and all authored profile data.
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

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_source_profile_version_id_fkey'
    ) THEN
        ALTER TABLE public.school_profile_versions
            ADD CONSTRAINT school_profile_versions_source_profile_version_id_fkey
            FOREIGN KEY (source_profile_version_id)
            REFERENCES public.school_profile_versions(profile_version_id)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_activation_result_profile_version_id_fkey'
    ) THEN
        ALTER TABLE public.school_profile_versions
            ADD CONSTRAINT school_profile_versions_activation_result_profile_version_id_fkey
            FOREIGN KEY (activation_result_profile_version_id)
            REFERENCES public.school_profile_versions(profile_version_id)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_complete_non_drafts'
    ) THEN
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
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_lifecycle'
    ) THEN
        ALTER TABLE public.school_profile_versions
            ADD CONSTRAINT school_profile_versions_lifecycle CHECK (
                (status = 'draft' AND activated_at IS NULL AND archived_at IS NULL)
                OR (status = 'active' AND activated_at IS NOT NULL AND archived_at IS NULL)
                OR (status = 'archived' AND archived_at IS NOT NULL)
            ) NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_profile_versions'::regclass
          AND conname = 'school_profile_versions_coach_identity'
    ) THEN
        ALTER TABLE public.school_profile_versions
            ADD CONSTRAINT school_profile_versions_coach_identity CHECK (
                (coach_avatar_id IS NULL AND coach_palette_id IS NULL)
                OR (
                    coach_avatar_id = coach_palette_id
                    AND coach_avatar_id IN (
                        'stuttering_sam', 'fluent_finn', 'brave_bella',
                        'quiet_quint', 'tech_black', 'casual_purple',
                        'casual_male', 'casual_female', 'casual_blue'
                    )
                )
            ) NOT VALID;
    END IF;
END;
$migration$;

ALTER TABLE public.school_profile_versions
    VALIDATE CONSTRAINT school_profile_versions_source_profile_version_id_fkey;
ALTER TABLE public.school_profile_versions
    VALIDATE CONSTRAINT school_profile_versions_activation_result_profile_version_id_fkey;
ALTER TABLE public.school_profile_versions
    VALIDATE CONSTRAINT school_profile_versions_complete_non_drafts;
ALTER TABLE public.school_profile_versions
    VALIDATE CONSTRAINT school_profile_versions_lifecycle;
ALTER TABLE public.school_profile_versions
    VALIDATE CONSTRAINT school_profile_versions_coach_identity;

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_active
    ON public.school_profile_versions(user_id)
    WHERE status = 'active';
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_draft
    ON public.school_profile_versions(user_id)
    WHERE status = 'draft';
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_activation_request
    ON public.school_profile_versions(user_id, activation_request_id)
    WHERE activation_request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_school_profile_versions_user_status_updated
    ON public.school_profile_versions(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.school_sessions (
    session_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID
        REFERENCES public.school_profile_versions(profile_version_id),
    api_version TEXT NOT NULL,
    flow_type TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    class_no INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    current_stage TEXT NOT NULL DEFAULT '',
    linked_session_id UUID,
    source_placement_report_id UUID,
    state_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE public.school_sessions
    ADD COLUMN IF NOT EXISTS profile_version_id UUID
        REFERENCES public.school_profile_versions(profile_version_id),
    ADD COLUMN IF NOT EXISTS source_placement_report_id UUID;

CREATE TABLE IF NOT EXISTS public.school_placement_reports (
    report_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    profile_version_id UUID NOT NULL
        REFERENCES public.school_profile_versions(profile_version_id),
    placement_session_id UUID NOT NULL
        REFERENCES public.school_sessions(session_id),
    placement_status TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    target_class_no INTEGER NOT NULL,
    evaluated_class_no INTEGER NOT NULL,
    active_learning_class_no INTEGER NOT NULL,
    unlock_state TEXT NOT NULL,
    blocking_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    watchlist_skills_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_recap_modules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    learner_summary TEXT NOT NULL DEFAULT '',
    parent_summary TEXT NOT NULL DEFAULT '',
    allowed_next_actions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, placement_session_id)
);

-- Backfill only explicit, same-user lineage carried by the historical state.
-- Missing or contradictory active lineage remains unresolved and is rejected
-- by the validated constraints below.
DO $lineage_conflict$
DECLARE
    conflict_count INTEGER;
BEGIN
    SELECT count(*)
    INTO conflict_count
    FROM public.school_sessions AS school_session
    JOIN public.school_placement_reports AS persisted_report
      ON persisted_report.report_id = school_session.source_placement_report_id
     AND persisted_report.user_id = school_session.user_id
    JOIN public.school_placement_reports AS state_report
      ON school_session.state_json ->> 'source_placement_report_id'
            ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     AND state_report.report_id::text = lower(
         school_session.state_json ->> 'source_placement_report_id'
     )
     AND state_report.user_id = school_session.user_id
    WHERE school_session.api_version = 'rebuild'
      AND school_session.flow_type IN ('recap', 'curriculum')
      AND persisted_report.report_id <> state_report.report_id;

    IF conflict_count <> 0 THEN
        RAISE EXCEPTION 'school_session_lineage_conflict:%', conflict_count
            USING ERRCODE = '55000';
    END IF;
END;
$lineage_conflict$;

WITH lineage_candidates AS (
    SELECT school_session.session_id,
           school_session.profile_version_id,
           school_session.source_placement_report_id,
           state_profile.profile_version_id AS state_profile_version_id,
           persisted_report.report_id AS persisted_report_id,
           persisted_report.profile_version_id AS persisted_profile_version_id,
           state_report.report_id AS state_report_id,
           state_report.profile_version_id AS state_report_profile_version_id
    FROM public.school_sessions AS school_session
    LEFT JOIN public.school_profile_versions AS state_profile
      ON school_session.api_version = 'rebuild'
     AND state_profile.user_id = school_session.user_id
     AND school_session.state_json ->> 'profile_version_id'
         ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     AND state_profile.profile_version_id::text = lower(
         school_session.state_json ->> 'profile_version_id'
     )
    LEFT JOIN public.school_placement_reports AS persisted_report
      ON school_session.api_version = 'rebuild'
     AND school_session.flow_type IN ('recap', 'curriculum')
     AND persisted_report.user_id = school_session.user_id
     AND persisted_report.report_id = school_session.source_placement_report_id
    LEFT JOIN public.school_placement_reports AS state_report
      ON school_session.api_version = 'rebuild'
     AND school_session.flow_type IN ('recap', 'curriculum')
     AND school_session.source_placement_report_id IS NULL
     AND state_report.user_id = school_session.user_id
     AND school_session.state_json ->> 'source_placement_report_id'
            ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     AND state_report.report_id::text = lower(
         school_session.state_json ->> 'source_placement_report_id'
     )
    WHERE school_session.api_version = 'rebuild'
),
lineage_decisions AS (
    SELECT lineage_candidates.*,
           COALESCE(
               profile_version_id,
               persisted_profile_version_id,
               state_profile_version_id,
               state_report_profile_version_id
           ) AS final_profile_version_id,
           CASE
               WHEN source_placement_report_id IS NOT NULL
               THEN source_placement_report_id
               WHEN state_report_id IS NOT NULL
                AND (
                    COALESCE(profile_version_id, state_profile_version_id) IS NULL
                    OR COALESCE(profile_version_id, state_profile_version_id)
                        = state_report_profile_version_id
                )
               THEN state_report_id
               ELSE NULL
           END AS final_source_placement_report_id
    FROM lineage_candidates
)
UPDATE public.school_sessions AS school_session
SET profile_version_id = decision.final_profile_version_id,
    source_placement_report_id = decision.final_source_placement_report_id,
    updated_at = now()
FROM lineage_decisions AS decision
WHERE school_session.session_id = decision.session_id
  AND (
      school_session.profile_version_id
          IS DISTINCT FROM decision.final_profile_version_id
      OR school_session.source_placement_report_id
          IS DISTINCT FROM decision.final_source_placement_report_id
  );

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_sessions_user_session_unique'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_sessions_user_session_unique
            UNIQUE (user_id, session_id);
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_sessions_profile_version_id_fkey'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_sessions_profile_version_id_fkey
            FOREIGN KEY (profile_version_id)
            REFERENCES public.school_profile_versions(profile_version_id)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_sessions_source_placement_report_id_fkey'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_sessions_source_placement_report_id_fkey
            FOREIGN KEY (source_placement_report_id)
            REFERENCES public.school_placement_reports(report_id)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_sessions_linked_same_user'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_sessions_linked_same_user
            FOREIGN KEY (user_id, linked_session_id)
            REFERENCES public.school_sessions(user_id, session_id)
            NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_sessions'::regclass
          AND conname = 'school_rebuild_active_profile_lineage'
    ) THEN
        ALTER TABLE public.school_sessions
            ADD CONSTRAINT school_rebuild_active_profile_lineage CHECK (
                api_version <> 'rebuild'
                OR status NOT IN ('active', 'paused_for_masterclass')
                OR profile_version_id IS NOT NULL
            ) NOT VALID;
    END IF;
END;
$migration$;

ALTER TABLE public.school_sessions
    VALIDATE CONSTRAINT school_sessions_profile_version_id_fkey;
ALTER TABLE public.school_sessions
    VALIDATE CONSTRAINT school_sessions_source_placement_report_id_fkey;
ALTER TABLE public.school_sessions
    VALIDATE CONSTRAINT school_sessions_linked_same_user;
ALTER TABLE public.school_sessions
    VALIDATE CONSTRAINT school_rebuild_active_profile_lineage;

ALTER TABLE public.school_sessions
    DROP CONSTRAINT IF EXISTS school_sessions_linked_session_id_fkey;

CREATE INDEX IF NOT EXISTS idx_school_sessions_user_status_updated
    ON public.school_sessions(user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_school_sessions_linked_session
    ON public.school_sessions(linked_session_id);
CREATE INDEX IF NOT EXISTS idx_school_sessions_profile_flow_updated
    ON public.school_sessions(
        user_id,
        profile_version_id,
        flow_type,
        subject_id,
        class_no,
        updated_at DESC
    );
CREATE INDEX IF NOT EXISTS idx_school_sessions_source_report
    ON public.school_sessions(source_placement_report_id, updated_at DESC)
    WHERE source_placement_report_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_sessions_one_active_flow
    ON public.school_sessions(user_id, flow_type, subject_id, class_no)
    WHERE status IN ('active', 'paused_for_masterclass');

CREATE INDEX IF NOT EXISTS idx_school_placement_reports_user_updated
    ON public.school_placement_reports(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.school_answer_requests (
    session_id UUID NOT NULL
        REFERENCES public.school_sessions(session_id) ON DELETE CASCADE,
    activity_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    answer_hash TEXT NOT NULL,
    claim_token TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
    response_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, activity_id)
);

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

ALTER TABLE public.school_migration_markers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_placement_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_answer_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.school_profile_draft_requests ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_migration_markers FROM anon;
REVOKE ALL ON TABLE public.school_migration_markers FROM authenticated;
REVOKE ALL ON TABLE public.school_migration_markers FROM PUBLIC;
REVOKE ALL ON TABLE public.school_profile_versions FROM anon;
REVOKE ALL ON TABLE public.school_profile_versions FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_versions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_sessions FROM anon;
REVOKE ALL ON TABLE public.school_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_placement_reports FROM anon;
REVOKE ALL ON TABLE public.school_placement_reports FROM authenticated;
REVOKE ALL ON TABLE public.school_placement_reports FROM PUBLIC;
REVOKE ALL ON TABLE public.school_answer_requests FROM anon;
REVOKE ALL ON TABLE public.school_answer_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_answer_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM anon;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM PUBLIC;
