CREATE TABLE IF NOT EXISTS public.school_answer_requests (
    session_id UUID NOT NULL REFERENCES public.school_sessions(session_id) ON DELETE CASCADE,
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

ALTER TABLE public.school_answer_requests
    ADD COLUMN IF NOT EXISTS claim_token TEXT;
UPDATE public.school_answer_requests
SET claim_token = md5(
    random()::text || clock_timestamp()::text || session_id::text || activity_id
)
WHERE claim_token IS NULL;
ALTER TABLE public.school_answer_requests
    ALTER COLUMN claim_token SET NOT NULL;

ALTER TABLE public.school_answer_requests ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.school_answer_requests FROM anon;
REVOKE ALL ON TABLE public.school_answer_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_answer_requests FROM PUBLIC;
