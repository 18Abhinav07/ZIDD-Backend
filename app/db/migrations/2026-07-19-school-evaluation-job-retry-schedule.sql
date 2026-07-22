-- Durable provider retry scheduling for School semantic-evaluation jobs.
-- A rate-limited provider releases its worker lease immediately; the database
-- controls when that exact idempotent answer can be claimed again.

BEGIN;

ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS next_attempt_at TIMESTAMPTZ;

UPDATE public.school_evaluation_jobs
SET next_attempt_at = COALESCE(next_attempt_at, updated_at, created_at, now())
WHERE next_attempt_at IS NULL;

ALTER TABLE public.school_evaluation_jobs
    ALTER COLUMN next_attempt_at SET DEFAULT now(),
    ALTER COLUMN next_attempt_at SET NOT NULL;

DROP INDEX IF EXISTS public.idx_school_evaluation_jobs_claimable;
CREATE INDEX IF NOT EXISTS idx_school_evaluation_jobs_claimable
    ON public.school_evaluation_jobs(
        status,
        next_attempt_at,
        lease_expires_at,
        created_at
    );

COMMIT;
