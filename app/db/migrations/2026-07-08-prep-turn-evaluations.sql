ALTER TABLE public.competency_nodes
    ADD COLUMN IF NOT EXISTS node_mastered BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS display_status TEXT NOT NULL DEFAULT 'active',
    ADD COLUMN IF NOT EXISTS best_independent_score REAL NOT NULL DEFAULT 0.0,
    ADD COLUMN IF NOT EXISTS independent_passes INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS transfer_passes INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS pressure_passes INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS scaffold_successes INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_gap TEXT NOT NULL DEFAULT '',
    ADD COLUMN IF NOT EXISTS mastery_evidence JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS public.turn_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES public.sessions(session_id),
    user_id TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    node_id TEXT NOT NULL,
    turn_id TEXT,
    attempt_index INTEGER NOT NULL,
    attempt_type TEXT NOT NULL,
    user_answer TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    raw_score REAL NOT NULL,
    effective_score REAL NOT NULL,
    criteria_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    pass_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    advance_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    mastery_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    tutor_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_name TEXT,
    prompt_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_turn_evaluations_session
    ON public.turn_evaluations(session_id, created_at);

CREATE INDEX IF NOT EXISTS idx_turn_evaluations_user_node
    ON public.turn_evaluations(user_id, node_id, created_at DESC);

ALTER TABLE public.turn_evaluations ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.turn_evaluations FROM anon;
REVOKE ALL ON TABLE public.turn_evaluations FROM authenticated;
REVOKE ALL ON TABLE public.turn_evaluations FROM PUBLIC;
