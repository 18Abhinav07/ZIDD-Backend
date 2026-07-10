"""Runtime schema drift guard for the Supabase-backed product store."""

from sqlalchemy import text


REQUIRED_RUNTIME_COLUMNS: dict[str, set[str]] = {
    "learner_profiles": {
        "preferences",
        "primary_motive",
        "onboarding_completed_at",
        "school_profile",
        "career_profile",
        "onboarding_state",
    },
    "sessions": {
        "status",
        "module_id",
        "task_type",
        "last_seen_at",
        "expires_at",
        "test_mode",
        "reattempt_of_session_id",
        "career_context",
        "scenario_config",
        "persona_roster",
        "context_hash",
    },
    "test_items": {
        "context_hash",
    },
    "credit_transactions": {
        "idempotency_key",
    },
    "competency_nodes": {
        "best_mastery",
        "node_completed",
        "node_mastered",
        "display_status",
        "best_independent_score",
        "independent_passes",
        "transfer_passes",
        "pressure_passes",
        "scaffold_successes",
        "last_gap",
        "mastery_evidence",
        "completed_at",
        "completion_count",
        "last_completed_session_id",
    },
    "session_runtime": {
        "session_id",
        "user_id",
        "current_node",
        "module_id",
        "task_type",
        "test_mode",
        "status",
        "state_snapshot",
        "pending_transition",
        "session_version",
        "active_turn_id",
        "active_opening_id",
        "last_error",
        "lease_expires_at",
    },
    "session_messages": {
        "message_id",
        "session_id",
        "sequence_index",
        "turn_id",
        "transition_id",
        "node_id",
        "role",
        "content",
        "speaker_name",
        "speaker_id",
        "message_kind",
        "status",
    },
    "session_turn_requests": {
        "session_id",
        "client_turn_id",
        "request_hash",
        "expected_version",
        "status",
        "transcript_delta",
        "done_snapshot",
        "error_code",
    },
    "session_start_requests": {
        "user_id",
        "client_start_id",
        "request_hash",
        "status",
        "session_id",
        "response_json",
        "error_code",
        "source_session_id",
        "source_transition_id",
        "claim_generation",
    },
    "session_opening_requests": {
        "session_id",
        "transition_id",
        "status",
        "message_id",
        "attempts",
        "last_error",
    },
    "session_end_requests": {
        "session_id",
        "status",
        "response_json",
        "error_code",
        "attempts",
    },
    "turn_evaluations": {
        "evaluation_id",
        "session_id",
        "user_id",
        "node_id",
        "turn_id",
        "attempt_index",
        "attempt_type",
        "user_answer",
        "rubric_version",
        "raw_score",
        "effective_score",
        "criteria_json",
        "blockers",
        "pass_eligible",
        "advance_eligible",
        "mastery_eligible",
        "tutor_plan_json",
        "context_json",
        "model_name",
        "prompt_version",
    },
    "learning_events": {
        "source_event_key",
        "user_id",
        "domain",
        "task_type",
        "module_id",
        "session_id",
        "node_id",
        "skill_id",
        "source",
        "attempt_type",
        "score",
        "confidence",
        "criteria_json",
        "evidence_json",
        "blockers",
        "gap",
        "scenario_json",
        "caveats",
        "model_name",
        "prompt_version",
        "occurred_at",
    },
    "session_reports": {
        "report_id",
        "session_id",
        "user_id",
        "report_type",
        "task_type",
        "module_id",
        "status",
        "score",
        "readiness_score",
        "summary",
        "strengths_json",
        "gaps_json",
        "evidence_json",
        "recommended_actions_json",
        "validity_json",
        "public_context_json",
    },
    "learner_skill_profiles": {
        "user_id",
        "domain",
        "skill_id",
        "module_id",
        "task_type",
        "mastery",
        "readiness",
        "confidence",
        "attempts",
        "last_seen_at",
        "strengths_json",
        "gaps_json",
        "evidence_json",
        "recommended_next_action",
        "source_summary",
    },
}

