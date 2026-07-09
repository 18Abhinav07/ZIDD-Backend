-- Durable tutor/session runtime. Product learner state lives in Supabase only;
-- process memory is an optimization, not authority.

CREATE TABLE IF NOT EXISTS public.session_runtime (
    session_id         TEXT PRIMARY KEY REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    user_id            TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    current_node       TEXT NOT NULL,
    module_id          TEXT,
    task_type          TEXT,
    test_mode          BOOLEAN NOT NULL DEFAULT FALSE,
    status             TEXT NOT NULL DEFAULT 'active',
    state_snapshot     JSONB NOT NULL DEFAULT '{}'::jsonb,
    pending_transition JSONB,
    session_version    INTEGER NOT NULL DEFAULT 1,
    active_turn_id     TEXT,
    active_opening_id  TEXT,
    last_error         JSONB,
    lease_expires_at   TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_session_runtime_user_status
    ON public.session_runtime(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS public.session_messages (
    message_id    TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    sequence_index INTEGER NOT NULL DEFAULT 0,
    turn_id       TEXT,
    transition_id TEXT,
    node_id       TEXT,
    role          TEXT NOT NULL,
    content       TEXT NOT NULL DEFAULT '',
    speaker_name  TEXT,
    speaker_id    TEXT,
    message_kind  TEXT,
    status        TEXT NOT NULL DEFAULT 'committed',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS sequence_index INTEGER NOT NULL DEFAULT 0;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS turn_id TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS transition_id TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS node_id TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'assistant';
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT '';
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS speaker_name TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS speaker_id TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS message_kind TEXT;
ALTER TABLE public.session_messages
    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'committed';

DROP INDEX IF EXISTS public.idx_session_messages_session_created;

CREATE INDEX IF NOT EXISTS idx_session_messages_session_sequence
    ON public.session_messages(session_id, sequence_index);

CREATE TABLE IF NOT EXISTS public.session_turn_requests (
    session_id        TEXT NOT NULL REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    client_turn_id    TEXT NOT NULL,
    request_hash      TEXT NOT NULL,
    expected_version  INTEGER,
    status            TEXT NOT NULL DEFAULT 'in_progress',
    transcript_delta  JSONB NOT NULL DEFAULT '[]'::jsonb,
    done_snapshot     JSONB,
    error_code        TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, client_turn_id)
);
WITH ranked_turn_requests AS (
    SELECT ctid,
           ROW_NUMBER() OVER (
               PARTITION BY session_id, expected_version
               ORDER BY created_at ASC, updated_at ASC, client_turn_id ASC
           ) AS active_rank
    FROM public.session_turn_requests
    WHERE expected_version IS NOT NULL
      AND status IN ('in_progress', 'completed')
)
UPDATE public.session_turn_requests request
SET status = 'failed',
    error_code = COALESCE(request.error_code, 'duplicate_active_version'),
    updated_at = now()
FROM ranked_turn_requests ranked
WHERE request.ctid = ranked.ctid
  AND ranked.active_rank > 1;
DROP INDEX IF EXISTS public.idx_session_turn_requests_session_version;
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_turn_requests_session_version
    ON public.session_turn_requests(session_id, expected_version)
    WHERE expected_version IS NOT NULL AND status IN ('in_progress', 'completed');

CREATE TABLE IF NOT EXISTS public.session_opening_requests (
    session_id    TEXT NOT NULL REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    transition_id TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'in_progress',
    message_id    TEXT,
    attempts      INTEGER NOT NULL DEFAULT 0,
    last_error    TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, transition_id)
);

CREATE TABLE IF NOT EXISTS public.session_end_requests (
    session_id    TEXT PRIMARY KEY REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'in_progress',
    response_json JSONB,
    error_code    TEXT,
    attempts      INTEGER NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE public.session_runtime ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_turn_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_opening_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_end_requests ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.session_runtime FROM anon;
REVOKE ALL ON TABLE public.session_runtime FROM authenticated;
REVOKE ALL ON TABLE public.session_runtime FROM PUBLIC;

REVOKE ALL ON TABLE public.session_messages FROM anon;
REVOKE ALL ON TABLE public.session_messages FROM authenticated;
REVOKE ALL ON TABLE public.session_messages FROM PUBLIC;

REVOKE ALL ON TABLE public.session_turn_requests FROM anon;
REVOKE ALL ON TABLE public.session_turn_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_turn_requests FROM PUBLIC;

REVOKE ALL ON TABLE public.session_opening_requests FROM anon;
REVOKE ALL ON TABLE public.session_opening_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_opening_requests FROM PUBLIC;

REVOKE ALL ON TABLE public.session_end_requests FROM anon;
REVOKE ALL ON TABLE public.session_end_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_end_requests FROM PUBLIC;
