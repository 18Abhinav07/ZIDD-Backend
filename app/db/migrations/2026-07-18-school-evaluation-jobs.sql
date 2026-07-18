CREATE TABLE IF NOT EXISTS public.school_evaluation_jobs (
    session_id            UUID NOT NULL,
    activity_id           TEXT NOT NULL,
    user_id               TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    raw_answer            TEXT NOT NULL,
    expected_state_json   JSONB NOT NULL,
    expected_state_digest TEXT NOT NULL,
    answer_hash           TEXT NOT NULL,
    answer_claim_token    TEXT NOT NULL,
    flow_type             TEXT NOT NULL,
    evaluation_mode       TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'queued'
        CONSTRAINT school_evaluation_jobs_status_check
        CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    attempts              INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    max_attempts          INTEGER NOT NULL DEFAULT 3 CHECK (max_attempts > 0),
    lease_owner           TEXT,
    lease_token           TEXT,
    lease_version         INTEGER NOT NULL DEFAULT 0 CHECK (lease_version >= 0),
    lease_expires_at      TIMESTAMPTZ,
    last_error_code       TEXT,
    error_json            JSONB,
    response_json         JSONB,
    result_data           JSONB,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at            TIMESTAMPTZ,
    completed_at          TIMESTAMPTZ,
    failed_at             TIMESTAMPTZ,
    cancelled_at          TIMESTAMPTZ,
    PRIMARY KEY (session_id, activity_id),
    FOREIGN KEY (session_id, activity_id)
        REFERENCES public.school_answer_requests(session_id, activity_id) ON DELETE CASCADE,
    CONSTRAINT school_evaluation_jobs_running_lease CHECK (
        (status = 'running'
            AND lease_owner IS NOT NULL
            AND lease_token IS NOT NULL
            AND lease_expires_at IS NOT NULL)
        OR (status <> 'running'
            AND lease_owner IS NULL
            AND lease_token IS NULL
            AND lease_expires_at IS NULL)
    )
);

ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3;
ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS lease_owner TEXT;
ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS lease_version INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS error_json JSONB;
ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ;

UPDATE public.school_evaluation_jobs
SET max_attempts = GREATEST(max_attempts, attempts, 1)
WHERE max_attempts < attempts OR max_attempts < 1;
UPDATE public.school_evaluation_jobs
SET lease_owner = 'legacy-unowned'
WHERE status = 'running' AND lease_owner IS NULL;

ALTER TABLE public.school_evaluation_jobs
    DROP CONSTRAINT IF EXISTS school_evaluation_jobs_max_attempts_check;
ALTER TABLE public.school_evaluation_jobs
    ADD CONSTRAINT school_evaluation_jobs_max_attempts_check
    CHECK (max_attempts > 0);
ALTER TABLE public.school_evaluation_jobs
    DROP CONSTRAINT IF EXISTS school_evaluation_jobs_lease_version_check;
ALTER TABLE public.school_evaluation_jobs
    ADD CONSTRAINT school_evaluation_jobs_lease_version_check
    CHECK (lease_version >= 0);
ALTER TABLE public.school_evaluation_jobs
    DROP CONSTRAINT IF EXISTS school_evaluation_jobs_status_check;
ALTER TABLE public.school_evaluation_jobs
    ADD CONSTRAINT school_evaluation_jobs_status_check
    CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled'));
ALTER TABLE public.school_evaluation_jobs
    DROP CONSTRAINT IF EXISTS school_evaluation_jobs_running_lease;
ALTER TABLE public.school_evaluation_jobs
    ADD CONSTRAINT school_evaluation_jobs_running_lease CHECK (
        (status = 'running'
            AND lease_owner IS NOT NULL
            AND lease_token IS NOT NULL
            AND lease_expires_at IS NOT NULL)
        OR (status <> 'running'
            AND lease_owner IS NULL
            AND lease_token IS NULL
            AND lease_expires_at IS NULL)
    );

CREATE INDEX IF NOT EXISTS idx_school_evaluation_jobs_claimable
    ON public.school_evaluation_jobs(status, lease_expires_at, created_at);

ALTER TABLE public.school_evaluation_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM anon;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM authenticated;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM PUBLIC;
