-- Zidd engine schema (architecture-v3 §408). Run once against Supabase.
-- Text + vectors only. NEVER store raw audio/files here (3GB free-tier rule).

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------- learners ----------
CREATE TABLE IF NOT EXISTS learner_profiles (
    user_id         TEXT PRIMARY KEY,
    display_name    TEXT,
    preferences     JSONB NOT NULL DEFAULT '{}'::jsonb,
    primary_motive  TEXT,
    onboarding_completed_at TIMESTAMPTZ,
    school_profile  JSONB NOT NULL DEFAULT '{}'::jsonb,
    career_profile  JSONB NOT NULL DEFAULT '{}'::jsonb,
    onboarding_state JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Present only for Google-linked or email-known accounts; both UNIQUE so
    -- login-by-email/login-by-google_sub lookups resolve to at most one row.
    email           TEXT UNIQUE,
    google_sub      TEXT UNIQUE,
    credits         INTEGER NOT NULL DEFAULT 0,
    -- Judge/demo bypass (architecture-v3 §621): when true, credit-deduction
    -- middleware skips ALL paywalls. NON-NEGOTIABLE for XPRIZE judging.
    demo_unlimited  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school_profile_versions (
    profile_version_id UUID PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'archived')),
    display_name TEXT,
    school_name TEXT,
    board_id TEXT CHECK (board_id IN ('cbse', 'ncert')),
    target_class_no INTEGER CHECK (target_class_no BETWEEN 2 AND 5),
    subject_ids JSONB,
    preferred_teaching_language TEXT CHECK (preferred_teaching_language IN ('en', 'hi', 'hi_en')),
    english_comfort TEXT CHECK (english_comfort IN ('low', 'medium', 'high')),
    learner_goal TEXT,
    parent_goal TEXT,
    prior_difficulty_signals JSONB,
    current_step INTEGER NOT NULL DEFAULT 0 CHECK (current_step BETWEEN 0 AND 4),
    draft_revision INTEGER NOT NULL DEFAULT 1 CHECK (draft_revision >= 1),
    last_save_request_id UUID,
    last_save_payload_hash TEXT,
    source_profile_version_id UUID REFERENCES school_profile_versions(profile_version_id),
    activation_request_id UUID,
    activation_payload_hash TEXT,
    activation_result_profile_version_id UUID REFERENCES school_profile_versions(profile_version_id),
    coach_avatar_id TEXT,
    coach_palette_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    activated_at TIMESTAMPTZ,
    archived_at TIMESTAMPTZ,
    CONSTRAINT school_profile_versions_complete_non_drafts CHECK (
        status <> 'active'
        OR (
            display_name IS NOT NULL
            AND school_name IS NOT NULL
            AND char_length(btrim(display_name)) >= 2
            AND char_length(btrim(school_name)) >= 2
            AND board_id IN ('cbse', 'ncert')
            AND target_class_no BETWEEN 2 AND 5
            AND subject_ids IS NOT NULL
            AND jsonb_typeof(subject_ids) = 'array'
            AND CASE
                WHEN jsonb_typeof(subject_ids) = 'array'
                THEN jsonb_array_length(subject_ids) > 0
                ELSE FALSE
            END
            AND subject_ids <@ '["english"]'::jsonb
            AND preferred_teaching_language IN ('en', 'hi', 'hi_en')
            AND english_comfort IN ('low', 'medium', 'high')
            AND learner_goal IS NOT NULL
            AND parent_goal IS NOT NULL
            AND (
                NULLIF(btrim(learner_goal), '') IS NOT NULL
                OR NULLIF(btrim(parent_goal), '') IS NOT NULL
            )
            AND prior_difficulty_signals IS NOT NULL
            AND jsonb_typeof(prior_difficulty_signals) = 'array'
            AND prior_difficulty_signals <@ '["reading", "vocabulary", "grammar", "writing", "chapter_answers"]'::jsonb
        )
    ),
    CONSTRAINT school_profile_versions_lifecycle CHECK (
        (status = 'draft' AND activated_at IS NULL AND archived_at IS NULL)
        OR (status = 'active' AND activated_at IS NOT NULL AND archived_at IS NULL)
        OR (status = 'archived' AND archived_at IS NOT NULL)
    ),
    CONSTRAINT school_profile_versions_coach_identity CHECK (
        (coach_avatar_id IS NULL AND coach_palette_id IS NULL)
        OR (
            coach_avatar_id = coach_palette_id
            AND coach_avatar_id IN (
                'stuttering_sam', 'fluent_finn', 'brave_bella',
                'quiet_quint', 'tech_black', 'casual_purple',
                'casual_male', 'casual_female', 'casual_blue'
            )
        )
    )
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_active
    ON school_profile_versions(user_id)
    WHERE status = 'active';
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_one_draft
    ON school_profile_versions(user_id)
    WHERE status = 'draft';
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_profile_versions_activation_request
    ON school_profile_versions(user_id, activation_request_id)
    WHERE activation_request_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_school_profile_versions_user_status_updated
    ON school_profile_versions(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS school_profile_draft_requests (
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    request_id UUID NOT NULL,
    profile_version_id UUID NOT NULL
        REFERENCES school_profile_versions(profile_version_id),
    payload_hash TEXT NOT NULL,
    response_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, request_id)
);

