"""Runtime schema drift guard for the Supabase-backed product store."""

from contextlib import asynccontextmanager
import hashlib
import json
import re

from sqlalchemy import text

from app.content.school.release_loader import load_release_manifest


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
    "school_profile_versions": {
        "profile_version_id",
        "user_id",
        "status",
        "display_name",
        "school_name",
        "board_id",
        "target_class_no",
        "subject_ids",
        "preferred_teaching_language",
        "english_comfort",
        "learner_goal",
        "parent_goal",
        "prior_difficulty_signals",
        "current_step",
        "draft_revision",
        "last_save_request_id",
        "last_save_payload_hash",
        "source_profile_version_id",
        "activation_request_id",
        "activation_payload_hash",
        "activation_result_profile_version_id",
        "coach_avatar_id",
        "coach_palette_id",
        "created_at",
        "updated_at",
        "activated_at",
        "archived_at",
    },
    "school_profile_draft_requests": {
        "user_id",
        "request_id",
        "profile_version_id",
        "payload_hash",
        "response_json",
        "created_at",
        "updated_at",
    },
    "school_migration_markers": {
        "migration_key",
        "claimed_at",
        "file_sha256",
        "applied_at",
    },
    "school_curriculum_releases": {
        "curriculum_release_id",
        "board_id",
        "subject_id",
        "class_no",
        "academic_year",
        "manifest",
        "release_digest",
        "status",
        "effective_from",
        "effective_through",
        "retired_on",
        "created_at",
        "updated_at",
    },
    "school_v2_placement_sessions": {
        "placement_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "preferred_language",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    },
    "school_v2_practice_sessions": {
        "practice_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "skill_id",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    },
    "school_v2_curriculum_sessions": {
        "curriculum_session_id",
        "user_id",
        "subject_id",
        "target_class_no",
        "chapter_id",
        "status",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    },
    "school_sessions": {
        "session_id",
        "user_id",
        "profile_version_id",
        "api_version",
        "flow_type",
        "subject_id",
        "class_no",
        "status",
        "current_stage",
        "linked_session_id",
        "source_placement_report_id",
        "curriculum_release_id",
        "taxonomy_version",
        "certification_epoch",
        "state_json",
        "started_at",
        "updated_at",
        "completed_at",
    },
    "school_answer_requests": {
        "session_id",
        "activity_id",
        "user_id",
        "answer_hash",
        "claim_token",
        "status",
        "response_json",
        "created_at",
        "updated_at",
    },
    "school_placement_reports": {
        "report_id",
        "user_id",
        "profile_version_id",
        "placement_session_id",
        "placement_status",
        "subject_id",
        "target_class_no",
        "evaluated_class_no",
        "active_learning_class_no",
        "unlock_state",
        "blocking_skills_json",
        "watchlist_skills_json",
        "evidence_summary_json",
        "recommended_recap_modules_json",
        "learner_summary",
        "parent_summary",
        "allowed_next_actions_json",
        "curriculum_release_id",
        "taxonomy_version",
        "certification_epoch",
        "created_at",
        "updated_at",
    },
    "school_language_confidence": {
        "user_id",
        "en_production_confidence",
        "total_signals",
        "updated_at",
    },
}

REQUIRED_RUNTIME_COLUMN_TYPES: dict[tuple[str, str], str] = {
    ("school_profile_draft_requests", "profile_version_id"): "uuid",
    ("school_profile_draft_requests", "request_id"): "uuid",
    ("school_profile_versions", "activation_request_id"): "uuid",
    ("school_profile_versions", "activation_result_profile_version_id"): "uuid",
    ("school_profile_versions", "last_save_request_id"): "uuid",
    ("school_profile_versions", "source_profile_version_id"): "uuid",
    ("school_sessions", "profile_version_id"): "uuid",
    ("school_sessions", "source_placement_report_id"): "uuid",
}

REQUIRED_RUNTIME_FOREIGN_KEYS: tuple[tuple[str, str, str, str], ...] = (
    (
        "school_profile_draft_requests",
        "profile_version_id",
        "school_profile_versions",
        "profile_version_id",
    ),
    (
        "school_profile_draft_requests",
        "user_id",
        "learner_profiles",
        "user_id",
    ),
    (
        "school_profile_versions",
        "source_profile_version_id",
        "school_profile_versions",
        "profile_version_id",
    ),
    (
        "school_profile_versions",
        "activation_result_profile_version_id",
        "school_profile_versions",
        "profile_version_id",
    ),
    (
        "school_sessions",
        "profile_version_id",
        "school_profile_versions",
        "profile_version_id",
    ),
    (
        "school_sessions",
        "source_placement_report_id",
        "school_placement_reports",
        "report_id",
    ),
    (
        "school_sessions",
        "curriculum_release_id",
        "school_curriculum_releases",
        "curriculum_release_id",
    ),
    (
        "school_placement_reports",
        "curriculum_release_id",
        "school_curriculum_releases",
        "curriculum_release_id",
    ),
)

REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEYS: tuple[
    tuple[str, tuple[str, ...], str, tuple[str, ...]], ...
] = (
    (
        "school_sessions",
        ("user_id", "linked_session_id"),
        "school_sessions",
        ("user_id", "session_id"),
    ),
)

SENSITIVE_SCHOOL_TABLES: frozenset[str] = frozenset(
    table for table in REQUIRED_RUNTIME_COLUMNS if table.startswith("school_")
)

REQUIRED_RUNTIME_CHECKS: dict[tuple[str, str], tuple[str, ...]] = {
    (
        "school_profile_versions",
        "school_profile_versions_complete_non_drafts",
    ): (
        "status_inactive_bypass",
        "complete_identity",
        "complete_class_subject",
        "complete_language",
        "complete_goal",
        "complete_difficulty_signals",
    ),
    (
        "school_profile_versions",
        "school_profile_versions_lifecycle",
    ): (
        "draft_lifecycle",
        "active_lifecycle",
        "archived_lifecycle",
    ),
    (
        "school_sessions",
        "school_rebuild_active_profile_lineage",
    ): (
        "api_version_not_rebuild",
        "status_not_active_or_paused",
        "profile_version_id_not_null",
    ),
}

REQUIRED_RUNTIME_INDEXES: dict[str, tuple[str, ...]] = {
    "school_curriculum_releases_identity_digest_unique": (
        "CREATE UNIQUE INDEX",
        "school_curriculum_releases",
        "board_id",
        "subject_id",
        "class_no",
        "academic_year",
        "release_digest",
    ),
    "idx_school_curriculum_releases_one_current": (
        "CREATE UNIQUE INDEX",
        "school_curriculum_releases",
        "board_id",
        "subject_id",
        "class_no",
        "academic_year",
        "WHERE",
        "status",
        "current",
    ),
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
    "idx_school_profile_versions_one_active": (
        "CREATE UNIQUE INDEX",
        "school_profile_versions",
        "user_id",
        "WHERE",
        "status",
        "active",
    ),
    "idx_school_profile_versions_one_draft": (
        "CREATE UNIQUE INDEX",
        "school_profile_versions",
        "user_id",
        "WHERE",
        "status",
        "draft",
    ),
    "idx_school_profile_versions_activation_request": (
        "CREATE UNIQUE INDEX",
        "school_profile_versions",
        "user_id",
        "activation_request_id",
        "WHERE",
        "activation_request_id",
        "IS NOT NULL",
    ),
    "idx_school_profile_versions_user_status_updated": (
        "CREATE INDEX",
        "school_profile_versions",
        "user_id",
        "status",
        "updated_at",
    ),
    "idx_school_v2_placement_user_status_updated": (
        "CREATE INDEX",
        "school_v2_placement_sessions",
        "user_id",
        "status",
        "updated_at",
    ),
    "idx_school_v2_one_active_placement": (
        "CREATE UNIQUE INDEX",
        "school_v2_placement_sessions",
        "user_id",
        "subject_id",
        "target_class_no",
        "WHERE",
        "status",
        "in_progress",
    ),
    "idx_school_v2_practice_user_status_updated": (
        "CREATE INDEX",
        "school_v2_practice_sessions",
        "user_id",
        "status",
        "updated_at",
    ),
    "idx_school_v2_one_active_practice": (
        "CREATE UNIQUE INDEX",
        "school_v2_practice_sessions",
        "user_id",
        "subject_id",
        "target_class_no",
        "skill_id",
        "WHERE",
        "status",
        "in_progress",
    ),
    "idx_school_v2_curriculum_user_status_updated": (
        "CREATE INDEX",
        "school_v2_curriculum_sessions",
        "user_id",
        "status",
        "updated_at",
    ),
    "idx_school_v2_one_active_curriculum": (
        "CREATE UNIQUE INDEX",
        "school_v2_curriculum_sessions",
        "user_id",
        "subject_id",
        "target_class_no",
        "chapter_id",
        "WHERE",
        "status",
        "in_progress",
    ),
    "idx_school_sessions_user_status_updated": (
        "CREATE INDEX",
        "school_sessions",
        "user_id",
        "status",
        "updated_at",
    ),
    "idx_school_sessions_linked_session": (
        "CREATE INDEX",
        "school_sessions",
        "linked_session_id",
    ),
    "idx_school_sessions_profile_flow_updated": (
        "CREATE INDEX",
        "school_sessions",
        "user_id",
        "profile_version_id",
        "flow_type",
        "subject_id",
        "class_no",
        "updated_at",
    ),
    "idx_school_sessions_source_report": (
        "CREATE INDEX",
        "school_sessions",
        "source_placement_report_id",
        "updated_at",
    ),
    "idx_school_sessions_one_active_flow": (
        "CREATE UNIQUE INDEX",
        "school_sessions",
        "user_id",
        "flow_type",
        "subject_id",
        "class_no",
        "WHERE",
        "status",
        "active",
        "paused_for_masterclass",
    ),
    "idx_school_placement_reports_user_updated": (
        "CREATE INDEX",
        "school_placement_reports",
        "user_id",
        "updated_at",
    ),
}

REQUIRED_EXACT_RUNTIME_INDEXES: frozenset[str] = frozenset(
    {
        "idx_school_curriculum_releases_one_current",
        "idx_school_sessions_one_active_flow",
        "school_curriculum_releases_identity_digest_unique",
    }
)

def _release_digest(manifest: dict[str, object]) -> str:
    encoded = json.dumps(
        manifest,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


REQUIRED_SCHOOL_CURRICULUM_RELEASES: tuple[dict[str, object], ...] = tuple(
    {
        "curriculum_release_id": release.curriculum_release_id,
        "board_id": release.board_id,
        "subject_id": release.subject_id,
        "class_no": release.class_no,
        "academic_year": release.academic_year,
        "manifest": release.model_dump(mode="json"),
        "release_digest": _release_digest(release.model_dump(mode="json")),
        "status": "current",
    }
    for release in load_release_manifest().releases
)

REQUIRED_MIGRATION_FILES: tuple[str, ...] = (
    "app/db/migrations/2026-07-04-session-hardening.sql",
    "app/db/migrations/2026-07-04-onboarding-profile.sql",
    "app/db/migrations/2026-07-05-career-simulation-personalization.sql",
    "app/db/migrations/2026-07-06-session-runtime.sql",
    "app/db/migrations/2026-07-06-session-start-idempotency.sql",
    "app/db/migrations/2026-07-08-prep-turn-evaluations.sql",
    "app/db/migrations/2026-07-09-career-learning-profile.sql",
    "app/db/migrations/2026-07-09-school-v2-placement.sql",
    "app/db/migrations/2026-07-09-school-v2-practice.sql",
    "app/db/migrations/2026-07-09-school-v2-curriculum.sql",
    "app/db/migrations/2026-07-09-school-v3-core.sql",
    "app/db/migrations/2026-07-10-school-rebuild-profile.sql",
    "app/db/migrations/2026-07-10-school-placement-reports.sql",
    "app/db/migrations/2026-07-11-school-answer-idempotency.sql",
    "app/db/migrations/2026-07-12-school-session-lineage.sql",
    "app/db/migrations/2026-07-12-school-onboarding-drafts.sql",
    "app/db/migrations/2026-07-13-001-school-release-authority.sql",
)


class SchemaDriftError(RuntimeError):
    """Raised when the live Supabase schema is older than the runtime code."""


def _normalize_definition(value: str) -> str:
    normalized = value.lower().replace('"', "")
    normalized = normalized.replace("::text[]", "").replace("::text", "")
    return re.sub(r"\s+", " ", normalized).strip()


def required_schema_points() -> list[str]:
    points: list[str] = []
    for table, columns in sorted(REQUIRED_RUNTIME_COLUMNS.items()):
        points.extend(f"public.{table}.{column}" for column in sorted(columns))
    points.extend(
        f"public.{table}.{column}.type.{required_type}"
        for (table, column), required_type in sorted(
            REQUIRED_RUNTIME_COLUMN_TYPES.items()
        )
    )
    points.extend(
        f"public.foreign_key.{table}.{column}"
        f"->public.{foreign_table}.{foreign_column}"
        for table, column, foreign_table, foreign_column in sorted(
            REQUIRED_RUNTIME_FOREIGN_KEYS
        )
    )
    points.extend(
        f"public.composite_foreign_key.{table}.({','.join(columns)})"
        f"->public.{foreign_table}.({','.join(foreign_columns)})"
        for table, columns, foreign_table, foreign_columns in sorted(
            REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEYS
        )
    )
    points.extend(
        f"public.check.{table}.{constraint_name}"
        for table, constraint_name in sorted(REQUIRED_RUNTIME_CHECKS)
    )
    points.extend(f"public.index.{index}" for index in sorted(REQUIRED_RUNTIME_INDEXES))
    points.append("public.data.school_curriculum_releases.canonical_rows")
    points.append("public.trigger.school_curriculum_releases_immutable")
    points.append(
        "public.function.reject_school_curriculum_release_identity_change"
    )
    for table in sorted(SENSITIVE_SCHOOL_TABLES):
        points.append(f"public.rls.{table}.enabled")
        points.append(f"public.privileges.{table}.api_roles_none")
    return points


def _check_definition_matches(
    definition: str,
    required_semantics: tuple[str, ...],
) -> bool:
    normalized = definition.lower().replace('"', "").replace("::text", "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    semantic_matches = {
        "api_version_not_rebuild": "api_version <> 'rebuild'" in normalized,
        "status_not_active_or_paused": (
            "status not in ('active', 'paused_for_masterclass')" in normalized
            or "status <> all (array['active', 'paused_for_masterclass'])" in normalized
        ),
        "profile_version_id_not_null": (
            "profile_version_id is not null" in normalized
        ),
        "status_inactive_bypass": "status <> 'active'" in normalized,
        "complete_identity": (
            "display_name is not null" in normalized
            and "school_name is not null" in normalized
        ),
        "complete_class_subject": (
            (
                "board_id in ('cbse', 'ncert')" in normalized
                or "board_id = any (array['cbse', 'ncert'])" in normalized
            )
            and
            "target_class_no" in normalized
            and "subject_ids is not null" in normalized
            and "jsonb_array_length(subject_ids) > 0" in normalized
            and "subject_ids <@ '[english]'::jsonb" in normalized
        ),
        "complete_language": (
            (
                "preferred_teaching_language in ('en', 'hi', 'hi_en')"
                in normalized
                or "preferred_teaching_language = any (array['en', 'hi', 'hi_en'])"
                in normalized
            )
            and (
                "english_comfort in ('low', 'medium', 'high')" in normalized
                or "english_comfort = any (array['low', 'medium', 'high'])"
                in normalized
            )
        ),
        "complete_goal": (
            "learner_goal is not null" in normalized
            and "parent_goal is not null" in normalized
            and "nullif(btrim(learner_goal), '') is not null" in normalized
            and "nullif(btrim(parent_goal), '') is not null" in normalized
        ),
        "complete_difficulty_signals": (
            "prior_difficulty_signals is not null" in normalized
            and "prior_difficulty_signals <@" in normalized
        ),
        "draft_lifecycle": (
            "status = 'draft'" in normalized
            and "activated_at is null" in normalized
            and "archived_at is null" in normalized
        ),
        "active_lifecycle": (
            "status = 'active'" in normalized
            and "activated_at is not null" in normalized
        ),
        "archived_lifecycle": (
            "status = 'archived'" in normalized
            and "archived_at is not null" in normalized
        ),
    }
    matched = all(
        semantic_matches.get(requirement, False) for requirement in required_semantics
    )
    if "api_version_not_rebuild" in required_semantics:
        return matched and normalized.count(" or ") >= 2
    return matched


def _strip_outer_parentheses(value: str) -> str:
    current = value.strip()
    while current.startswith("(") and current.endswith(")"):
        depth = 0
        closes_at_end = False
        for index, character in enumerate(current):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = index == len(current) - 1
                    break
        if not closes_at_end:
            break
        current = current[1:-1].strip()
    return current


def _exact_runtime_index_matches(index_name: str, definition: str) -> bool:
    normalized = definition.lower().replace('"', "")
    normalized = normalized.replace("::text[]", "").replace("::text", "")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized.startswith("create unique index "):
        return False
    if index_name in {
        "idx_school_curriculum_releases_one_current",
        "school_curriculum_releases_identity_digest_unique",
    }:
        key_match = re.search(
            r"\bon\s+(?:public\.)?school_curriculum_releases"
            r"(?:\s+using\s+\w+)?\s*\(([^)]*)\)",
            normalized,
        )
        if not key_match:
            return False
        keys = tuple(part.strip() for part in key_match.group(1).split(","))
        expected_keys = (
            "board_id",
            "subject_id",
            "class_no",
            "academic_year",
        )
        if index_name == "school_curriculum_releases_identity_digest_unique":
            return (
                keys == (*expected_keys, "release_digest")
                and " where " not in normalized
            )
        if keys != expected_keys or " where " not in normalized:
            return False
        predicate = _strip_outer_parentheses(normalized.split(" where ", 1)[1])
        return predicate == "status = 'current'"
    if index_name != "idx_school_sessions_one_active_flow":
        return True
    key_match = re.search(
        r"\bon\s+(?:public\.)?school_sessions(?:\s+using\s+\w+)?\s*\(([^)]*)\)",
        normalized,
    )
    if not key_match:
        return False
    keys = tuple(part.strip() for part in key_match.group(1).split(","))
    if keys != ("user_id", "flow_type", "subject_id", "class_no"):
        return False
    if " where " not in normalized:
        return False
    predicate = _strip_outer_parentheses(normalized.split(" where ", 1)[1])
    return predicate in {
        "status in ('active', 'paused_for_masterclass')",
        "status = any (array['active', 'paused_for_masterclass'])",
    }


@asynccontextmanager
async def _runtime_schema_executor(connection=None):
    if connection is not None:
        yield connection
        return
    from app.db.engine import get_sessionmaker

    async with get_sessionmaker()() as session:
        yield session


async def validate_runtime_schema(connection=None) -> None:
    """Fail fast if Supabase has not had the hardening migrations applied.

    This intentionally runs at boot, not during a learner flow. A stale schema
    should be an operator-visible startup error, not a random /map or lesson-start
    500 after the UI has already accepted a click.
    """
    table_filter = ", ".join(f"'{table}'" for table in sorted(REQUIRED_RUNTIME_COLUMNS))
    query = text(
        f"""
        SELECT table_name, column_name, data_type, udt_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name IN ({table_filter})
        """
    )

    async with _runtime_schema_executor(connection) as session:
        result = await session.execute(query)
        index_result = await session.execute(
            text(
                """
                SELECT index_class.relname AS indexname,
                       pg_get_indexdef(index_row.indexrelid) AS indexdef,
                       index_row.indisvalid,
                       index_row.indisready
                FROM pg_index AS index_row
                JOIN pg_class AS index_class
                  ON index_class.oid = index_row.indexrelid
                JOIN pg_namespace AS namespace_row
                  ON namespace_row.oid = index_class.relnamespace
                WHERE namespace_row.nspname = 'public'
                """
            )
        )
        foreign_key_result = await session.execute(
            text(
                """
                SELECT source_table.relname AS table_name,
                       constraint_row.conname AS constraint_name,
                       source_column.attname AS column_name,
                       target_table.relname AS foreign_table_name,
                       target_column.attname AS foreign_column_name,
                       source_key.position AS column_position,
                       constraint_row.convalidated,
                       constraint_row.confupdtype::text AS confupdtype,
                       constraint_row.confdeltype::text AS confdeltype
                FROM pg_constraint AS constraint_row
                JOIN pg_class AS source_table
                  ON source_table.oid = constraint_row.conrelid
                JOIN pg_namespace AS source_namespace
                  ON source_namespace.oid = source_table.relnamespace
                JOIN pg_class AS target_table
                  ON target_table.oid = constraint_row.confrelid
                JOIN pg_namespace AS target_namespace
                  ON target_namespace.oid = target_table.relnamespace
                JOIN LATERAL unnest(constraint_row.conkey) WITH ORDINALITY
                  AS source_key(attnum, position) ON TRUE
                JOIN LATERAL unnest(constraint_row.confkey) WITH ORDINALITY
                  AS target_key(attnum, position)
                  ON target_key.position = source_key.position
                JOIN pg_attribute AS source_column
                  ON source_column.attrelid = source_table.oid
                 AND source_column.attnum = source_key.attnum
                JOIN pg_attribute AS target_column
                  ON target_column.attrelid = target_table.oid
                 AND target_column.attnum = target_key.attnum
                WHERE constraint_row.contype = 'f'
                  AND source_namespace.nspname = 'public'
                  AND target_namespace.nspname = 'public'
                """
            )
        )
        check_result = await session.execute(
            text(
                """
                SELECT table_row.relname AS table_name,
                       constraint_row.conname AS constraint_name,
                       pg_get_constraintdef(constraint_row.oid, true)
                           AS constraint_definition
                FROM pg_constraint AS constraint_row
                JOIN pg_class AS table_row
                  ON table_row.oid = constraint_row.conrelid
                JOIN pg_namespace AS table_namespace
                  ON table_namespace.oid = table_row.relnamespace
                WHERE constraint_row.contype = 'c'
                  AND table_namespace.nspname = 'public'
                """
            )
        )
        rls_result = await session.execute(
            text(
                """
                SELECT table_row.relname AS table_name,
                       table_row.relrowsecurity AS rls_enabled
                FROM pg_class AS table_row
                JOIN pg_namespace AS namespace_row
                  ON namespace_row.oid = table_row.relnamespace
                WHERE namespace_row.nspname = 'public'
                  AND table_row.relname LIKE 'school_%'
                """
            )
        )
        privilege_result = await session.execute(
            text(
                """
                SELECT table_name, grantee, privilege_type
                FROM information_schema.table_privileges
                WHERE table_schema = 'public'
                  AND table_name LIKE 'school_%'
                  AND grantee IN ('anon', 'authenticated', 'PUBLIC')
                """
            )
        )
        release_result = await session.execute(
            text(
                """
                SELECT curriculum_release_id, board_id, subject_id, class_no,
                       academic_year, manifest, release_digest, status
                FROM public.school_curriculum_releases
                ORDER BY class_no, curriculum_release_id
                """
            )
        )
        immutability_result = await session.execute(
            text(
                """
                SELECT trigger_row.tgname AS trigger_name,
                       trigger_row.tgenabled::text AS tgenabled,
                       pg_get_triggerdef(trigger_row.oid, true)
                           AS trigger_definition,
                       pg_get_functiondef(function_row.oid)
                           AS function_definition
                FROM pg_trigger AS trigger_row
                JOIN pg_class AS table_row
                  ON table_row.oid = trigger_row.tgrelid
                JOIN pg_namespace AS namespace_row
                  ON namespace_row.oid = table_row.relnamespace
                JOIN pg_proc AS function_row
                  ON function_row.oid = trigger_row.tgfoid
                WHERE namespace_row.nspname = 'public'
                  AND table_row.relname = 'school_curriculum_releases'
                  AND trigger_row.tgname = 'school_curriculum_releases_immutable'
                  AND NOT trigger_row.tgisinternal
                """
            )
        )

    column_rows = result.mappings().all()
    found = {
        (str(row["table_name"]), str(row["column_name"]))
        for row in column_rows
    }
    column_types = {
        (str(row["table_name"]), str(row["column_name"])): str(
            row.get("udt_name") or row.get("data_type") or ""
        ).lower()
        for row in column_rows
    }
    indexes = {
        str(row["indexname"]): row
        for row in index_result.mappings().all()
    }
    foreign_key_rows = foreign_key_result.mappings().all()
    valid_foreign_key_rows = [
        row
        for row in foreign_key_rows
        if bool(row.get("convalidated"))
        and str(row.get("confupdtype") or "") == "a"
        and str(row.get("confdeltype") or "") == "a"
    ]
    foreign_keys = {
        (
            str(row["table_name"]),
            str(row["column_name"]),
            str(row["foreign_table_name"]),
            str(row["foreign_column_name"]),
        )
        for row in valid_foreign_key_rows
    }
    composite_foreign_keys: set[
        tuple[str, tuple[str, ...], str, tuple[str, ...]]
    ] = set()
    grouped_foreign_keys: dict[
        tuple[str, str, str], list[tuple[int, str, str]]
    ] = {}
    for row in valid_foreign_key_rows:
        constraint_name = str(row.get("constraint_name") or "")
        if not constraint_name:
            continue
        key = (
            str(row["table_name"]),
            constraint_name,
            str(row["foreign_table_name"]),
        )
        grouped_foreign_keys.setdefault(key, []).append(
            (
                int(row.get("column_position") or 0),
                str(row["column_name"]),
                str(row["foreign_column_name"]),
            )
        )
    for (table, _constraint, foreign_table), rows in grouped_foreign_keys.items():
        ordered = sorted(rows)
        composite_foreign_keys.add(
            (
                table,
                tuple(row[1] for row in ordered),
                foreign_table,
                tuple(row[2] for row in ordered),
            )
        )
    checks = {
        (str(row["table_name"]), str(row["constraint_name"])): str(
            row["constraint_definition"]
        )
        for row in check_result.mappings().all()
    }
    rls_enabled = {
        str(row["table_name"]): bool(row["rls_enabled"])
        for row in rls_result.mappings().all()
    }
    api_privilege_tables = {
        str(row["table_name"])
        for row in privilege_result.mappings().all()
    }
    release_rows = [
        {
            "curriculum_release_id": str(row["curriculum_release_id"]),
            "board_id": str(row["board_id"]),
            "subject_id": str(row["subject_id"]),
            "class_no": int(row["class_no"]),
            "academic_year": str(row["academic_year"]),
            "manifest": dict(row["manifest"]),
            "release_digest": str(row["release_digest"]),
            "status": str(row["status"]),
        }
        for row in release_result.mappings().all()
    ]
    immutability_rows = immutability_result.mappings().all()
    missing = [
        f"public.{table}.{column}"
        for table, columns in sorted(REQUIRED_RUNTIME_COLUMNS.items())
        for column in sorted(columns)
        if (table, column) not in found
    ]
    for (table, column), required_type in sorted(
        REQUIRED_RUNTIME_COLUMN_TYPES.items()
    ):
        if column_types.get((table, column)) != required_type:
            missing.append(f"public.{table}.{column}.type.{required_type}")
    for table, column, foreign_table, foreign_column in sorted(
        REQUIRED_RUNTIME_FOREIGN_KEYS
    ):
        requirement = (table, column, foreign_table, foreign_column)
        if requirement not in foreign_keys:
            missing.append(
                f"public.foreign_key.{table}.{column}"
                f"->public.{foreign_table}.{foreign_column}"
            )
    for requirement in sorted(REQUIRED_RUNTIME_COMPOSITE_FOREIGN_KEYS):
        if requirement not in composite_foreign_keys:
            table, columns, foreign_table, foreign_columns = requirement
            missing.append(
                f"public.composite_foreign_key.{table}.({','.join(columns)})"
                f"->public.{foreign_table}.({','.join(foreign_columns)})"
            )
    for (table, constraint_name), required_semantics in sorted(
        REQUIRED_RUNTIME_CHECKS.items()
    ):
        definition = checks.get((table, constraint_name), "")
        if not definition or not _check_definition_matches(
            definition,
            required_semantics,
        ):
            missing.append(f"public.check.{table}.{constraint_name}")
    for index_name, required_tokens in sorted(REQUIRED_RUNTIME_INDEXES.items()):
        index_row = indexes.get(index_name)
        index_def = str(index_row["indexdef"]) if index_row else ""
        normalized = index_def.lower()
        missing_tokens = any(
            token.lower() not in normalized for token in required_tokens
        )
        wrong_exact_shape = (
            index_name in REQUIRED_EXACT_RUNTIME_INDEXES
            and not _exact_runtime_index_matches(index_name, index_def)
        )
        invalid_catalog_state = not (
            index_row
            and bool(index_row.get("indisvalid"))
            and bool(index_row.get("indisready"))
        )
        if not index_def or missing_tokens or wrong_exact_shape or invalid_catalog_state:
            missing.append(f"public.index.{index_name}")
    release_rows_are_canonical = (
        release_rows == [dict(row) for row in REQUIRED_SCHOOL_CURRICULUM_RELEASES]
        and all(
            row["release_digest"] == _release_digest(row["manifest"])
            for row in release_rows
        )
    )
    if not release_rows_are_canonical:
        missing.append("public.data.school_curriculum_releases.canonical_rows")
    immutability = next(
        (
            row
            for row in immutability_rows
            if str(row.get("trigger_name") or "")
            == "school_curriculum_releases_immutable"
        ),
        None,
    )
    trigger_definition = _normalize_definition(
        str(immutability.get("trigger_definition") or "")
        if immutability
        else ""
    )
    trigger_enabled = str(immutability.get("tgenabled") or "") if immutability else ""
    if trigger_enabled not in {"O", "A"} or not re.fullmatch(
        r"create trigger school_curriculum_releases_immutable before "
        r"(?:update or delete|delete or update) on "
        r"(?:public\.)?school_curriculum_releases for each row execute function "
        r"(?:public\.)?reject_school_curriculum_release_identity_change\(\)",
        trigger_definition,
    ):
        missing.append("public.trigger.school_curriculum_releases_immutable")
    function_definition = _normalize_definition(
        str(immutability.get("function_definition") or "")
        if immutability
        else ""
    )
    if not (
        "reject_school_curriculum_release_identity_change" in function_definition
        and "school_curriculum_release_immutable" in function_definition
        and "raise exception" in function_definition
        and "return old" in function_definition
        and "return new" not in function_definition
    ):
        missing.append(
            "public.function.reject_school_curriculum_release_identity_change"
        )
    for table in sorted(SENSITIVE_SCHOOL_TABLES):
        if not rls_enabled.get(table, False):
            missing.append(f"public.rls.{table}.enabled")
        if table in api_privilege_tables:
            missing.append(f"public.privileges.{table}.api_roles_none")
    if missing:
        joined = ", ".join(missing)
        migrations = ", ".join(REQUIRED_MIGRATION_FILES)
        raise SchemaDriftError(
            "Supabase schema is missing required runtime schema points "
            "(columns, types, foreign keys, checks, indexes, RLS, and/or privileges): "
            f"{joined}. Run these migrations in order: {migrations}."
        )
