-- Durable, immutable-at-execution metadata captured when a School answer arrives.

BEGIN;

ALTER TABLE public.school_evaluation_jobs
    ADD COLUMN IF NOT EXISTS request_metadata_json JSONB;

UPDATE public.school_evaluation_jobs
SET request_metadata_json = '{}'::jsonb
WHERE jsonb_typeof(request_metadata_json) IS DISTINCT FROM 'object';

ALTER TABLE public.school_evaluation_jobs
    ALTER COLUMN request_metadata_json SET DEFAULT '{}'::jsonb,
    ALTER COLUMN request_metadata_json SET NOT NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conrelid = 'public.school_evaluation_jobs'::regclass
          AND conname = 'school_evaluation_jobs_request_metadata_object'
    ) THEN
        ALTER TABLE public.school_evaluation_jobs
            ADD CONSTRAINT school_evaluation_jobs_request_metadata_object
            CHECK (jsonb_typeof(request_metadata_json) = 'object');
    END IF;
END $$;

COMMIT;