-- ---------- sessions ----------
CREATE TABLE IF NOT EXISTS sessions (
    session_id      TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    module_id       TEXT,
    task_type       TEXT,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    test_mode       BOOLEAN NOT NULL DEFAULT FALSE,
    reattempt_of_session_id TEXT,
    career_context  JSONB NOT NULL DEFAULT '{}'::jsonb,
    scenario_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    persona_roster  JSONB NOT NULL DEFAULT '[]'::jsonb,
    context_hash    TEXT NOT NULL DEFAULT 'default',
    turn_count      INTEGER NOT NULL DEFAULT 0,
    final_mastery   REAL,
    summary         TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

-- ---------- durable live session runtime ----------
CREATE TABLE IF NOT EXISTS session_runtime (
    session_id        TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id           TEXT NOT NULL REFERENCES learner_profiles(user_id),
    current_node      TEXT NOT NULL,
    module_id         TEXT,
    task_type         TEXT,
    test_mode         BOOLEAN NOT NULL DEFAULT FALSE,
    status            TEXT NOT NULL DEFAULT 'active',
    state_snapshot    JSONB NOT NULL DEFAULT '{}'::jsonb,
    pending_transition JSONB,
    session_version   INTEGER NOT NULL DEFAULT 1,
    active_turn_id    TEXT,
    active_opening_id TEXT,
    last_error        JSONB,
    lease_expires_at  TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_runtime_user_status
    ON session_runtime(user_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS session_messages (
    message_id     TEXT PRIMARY KEY,
    session_id     TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    sequence_index INTEGER NOT NULL DEFAULT 0,
    turn_id        TEXT,
    transition_id  TEXT,
    node_id        TEXT,
    role           TEXT NOT NULL,
    content        TEXT NOT NULL DEFAULT '',
    speaker_name   TEXT,
    speaker_id     TEXT,
    message_kind   TEXT,
    status         TEXT NOT NULL DEFAULT 'committed',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_session_messages_session_sequence
    ON session_messages(session_id, sequence_index);

CREATE TABLE IF NOT EXISTS session_turn_requests (
    session_id       TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    client_turn_id   TEXT NOT NULL,
    request_hash     TEXT NOT NULL,
    expected_version INTEGER,
    status           TEXT NOT NULL DEFAULT 'in_progress',
    transcript_delta JSONB NOT NULL DEFAULT '[]'::jsonb,
    done_snapshot    JSONB,
    error_code       TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, client_turn_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_turn_requests_session_version
    ON session_turn_requests(session_id, expected_version)
    WHERE expected_version IS NOT NULL AND status IN ('in_progress', 'completed');

CREATE TABLE IF NOT EXISTS session_start_requests (
    user_id              TEXT NOT NULL REFERENCES learner_profiles(user_id),
    client_start_id      TEXT NOT NULL,
    request_hash         TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'in_progress',
    session_id           TEXT,
    response_json        JSONB,
    error_code           TEXT,
    source_session_id    TEXT,
    source_transition_id TEXT,
    claim_generation     INTEGER NOT NULL DEFAULT 1,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, client_start_id)
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_session_start_requests_source_transition
    ON session_start_requests(source_session_id, source_transition_id)
    WHERE source_session_id IS NOT NULL
      AND source_transition_id IS NOT NULL
      AND status IN ('in_progress', 'completed');

CREATE TABLE IF NOT EXISTS session_opening_requests (
    session_id     TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    transition_id  TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'in_progress',
    message_id     TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    last_error     TEXT,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, transition_id)
);

CREATE TABLE IF NOT EXISTS session_end_requests (
    session_id     TEXT PRIMARY KEY REFERENCES sessions(session_id) ON DELETE CASCADE,
    status         TEXT NOT NULL DEFAULT 'in_progress',
    response_json  JSONB,
    error_code     TEXT,
    attempts       INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- turns ----------
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

CREATE TABLE IF NOT EXISTS turn_evaluations (
    evaluation_id TEXT PRIMARY KEY,
    session_id    TEXT NOT NULL REFERENCES sessions(session_id),
    user_id       TEXT NOT NULL REFERENCES learner_profiles(user_id),
    node_id       TEXT NOT NULL,
    turn_id       TEXT,
    attempt_index INTEGER NOT NULL,
    attempt_type  TEXT NOT NULL,
    user_answer   TEXT NOT NULL,
    rubric_version TEXT NOT NULL,
    raw_score     REAL NOT NULL,
    effective_score REAL NOT NULL,
    criteria_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers      JSONB NOT NULL DEFAULT '[]'::jsonb,
    pass_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    advance_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    mastery_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    tutor_plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    context_json   JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_name    TEXT,
    prompt_version TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_turn_evaluations_session
    ON turn_evaluations(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_turn_evaluations_user_node
    ON turn_evaluations(user_id, node_id, created_at DESC);

-- ---------- long-term memory (pgvector) ----------
CREATE TABLE IF NOT EXISTS memory_entries (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    session_id      TEXT,
    competency_node TEXT NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(768),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_memory_user_node
    ON memory_entries(user_id, competency_node);
-- NOTE: no IVFFlat index until >10K rows (architecture-v3 §408). Exact scan
-- is faster and recall-perfect below that threshold.

-- ---------- per-node mastery ----------
CREATE TABLE IF NOT EXISTS competency_nodes (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    mastery         REAL NOT NULL DEFAULT 0.0,
    best_mastery    REAL NOT NULL DEFAULT 0.0,
    attempts        INTEGER NOT NULL DEFAULT 0,
    clean_pass      BOOLEAN NOT NULL DEFAULT FALSE,   -- passed in <=2 attempts
    node_completed  BOOLEAN NOT NULL DEFAULT FALSE,   -- user advanced past this node
    node_mastered   BOOLEAN NOT NULL DEFAULT FALSE,   -- stricter career-prep mastery
    display_status  TEXT NOT NULL DEFAULT 'active',
    best_independent_score REAL NOT NULL DEFAULT 0.0,
    independent_passes INTEGER NOT NULL DEFAULT 0,
    transfer_passes INTEGER NOT NULL DEFAULT 0,
    pressure_passes INTEGER NOT NULL DEFAULT 0,
    scaffold_successes INTEGER NOT NULL DEFAULT 0,
    last_gap        TEXT NOT NULL DEFAULT '',
    mastery_evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    completed_at    TIMESTAMPTZ,
    completion_count INTEGER NOT NULL DEFAULT 0,
    last_completed_session_id TEXT,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, competency_node)
);

CREATE TABLE IF NOT EXISTS node_attempts (
    attempt_id TEXT PRIMARY KEY,
    session_id TEXT REFERENCES sessions(session_id),
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    competency_node TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ,
    starting_mastery REAL NOT NULL DEFAULT 0.0,
    ending_mastery REAL NOT NULL DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_node_attempts_user_node
    ON node_attempts(user_id, competency_node, started_at DESC);

-- ---------- weaknesses ----------
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

-- ---------- global learner evidence/profile ----------
CREATE TABLE IF NOT EXISTS learning_events (
    event_id         BIGSERIAL PRIMARY KEY,
    source_event_key TEXT NOT NULL UNIQUE,
    user_id          TEXT NOT NULL REFERENCES learner_profiles(user_id),
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
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT learning_events_domain CHECK (domain IN ('career', 'school')),
    CONSTRAINT learning_events_domain_task CHECK (
        (domain = 'school' AND task_type LIKE 'school\_%' ESCAPE '\')
        OR (domain = 'career' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
    )
);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_time
    ON learning_events(user_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_user_domain_skill_time
    ON learning_events(user_id, domain, skill_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_learning_events_session
    ON learning_events(session_id);

CREATE TABLE IF NOT EXISTS session_reports (
    report_id       TEXT PRIMARY KEY,
    session_id      TEXT NOT NULL UNIQUE REFERENCES sessions(session_id) ON DELETE CASCADE,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
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
    ON session_reports(user_id, report_type, created_at DESC);

CREATE TABLE IF NOT EXISTS learner_skill_profiles (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
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
    PRIMARY KEY (user_id, domain, skill_id),
    CONSTRAINT learner_skill_profiles_domain CHECK (domain IN ('career', 'school')),
    CONSTRAINT learner_skill_profiles_domain_task CHECK (
        (domain = 'school' AND task_type LIKE 'school\_%' ESCAPE '\')
        OR (domain = 'career' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
    )
);
CREATE INDEX IF NOT EXISTS idx_learner_skill_profiles_user_domain_mastery_seen
    ON learner_skill_profiles(user_id, domain, mastery, last_seen_at DESC);

-- ---------- school progress ----------
CREATE TABLE IF NOT EXISTS school_curriculum_releases (
    curriculum_release_id TEXT PRIMARY KEY,
    board_id TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    class_no INTEGER NOT NULL CHECK (class_no BETWEEN 1 AND 12),
    academic_year TEXT NOT NULL,
    manifest JSONB NOT NULL,
    release_digest TEXT NOT NULL CHECK (release_digest ~ '^[0-9a-f]{64}$'),
    status TEXT NOT NULL CHECK (status IN ('current', 'retired')),
    effective_from DATE NOT NULL,
    effective_through DATE NOT NULL,
    retired_on DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT school_curriculum_releases_identity_digest_unique
        UNIQUE (board_id, subject_id, class_no, academic_year, release_digest),
    CHECK (effective_through >= effective_from),
    CHECK (retired_on IS NULL OR retired_on BETWEEN effective_from AND effective_through)
);

CREATE OR REPLACE FUNCTION reject_school_curriculum_release_identity_change()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    RAISE EXCEPTION 'school_curriculum_release_immutable:%',
        OLD.curriculum_release_id
        USING ERRCODE = '55000';
    RETURN OLD;
END;
$function$;

DROP TRIGGER IF EXISTS school_curriculum_releases_immutable
    ON school_curriculum_releases;
CREATE TRIGGER school_curriculum_releases_immutable
BEFORE UPDATE OR DELETE ON school_curriculum_releases
FOR EACH ROW
EXECUTE FUNCTION reject_school_curriculum_release_identity_change();

CREATE UNIQUE INDEX IF NOT EXISTS idx_school_curriculum_releases_one_current
ON school_curriculum_releases(board_id, subject_id, class_no, academic_year)
WHERE status = 'current';

INSERT INTO public.school_curriculum_releases
    (curriculum_release_id, board_id, subject_id, class_no, academic_year,
     manifest, release_digest, status, effective_from, effective_through,
     retired_on)
VALUES
    ('english_cbse_2026_27_c2_bemr1', 'cbse', 'english', 2, '2026-27',
     $release_0${"academic_year":"2026-27","board_id":"cbse","book_code":"bemr1","book_title":"Mridang","class_no":2,"curriculum_release_id":"english_cbse_2026_27_c2_bemr1","edition_history":[{"kind":"first_edition","month":"May","year":2023},{"kind":"reprint","month":"March","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"February","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-434-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Sing","mode":"singing","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Read","mode":"reading","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Draw","mode":"drawing","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Say","mode":"pronunciation","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"bd8b09e5eec4502a47bcaa5b46a0e4cb3cee9643fd5e20918a8b72a496ac22ca","source_size_bytes":2812044,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c2_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"My Bicycle"},{"kind":"picture_reading","module_id":"eng_c2_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c2_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"It is Fun"},{"kind":"lesson","module_id":"eng_c2_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Seeing without Seeing"}],"order":2,"title":"Welcome to My World","unit_id":"eng_c2_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Come Back Soon"},{"kind":"lesson","module_id":"eng_c2_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Between Home and School"},{"kind":"lesson","module_id":"eng_c2_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"This is My Town"}],"order":3,"title":"Going Places","unit_id":"eng_c2_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"A Show of Clouds"},{"kind":"lesson","module_id":"eng_c2_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"My Name"},{"kind":"lesson","module_id":"eng_c2_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Crow"},{"kind":"lesson","module_id":"eng_c2_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"The Smart Monkey"}],"order":4,"title":"Life Around Us","unit_id":"eng_c2_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Little Drops of Water"},{"kind":"lesson","module_id":"eng_c2_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"mixed","title":"We are all Indians"}],"order":5,"title":"Harmony","unit_id":"eng_c2_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_0$::jsonb,
     'a03eabb3015cf0917e54894caa5c3b7526671537bdfb58b76493579d41964c19', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c3_cesa1', 'cbse', 'english', 3, '2026-27',
     $release_1${"academic_year":"2026-27","board_id":"cbse","book_code":"cesa1","book_title":"Santoor","class_no":3,"curriculum_release_id":"english_cbse_2026_27_c3_cesa1","edition_history":[{"kind":"first_edition","month":"April","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-991-7","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c3_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Our National Anthem"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"6b0ce2a24327c9fad6acd997b38a12ce4bff961e729856133c4474656b424816","source_size_bytes":1956951,"subject_id":"english","units":[{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Colours"},{"kind":"lesson","module_id":"eng_c3_u01_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Badal and Moti"},{"kind":"lesson","module_id":"eng_c3_u01_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Best Friends"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c3_u01"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Out in the Garden"},{"kind":"lesson","module_id":"eng_c3_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"play","title":"Talking Toys"},{"kind":"lesson","module_id":"eng_c3_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Paper Boats"},{"kind":"self_assessment","module_id":"eng_c3_u02_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":2,"title":"Toys and Games","unit_id":"eng_c3_u02"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Big Laddoo"},{"kind":"lesson","module_id":"eng_c3_u03_m03","order":3,"phase_0_public_display_title":"Thank God!","source_genre":"poem","title":"Thank God"},{"kind":"lesson","module_id":"eng_c3_u03_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"Madhu's Wish"}],"order":3,"title":"Good Food","unit_id":"eng_c3_u03"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Night"},{"kind":"lesson","module_id":"eng_c3_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Chanda Mama Counts the Stars"},{"kind":"lesson","module_id":"eng_c3_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"informational","title":"Chandrayaan"},{"kind":"self_assessment","module_id":"eng_c3_u04_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":4,"title":"The Sky","unit_id":"eng_c3_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_1$::jsonb,
     '3330785de9b1378ef5da4dd702883d9bffc470d8aa2effec33832c5c9ff3f8b1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c4_desa1', 'cbse', 'english', 4, '2026-27',
     $release_2${"academic_year":"2026-27","board_id":"cbse","book_code":"desa1","book_title":"Santoor","class_no":4,"curriculum_release_id":"english_cbse_2026_27_c4_desa1","edition_history":[{"kind":"first_edition","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-932-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Read","mode":"reading","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Recite","mode":"recitation","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":8,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":9,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c4_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Constitution of India"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"ab890381b64c55094ea0651adb3e2c68d32a8341665d587ef90873fb9ab35f9a","source_size_bytes":6888606,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c4_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Together We Can"},{"kind":"lesson","module_id":"eng_c4_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Tinkling Bells"},{"kind":"lesson","module_id":"eng_c4_u01_m03","order":3,"phase_0_public_display_title":"Be Smart, Be Safe","source_genre":"informational","title":"Be Smart Be Safe"}],"order":1,"title":"My Land","unit_id":"eng_c4_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"One Thing at a Time"},{"kind":"lesson","module_id":"eng_c4_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Old Stag"},{"kind":"lesson","module_id":"eng_c4_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Braille"},{"kind":"self_assessment","module_id":"eng_c4_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 1"}],"order":2,"title":"My Beautiful World","unit_id":"eng_c4_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u03_m01","order":1,"phase_0_public_display_title":"Fit Body, Fit Mind, Fit Nation","source_genre":"informational","title":"Fit Body Fit Mind Fit Nation"},{"kind":"lesson","module_id":"eng_c4_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Lagori Champions"},{"kind":"lesson","module_id":"eng_c4_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Hekko"}],"order":3,"title":"Fun with Games","unit_id":"eng_c4_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Swing"},{"kind":"lesson","module_id":"eng_c4_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"A Journey to the Magical Mountains"},{"kind":"lesson","module_id":"eng_c4_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Maheshwar"},{"kind":"self_assessment","module_id":"eng_c4_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 2"}],"order":4,"title":"Up High","unit_id":"eng_c4_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_2$::jsonb,
     '426767f21ba2f38082aca8a2b05da202055e423245b3ece43c9c55f92b571ab1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
    ('english_cbse_2026_27_c5_eesa1', 'cbse', 'english', 5, '2026-27',
     $release_3${"academic_year":"2026-27","board_id":"cbse","book_code":"eesa1","book_title":"Santoor","class_no":5,"curriculum_release_id":"english_cbse_2026_27_c5_eesa1","edition_history":[{"kind":"first_edition","month":"June","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-062-3","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c5_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Gandhiji's Talisman"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"7ecaefaa0ed0ada410282fa18ab5a944b8e818cbc897993404cc4924a2682e5d","source_size_bytes":4469179,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c5_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"play","title":"Papa's Spectacles"},{"kind":"lesson","module_id":"eng_c5_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"Gone with the Scooter"}],"order":1,"title":"Let's Have Fun","unit_id":"eng_c5_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Rainbow"},{"kind":"lesson","module_id":"eng_c5_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Wise Parrot"},{"kind":"self_assessment","module_id":"eng_c5_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 1"}],"order":2,"title":"My Colourful World","unit_id":"eng_c5_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Frog"},{"kind":"lesson","module_id":"eng_c5_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"What a Tank!"}],"order":3,"title":"Water","unit_id":"eng_c5_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"story","title":"Gilli Danda"},{"kind":"lesson","module_id":"eng_c5_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"play","title":"The Decision of the Panchayat"}],"order":4,"title":"Ups and Downs","unit_id":"eng_c5_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Vocation"},{"kind":"lesson","module_id":"eng_c5_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"Glass Bangles"},{"kind":"self_assessment","module_id":"eng_c5_u05_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 2"}],"order":5,"title":"Work is Worship","unit_id":"eng_c5_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$release_3$::jsonb,
     'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date)
ON CONFLICT (curriculum_release_id) DO NOTHING;

DO $seed_validation$
DECLARE
    mismatch_count INTEGER;
BEGIN
    SELECT count(*)
    INTO mismatch_count
    FROM (
        VALUES
            ('english_cbse_2026_27_c2_bemr1', 'cbse', 'english', 2, '2026-27',
             $expected_0${"academic_year":"2026-27","board_id":"cbse","book_code":"bemr1","book_title":"Mridang","class_no":2,"curriculum_release_id":"english_cbse_2026_27_c2_bemr1","edition_history":[{"kind":"first_edition","month":"May","year":2023},{"kind":"reprint","month":"March","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"February","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-434-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Sing","mode":"singing","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Read","mode":"reading","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Draw","mode":"drawing","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Say","mode":"pronunciation","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"bd8b09e5eec4502a47bcaa5b46a0e4cb3cee9643fd5e20918a8b72a496ac22ca","source_size_bytes":2812044,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c2_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"My Bicycle"},{"kind":"picture_reading","module_id":"eng_c2_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c2_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"It is Fun"},{"kind":"lesson","module_id":"eng_c2_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Seeing without Seeing"}],"order":2,"title":"Welcome to My World","unit_id":"eng_c2_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Come Back Soon"},{"kind":"lesson","module_id":"eng_c2_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"prose","title":"Between Home and School"},{"kind":"lesson","module_id":"eng_c2_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"This is My Town"}],"order":3,"title":"Going Places","unit_id":"eng_c2_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"A Show of Clouds"},{"kind":"lesson","module_id":"eng_c2_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"My Name"},{"kind":"lesson","module_id":"eng_c2_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Crow"},{"kind":"lesson","module_id":"eng_c2_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"The Smart Monkey"}],"order":4,"title":"Life Around Us","unit_id":"eng_c2_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c2_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Little Drops of Water"},{"kind":"lesson","module_id":"eng_c2_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"mixed","title":"We are all Indians"}],"order":5,"title":"Harmony","unit_id":"eng_c2_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/bemr1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_0$::jsonb,
             'a03eabb3015cf0917e54894caa5c3b7526671537bdfb58b76493579d41964c19', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c3_cesa1', 'cbse', 'english', 3, '2026-27',
             $expected_1${"academic_year":"2026-27","board_id":"cbse","book_code":"cesa1","book_title":"Santoor","class_no":3,"curriculum_release_id":"english_cbse_2026_27_c3_cesa1","edition_history":[{"kind":"first_edition","month":"April","year":2024},{"kind":"reprint","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5292-991-7","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c3_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Our National Anthem"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"6b0ce2a24327c9fad6acd997b38a12ce4bff961e729856133c4474656b424816","source_size_bytes":1956951,"subject_id":"english","units":[{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Colours"},{"kind":"lesson","module_id":"eng_c3_u01_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Badal and Moti"},{"kind":"lesson","module_id":"eng_c3_u01_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Best Friends"}],"order":1,"title":"Fun with Friends","unit_id":"eng_c3_u01"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Out in the Garden"},{"kind":"lesson","module_id":"eng_c3_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"play","title":"Talking Toys"},{"kind":"lesson","module_id":"eng_c3_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"poem","title":"Paper Boats"},{"kind":"self_assessment","module_id":"eng_c3_u02_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":2,"title":"Toys and Games","unit_id":"eng_c3_u02"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Big Laddoo"},{"kind":"lesson","module_id":"eng_c3_u03_m03","order":3,"phase_0_public_display_title":"Thank God!","source_genre":"poem","title":"Thank God"},{"kind":"lesson","module_id":"eng_c3_u03_m04","order":4,"phase_0_public_display_title":null,"source_genre":"story","title":"Madhu's Wish"}],"order":3,"title":"Good Food","unit_id":"eng_c3_u03"},{"modules":[{"kind":"picture_reading","module_id":"eng_c3_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"none","title":"Picture Reading"},{"kind":"lesson","module_id":"eng_c3_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"poem","title":"Night"},{"kind":"lesson","module_id":"eng_c3_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"story","title":"Chanda Mama Counts the Stars"},{"kind":"lesson","module_id":"eng_c3_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"informational","title":"Chandrayaan"},{"kind":"self_assessment","module_id":"eng_c3_u04_m05","order":5,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment"}],"order":4,"title":"The Sky","unit_id":"eng_c3_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/cesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_1$::jsonb,
             '3330785de9b1378ef5da4dd702883d9bffc470d8aa2effec33832c5c9ff3f8b1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c4_desa1', 'cbse', 'english', 4, '2026-27',
             $expected_2${"academic_year":"2026-27","board_id":"cbse","book_code":"desa1","book_title":"Santoor","class_no":4,"curriculum_release_id":"english_cbse_2026_27_c4_desa1","edition_history":[{"kind":"first_edition","month":"March","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-932-9","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Read","mode":"reading","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Recite","mode":"recitation","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":8,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":9,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c4_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Constitution of India"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"ab890381b64c55094ea0651adb3e2c68d32a8341665d587ef90873fb9ab35f9a","source_size_bytes":6888606,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c4_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Together We Can"},{"kind":"lesson","module_id":"eng_c4_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Tinkling Bells"},{"kind":"lesson","module_id":"eng_c4_u01_m03","order":3,"phase_0_public_display_title":"Be Smart, Be Safe","source_genre":"informational","title":"Be Smart Be Safe"}],"order":1,"title":"My Land","unit_id":"eng_c4_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"One Thing at a Time"},{"kind":"lesson","module_id":"eng_c4_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Old Stag"},{"kind":"lesson","module_id":"eng_c4_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Braille"},{"kind":"self_assessment","module_id":"eng_c4_u02_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 1"}],"order":2,"title":"My Beautiful World","unit_id":"eng_c4_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u03_m01","order":1,"phase_0_public_display_title":"Fit Body, Fit Mind, Fit Nation","source_genre":"informational","title":"Fit Body Fit Mind Fit Nation"},{"kind":"lesson","module_id":"eng_c4_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Lagori Champions"},{"kind":"lesson","module_id":"eng_c4_u03_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Hekko"}],"order":3,"title":"Fun with Games","unit_id":"eng_c4_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c4_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Swing"},{"kind":"lesson","module_id":"eng_c4_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"A Journey to the Magical Mountains"},{"kind":"lesson","module_id":"eng_c4_u04_m03","order":3,"phase_0_public_display_title":null,"source_genre":"informational","title":"Maheshwar"},{"kind":"self_assessment","module_id":"eng_c4_u04_m04","order":4,"phase_0_public_display_title":null,"source_genre":"none","title":"Self Assessment 2"}],"order":4,"title":"Up High","unit_id":"eng_c4_u04"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/desa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_2$::jsonb,
             '426767f21ba2f38082aca8a2b05da202055e423245b3ece43c9c55f92b571ab1', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date),
            ('english_cbse_2026_27_c5_eesa1', 'cbse', 'english', 5, '2026-27',
             $expected_3${"academic_year":"2026-27","board_id":"cbse","book_code":"eesa1","book_title":"Santoor","class_no":5,"curriculum_release_id":"english_cbse_2026_27_c5_eesa1","edition_history":[{"kind":"first_edition","month":"June","year":2025},{"kind":"reprint","month":"January","year":2026}],"effective_from":"2026-04-01","effective_through":"2027-03-31","isbn":"978-93-5729-062-3","language_structures":["listening","speaking","reading","writing"],"official_pdf_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","official_selector_url":"https://ncert.nic.in/textbook.php","pedagogical_sections":[{"label":"Recite","mode":"recitation","order":1,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Think","mode":"reasoning","order":2,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Speak","mode":"oral_expression","order":3,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Learn","mode":"language_focus","order":4,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Listen","mode":"listening","order":5,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Write","mode":"writing","order":6,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Do","mode":"activity","order":7,"source_evidence":"official_front_matter","source_pdf_page":6},{"label":"Explore","mode":"exploration","order":8,"source_evidence":"official_front_matter","source_pdf_page":6}],"reference_modules":[{"kind":"reference","module_id":"eng_c5_ref01","order":1,"phase_0_public_display_title":null,"source_genre":"reference","title":"Gandhiji's Talisman"}],"release_label":"Reprint 2026-27","release_status":"current","retired_on":null,"source_sha256":"7ecaefaa0ed0ada410282fa18ab5a944b8e818cbc897993404cc4924a2682e5d","source_size_bytes":4469179,"subject_id":"english","units":[{"modules":[{"kind":"lesson","module_id":"eng_c5_u01_m01","order":1,"phase_0_public_display_title":null,"source_genre":"play","title":"Papa's Spectacles"},{"kind":"lesson","module_id":"eng_c5_u01_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"Gone with the Scooter"}],"order":1,"title":"Let's Have Fun","unit_id":"eng_c5_u01"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u02_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Rainbow"},{"kind":"lesson","module_id":"eng_c5_u02_m02","order":2,"phase_0_public_display_title":null,"source_genre":"story","title":"The Wise Parrot"},{"kind":"self_assessment","module_id":"eng_c5_u02_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 1"}],"order":2,"title":"My Colourful World","unit_id":"eng_c5_u02"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u03_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"The Frog"},{"kind":"lesson","module_id":"eng_c5_u03_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"What a Tank!"}],"order":3,"title":"Water","unit_id":"eng_c5_u03"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u04_m01","order":1,"phase_0_public_display_title":null,"source_genre":"story","title":"Gilli Danda"},{"kind":"lesson","module_id":"eng_c5_u04_m02","order":2,"phase_0_public_display_title":null,"source_genre":"play","title":"The Decision of the Panchayat"}],"order":4,"title":"Ups and Downs","unit_id":"eng_c5_u04"},{"modules":[{"kind":"lesson","module_id":"eng_c5_u05_m01","order":1,"phase_0_public_display_title":null,"source_genre":"poem","title":"Vocation"},{"kind":"lesson","module_id":"eng_c5_u05_m02","order":2,"phase_0_public_display_title":null,"source_genre":"informational","title":"Glass Bangles"},{"kind":"self_assessment","module_id":"eng_c5_u05_m03","order":3,"phase_0_public_display_title":null,"source_genre":"none","title":"Self-assessment 2"}],"order":5,"title":"Work is Worship","unit_id":"eng_c5_u05"}],"verification_evidence":{"evidence_note":"Official NCERT Reprint 2026-27 PDF metadata and local byte hash verified; no textbook body is stored.","hash_algorithm":"sha256","method":"official_pdf_metadata_and_local_sha256","official_url":"https://ncert.nic.in/textbook/pdf/eesa1ps.pdf","provenance":"official_ncert_pdf","verified_on":"2026-07-13"},"verification_status":"verified"}$expected_3$::jsonb,
             'b2af0483dd918273dc2d5c6c9fb785da1063a33fa69ca7d628a6cf5f4950bf6b', 'current', DATE '2026-04-01', DATE '2027-03-31', NULL::date)
    ) AS expected(
        curriculum_release_id,
        board_id,
        subject_id,
        class_no,
        academic_year,
        manifest,
        release_digest,
        status,
        effective_from,
        effective_through,
        retired_on
    )
    LEFT JOIN public.school_curriculum_releases AS actual
      ON actual.curriculum_release_id = expected.curriculum_release_id
    WHERE actual.curriculum_release_id IS NULL
       OR actual.board_id IS DISTINCT FROM expected.board_id
       OR actual.subject_id IS DISTINCT FROM expected.subject_id
       OR actual.class_no IS DISTINCT FROM expected.class_no
       OR actual.academic_year IS DISTINCT FROM expected.academic_year
       OR actual.manifest IS DISTINCT FROM expected.manifest
       OR actual.release_digest IS DISTINCT FROM expected.release_digest
       OR actual.status IS DISTINCT FROM expected.status
       OR actual.effective_from IS DISTINCT FROM expected.effective_from
       OR actual.effective_through IS DISTINCT FROM expected.effective_through
       OR actual.retired_on IS DISTINCT FROM expected.retired_on;

    IF mismatch_count <> 0 THEN
        RAISE EXCEPTION 'school_curriculum_release_seed_mismatch:%', mismatch_count
            USING ERRCODE = '55000';
    END IF;
END;
$seed_validation$;


CREATE TABLE IF NOT EXISTS school_migration_markers (
    migration_key TEXT PRIMARY KEY,
    claimed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    file_sha256 TEXT CHECK (file_sha256 IS NULL OR file_sha256 ~ '^[0-9a-f]{64}$'),
    applied_at TIMESTAMPTZ
);

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

CREATE TABLE IF NOT EXISTS school_sessions (
    session_id        UUID PRIMARY KEY,
    user_id           TEXT NOT NULL REFERENCES learner_profiles(user_id),
    profile_version_id UUID REFERENCES school_profile_versions(profile_version_id),
    api_version       TEXT NOT NULL,
    flow_type         TEXT NOT NULL,
    subject_id        TEXT NOT NULL,
    class_no          INTEGER NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active',
    current_stage     TEXT NOT NULL DEFAULT '',
    linked_session_id UUID,
    source_placement_report_id UUID,
    curriculum_release_id TEXT REFERENCES school_curriculum_releases(curriculum_release_id),
    taxonomy_version TEXT,
    certification_epoch TEXT,
    state_json        JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at      TIMESTAMPTZ,
    CONSTRAINT school_rebuild_active_profile_lineage CHECK (
        api_version <> 'rebuild'
        OR status NOT IN ('active', 'paused_for_masterclass')
        OR profile_version_id IS NOT NULL
    ),
    CONSTRAINT school_sessions_user_session_unique UNIQUE (user_id, session_id),
    CONSTRAINT school_sessions_linked_same_user FOREIGN KEY (user_id, linked_session_id)
        REFERENCES school_sessions(user_id, session_id)
);
CREATE INDEX IF NOT EXISTS idx_school_sessions_user_status_updated
    ON school_sessions(user_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_school_sessions_linked_session
    ON school_sessions(linked_session_id);
CREATE INDEX IF NOT EXISTS idx_school_sessions_profile_flow_updated
    ON school_sessions(
        user_id,
        profile_version_id,
        flow_type,
        subject_id,
        class_no,
        updated_at DESC
    );
CREATE INDEX IF NOT EXISTS idx_school_sessions_source_report
    ON school_sessions(source_placement_report_id, updated_at DESC)
    WHERE source_placement_report_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_sessions_one_active_flow
    ON school_sessions(user_id, flow_type, subject_id, class_no)
    WHERE status IN ('active', 'paused_for_masterclass');

CREATE TABLE IF NOT EXISTS school_answer_requests (
    session_id UUID NOT NULL REFERENCES school_sessions(session_id) ON DELETE CASCADE,
    activity_id TEXT NOT NULL,
    user_id TEXT NOT NULL REFERENCES learner_profiles(user_id),
    answer_hash TEXT NOT NULL,
    claim_token TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
    response_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, activity_id)
);

CREATE TABLE IF NOT EXISTS school_placement_reports (
    report_id                      UUID PRIMARY KEY,
    user_id                        TEXT NOT NULL REFERENCES learner_profiles(user_id),
    profile_version_id             UUID NOT NULL REFERENCES school_profile_versions(profile_version_id),
    placement_session_id           UUID NOT NULL REFERENCES school_sessions(session_id),
    placement_status               TEXT NOT NULL,
    subject_id                     TEXT NOT NULL,
    target_class_no                INTEGER NOT NULL,
    evaluated_class_no             INTEGER NOT NULL,
    active_learning_class_no       INTEGER NOT NULL,
    unlock_state                   TEXT NOT NULL,
    blocking_skills_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
    watchlist_skills_json          JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_summary_json          JSONB NOT NULL DEFAULT '{}'::jsonb,
    recommended_recap_modules_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    learner_summary                TEXT NOT NULL DEFAULT '',
    parent_summary                 TEXT NOT NULL DEFAULT '',
    allowed_next_actions_json      JSONB NOT NULL DEFAULT '[]'::jsonb,
    curriculum_release_id          TEXT REFERENCES school_curriculum_releases(curriculum_release_id),
    taxonomy_version               TEXT,
    certification_epoch            TEXT,
    created_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, placement_session_id)
);
CREATE INDEX IF NOT EXISTS idx_school_placement_reports_user_updated
    ON school_placement_reports(user_id, updated_at DESC);

ALTER TABLE school_sessions
    DROP CONSTRAINT IF EXISTS school_sessions_source_placement_report_id_fkey;
ALTER TABLE school_sessions
    ADD CONSTRAINT school_sessions_source_placement_report_id_fkey
    FOREIGN KEY (source_placement_report_id)
    REFERENCES school_placement_reports(report_id);
ALTER TABLE school_sessions
    DROP CONSTRAINT IF EXISTS school_rebuild_active_profile_lineage;
ALTER TABLE school_sessions
    ADD CONSTRAINT school_rebuild_active_profile_lineage
    CHECK (
        api_version <> 'rebuild'
        OR status NOT IN ('active', 'paused_for_masterclass')
        OR profile_version_id IS NOT NULL
    );

CREATE TABLE IF NOT EXISTS school_language_confidence (
    user_id                  TEXT PRIMARY KEY REFERENCES learner_profiles(user_id),
    en_production_confidence REAL NOT NULL DEFAULT 0.0,
    total_signals            INTEGER NOT NULL DEFAULT 0,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS school_v2_placement_sessions (
    placement_session_id TEXT PRIMARY KEY,
    user_id              TEXT NOT NULL REFERENCES learner_profiles(user_id),
    subject_id           TEXT NOT NULL,
    target_class_no      INTEGER NOT NULL,
    preferred_language   TEXT NOT NULL DEFAULT '',
    status               TEXT NOT NULL DEFAULT 'in_progress',
    state_json           JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at         TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_school_v2_placement_user_status_updated
    ON school_v2_placement_sessions(user_id, status, updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_v2_one_active_placement
    ON school_v2_placement_sessions(user_id, subject_id, target_class_no)
    WHERE status = 'in_progress';

CREATE TABLE IF NOT EXISTS school_v2_practice_sessions (
    practice_session_id TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL REFERENCES learner_profiles(user_id),
    subject_id          TEXT NOT NULL,
    target_class_no     INTEGER NOT NULL,
    skill_id            TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'in_progress',
    state_json          JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at        TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_school_v2_practice_user_status_updated
    ON school_v2_practice_sessions(user_id, status, updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_v2_one_active_practice
    ON school_v2_practice_sessions(user_id, subject_id, target_class_no, skill_id)
    WHERE status = 'in_progress';

CREATE TABLE IF NOT EXISTS school_v2_curriculum_sessions (
    curriculum_session_id TEXT PRIMARY KEY,
    user_id               TEXT NOT NULL REFERENCES learner_profiles(user_id),
    subject_id            TEXT NOT NULL,
    target_class_no       INTEGER NOT NULL,
    chapter_id            TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'in_progress',
    state_json            JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at          TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_school_v2_curriculum_user_status_updated
    ON school_v2_curriculum_sessions(user_id, status, updated_at DESC);
CREATE UNIQUE INDEX IF NOT EXISTS idx_school_v2_one_active_curriculum
    ON school_v2_curriculum_sessions(user_id, subject_id, target_class_no, chapter_id)
    WHERE status = 'in_progress';

-- ---------- test-item cache ----------
CREATE TABLE IF NOT EXISTS test_items (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    task_type       TEXT NOT NULL,
    context_hash    TEXT NOT NULL DEFAULT 'default',
    items           JSONB NOT NULL DEFAULT '[]'::jsonb,
    cached_at       DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, task_type, context_hash)
);

-- ---------- credit ledger ----------
CREATE TABLE IF NOT EXISTS credit_transactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL REFERENCES learner_profiles(user_id),
    delta       INTEGER NOT NULL,        -- negative = spend, positive = grant
    reason      TEXT NOT NULL,
    idempotency_key TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_credit_user ON credit_transactions(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_credit_transactions_idempotency_key
    ON credit_transactions(user_id, idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- ---------- content unlocks + purchases ----------
CREATE TABLE IF NOT EXISTS content_unlocks (
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    scope           TEXT NOT NULL,
    ref_id          TEXT NOT NULL,
    credits_spent   INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, scope, ref_id)
);
CREATE INDEX IF NOT EXISTS idx_unlocks_user ON content_unlocks(user_id);

CREATE TABLE IF NOT EXISTS purchases (
    order_id        TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES learner_profiles(user_id),
    pack_id         TEXT NOT NULL,
    credits         INTEGER NOT NULL,
    amount_paise    INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'created',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);

-- ---------- row-level security ----------
-- Lock every table to superuser / service_role only. No policies are defined,
-- so anon + authenticated keys get ZERO access. The backend connects via the
-- transaction pooler as the `postgres` role, which bypasses RLS, so the engine
-- is unaffected. Defense-in-depth for the XPRIZE public submission: a leaked
-- anon key cannot read learner data.
ALTER TABLE learner_profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions            ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_runtime     ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_messages    ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_turn_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_start_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_opening_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_end_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE turns               ENABLE ROW LEVEL SECURITY;
ALTER TABLE turn_evaluations    ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_entries      ENABLE ROW LEVEL SECURITY;
ALTER TABLE competency_nodes    ENABLE ROW LEVEL SECURITY;
ALTER TABLE weaknesses          ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_events     ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_reports     ENABLE ROW LEVEL SECURITY;
ALTER TABLE learner_skill_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_profile_draft_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_curriculum_releases ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_migration_markers ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_skill_mastery ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_results      ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_sessions     ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_answer_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_placement_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_language_confidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_v2_placement_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_v2_practice_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE school_v2_curriculum_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_items          ENABLE ROW LEVEL SECURITY;
ALTER TABLE credit_transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE content_unlocks     ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchases           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.node_attempts ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE public.session_runtime FROM anon;
REVOKE ALL ON TABLE public.session_runtime FROM authenticated;
REVOKE ALL ON TABLE public.session_runtime FROM PUBLIC;
REVOKE ALL ON TABLE public.session_messages FROM anon;
REVOKE ALL ON TABLE public.session_messages FROM authenticated;
REVOKE ALL ON TABLE public.session_messages FROM PUBLIC;
REVOKE ALL ON TABLE public.session_turn_requests FROM anon;
REVOKE ALL ON TABLE public.session_turn_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_turn_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_start_requests FROM anon;
REVOKE ALL ON TABLE public.session_start_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_start_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_opening_requests FROM anon;
REVOKE ALL ON TABLE public.session_opening_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_opening_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.session_end_requests FROM anon;
REVOKE ALL ON TABLE public.session_end_requests FROM authenticated;
REVOKE ALL ON TABLE public.session_end_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.turn_evaluations FROM anon;
REVOKE ALL ON TABLE public.turn_evaluations FROM authenticated;
REVOKE ALL ON TABLE public.turn_evaluations FROM PUBLIC;
REVOKE ALL ON TABLE public.learning_events FROM anon;
REVOKE ALL ON TABLE public.learning_events FROM authenticated;
REVOKE ALL ON TABLE public.learning_events FROM PUBLIC;
REVOKE ALL ON TABLE public.session_reports FROM anon;
REVOKE ALL ON TABLE public.session_reports FROM authenticated;
REVOKE ALL ON TABLE public.session_reports FROM PUBLIC;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM anon;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM authenticated;
REVOKE ALL ON TABLE public.learner_skill_profiles FROM PUBLIC;
REVOKE ALL ON TABLE public.school_profile_versions FROM anon;
REVOKE ALL ON TABLE public.school_profile_versions FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_versions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM anon;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_profile_draft_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM anon;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM authenticated;
REVOKE ALL ON TABLE public.school_curriculum_releases FROM PUBLIC;
REVOKE ALL ON TABLE public.school_migration_markers FROM anon;
REVOKE ALL ON TABLE public.school_migration_markers FROM authenticated;
REVOKE ALL ON TABLE public.school_migration_markers FROM PUBLIC;
REVOKE ALL ON TABLE public.school_sessions FROM anon;
REVOKE ALL ON TABLE public.school_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_answer_requests FROM anon;
REVOKE ALL ON TABLE public.school_answer_requests FROM authenticated;
REVOKE ALL ON TABLE public.school_answer_requests FROM PUBLIC;
REVOKE ALL ON TABLE public.school_placement_reports FROM anon;
REVOKE ALL ON TABLE public.school_placement_reports FROM authenticated;
REVOKE ALL ON TABLE public.school_placement_reports FROM PUBLIC;
REVOKE ALL ON TABLE public.school_language_confidence FROM anon;
REVOKE ALL ON TABLE public.school_language_confidence FROM authenticated;
REVOKE ALL ON TABLE public.school_language_confidence FROM PUBLIC;
REVOKE ALL ON TABLE public.school_v2_placement_sessions FROM anon;
REVOKE ALL ON TABLE public.school_v2_placement_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_v2_placement_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM anon;
REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_v2_practice_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.school_v2_curriculum_sessions FROM anon;
REVOKE ALL ON TABLE public.school_v2_curriculum_sessions FROM authenticated;
REVOKE ALL ON TABLE public.school_v2_curriculum_sessions FROM PUBLIC;
REVOKE ALL ON TABLE public.node_attempts FROM anon;
REVOKE ALL ON TABLE public.node_attempts FROM authenticated;
REVOKE ALL ON TABLE public.node_attempts FROM PUBLIC;
