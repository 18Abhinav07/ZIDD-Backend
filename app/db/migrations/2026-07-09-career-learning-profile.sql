CREATE TABLE IF NOT EXISTS public.learning_events (
    event_id         BIGSERIAL PRIMARY KEY,
    source_event_key TEXT NOT NULL UNIQUE,
    user_id          TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    domain           TEXT NOT NULL,
    task_type        TEXT NOT NULL,
    module_id        TEXT NOT NULL DEFAULT '',
    session_id       TEXT,
    node_id          TEXT NOT NULL DEFAULT '',
    skill_id         TEXT NOT NULL,
    source           TEXT NOT NULL,
    attempt_type     TEXT NOT NULL DEFAULT '',
    score            REAL NOT NULL DEFAULT 0.0,
    confidence       REAL NOT NULL DEFAULT 0.0,
    criteria_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    blockers         JSONB NOT NULL DEFAULT '[]'::jsonb,
    gap              TEXT NOT NULL DEFAULT '',
    scenario_json    JSONB NOT NULL DEFAULT '{}'::jsonb,
    caveats          JSONB NOT NULL DEFAULT '[]'::jsonb,
    model_name       TEXT,
    prompt_version   TEXT,
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_events_user_time
    ON public.learning_events(user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_domain_skill_time
    ON public.learning_events(user_id, domain, skill_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_session
    ON public.learning_events(session_id);

CREATE TABLE IF NOT EXISTS public.session_reports (
    report_id       TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL UNIQUE REFERENCES public.sessions(session_id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    report_type     TEXT NOT NULL,
    task_type       TEXT NOT NULL,
    module_id       TEXT NOT NULL DEFAULT '',
    status          TEXT NOT NULL,
    score           REAL NOT NULL DEFAULT 0.0,
    readiness_score REAL NOT NULL DEFAULT 0.0,
    summary         TEXT NOT NULL DEFAULT '',
    strengths_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_actions_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    validity_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    public_context_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_session_reports_user_type_time
    ON public.session_reports(user_id, report_type, created_at DESC);

CREATE TABLE IF NOT EXISTS public.learner_skill_profiles (
    user_id         TEXT NOT NULL REFERENCES public.learner_profiles(user_id),
    domain          TEXT NOT NULL,
    skill_id        TEXT NOT NULL,
    module_id       TEXT NOT NULL DEFAULT '',
    task_type       TEXT NOT NULL DEFAULT '',
    mastery         REAL NOT NULL DEFAULT 0.0,
    readiness       REAL NOT NULL DEFAULT 0.0,
    confidence      REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    strengths_json  JSONB NOT NULL DEFAULT '[]'::jsonb,
    gaps_json       JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_next_action TEXT NOT NULL DEFAULT '',
    source_summary  TEXT NOT NULL DEFAULT '',
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, domain, skill_id)
);

CREATE INDEX IF NOT EXISTS idx_learner_skill_profiles_user_domain_mastery_seen
    ON public.learner_skill_profiles(user_id, domain, mastery, last_seen_at DESC);

ALTER TABLE public.learning_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.session_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learner_skill_profiles ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.learning_events FROM anon;
REVOKE ALL ON TABLE public.learning_events FROM authenticated;
REVOKE ALL ON TABLE public.learning_events FROM PUBLIC;
REVOKE ALL ON TABLE public.session_reports FROM anon;
REVOKE ALL ON TABLE public.session_reports FROM authenticated;
REVOKE ALL ON TABLE public.session_reports FROM PUBLIC;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM anon;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM authenticated;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM PUBLIC;
