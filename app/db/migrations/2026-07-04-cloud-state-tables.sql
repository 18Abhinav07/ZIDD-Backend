CREATE TABLE IF NOT EXISTS turns (
    id              BIGSERIAL PRIMARY KEY,
    session_id      TEXT REFERENCES sessions(session_id),
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    node_id         TEXT NOT NULL,
    score           REAL,
    on_task         BOOLEAN NOT NULL DEFAULT TRUE,
    english         BOOLEAN NOT NULL DEFAULT TRUE,
    affect          TEXT NOT NULL DEFAULT 'neutral',
    ts              DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_turns_session ON turns(session_id, id);

CREATE TABLE IF NOT EXISTS weaknesses (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    task_type       TEXT NOT NULL,
    skill_id        TEXT NOT NULL,
    hit_count       INTEGER NOT NULL DEFAULT 0,
    last_score      REAL,
    last_seen       DOUBLE PRECISION NOT NULL,
    last_raw        TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (user_id, task_type, skill_id)
);
CREATE INDEX IF NOT EXISTS idx_weaknesses_user_task_seen
    ON weaknesses(user_id, task_type, last_seen DESC);

CREATE TABLE IF NOT EXISTS school_skill_mastery (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    skill           TEXT NOT NULL,
    ema             REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_seen       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, skill)
);

CREATE TABLE IF NOT EXISTS school_results (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    test_id         TEXT NOT NULL,
    class_no        INTEGER NOT NULL,
    kind            TEXT NOT NULL,
    score           REAL NOT NULL,
    passed          BOOLEAN NOT NULL DEFAULT FALSE,
    by_skill        JSONB NOT NULL DEFAULT '[]'::jsonb,
    weak_skills     JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at      DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, test_id)
);

CREATE TABLE IF NOT EXISTS test_items (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    task_type       TEXT NOT NULL,
    items           JSONB NOT NULL DEFAULT '[]'::jsonb,
    cached_at       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, task_type)
);

ALTER TABLE turns                ENABLE ROW LEVEL SECURITY;
ALTER TABLE weaknesses           ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_skill_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_results       ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_items           ENABLE ROW LEVEL SECURITY;
