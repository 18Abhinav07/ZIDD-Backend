CREATE TABLE IF NOT EXISTS public.school_migration_markers (
    migration_key TEXT PRIMARY KEY,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.school_migration_markers ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_migration_markers FROM anon;
REVOKE ALL ON TABLE public.school_migration_markers FROM authenticated;
REVOKE ALL ON TABLE public.school_migration_markers FROM PUBLIC;

ALTER TABLE public.school_sessions
    ADD COLUMN IF NOT EXISTS profile_version_id UUID
        REFERENCES public.school_profile_versions(profile_version_id),
    ADD COLUMN IF NOT EXISTS source_placement_report_id UUID
        REFERENCES public.school_placement_reports(report_id);

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

WITH claimed_cutover AS (
    INSERT INTO public.school_migration_markers (migration_key)
    VALUES ('2026-07-12-school-session-lineage-cutover-v1')
    ON CONFLICT (migration_key) DO NOTHING
    RETURNING migration_key
),
lineage_candidates AS (
    SELECT school_session.session_id,
           school_session.api_version,
           school_session.status,
           school_session.profile_version_id,
           school_session.source_placement_report_id,
           profile.profile_version_id AS state_profile_version_id,
           placement_report.report_id AS trusted_report_id,
           placement_report.profile_version_id AS report_profile_version_id
    FROM public.school_sessions AS school_session
    LEFT JOIN public.school_profile_versions AS profile
      ON school_session.api_version = 'rebuild'
     AND profile.user_id = school_session.user_id
     AND school_session.state_json ->> 'profile_version_id'
         ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
     AND profile.profile_version_id::text = lower(
         school_session.state_json ->> 'profile_version_id'
     )
    LEFT JOIN public.school_placement_reports AS placement_report
      ON school_session.api_version = 'rebuild'
     AND school_session.flow_type IN ('recap', 'curriculum')
     AND placement_report.user_id = school_session.user_id
     AND (
         (
             school_session.state_json ->> 'source_placement_report_id'
                 ~* '^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
             AND placement_report.report_id::text = lower(
                 school_session.state_json ->> 'source_placement_report_id'
             )
         )
         OR placement_report.report_id = school_session.source_placement_report_id
     )
    WHERE EXISTS (SELECT 1 FROM claimed_cutover)
),
lineage_bases AS (
    SELECT lineage_candidates.*,
           COALESCE(
               profile_version_id,
               state_profile_version_id
           ) AS base_profile_version_id
    FROM lineage_candidates
),
lineage_decisions AS (
    SELECT lineage_bases.*,
           COALESCE(
               base_profile_version_id,
               report_profile_version_id
           ) AS final_profile_version_id,
           CASE
               WHEN trusted_report_id IS NOT NULL
                AND (
                    base_profile_version_id IS NULL
                    OR base_profile_version_id = report_profile_version_id
                )
               THEN trusted_report_id
               ELSE source_placement_report_id
           END AS final_source_placement_report_id
    FROM lineage_bases
),
cutover_decisions AS (
    SELECT lineage_decisions.*,
           (
               api_version <> 'rebuild'
               AND status IN ('active', 'paused_for_masterclass')
           )
           OR (
               api_version = 'rebuild'
               AND status IN ('active', 'paused_for_masterclass')
               AND final_profile_version_id IS NULL
           ) AS should_expire
    FROM lineage_decisions
)
UPDATE public.school_sessions AS school_session
SET profile_version_id = decision.final_profile_version_id,
    source_placement_report_id = decision.final_source_placement_report_id,
    status = CASE WHEN decision.should_expire THEN 'expired' ELSE school_session.status END,
    updated_at = now(),
    completed_at = CASE
        WHEN decision.should_expire
        THEN COALESCE(school_session.completed_at, now())
        ELSE school_session.completed_at
    END
FROM cutover_decisions AS decision
WHERE school_session.session_id = decision.session_id
  AND (
      decision.should_expire
      OR school_session.profile_version_id
          IS DISTINCT FROM decision.final_profile_version_id
      OR school_session.source_placement_report_id
          IS DISTINCT FROM decision.final_source_placement_report_id
  );

ALTER TABLE public.school_sessions
    DROP CONSTRAINT IF EXISTS school_rebuild_active_profile_lineage;

ALTER TABLE public.school_sessions
    ADD CONSTRAINT school_rebuild_active_profile_lineage
    CHECK (
        api_version <> 'rebuild'
        OR status NOT IN ('active', 'paused_for_masterclass')
        OR profile_version_id IS NOT NULL
    );

ALTER TABLE public.school_sessions
    DROP CONSTRAINT IF EXISTS school_sessions_linked_same_user;

ALTER TABLE public.school_sessions
    DROP CONSTRAINT IF EXISTS school_sessions_linked_session_id_fkey;

ALTER TABLE public.school_sessions
    DROP CONSTRAINT IF EXISTS school_sessions_user_session_unique;

WITH legacy_cross_user_links AS (
    SELECT child.session_id
    FROM public.school_sessions AS child
    LEFT JOIN public.school_sessions AS parent
      ON parent.session_id = child.linked_session_id
    WHERE child.linked_session_id IS NOT NULL
      AND (parent.session_id IS NULL OR parent.user_id <> child.user_id)
)
UPDATE public.school_sessions AS child
SET linked_session_id = NULL,
    updated_at = now()
FROM legacy_cross_user_links AS legacy
WHERE child.session_id = legacy.session_id;

ALTER TABLE public.school_sessions
    ADD CONSTRAINT school_sessions_user_session_unique
    UNIQUE (user_id, session_id);

ALTER TABLE public.school_sessions
    ADD CONSTRAINT school_sessions_linked_same_user
    FOREIGN KEY (user_id, linked_session_id)
    REFERENCES public.school_sessions(user_id, session_id);

ALTER TABLE public.school_sessions ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.school_sessions FROM anon;
REVOKE ALL ON TABLE public.school_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_sessions FROM PUBLIC;
