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
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    attempts              INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    lease_token           TEXT,
    lease_expires_at      TIMESTAMPTZ,
    last_error_code       TEXT,
    response_json         JSONB,
    result_data           JSONB,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at            TIMESTAMPTZ,
    completed_at          TIMESTAMPTZ,
    failed_at             TIMESTAMPTZ,
    PRIMARY KEY (session_id, activity_id),
    FOREIGN KEY (session_id, activity_id)
        REFERENCES public.school_answer_requests(session_id, activity_id) ON DELETE CASCADE,
    CONSTRAINT school_evaluation_jobs_running_lease CHECK (
        (status = 'running' AND lease_token IS NOT NULL AND lease_expires_at IS NOT NULL)
        OR (status <> 'running' AND lease_token IS NULL AND lease_expires_at IS NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_school_evaluation_jobs_claimable
    ON public.school_evaluation_jobs(status, lease_expires_at, created_at);

ALTER TABLE public.school_evaluation_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM anon;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM authenticated;
REVOKE ALL ON TABLE public.school_evaluation_jobs FROM PUBLIC;
