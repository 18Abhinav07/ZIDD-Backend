ALTER TABLE public.session_start_requests
    ADD COLUMN IF NOT EXISTS claim_generation INTEGER NOT NULL DEFAULT 1;

DROP INDEX IF EXISTS public.idx_session_start_requests_source_transition;

CREATE UNIQUE INDEX idx_session_start_requests_source_transition
    ON public.session_start_requests(source_session_id, source_transition_id)
    WHERE source_session_id IS NOT NULL
      AND source_transition_id IS NOT NULL
      AND status IN ('in_progress', 'completed');