REQUIRED_RUNTIME_INDEXES: dict[str, tuple[str, ...]] = {
    "idx_session_turn_requests_session_version": (
        "CREATE UNIQUE INDEX",
        "session_turn_requests",
        "session_id",
        "expected_version",
        "WHERE",
        "status",
        "in_progress",
        "completed",
    ),
    "idx_session_start_requests_source_transition": (
        "CREATE UNIQUE INDEX",
        "session_start_requests",
        "source_session_id",
        "source_transition_id",
        "WHERE",
        "status",
        "in_progress",
        "completed",
    ),
    "idx_turn_evaluations_session": (
        "CREATE INDEX",
        "turn_evaluations",
        "session_id",
        "created_at",
    ),
    "idx_turn_evaluations_user_node": (
        "CREATE INDEX",
        "turn_evaluations",
        "user_id",
        "node_id",
    ),
    "idx_learning_events_user_time": (
        "CREATE INDEX",
        "learning_events",
        "user_id",
        "occurred_at",
    ),
    "idx_learning_events_user_domain_skill_time": (
        "CREATE INDEX",
        "learning_events",
        "user_id",
        "domain",
        "skill_id",
        "occurred_at",
    ),
    "idx_learning_events_session": (
        "CREATE INDEX",
        "learning_events",
        "session_id",
    ),
    "idx_session_reports_user_type_time": (
        "CREATE INDEX",
        "session_reports",
        "user_id",
        "report_type",
        "created_at",
    ),
    "idx_learner_skill_profiles_user_domain_mastery_seen": (
        "CREATE INDEX",
        "learner_skill_profiles",
        "user_id",
        "domain",
        "mastery",
        "last_seen_at",
    ),
    "idx_credit_transactions_idempotency_key": (
        "CREATE UNIQUE INDEX",
        "credit_transactions",
        "user_id",
        "idempotency_key",
    ),
}

REQUIRED_MIGRATION_FILES: tuple[str, ...] = (
    "app/db/migrations/2026-07-04-session-hardening.sql",
    "app/db/migrations/2026-07-04-onboarding-profile.sql",
    "app/db/migrations/2026-07-05-career-simulation-personalization.sql",
    "app/db/migrations/2026-07-06-session-runtime.sql",
    "app/db/migrations/2026-07-06-session-start-idempotency.sql",
    "app/db/migrations/2026-07-08-prep-turn-evaluations.sql",
    "app/db/migrations/2026-07-09-career-learning-profile.sql",
    "app/db/migrations/2026-07-11-attempt-charge-idempotency.sql",
    "app/db/migrations/2026-07-11-start-request-claim-generation.sql",
    "app/db/migrations/2026-07-12-turn-evaluation-context.sql",
)


class SchemaDriftError(RuntimeError):
    """Raised when the live Supabase schema is older than the runtime code."""


def required_schema_points() -> list[str]:
    points: list[str] = []
    for table, columns in sorted(REQUIRED_RUNTIME_COLUMNS.items()):
        points.extend(f"public.{table}.{column}" for column in sorted(columns))
    points.extend(f"public.index.{index}" for index in sorted(REQUIRED_RUNTIME_INDEXES))
    return points


async def validate_runtime_schema() -> None:
    """Fail fast if Supabase has not had the hardening migrations applied.

    This intentionally runs at boot, not during a learner flow. A stale schema
    should be an operator-visible startup error, not a random /map or lesson-start
    500 after the UI has already accepted a click.
    """
    from app.db.engine import get_sessionmaker

    table_filter = ", ".join(f"'{table}'" for table in sorted(REQUIRED_RUNTIME_COLUMNS))
    query = text(
        f"""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name IN ({table_filter})
        """
    )

    async with get_sessionmaker()() as session:
        result = await session.execute(query)
        index_result = await session.execute(
            text(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = 'public'
                """
            )
        )

    found = {
        (str(row["table_name"]), str(row["column_name"]))
        for row in result.mappings().all()
    }
    indexes = {
        str(row["indexname"]): str(row["indexdef"])
        for row in index_result.mappings().all()
    }
    missing = [
        f"public.{table}.{column}"
        for table, columns in sorted(REQUIRED_RUNTIME_COLUMNS.items())
        for column in sorted(columns)
        if (table, column) not in found
    ]
    for index_name, required_tokens in sorted(REQUIRED_RUNTIME_INDEXES.items()):
        index_def = indexes.get(index_name, "")
        normalized = index_def.lower()
        if not index_def or any(token.lower() not in normalized for token in required_tokens):
            missing.append(f"public.index.{index_name}")
    if missing:
        joined = ", ".join(missing)
        migrations = ", ".join(REQUIRED_MIGRATION_FILES)
        raise SchemaDriftError(
            "Supabase schema is missing required runtime schema points "
            "(columns and/or indexes): "
            f"{joined}. Run these migrations in order: {migrations}."
        )
