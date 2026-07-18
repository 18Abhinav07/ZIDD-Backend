-- The canonical School product no longer uses the shared session runtime.
-- Terminalize both halves of every legacy row so stale clients cannot resume it.
-- Apply only against a stopped backend. Any live writer makes the migration
-- fail immediately, rolling back trigger DDL, terminalization, and its marker.
LOCK TABLE public.sessions, public.session_runtime
IN ACCESS EXCLUSIVE MODE NOWAIT;

CREATE OR REPLACE FUNCTION public.reject_active_legacy_school_session_row()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.status IS DISTINCT FROM 'ended'
       AND (
            NEW.module_id = 'school_english'
            OR NEW.task_type = 'school_english'
            OR EXISTS (
                SELECT 1
                FROM public.session_runtime runtime
                WHERE runtime.session_id = NEW.session_id
                  AND (
                        runtime.module_id = 'school_english'
                        OR runtime.task_type = 'school_english'
                        OR runtime.state_snapshot ->> 'module_id'
                            = 'school_english'
                        OR runtime.state_snapshot ->> 'task_type'
                            = 'school_english'
                        OR runtime.state_snapshot ->> 'block_reason'
                            = 'legacy_school_module_retired'
                        OR runtime.state_snapshot -> 'last_error' ->> 'code'
                            = 'legacy_school_module_retired'
                        OR runtime.last_error ->> 'code'
                            = 'legacy_school_module_retired'
                  )
            )
       )
    THEN
        RAISE EXCEPTION 'legacy_school_module_retired:%', NEW.session_id
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS sessions_reject_active_legacy_school
    ON public.sessions;
CREATE TRIGGER sessions_reject_active_legacy_school
BEFORE INSERT OR UPDATE ON public.sessions
FOR EACH ROW
EXECUTE FUNCTION public.reject_active_legacy_school_session_row();

CREATE OR REPLACE FUNCTION public.reject_active_legacy_school_runtime_row()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.status IS DISTINCT FROM 'ended'
       AND (
            NEW.module_id = 'school_english'
            OR NEW.task_type = 'school_english'
            OR NEW.state_snapshot ->> 'module_id' = 'school_english'
            OR NEW.state_snapshot ->> 'task_type' = 'school_english'
            OR NEW.state_snapshot ->> 'block_reason'
                = 'legacy_school_module_retired'
            OR NEW.state_snapshot -> 'last_error' ->> 'code'
                = 'legacy_school_module_retired'
            OR NEW.last_error ->> 'code' = 'legacy_school_module_retired'
            OR EXISTS (
                SELECT 1
                FROM public.sessions parent
                WHERE parent.session_id = NEW.session_id
                  AND (
                        parent.module_id = 'school_english'
                        OR parent.task_type = 'school_english'
                  )
            )
       )
    THEN
        RAISE EXCEPTION 'legacy_school_module_retired:%', NEW.session_id
            USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END;
$function$;

DROP TRIGGER IF EXISTS session_runtime_reject_active_legacy_school
    ON public.session_runtime;
CREATE TRIGGER session_runtime_reject_active_legacy_school
BEFORE INSERT OR UPDATE ON public.session_runtime
FOR EACH ROW
EXECUTE FUNCTION public.reject_active_legacy_school_runtime_row();

UPDATE public.session_runtime
SET status = 'ended',
    state_snapshot = COALESCE(state_snapshot, '{}'::jsonb)
        || jsonb_build_object(
            'status', 'ended',
            'session_over', true,
            'input_allowed', false,
            'block_reason', 'legacy_school_module_retired'
        ),
    pending_transition = NULL,
    session_version = session_version + 1,
    active_turn_id = NULL,
    active_opening_id = NULL,
    last_error = jsonb_build_object(
        'code', 'legacy_school_module_retired',
        'replacement', '/school'
    ),
    lease_expires_at = NULL,
    updated_at = now()
WHERE (
        module_id = 'school_english'
        OR task_type = 'school_english'
        OR state_snapshot ->> 'module_id' = 'school_english'
        OR state_snapshot ->> 'task_type' = 'school_english'
        OR state_snapshot ->> 'block_reason'
            = 'legacy_school_module_retired'
        OR state_snapshot -> 'last_error' ->> 'code'
            = 'legacy_school_module_retired'
        OR last_error ->> 'code' = 'legacy_school_module_retired'
        OR session_id IN (
            SELECT session_id
            FROM public.sessions
            WHERE module_id = 'school_english'
               OR task_type = 'school_english'
        )
    )
  AND (
        status IS DISTINCT FROM 'ended'
        OR state_snapshot ->> 'block_reason'
            IS DISTINCT FROM 'legacy_school_module_retired'
        OR state_snapshot ->> 'session_over' IS DISTINCT FROM 'true'
        OR pending_transition IS NOT NULL
        OR active_turn_id IS NOT NULL
        OR active_opening_id IS NOT NULL
        OR lease_expires_at IS NOT NULL
    );

UPDATE public.sessions
SET status = 'ended',
    ended_at = COALESCE(ended_at, now()),
    last_seen_at = now()
WHERE (
        module_id = 'school_english'
        OR task_type = 'school_english'
        OR session_id IN (
            SELECT session_id
            FROM public.session_runtime
            WHERE module_id = 'school_english'
               OR task_type = 'school_english'
               OR state_snapshot ->> 'module_id' = 'school_english'
               OR state_snapshot ->> 'task_type' = 'school_english'
               OR state_snapshot ->> 'block_reason'
                    = 'legacy_school_module_retired'
               OR state_snapshot -> 'last_error' ->> 'code'
                    = 'legacy_school_module_retired'
               OR last_error ->> 'code' = 'legacy_school_module_retired'
        )
    )
  AND (status IS DISTINCT FROM 'ended' OR ended_at IS NULL);
