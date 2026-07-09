-- Durable /session/start idempotency latch. Prevents duplicate credit charges,
-- duplicate free-attempt consumption, and ambiguous next-skill handoffs.

CREATE TABLE IF NOT EXISTS public.session_start_requests (
    user_id              TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    client_start_id      TEXT NOT NULL,
    request_hash         TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'in_progress',
    session_id           TEXT,
    response_json        JSONB,
    error_code           TEXT,
    source_session_id    TEXT,
    source_transition_id TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, client_start_id)
);

WITH ranked_start_requests AS (
    SELECT ctid,
           ROW_NUMBER() OVER (
               PARTITION BY source_session_id, source_transition_id
               ORDER BY created_at ASC, updated_at ASC, client_start_id ASC
           ) AS active_rank
    FROM public.session_start_requests
    WHERE source_session_id IS NOT NULL
      AND source_transition_id IS NOT NULL
      AND status IN ('in_progress', 'completed')
)
UPDATE public.session_start_requests request
SET status = 'failed',
    error_code = COALESCE(request.error_code, 'duplicate_source_transition'),
    updated_at = now()
FROM ranked_start_requests ranked
WHERE request.ctid = ranked.ctid
  AND ranked.active_rank > 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_session_start_requests_source_transition
    ON public.session_start_requests(source_session_id, source_transition_id)
    WHERE source_session_id IS NOT NULL
      AND source_transition_id IS NOT NULL
      AND status IN ('in_progress', 'completed');

ALTER TABLE public.session_start_requests ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.session_start_requests FROM anon;
REVOKE ALL ON TABLE public.session_start_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_start_requests FROM PUBLIC;
