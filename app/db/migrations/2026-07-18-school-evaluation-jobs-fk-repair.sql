-- Repair the composite answer-request foreign key for databases where
-- school_evaluation_jobs predated the canonical CREATE TABLE definition.
-- Do not delete orphaned rows: fail closed so an operator can investigate.

DO $migration$
DECLARE
    job_session_attnum SMALLINT;
    job_activity_attnum SMALLINT;
    request_session_attnum SMALLINT;
    request_activity_attnum SMALLINT;
    constraint_row RECORD;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.school_evaluation_jobs AS job
        LEFT JOIN public.school_answer_requests AS request
          ON request.session_id = job.session_id
         AND request.activity_id = job.activity_id
        WHERE request.session_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'school_evaluation_jobs_answer_request_fk_repair_blocked:orphan_job';
    END IF;

    SELECT attnum
    INTO job_session_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.school_evaluation_jobs'::regclass
      AND attname = 'session_id'
      AND NOT attisdropped;

    SELECT attnum
    INTO job_activity_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.school_evaluation_jobs'::regclass
      AND attname = 'activity_id'
      AND NOT attisdropped;

    SELECT attnum
    INTO request_session_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.school_answer_requests'::regclass
      AND attname = 'session_id'
      AND NOT attisdropped;

    SELECT attnum
    INTO request_activity_attnum
    FROM pg_attribute
    WHERE attrelid = 'public.school_answer_requests'::regclass
      AND attname = 'activity_id'
      AND NOT attisdropped;

    -- Historical development databases can already have this exact composite
    -- foreign key with ON DELETE NO ACTION. The runtime guard requires the
    -- job to be a true private child of its answer request, so retain a valid
    -- cascade FK and replace only matching FKs with the wrong delete action.
    FOR constraint_row IN
        SELECT foreign_key.conname
        FROM pg_constraint AS foreign_key
        WHERE foreign_key.conrelid = 'public.school_evaluation_jobs'::regclass
          AND foreign_key.confrelid = 'public.school_answer_requests'::regclass
          AND foreign_key.contype = 'f'
          AND foreign_key.conkey = ARRAY[job_session_attnum, job_activity_attnum]
          AND foreign_key.confkey = ARRAY[
              request_session_attnum,
              request_activity_attnum
          ]
          AND foreign_key.confdeltype <> 'c'
    LOOP
        EXECUTE format(
            'ALTER TABLE public.school_evaluation_jobs DROP CONSTRAINT %I',
            constraint_row.conname
        );
    END LOOP;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint AS foreign_key
        WHERE foreign_key.conrelid = 'public.school_evaluation_jobs'::regclass
          AND foreign_key.confrelid = 'public.school_answer_requests'::regclass
          AND foreign_key.contype = 'f'
          AND foreign_key.conkey = ARRAY[job_session_attnum, job_activity_attnum]
          AND foreign_key.confkey = ARRAY[
              request_session_attnum,
              request_activity_attnum
          ]
          AND foreign_key.confdeltype = 'c'
    ) THEN
        ALTER TABLE public.school_evaluation_jobs
            ADD CONSTRAINT school_evaluation_jobs_answer_request_fkey
            FOREIGN KEY (session_id, activity_id)
            REFERENCES public.school_answer_requests(session_id, activity_id)
            ON DELETE CASCADE;
    END IF;
END;
$migration$;
