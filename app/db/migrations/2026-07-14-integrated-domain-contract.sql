DO $validation$
BEGIN
    IF EXISTS (
        SELECT 1 FROM public.learning_events
        WHERE domain NOT IN ('career', 'school')
           OR (domain = 'school' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
           OR (domain = 'career' AND task_type LIKE 'school\_%' ESCAPE '\')
    ) THEN
        RAISE EXCEPTION 'ambiguous_learning_event_domain_backfill'
            USING ERRCODE = '23514';
    END IF;
    IF EXISTS (
        SELECT 1 FROM public.learner_skill_profiles
        WHERE domain NOT IN ('career', 'school')
           OR (domain = 'school' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
           OR (domain = 'career' AND task_type LIKE 'school\_%' ESCAPE '\')
    ) THEN
        RAISE EXCEPTION 'ambiguous_skill_profile_domain_backfill'
            USING ERRCODE = '23514';
    END IF;
END;
$validation$;

ALTER TABLE public.learning_events
    DROP CONSTRAINT IF EXISTS learning_events_domain,
    DROP CONSTRAINT IF EXISTS learning_events_domain_task;
ALTER TABLE public.learning_events
    ADD CONSTRAINT learning_events_domain
        CHECK (domain IN ('career', 'school')) NOT VALID,
    ADD CONSTRAINT learning_events_domain_task
        CHECK (
            (domain = 'school' AND task_type LIKE 'school\_%' ESCAPE '\')
            OR (domain = 'career' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
        ) NOT VALID;
ALTER TABLE public.learning_events VALIDATE CONSTRAINT learning_events_domain;
ALTER TABLE public.learning_events VALIDATE CONSTRAINT learning_events_domain_task;

ALTER TABLE public.learner_skill_profiles
    DROP CONSTRAINT IF EXISTS learner_skill_profiles_domain,
    DROP CONSTRAINT IF EXISTS learner_skill_profiles_domain_task;
ALTER TABLE public.learner_skill_profiles
    ADD CONSTRAINT learner_skill_profiles_domain
        CHECK (domain IN ('career', 'school')) NOT VALID,
    ADD CONSTRAINT learner_skill_profiles_domain_task
        CHECK (
            (domain = 'school' AND task_type LIKE 'school\_%' ESCAPE '\')
            OR (domain = 'career' AND task_type NOT LIKE 'school\_%' ESCAPE '\')
        ) NOT VALID;
ALTER TABLE public.learner_skill_profiles
    VALIDATE CONSTRAINT learner_skill_profiles_domain;
ALTER TABLE public.learner_skill_profiles
    VALIDATE CONSTRAINT learner_skill_profiles_domain_task;
