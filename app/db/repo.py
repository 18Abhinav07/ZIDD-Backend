"""Persistence repository — thin async SQL over the product data tables.

Pure data access: no pedagogy, no AI. The service layer owns flow; this owns
rows. Every function takes an AsyncSession so the caller controls the txn
boundary. Product runtime must use Supabase/Postgres; storage failures should
surface to callers instead of silently losing learner state.
"""
import asyncio
import hashlib
import json
import math
import time
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.billing.wallet import (
    CreditLot,
    allocate_spend,
    recovery_credit_amount,
    wallet_summary,
)
from app.content.skills import coerce_skill_id
from app.db.cancellation import finish_cleanup

_WEAKNESS_RECENCY_SECONDS = 30 * 24 * 60 * 60
_WEAKNESS_SURFACE_CAP = 5
_SCHOOL_MASTERY_ALPHA = 0.5
_SCHOOL_PASS_MARK = 0.6
_SCHOOL_WEAK_SURFACE_CAP = 5
_SCHOOL_MASTERED_THRESHOLD = 0.8
_SCHOOL_REVIEW_STALE_SECONDS = 5 * 24 * 60 * 60
_REQUEST_STALE_SECONDS = 120
CAREER_LEARNING_EVENT_LIMIT = 200
_SCHOOL_ANSWER_REQUEST_STALE_SECONDS = 120
_SCHOOL_EVALUATION_JOB_LEASE_SECONDS = 120
_SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS = 10 * 60
_SCHOOL_EVALUATION_JOB_DEFAULT_LEASE_OWNER = "school-evaluation-worker"
_SCHOOL_EVALUATION_JOB_MAX_RETRY_DELAY_SECONDS = 15 * 60
_PLACEMENT_RETRY_TIMING_FIELDS = frozenset(
    {
        "item_id",
        "retry_pending",
        "accrued_learner_seconds",
        "presented_at",
    }
)
_SCHOOL_ACTIVE_SESSION_STATUSES = {"active", "paused_for_masterclass"}
_SCHOOL_TERMINAL_SESSION_STATUSES = {
    "complete",
    "insufficient_evidence",
    "abandoned",
    "expired",
}


def _validate_learning_domain_task(domain: str, task_type: str) -> None:
    normalized_domain = str(domain or "").strip()
    normalized_task = str(task_type or "").strip()
    if normalized_domain not in {"career", "school"}:
        raise ValueError("invalid_learning_domain")
    is_school_task = normalized_task.startswith("school_")
    if normalized_domain == "school" and not is_school_task:
        raise ValueError("school_learning_task_domain_mismatch")
    if normalized_domain == "career" and is_school_task:
        raise ValueError("career_learning_task_domain_mismatch")


def _validated_placement_retry_timing(
    placement_retry_timing: dict | None,
    *,
    activity_id: str,
) -> dict | None:
    """Accept only the server-generated retry-timing patch shape."""
    if placement_retry_timing is None:
        return None
    error = ValueError("invalid_school_evaluation_job_placement_retry_timing")
    if (
        not isinstance(placement_retry_timing, dict)
        or set(placement_retry_timing) != _PLACEMENT_RETRY_TIMING_FIELDS
    ):
        raise error
    item_id = placement_retry_timing.get("item_id")
    presented_at = placement_retry_timing.get("presented_at")
    accrued_learner_seconds = placement_retry_timing.get("accrued_learner_seconds")
    if (
        not isinstance(item_id, str)
        or item_id != activity_id
        or placement_retry_timing.get("retry_pending") is not True
        or isinstance(accrued_learner_seconds, bool)
        or not isinstance(accrued_learner_seconds, (int, float))
        or not math.isfinite(float(accrued_learner_seconds))
        or float(accrued_learner_seconds) < 0
        or not isinstance(presented_at, str)
        or not presented_at
    ):
        raise error
    try:
        datetime.fromisoformat(presented_at)
    except ValueError as exc:
        raise error from exc
    return {
        "item_id": item_id,
        "retry_pending": True,
        "accrued_learner_seconds": float(accrued_learner_seconds),
        "presented_at": presented_at,
    }

# ---------- profiles ----------

async def ensure_profile(
    session: AsyncSession,
    user_id: str,
    name: str = "",
    email: str | None = None,
    google_sub: str | None = None,
) -> None:
    display_name = (name or "").strip()
    await session.execute(
        text(
            """
            INSERT INTO learner_profiles (user_id, display_name, email, google_sub)
            VALUES (:uid, :name, :email, :gsub)
            ON CONFLICT (user_id) DO UPDATE SET
            display_name = CASE WHEN excluded.display_name != '' THEN excluded.display_name ELSE learner_profiles.display_name END,
            email = CASE WHEN excluded.email IS NOT NULL THEN excluded.email ELSE learner_profiles.email END,
            google_sub = CASE WHEN excluded.google_sub IS NOT NULL THEN excluded.google_sub ELSE learner_profiles.google_sub END
            """
        ),
        {"uid": user_id, "name": display_name, "email": email, "gsub": google_sub},
    )
    await session.commit()


async def get_profile(session: AsyncSession, user_id: str) -> dict | None:
    result = await session.execute(
        text(
            "SELECT user_id, credits, demo_unlimited, display_name as name, email, google_sub, "
            "preferences, primary_motive, onboarding_completed_at, school_profile, "
            "career_profile, onboarding_state "
            "FROM learner_profiles WHERE user_id = :uid"
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_profile_by_email(session: AsyncSession, email: str) -> dict | None:
    result = await session.execute(
        text(
            "SELECT user_id, credits, demo_unlimited, display_name as name, email, google_sub, "
            "preferences, primary_motive, onboarding_completed_at, school_profile, "
            "career_profile, onboarding_state "
            "FROM learner_profiles WHERE email = :email"
        ),
        {"email": email},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_profile_by_google_sub(session: AsyncSession, google_sub: str) -> dict | None:
    result = await session.execute(
        text(
            "SELECT user_id, credits, demo_unlimited, display_name as name, email, google_sub, "
            "preferences, primary_motive, onboarding_completed_at, school_profile, "
            "career_profile, onboarding_state "
            "FROM learner_profiles WHERE google_sub = :gsub"
        ),
        {"gsub": google_sub},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def resolve_google_login(
    session: AsyncSession,
    google_sub: str,
    email: str,
    name: str,
    welcome_credits: int,
    *,
    beta_credit_grant_enabled: bool = False,
    beta_credit_grant_credits: int = 0,
    beta_credit_grant_campaign_id: str = "",
    beta_credit_grant_expires_at: datetime | None = None,
) -> dict:
    """Resolve/link/create a Google learner in one DB transaction.

    The old route opened separate Supabase connections for sub lookup, email
    lookup, profile upsert, welcome credit grant, and balance read. Over the
    transaction pooler that made first login painfully slow. Keep this path on
    one AsyncSession and one commit.
    """
    if beta_credit_grant_enabled:
        if beta_credit_grant_credits <= 0:
            raise ValueError("beta_credit_grant_credits_must_be_positive")
        if not beta_credit_grant_campaign_id.strip():
            raise ValueError("beta_credit_grant_campaign_id_required")
        if beta_credit_grant_expires_at is None:
            raise ValueError("beta_credit_grant_expiry_required")
        if (
            beta_credit_grant_expires_at.tzinfo is None
            or beta_credit_grant_expires_at.utcoffset() is None
        ):
            raise ValueError("beta_credit_grant_expiry_must_be_timezone_aware")
        if beta_credit_grant_expires_at <= datetime.now(timezone.utc):
            raise ValueError("beta_credit_grant_expiry_must_be_future")
    user_id = f"google:{google_sub}"
    try:
        result = await session.execute(
            text(
                """
                WITH by_sub AS (
                    SELECT user_id
                    FROM learner_profiles
                    WHERE google_sub = :gsub
                    LIMIT 1
                ),
                by_email AS (
                    SELECT user_id
                    FROM learner_profiles
                    WHERE email = :email
                      AND NOT EXISTS (SELECT 1 FROM by_sub)
                    LIMIT 1
                ),
                linked AS (
                    UPDATE learner_profiles
                    SET google_sub = :gsub,
                        email = :email,
                        display_name = CASE
                            WHEN COALESCE(display_name, '') = '' AND :name != '' THEN :name
                            ELSE display_name
                        END
                    WHERE user_id = (SELECT user_id FROM by_email)
                    RETURNING user_id, false AS is_new_user
                ),
                created AS (
                    INSERT INTO learner_profiles
                        (user_id, display_name, email, google_sub, credits)
                    SELECT :uid, :name, :email, :gsub, :credits
                    WHERE NOT EXISTS (SELECT 1 FROM by_sub)
                      AND NOT EXISTS (SELECT 1 FROM by_email)
                    ON CONFLICT DO NOTHING
                    RETURNING user_id, true AS is_new_user
                ),
                welcome AS (
                    INSERT INTO credit_transactions (user_id, delta, reason)
                    SELECT user_id, :credits, 'welcome'
                    FROM created
                    WHERE :credits != 0
                    RETURNING 1
                )
                SELECT user_id, false AS is_new_user FROM by_sub
                UNION ALL
                SELECT user_id, is_new_user FROM linked
                UNION ALL
                SELECT user_id, is_new_user FROM created
                LIMIT 1
                """
            ),
            {
                "uid": user_id,
                "name": (name or "").strip(),
                "email": email,
                "gsub": google_sub,
                "credits": welcome_credits,
            },
        )
        row = result.mappings().first()
        if row:
            if beta_credit_grant_enabled:
                await _grant_credit_lot(
                    session,
                    user_id=str(row["user_id"]),
                    amount=int(beta_credit_grant_credits),
                    reason="beta_credit_grant",
                    source="beta_grant",
                    grant_key=f"beta:{beta_credit_grant_campaign_id}",
                    expires_at=beta_credit_grant_expires_at,
                )
            await session.commit()
            return {
                "user_id": row["user_id"],
                "is_new_user": bool(row["is_new_user"]),
            }
    except IntegrityError:
        # Another callback may have created/linked the row between our lookups
        # and insert. Roll back and resolve against the now-existing identity.
        await session.rollback()

    # Race fallback: ON CONFLICT DO NOTHING can return no row if another request
    # inserted the profile concurrently. Resolve once more without creating.
    profile = (
        await get_profile_by_google_sub(session, google_sub)
        or await get_profile_by_email(session, email)
    )
    if not profile:
        raise KeyError(f"could not resolve Google profile for {email}")
    if beta_credit_grant_enabled:
        await _grant_credit_lot(
            session,
            user_id=str(profile["user_id"]),
            amount=int(beta_credit_grant_credits),
            reason="beta_credit_grant",
            source="beta_grant",
            grant_key=f"beta:{beta_credit_grant_campaign_id}",
            expires_at=beta_credit_grant_expires_at,
        )
        await session.commit()
    return {"user_id": profile["user_id"], "is_new_user": False}


async def get_preferences(session: AsyncSession, user_id: str) -> dict:
    result = await session.execute(
        text("SELECT preferences FROM learner_profiles WHERE user_id = :uid"),
        {"uid": user_id},
    )
    row = result.first()
    if not row or not isinstance(row[0], dict):
        return {}
    return dict(row[0])


async def update_preferences(session: AsyncSession, user_id: str, patch: dict) -> dict:
    current = await get_preferences(session, user_id)
    for key, value in patch.items():
        current[key] = value
    result = await session.execute(
        text(
            """
            UPDATE learner_profiles
            SET preferences = CAST(:prefs AS jsonb)
            WHERE user_id = :uid
            RETURNING preferences
            """
        ),
        {"uid": user_id, "prefs": json.dumps(current)},
    )
    await session.commit()
    row = result.first()
    if row and isinstance(row[0], dict):
        return dict(row[0])
    return current


async def update_onboarding_state(
    session: AsyncSession, user_id: str, draft: dict
) -> dict:
    clean = dict(draft or {})
    result = await session.execute(
        text(
            """
            UPDATE learner_profiles
            SET onboarding_state = CAST(:draft AS jsonb)
            WHERE user_id = :uid
            RETURNING onboarding_state
            """
        ),
        {"uid": user_id, "draft": json.dumps(clean)},
    )
    row = result.first()
    await session.commit()
    if row and isinstance(row[0], dict):
        return dict(row[0])
    return clean


async def complete_onboarding(
    session: AsyncSession,
    user_id: str,
    display_name: str,
    primary_motive: str,
    school_profile: dict,
    career_profile: dict,
) -> dict:
    result = await session.execute(
        text(
            """
            UPDATE learner_profiles
            SET display_name = CASE
                    WHEN :name != '' THEN :name
                    ELSE learner_profiles.display_name
                END,
                primary_motive = :primary_motive,
                onboarding_completed_at = now(),
                school_profile = CASE
                    WHEN :primary_motive = 'school'
                        THEN CAST(:school_profile AS jsonb)
                    ELSE learner_profiles.school_profile
                END,
                career_profile = CASE
                    WHEN :primary_motive = 'career'
                        THEN CAST(:career_profile AS jsonb)
                    ELSE learner_profiles.career_profile
                END,
                onboarding_state = '{}'::jsonb
            WHERE user_id = :uid
            RETURNING user_id, credits, demo_unlimited, display_name as name,
                email, google_sub, preferences, primary_motive,
                onboarding_completed_at, school_profile, career_profile,
                onboarding_state
            """
        ),
        {
            "uid": user_id,
            "name": display_name.strip(),
            "primary_motive": primary_motive,
            "school_profile": json.dumps(dict(school_profile or {})),
            "career_profile": json.dumps(dict(career_profile or {})),
        },
    )
    row = result.mappings().first()
    await session.commit()
    if row is None:
        raise KeyError(user_id)
    return dict(row)


async def get_active_school_profile_version(
    session: AsyncSession,
    user_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT *
            FROM school_profile_versions
            WHERE user_id = :uid AND status = 'active'
            ORDER BY activated_at DESC NULLS LAST, updated_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_school_state_snapshot(
    session: AsyncSession,
    user_id: str,
) -> dict:
    """Load the common canonical School read model in one database round trip.

    A normal School page previously reopened a Supabase session for every piece
    of state.  The values below share one active profile and report lineage, so
    fetching them independently was slower and allowed cross-query drift.
    Historical compatible-profile recovery remains a route-level fallback.
    """

    result = await session.execute(
        text(
            """
            WITH active_profile AS (
                SELECT *
                FROM school_profile_versions
                WHERE user_id = :uid AND status = 'active'
                ORDER BY activated_at DESC NULLS LAST, updated_at DESC
                LIMIT 1
            ),
            latest_placement AS (
                SELECT s.*
                FROM school_sessions AS s
                JOIN active_profile AS p
                  ON p.user_id = s.user_id
                 AND p.profile_version_id = s.profile_version_id
                 AND s.subject_id = p.subject_ids ->> 0
                 AND s.class_no = p.target_class_no
                WHERE s.user_id = :uid
                  AND s.api_version = 'rebuild'
                  AND s.flow_type = 'placement'
                ORDER BY
                    CASE WHEN s.status IN ('active', 'paused_for_masterclass')
                         THEN 0 ELSE 1 END,
                    s.updated_at DESC
                LIMIT 1
            ),
            latest_report AS (
                SELECT r.*
                FROM school_placement_reports AS r
                JOIN active_profile AS p
                  ON p.user_id = r.user_id
                 AND p.profile_version_id = r.profile_version_id
                 AND r.subject_id = p.subject_ids ->> 0
                 AND r.target_class_no = p.target_class_no
                WHERE r.user_id = :uid
                ORDER BY
                    CASE WHEN r.placement_session_id =
                                   (SELECT session_id FROM latest_placement)
                         THEN 0 ELSE 1 END,
                    r.updated_at DESC
                LIMIT 1
            ),
            latest_recap AS (
                SELECT s.*
                FROM school_sessions AS s
                JOIN active_profile AS p
                  ON p.user_id = s.user_id
                 AND p.profile_version_id = s.profile_version_id
                 AND s.subject_id = p.subject_ids ->> 0
                 AND s.class_no = p.target_class_no
                JOIN latest_report AS r
                  ON r.report_id = s.source_placement_report_id
                WHERE s.user_id = :uid
                  AND s.api_version = 'rebuild'
                  AND s.flow_type = 'recap'
                ORDER BY
                    CASE WHEN s.status IN ('active', 'paused_for_masterclass')
                         THEN 0 ELSE 1 END,
                    s.updated_at DESC
                LIMIT 1
            ),
            latest_curriculum AS (
                SELECT s.*
                FROM school_sessions AS s
                JOIN active_profile AS p
                  ON p.user_id = s.user_id
                 AND p.profile_version_id = s.profile_version_id
                 AND s.subject_id = p.subject_ids ->> 0
                 AND s.class_no = p.target_class_no
                JOIN latest_report AS r
                  ON r.report_id = s.source_placement_report_id
                WHERE s.user_id = :uid
                  AND s.api_version = 'rebuild'
                  AND s.flow_type = 'curriculum'
                ORDER BY
                    CASE WHEN s.status IN ('active', 'paused_for_masterclass')
                         THEN 0 ELSE 1 END,
                    s.updated_at DESC
                LIMIT 1
            ),
            active_parent AS (
                SELECT session_id FROM latest_curriculum
                UNION ALL
                SELECT session_id FROM latest_recap
                WHERE NOT EXISTS (SELECT 1 FROM latest_curriculum)
                LIMIT 1
            ),
            relevant_answer_sessions AS (
                SELECT session_id FROM latest_placement
                UNION
                SELECT session_id FROM latest_recap
                UNION
                SELECT session_id FROM latest_curriculum
                UNION
                SELECT s.session_id
                FROM school_sessions AS s
                WHERE s.user_id = :uid
                  AND s.linked_session_id =
                      (SELECT session_id FROM active_parent)
            )
            SELECT
                (
                    SELECT jsonb_build_object(
                        'user_id', lp.user_id,
                        'credits', lp.credits,
                        'demo_unlimited', lp.demo_unlimited,
                        'name', lp.display_name,
                        'email', lp.email,
                        'google_sub', lp.google_sub,
                        'preferences', lp.preferences,
                        'primary_motive', lp.primary_motive,
                        'onboarding_completed_at', lp.onboarding_completed_at,
                        'school_profile', lp.school_profile,
                        'career_profile', lp.career_profile,
                        'onboarding_state', lp.onboarding_state
                    )
                    FROM learner_profiles AS lp
                    WHERE lp.user_id = :uid
                ) AS learner_profile,
                (SELECT to_jsonb(p) FROM active_profile AS p) AS school_profile,
                (SELECT to_jsonb(s) FROM latest_placement AS s) AS placement_session,
                (SELECT to_jsonb(r) FROM latest_report AS r) AS placement_report,
                (SELECT to_jsonb(s) FROM latest_recap AS s) AS recap_session,
                (SELECT to_jsonb(s) FROM latest_curriculum AS s) AS curriculum_session,
                COALESCE(
                    (
                        SELECT jsonb_agg(to_jsonb(s) ORDER BY s.updated_at DESC)
                        FROM school_sessions AS s
                        WHERE s.user_id = :uid
                          AND s.linked_session_id =
                              (SELECT session_id FROM active_parent)
                    ),
                    '[]'::jsonb
                ) AS linked_sessions,
                COALESCE(
                    (
                        SELECT jsonb_agg(
                            to_jsonb(a) || jsonb_build_object(
                                'age_seconds', GREATEST(
                                    0,
                                    EXTRACT(EPOCH FROM (now() - a.updated_at))
                                ),
                                'stale', EXTRACT(EPOCH FROM (now() - a.updated_at))
                                    >= :stale_seconds,
                                'evaluation_job_status', job.status,
                                'evaluation_job_within_deadline',
                                    job.status IN ('queued', 'running')
                                    AND job.created_at > now() - (
                                        CAST(:evaluation_deadline_seconds AS integer)
                                        * INTERVAL '1 second'
                                    )
                            )
                            ORDER BY a.updated_at DESC
                        )
                        FROM school_answer_requests AS a
                        LEFT JOIN school_evaluation_jobs AS job
                          ON job.session_id = a.session_id
                         AND job.activity_id = a.activity_id
                         AND job.user_id = a.user_id
                         AND job.answer_hash = a.answer_hash
                         AND job.answer_claim_token = a.claim_token
                        WHERE a.user_id = :uid
                          AND a.session_id IN (
                              SELECT session_id FROM relevant_answer_sessions
                          )
                          AND a.status = 'processing'
                    ),
                    '[]'::jsonb
                ) AS processing_answer_requests,
                COALESCE(
                    (
                        SELECT jsonb_agg(to_jsonb(sp) ORDER BY sp.last_seen_at DESC)
                        FROM learner_skill_profiles AS sp
                        WHERE sp.user_id = :uid AND sp.domain = 'school'
                    ),
                    '[]'::jsonb
                ) AS school_skill_profiles
            """
        ),
        {
            "uid": user_id,
            "stale_seconds": _SCHOOL_ANSWER_REQUEST_STALE_SECONDS,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().first()
    if row is None:
        return {
            "learner_profile": None,
            "school_profile": None,
            "placement_session": None,
            "placement_report": None,
            "recap_session": None,
            "curriculum_session": None,
            "linked_sessions": [],
            "processing_answer_requests": [],
            "school_skill_profiles": [],
        }
    snapshot = dict(row)
    raw_report = snapshot.get("placement_report")
    if isinstance(raw_report, dict):
        snapshot["placement_report"] = _school_placement_report_from_row(raw_report)
    for key in (
        "linked_sessions",
        "processing_answer_requests",
        "school_skill_profiles",
    ):
        snapshot[key] = list(snapshot.get(key) or [])

    requests_by_session: dict[str, dict] = {}
    for request in snapshot["processing_answer_requests"]:
        if not isinstance(request, dict):
            continue
        session_id = str(request.get("session_id") or "")
        if session_id and session_id not in requests_by_session:
            requests_by_session[session_id] = request

    def attach_processing_request(value: object) -> object:
        if not isinstance(value, dict):
            return value
        request = requests_by_session.get(str(value.get("session_id") or ""))
        return {**value, "processing_answer_request": request} if request else value

    for key in ("placement_session", "recap_session", "curriculum_session"):
        snapshot[key] = attach_processing_request(snapshot.get(key))
    snapshot["linked_sessions"] = [
        attach_processing_request(value) for value in snapshot["linked_sessions"]
    ]
    return snapshot


async def get_school_profile_draft(
    session: AsyncSession,
    user_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT *
            FROM school_profile_versions
            WHERE user_id = :uid AND status = 'draft'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_school_profile_version(
    session: AsyncSession,
    user_id: str,
    profile_version_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT *
            FROM school_profile_versions
            WHERE user_id = :uid
              AND profile_version_id = CAST(:profile_version_id AS uuid)
            LIMIT 1
            """
        ),
        {"uid": user_id, "profile_version_id": profile_version_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def _lock_school_profile_lineage(
    session: AsyncSession,
    user_id: str,
) -> None:
    result = await session.execute(
        text(
            """
            SELECT user_id
            FROM learner_profiles
            WHERE user_id = :uid
            FOR UPDATE
            """
        ),
        {"uid": user_id},
    )
    if result.first() is None:
        raise KeyError(user_id)


def _school_profile_json_value(value):
    if value is None:
        return None
    return json.dumps(value)


_SCHOOL_PROFILE_ALL_FIELDS = (
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
)
_SCHOOL_PROFILE_COMPATIBILITY_FIELDS = (
    "board_id",
    "target_class_no",
    "subject_ids",
    "preferred_teaching_language",
    "english_comfort",
    "prior_difficulty_signals",
)


def _school_profile_values(row: dict, fields: tuple[str, ...]) -> tuple:
    values = []
    for field in fields:
        value = row.get(field)
        if field in {"subject_ids", "prior_difficulty_signals"} and isinstance(value, str):
            value = json.loads(value)
        if isinstance(value, list):
            value = tuple(sorted(set(value)))
        values.append(value)
    return tuple(values)


def _school_profile_all_values(row: dict) -> tuple:
    return _school_profile_values(row, _SCHOOL_PROFILE_ALL_FIELDS)


def _school_profile_compatibility_values(row: dict) -> tuple:
    return _school_profile_values(row, _SCHOOL_PROFILE_COMPATIBILITY_FIELDS)


def _school_profile_draft_snapshot(row: dict) -> dict:
    def list_value(field: str):
        value = row.get(field)
        if isinstance(value, str):
            value = json.loads(value)
        return list(value) if isinstance(value, (list, tuple)) else value

    target_class_no = row.get("target_class_no")
    return {
        "profile_version_id": str(row["profile_version_id"]),
        "status": "draft",
        "current_step": int(row.get("current_step") or 0),
        "draft_revision": int(row.get("draft_revision") or 1),
        "display_name": row.get("display_name"),
        "school_name": row.get("school_name"),
        "board_id": row.get("board_id"),
        "target_class_no": (
            int(target_class_no) if target_class_no is not None else None
        ),
        "subject_ids": list_value("subject_ids"),
        "preferred_teaching_language": row.get("preferred_teaching_language"),
        "english_comfort": row.get("english_comfort"),
        "learner_goal": row.get("learner_goal"),
        "parent_goal": row.get("parent_goal"),
        "prior_difficulty_signals": list_value("prior_difficulty_signals"),
        "coach_avatar_id": row.get("coach_avatar_id"),
        "coach_palette_id": row.get("coach_palette_id"),
    }


async def save_school_profile_draft(
    session: AsyncSession,
    *,
    user_id: str,
    profile_version_id: str | None,
    expected_revision: int | None,
    current_step: int,
    request_id: str,
    payload_hash: str,
    patch: dict,
) -> dict:
    try:
        await _lock_school_profile_lineage(session, user_id)
        request_result = await session.execute(
            text(
                """
                SELECT payload_hash, response_json
                FROM school_profile_draft_requests
                WHERE user_id = :uid
                  AND request_id = CAST(:request_id AS uuid)
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"uid": user_id, "request_id": request_id},
        )
        request_row = request_result.mappings().first()
        if request_row:
            if request_row.get("payload_hash") != payload_hash:
                raise ValueError("school_draft_request_conflict")
            response_json = request_row.get("response_json") or {}
            if isinstance(response_json, str):
                response_json = json.loads(response_json)
            await session.commit()
            return dict(response_json)

        result = await session.execute(
            text(
                """
                SELECT *
                FROM school_profile_versions
                WHERE user_id = :uid AND status = 'draft'
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"uid": user_id},
        )
        existing_row = result.mappings().first()
        existing = dict(existing_row) if existing_row else None

        if existing:
            if profile_version_id is None or expected_revision is None:
                raise ValueError("school_draft_lineage_required")
            if (
                str(existing["profile_version_id"]) != str(profile_version_id)
            ):
                raise ValueError("school_draft_profile_conflict")
            if (
                int(existing.get("draft_revision") or 1) != int(expected_revision)
            ):
                raise ValueError("school_draft_revision_conflict")
            values = {**existing, **patch}
            next_revision = int(existing.get("draft_revision") or 1) + 1
            draft_id = str(existing["profile_version_id"])
            update_result = await session.execute(
                text(
                    """
                    UPDATE school_profile_versions
                    SET display_name = :display_name,
                        school_name = :school_name,
                        board_id = :board_id,
                        target_class_no = :target_class_no,
                        subject_ids = CAST(:subject_ids AS jsonb),
                        preferred_teaching_language = :preferred_teaching_language,
                        english_comfort = :english_comfort,
                        learner_goal = :learner_goal,
                        parent_goal = :parent_goal,
                        prior_difficulty_signals = CAST(:prior_difficulty_signals AS jsonb),
                        coach_avatar_id = :coach_avatar_id,
                        coach_palette_id = :coach_palette_id,
                        current_step = :current_step,
                        draft_revision = :draft_revision,
                        last_save_request_id = CAST(:request_id AS uuid),
                        last_save_payload_hash = :payload_hash,
                        updated_at = now()
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:profile_version_id AS uuid)
                      AND status = 'draft'
                    RETURNING *
                    """
                ),
                {
                    "uid": user_id,
                    "profile_version_id": draft_id,
                    "display_name": values.get("display_name"),
                    "school_name": values.get("school_name"),
                    "board_id": values.get("board_id"),
                    "target_class_no": values.get("target_class_no"),
                    "subject_ids": _school_profile_json_value(values.get("subject_ids")),
                    "preferred_teaching_language": values.get(
                        "preferred_teaching_language"
                    ),
                    "english_comfort": values.get("english_comfort"),
                    "learner_goal": values.get("learner_goal"),
                    "parent_goal": values.get("parent_goal"),
                    "prior_difficulty_signals": _school_profile_json_value(
                        values.get("prior_difficulty_signals")
                    ),
                    "coach_avatar_id": values.get("coach_avatar_id"),
                    "coach_palette_id": values.get("coach_palette_id"),
                    "current_step": int(current_step),
                    "draft_revision": next_revision,
                    "request_id": request_id,
                    "payload_hash": payload_hash,
                },
            )
            row = update_result.mappings().first()
        else:
            if profile_version_id is not None or expected_revision is not None:
                raise ValueError("school_draft_not_found")
            active_result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM school_profile_versions
                    WHERE user_id = :uid AND status = 'active'
                    LIMIT 1
                    FOR UPDATE
                    """
                ),
                {"uid": user_id},
            )
            active_row = active_result.mappings().first()
            active = dict(active_row) if active_row else {}
            values = {**active, **patch}
            draft_id = str(uuid4())
            insert_result = await session.execute(
                text(
                    """
                    INSERT INTO school_profile_versions
                        (profile_version_id, user_id, status, display_name, school_name,
                         board_id, target_class_no, subject_ids,
                         preferred_teaching_language, english_comfort, learner_goal,
                         parent_goal, prior_difficulty_signals, current_step,
                         coach_avatar_id, coach_palette_id,
                         draft_revision, last_save_request_id, last_save_payload_hash,
                         source_profile_version_id)
                    VALUES
                        (CAST(:profile_version_id AS uuid), :uid, 'draft', :display_name,
                         :school_name, :board_id, :target_class_no,
                         CAST(:subject_ids AS jsonb), :preferred_teaching_language,
                         :english_comfort, :learner_goal, :parent_goal,
                         CAST(:prior_difficulty_signals AS jsonb), :current_step,
                         :coach_avatar_id, :coach_palette_id, 1,
                         CAST(:request_id AS uuid), :payload_hash,
                         CAST(:source_profile_version_id AS uuid))
                    RETURNING *
                    """
                ),
                {
                    "uid": user_id,
                    "profile_version_id": draft_id,
                    "display_name": values.get("display_name"),
                    "school_name": values.get("school_name"),
                    "board_id": values.get("board_id"),
                    "target_class_no": values.get("target_class_no"),
                    "subject_ids": _school_profile_json_value(values.get("subject_ids")),
                    "preferred_teaching_language": values.get(
                        "preferred_teaching_language"
                    ),
                    "english_comfort": values.get("english_comfort"),
                    "learner_goal": values.get("learner_goal"),
                    "parent_goal": values.get("parent_goal"),
                    "prior_difficulty_signals": _school_profile_json_value(
                        values.get("prior_difficulty_signals")
                    ),
                    "coach_avatar_id": values.get("coach_avatar_id"),
                    "coach_palette_id": values.get("coach_palette_id"),
                    "current_step": int(current_step),
                    "request_id": request_id,
                    "payload_hash": payload_hash,
                    "source_profile_version_id": (
                        str(active["profile_version_id"]) if active else None
                    ),
                },
            )
            row = insert_result.mappings().first()

        if row is None:
            raise KeyError(user_id)
        snapshot = _school_profile_draft_snapshot(dict(row))
        await session.execute(
            text(
                """
                INSERT INTO school_profile_draft_requests
                    (user_id, request_id, profile_version_id, payload_hash, response_json)
                VALUES
                    (:uid, CAST(:request_id AS uuid),
                     CAST(:profile_version_id AS uuid), :payload_hash,
                     CAST(:response_json AS jsonb))
                """
            ),
            {
                "uid": user_id,
                "request_id": request_id,
                "profile_version_id": snapshot["profile_version_id"],
                "payload_hash": payload_hash,
                "response_json": json.dumps(snapshot),
            },
        )
        await session.commit()
        return snapshot
    except Exception:
        await session.rollback()
        raise


async def activate_school_profile_draft(
    session: AsyncSession,
    *,
    user_id: str,
    profile_version_id: str,
    expected_revision: int,
    request_id: str,
    payload_hash: str,
) -> dict:
    try:
        await _lock_school_profile_lineage(session, user_id)
        replay_result = await session.execute(
            text(
                """
                SELECT *
                FROM school_profile_versions
                WHERE user_id = :uid
                  AND activation_request_id = CAST(:request_id AS uuid)
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"uid": user_id, "request_id": request_id},
        )
        replay_row = replay_result.mappings().first()
        if replay_row:
            replay = dict(replay_row)
            if replay.get("activation_payload_hash") != payload_hash:
                raise ValueError("school_activation_request_conflict")
            result_profile_id = (
                replay.get("activation_result_profile_version_id")
                or replay.get("profile_version_id")
            )
            profile_result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM school_profile_versions
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:profile_version_id AS uuid)
                    LIMIT 1
                    """
                ),
                {"uid": user_id, "profile_version_id": str(result_profile_id)},
            )
            profile_row = profile_result.mappings().first()
            if profile_row is None:
                raise ValueError("school_activation_result_missing")
            await session.commit()
            return dict(profile_row)

        target_result = await session.execute(
            text(
                """
                SELECT *
                FROM school_profile_versions
                WHERE user_id = :uid
                  AND profile_version_id = CAST(:profile_version_id AS uuid)
                LIMIT 1
                FOR UPDATE
                """
            ),
            {"uid": user_id, "profile_version_id": profile_version_id},
        )
        target_row = target_result.mappings().first()
        if target_row is None:
            raise ValueError("school_profile_not_found")
        target = dict(target_row)
        if int(target.get("draft_revision") or 1) != int(expected_revision):
            raise ValueError("school_profile_revision_conflict")
        if target.get("status") == "active":
            raise ValueError("school_profile_already_active")
        if target.get("status") != "draft":
            raise ValueError("school_profile_not_draft")

        from app.services.school_rebuild_profile import (
            CANONICAL_SCHOOL_COACH_IDS,
            choose_school_coach_identity,
            school_catalog_selection_available,
        )

        if not school_catalog_selection_available(target):
            raise ValueError("school_catalog_selection_unavailable")

        source = None
        source_profile_version_id = target.get("source_profile_version_id")
        if source_profile_version_id is not None:
            source_result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM school_profile_versions
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:profile_version_id AS uuid)
                      AND status = 'active'
                    LIMIT 1
                    FOR UPDATE
                    """
                ),
                {
                    "uid": user_id,
                    "profile_version_id": str(source_profile_version_id),
                },
            )
            source_row = source_result.mappings().first()
            source = dict(source_row) if source_row else None

        if source and _school_profile_all_values(source) == _school_profile_all_values(target):
            await session.execute(
                text(
                    """
                    UPDATE school_profile_versions
                    SET status = 'archived',
                        archived_at = now(),
                        activation_request_id = CAST(:request_id AS uuid),
                        activation_payload_hash = :payload_hash,
                        activation_result_profile_version_id = CAST(:result_profile_id AS uuid),
                        updated_at = now()
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:profile_version_id AS uuid)
                      AND status = 'draft'
                    """
                ),
                {
                    "uid": user_id,
                    "profile_version_id": profile_version_id,
                    "request_id": request_id,
                    "payload_hash": payload_hash,
                    "result_profile_id": str(source["profile_version_id"]),
                },
            )
            await session.commit()
            return source

        existing_avatar_id = target.get("coach_avatar_id")
        existing_palette_id = target.get("coach_palette_id")
        if (
            existing_avatar_id in CANONICAL_SCHOOL_COACH_IDS
            and existing_palette_id == existing_avatar_id
        ):
            coach_identity = {
                "coach_avatar_id": existing_avatar_id,
                "coach_palette_id": existing_palette_id,
            }
        else:
            coach_identity = choose_school_coach_identity()

        await session.execute(
            text(
                """
                UPDATE school_profile_versions
                SET status = 'archived', archived_at = now(), updated_at = now()
                WHERE user_id = :uid AND status = 'active'
                """
            ),
            {"uid": user_id},
        )
        activated_result = await session.execute(
            text(
                """
                UPDATE school_profile_versions
                SET status = 'active',
                    activated_at = now(),
                    archived_at = NULL,
                    coach_avatar_id = :coach_avatar_id,
                    coach_palette_id = :coach_palette_id,
                    activation_request_id = CAST(:request_id AS uuid),
                    activation_payload_hash = :payload_hash,
                    activation_result_profile_version_id = profile_version_id,
                    updated_at = now()
                WHERE user_id = :uid
                  AND profile_version_id = CAST(:profile_version_id AS uuid)
                  AND status = 'draft'
                RETURNING *
                """
            ),
            {
                "uid": user_id,
                "profile_version_id": profile_version_id,
                "request_id": request_id,
                "payload_hash": payload_hash,
                **coach_identity,
            },
        )
        activated_row = activated_result.mappings().first()
        if activated_row is None:
            raise ValueError("school_profile_not_draft")
        activated = dict(activated_row)
        compatible_edit = bool(
            source
            and _school_profile_compatibility_values(source)
            == _school_profile_compatibility_values(target)
        )
        if compatible_edit:
            await session.execute(
                text(
                    """
                    UPDATE school_sessions
                    SET profile_version_id = CAST(:profile_version_id AS uuid),
                        state_json = jsonb_set(
                            state_json,
                            '{profile_version_id}',
                            to_jsonb(CAST(:profile_version_id AS text)),
                            true
                        ),
                        updated_at = now()
                    WHERE user_id = :uid
                      AND profile_version_id = CAST(:source_profile_version_id AS uuid)
                      AND status IN ('active', 'paused_for_masterclass')
                    """
                ),
                {
                    "uid": user_id,
                    "profile_version_id": profile_version_id,
                    "source_profile_version_id": str(source["profile_version_id"]),
                },
            )
        await session.execute(
            text(
                """
                UPDATE school_sessions
                SET status = 'expired', updated_at = now(),
                    completed_at = COALESCE(completed_at, now())
                WHERE user_id = :uid
                  AND status IN ('active', 'paused_for_masterclass')
                  AND profile_version_id IS DISTINCT FROM CAST(:profile_version_id AS uuid)
                """
            ),
            {"uid": user_id, "profile_version_id": profile_version_id},
        )
        await session.execute(
            text(
                """
                UPDATE learner_profiles
                SET display_name = :display_name,
                    primary_motive = 'school',
                    school_profile = CAST(:school_profile AS jsonb),
                    onboarding_completed_at = now(),
                    onboarding_state = '{}'::jsonb
                WHERE user_id = :uid
                """
            ),
            {
                "uid": user_id,
                "display_name": activated["display_name"],
                "school_profile": json.dumps(
                    {
                        field: activated.get(field)
                        for field in (
                            "school_name",
                            "board_id",
                            "target_class_no",
                            "subject_ids",
                            "preferred_teaching_language",
                            "english_comfort",
                            "learner_goal",
                            "parent_goal",
                            "prior_difficulty_signals",
                        )
                    }
                ),
            },
        )
        await session.commit()
        return activated
    except Exception:
        await session.rollback()
        raise


async def _lock_wallet_profile(session: AsyncSession, user_id: str) -> dict | None:
    """Lock one learner's wallet before examining idempotency or lots."""
    result = await session.execute(
        text(
            """
            SELECT user_id, demo_unlimited
            FROM learner_profiles
            WHERE user_id = :uid
            FOR UPDATE
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def _ensure_legacy_credit_lot(session: AsyncSession, user_id: str) -> None:
    """Make pre-lot balances spendable exactly once after the migration."""
    await session.execute(
        text(
            """
            INSERT INTO credit_lots (
                user_id, source, grant_key, original_credits, remaining_credits
            )
            SELECT user_id, 'legacy_migrated', 'legacy_balance_v1', credits, credits
            FROM learner_profiles
            WHERE user_id = :uid
              AND credits > 0
              AND NOT EXISTS (SELECT 1 FROM credit_lots WHERE user_id = :uid)
            ON CONFLICT (user_id, grant_key) DO NOTHING
            """
        ),
        {"uid": user_id},
    )


async def _expire_wallet_lots(session: AsyncSession, user_id: str) -> None:
    """Zero expired grants before every observable balance or debit."""
    await session.execute(
        text(
            """
            UPDATE credit_lots
            SET remaining_credits = 0
            WHERE user_id = :uid
              AND remaining_credits > 0
              AND expires_at IS NOT NULL
              AND expires_at <= now()
            """
        ),
        {"uid": user_id},
    )


async def _wallet_lots_for_update(
    session: AsyncSession,
    user_id: str,
) -> list[CreditLot]:
    result = await session.execute(
        text(
            """
            SELECT id, source, remaining_credits, expires_at
            FROM credit_lots
            WHERE user_id = :uid
              AND remaining_credits > 0
              AND (expires_at IS NULL OR expires_at > now())
            ORDER BY
                CASE WHEN expires_at IS NULL THEN 1 ELSE 0 END,
                expires_at NULLS LAST,
                id
            FOR UPDATE
            """
        ),
        {"uid": user_id},
    )
    return [
        CreditLot(
            lot_id=int(row["id"]),
            source=str(row["source"]),
            remaining_credits=int(row["remaining_credits"]),
            expires_at=row["expires_at"],
        )
        for row in result.mappings().all()
    ]


async def _sync_cached_wallet_balance(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        text(
            """
            UPDATE learner_profiles
            SET credits = COALESCE(
                (SELECT SUM(remaining_credits) FROM credit_lots WHERE user_id = :uid),
                0
            )
            WHERE user_id = :uid
            RETURNING credits
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    if row is None:
        raise KeyError(user_id)
    return int(row["credits"])


async def _spend_wallet_credits(
    session: AsyncSession,
    *,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: str | None = None,
) -> tuple[bool, bool]:
    """Apply one wallet debit without committing.

    Returns `(allowed, newly_charged)`. The profile row serializes all wallet
    decisions for a learner. A single debit event may draw from several lots,
    which `credit_lot_spends` records for a precise later refund.
    """
    if amount < 0:
        raise ValueError("credit_amount_must_not_be_negative")
    profile = await _lock_wallet_profile(session, user_id)
    if profile is None:
        return False, False
    if bool(profile["demo_unlimited"]):
        return True, False
    if idempotency_key:
        existing = await session.execute(
            text(
                """
                SELECT delta, reason
                FROM credit_transactions
                WHERE user_id = :uid AND idempotency_key = :key
                """
            ),
            {"uid": user_id, "key": idempotency_key},
        )
        row = existing.mappings().first()
        if row is not None:
            if int(row["delta"]) != -amount or str(row["reason"]) != reason:
                raise ValueError("credit_idempotency_key_reused_with_different_payload")
            return True, False
    if amount == 0:
        return True, False
    await _ensure_legacy_credit_lot(session, user_id)
    await _expire_wallet_lots(session, user_id)
    lots = await _wallet_lots_for_update(session, user_id)
    allocations = allocate_spend(
        lots,
        amount=amount,
        now=datetime.now(timezone.utc),
    )
    if allocations is None:
        await _sync_cached_wallet_balance(session, user_id)
        return False, False
    inserted = await session.execute(
        text(
            """
            INSERT INTO credit_transactions (user_id, delta, reason, idempotency_key)
            VALUES (:uid, :delta, :reason, :key)
            RETURNING id
            """
        ),
        {
            "uid": user_id,
            "delta": -amount,
            "reason": reason,
            "key": idempotency_key,
        },
    )
    transaction_id = int(inserted.scalar_one())
    for lot_id, debit in allocations:
        updated = await session.execute(
            text(
                """
                UPDATE credit_lots
                SET remaining_credits = remaining_credits - :amount
                WHERE id = :lot_id
                  AND remaining_credits >= :amount
                """
            ),
            {"lot_id": lot_id, "amount": debit},
        )
        if updated.rowcount != 1:
            raise RuntimeError("credit_lot_balance_changed_during_locked_debit")
        await session.execute(
            text(
                """
                INSERT INTO credit_lot_spends (transaction_id, lot_id, amount)
                VALUES (:transaction_id, :lot_id, :amount)
                """
            ),
            {
                "transaction_id": transaction_id,
                "lot_id": lot_id,
                "amount": debit,
            },
        )
    await _sync_cached_wallet_balance(session, user_id)
    return True, True


async def _grant_credit_lot(
    session: AsyncSession,
    *,
    user_id: str,
    amount: int,
    reason: str,
    source: str,
    grant_key: str,
    expires_at: datetime | None = None,
) -> bool:
    """Create one idempotent lot and matching grant ledger entry, no commit."""
    if amount < 0:
        raise ValueError("grant_amount_must_not_be_negative")
    profile = await _lock_wallet_profile(session, user_id)
    if profile is None:
        raise KeyError(user_id)
    await _ensure_legacy_credit_lot(session, user_id)
    result = await session.execute(
        text(
            """
            INSERT INTO credit_lots (
                user_id, source, grant_key, original_credits, remaining_credits, expires_at
            )
            VALUES (:uid, :source, :grant_key, :amount, :amount, :expires_at)
            ON CONFLICT (user_id, grant_key) DO NOTHING
            RETURNING id
            """
        ),
        {
            "uid": user_id,
            "source": source,
            "grant_key": grant_key,
            "amount": amount,
            "expires_at": expires_at,
        },
    )
    if result.scalar_one_or_none() is None:
        return False
    await session.execute(
        text(
            """
            INSERT INTO credit_transactions (user_id, delta, reason, idempotency_key)
            VALUES (:uid, :delta, :reason, :key)
            """
        ),
        {
            "uid": user_id,
            "delta": amount,
            "reason": reason,
            "key": f"grant:{grant_key}",
        },
    )
    await _sync_cached_wallet_balance(session, user_id)
    return True


async def _restore_wallet_debit_allocations(
    session: AsyncSession,
    *,
    user_id: str,
    transaction_id: int,
    amount: int,
) -> None:
    """Restore a debit's original lots or issue recovery credit if they expired."""
    allocations = await session.execute(
        text(
            """
            SELECT lot_id, amount
            FROM credit_lot_spends
            WHERE transaction_id = :transaction_id
            ORDER BY lot_id
            FOR UPDATE
            """
        ),
        {"transaction_id": transaction_id},
    )
    rows = list(allocations.mappings().all())
    allocation_total = sum(int(row["amount"]) for row in rows)
    restored_amount = 0
    for row in rows:
        debit = int(row["amount"])
        updated = await session.execute(
            text(
                """
                UPDATE credit_lots
                SET remaining_credits = LEAST(
                    original_credits,
                    remaining_credits + :amount
                )
                WHERE id = :lot_id
                  AND (expires_at IS NULL OR expires_at > now())
                """
            ),
            {"lot_id": row["lot_id"], "amount": debit},
        )
        if updated.rowcount == 1:
            restored_amount += debit
    recovery_amount = recovery_credit_amount(
        amount=amount,
        allocation_total=allocation_total,
        restored_amount=restored_amount,
    )
    if recovery_amount:
        await session.execute(
            text(
                """
                INSERT INTO credit_lots (
                    user_id, source, grant_key, original_credits, remaining_credits
                )
                VALUES (:uid, 'promo', :grant_key, :amount, :amount)
                ON CONFLICT (user_id, grant_key) DO NOTHING
                """
            ),
            {
                "uid": user_id,
                "grant_key": f"refund:{transaction_id}",
                "amount": recovery_amount,
            },
        )
    await _sync_cached_wallet_balance(session, user_id)


async def deduct_credit(
    session: AsyncSession, user_id: str, amount: int, reason: str
) -> bool:
    """Spend from expiring lots first, preserving paid credit where possible."""
    try:
        allowed, _charged = await _spend_wallet_credits(
            session,
            user_id=user_id,
            amount=amount,
            reason=reason,
        )
        if not allowed:
            await session.rollback()
            return False
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def deduct_credit_once(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: str,
) -> bool:
    """Atomically debit one metered action at most once per user/key."""
    try:
        allowed, _charged = await _spend_wallet_credits(
            session,
            user_id=user_id,
            amount=amount,
            reason=reason,
            idempotency_key=idempotency_key,
        )
        if not allowed:
            await session.rollback()
            return False
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def refund_idempotent_charge(
    session: AsyncSession,
    user_id: str,
    amount: int,
    idempotency_key: str,
    reason: str = "refund",
) -> bool:
    """Reverse one keyed debit, preserving a net-zero audit trail for retries."""
    try:
        profile = await _lock_wallet_profile(session, user_id)
        if profile is None:
            await session.rollback()
            return False
        released = await session.execute(
            text(
                """
                UPDATE credit_transactions
                SET idempotency_key = NULL
                WHERE user_id = :uid
                  AND idempotency_key = :key
                  AND delta = :delta
                RETURNING id
                """
            ),
            {"uid": user_id, "key": idempotency_key, "delta": -amount},
        )
        transaction_id = released.scalar_one_or_none()
        if transaction_id is None:
            await session.rollback()
            return False
        await _restore_wallet_debit_allocations(
            session,
            user_id=user_id,
            transaction_id=int(transaction_id),
            amount=amount,
        )
        await session.execute(
            text(
                "INSERT INTO credit_transactions (user_id, delta, reason) "
                "VALUES (:uid, :amt, :reason)"
            ),
            {"uid": user_id, "amt": amount, "reason": reason},
        )
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def charge_and_unlock(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    scope: str,
    ref_id: str,
) -> tuple[bool, bool]:
    """Deduct credits AND insert a content_unlocks row in ONE transaction.

    Atomic combination of deduct_credit + add_unlock: the credit debit, the
    ledger row, and the unlock insert all land under a single commit(), so a
    learner can never pay without the unlock being recorded. If the unlock
    insert raises, the whole transaction rolls back and credits are NOT
    deducted. Mirrors deduct_credit semantics: the demo bypass returns True
    without charging, and the atomic balance guard (credits >= :amt) returns
    False on insufficient funds without a partial write.
    """
    try:
        # Insert the unlock FIRST and let ON CONFLICT arbitrate idempotency: an
        # already-owned (user, scope, ref) inserts 0 rows, so only a FRESH unlock
        # (rowcount == 1) is charged. Under Postgres a concurrent ON CONFLICT
        # insert of the same key blocks on the uncommitted row, so two
        # simultaneous starts for the same module serialize — the loser sees
        # rowcount == 0 and returns True WITHOUT a second debit. This closes the
        # check-then-charge TOCTOU race at the store level rather than trusting
        # the gate's has_unlock read to be race-free.
        unlock_result = await session.execute(
            text(
                "INSERT INTO content_unlocks (user_id, scope, ref_id, credits_spent) "
                "VALUES (:u, :s, :r, :c) "
                "ON CONFLICT (user_id, scope, ref_id) DO NOTHING"
            ),
            {"u": user_id, "s": scope, "r": ref_id, "c": amount},
        )
        if unlock_result.rowcount == 0:
            # Already owned: the unique unlock is the durable entitlement.
            await session.commit()
            return True, False
        allowed, charged = await _spend_wallet_credits(
            session,
            user_id=user_id,
            amount=amount,
            reason=reason,
        )
        if not allowed:
            await session.rollback()
            return False, False
        await session.commit()
        return True, charged
    except Exception:
        # Any failure mid-transaction rolls back the whole unit: no debit, no
        # ledger row, no unlock.
        await session.rollback()
        raise


# ---------- sessions ----------

async def create_session(
    session: AsyncSession,
    session_id: str,
    user_id: str,
    task_type: str,
    module_id: str,
    node_id: str,
    test_mode: bool = False,
    career_context: dict | None = None,
    scenario_config: dict | None = None,
    persona_roster: list | None = None,
    context_hash: str = "default",
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO sessions (
                session_id, user_id, competency_node, task_type, module_id,
                test_mode, career_context, scenario_config, persona_roster,
                context_hash
            )
            VALUES (
                :sid, :uid, :node, :task_type, :module_id, :test_mode,
                CAST(:career_context AS jsonb), CAST(:scenario_config AS jsonb),
                CAST(:persona_roster AS jsonb), :context_hash
            )
            ON CONFLICT (session_id) DO NOTHING
            """
        ),
        {
            "sid": session_id,
            "uid": user_id,
            "node": node_id,
            "task_type": task_type,
            "module_id": module_id,
            "test_mode": bool(test_mode),
            "career_context": json.dumps(career_context or {}),
            "scenario_config": json.dumps(scenario_config or {}),
            "persona_roster": json.dumps(persona_roster or []),
            "context_hash": context_hash or "default",
        },
    )
    await session.commit()


async def begin_start_request(
    session: AsyncSession,
    user_id: str,
    client_start_id: str,
    request_hash: str,
    source_session_id: str | None = None,
    source_transition_id: str | None = None,
) -> dict:
    if source_session_id and source_transition_id:
        source_key = f"{source_session_id}:{source_transition_id}"
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:source_key)::bigint)"),
            {"source_key": source_key},
        )
        await session.execute(
            text(
                """
                UPDATE session_start_requests
                SET status = 'failed',
                    error_code = 'stale_in_progress',
                    updated_at = now()
                WHERE source_session_id = :source_session_id
                  AND source_transition_id = :source_transition_id
                  AND status = 'in_progress'
                  AND updated_at < now() - make_interval(secs => :stale_seconds)
                """
            ),
            {
                "source_session_id": source_session_id,
                "source_transition_id": source_transition_id,
                "stale_seconds": _REQUEST_STALE_SECONDS,
            },
        )
        consumed = await session.execute(
            text(
                """
                SELECT user_id, client_start_id, request_hash, status, session_id,
                       response_json, error_code, source_session_id, source_transition_id,
                       claim_generation,
                       created_at, updated_at
                FROM session_start_requests
                WHERE source_session_id = :source_session_id
                  AND source_transition_id = :source_transition_id
                  AND status IN ('in_progress', 'completed')
                  AND NOT (user_id = :uid AND client_start_id = :client_start_id)
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "source_session_id": source_session_id,
                "source_transition_id": source_transition_id,
            },
        )
        consumed_row = consumed.mappings().first()
        if consumed_row:
            await session.rollback()
            data = dict(consumed_row)
            response_json = data.get("response_json")
            if isinstance(response_json, str):
                try:
                    data["response_json"] = json.loads(response_json)
                except json.JSONDecodeError:
                    data["response_json"] = None
            data["accepted"] = False
            data["request_mismatch"] = False
            data["consumed_status"] = data.get("status")
            data["status"] = "source_transition_consumed"
            data["accepted_client_start_id"] = data.get("client_start_id")
            return data

    result = await session.execute(
        text(
            """
            INSERT INTO session_start_requests (
                user_id, client_start_id, request_hash, status,
                source_session_id, source_transition_id
            )
            VALUES (
                :uid, :client_start_id, :request_hash, 'in_progress',
                :source_session_id, :source_transition_id
            )
            ON CONFLICT (user_id, client_start_id) DO NOTHING
            RETURNING user_id, client_start_id, request_hash, status, session_id,
                      response_json, error_code, source_session_id, source_transition_id,
                      claim_generation,
                      created_at, updated_at
            """
        ),
        {
            "uid": user_id,
            "client_start_id": client_start_id,
            "request_hash": request_hash,
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
        },
    )
    inserted = result.mappings().first()
    if inserted:
        await session.commit()
        row = dict(inserted)
        row["accepted"] = True
        row["request_mismatch"] = False
        return row

    existing_result = await session.execute(
        text(
            """
            SELECT user_id, client_start_id, request_hash, status, session_id,
                   response_json, error_code, source_session_id, source_transition_id,
                   claim_generation,
                   created_at, updated_at
            FROM session_start_requests
            WHERE user_id = :uid AND client_start_id = :client_start_id
            """
        ),
        {"uid": user_id, "client_start_id": client_start_id},
    )
    existing = existing_result.mappings().first()
    row = dict(existing or {})
    row["accepted"] = False
    row["request_mismatch"] = bool(row) and row.get("request_hash") != request_hash
    response_json = row.get("response_json")
    if isinstance(response_json, str):
        try:
            row["response_json"] = json.loads(response_json)
        except json.JSONDecodeError:
            row["response_json"] = None
    return row


async def get_start_request(
    session: AsyncSession,
    user_id: str,
    client_start_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT user_id, client_start_id, request_hash, status, session_id,
                   response_json, error_code, source_session_id, source_transition_id,
                   claim_generation,
                   created_at, updated_at
            FROM session_start_requests
            WHERE user_id = :uid AND client_start_id = :client_start_id
            """
        ),
        {"uid": user_id, "client_start_id": client_start_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    if row.get("status") == "in_progress":
        stale = await session.execute(
            text(
                """
                UPDATE session_start_requests
                SET status = 'failed',
                    error_code = 'stale_in_progress',
                    updated_at = now()
                WHERE user_id = :uid
                  AND client_start_id = :client_start_id
                  AND status = 'in_progress'
                  AND updated_at < now() - make_interval(secs => :stale_seconds)
                RETURNING user_id, client_start_id, request_hash, status, session_id,
                          response_json, error_code, source_session_id, source_transition_id,
                          claim_generation,
                          created_at, updated_at
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "stale_seconds": _REQUEST_STALE_SECONDS,
            },
        )
        stale_row = stale.mappings().first()
        if stale_row:
            await session.commit()
            row = stale_row
    data = dict(row)
    response_json = data.get("response_json")
    if isinstance(response_json, str):
        try:
            data["response_json"] = json.loads(response_json)
        except json.JSONDecodeError:
            data["response_json"] = None
    return data


async def get_start_request_for_source_transition(
    session: AsyncSession,
    source_session_id: str,
    source_transition_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT user_id, client_start_id, request_hash, status, session_id,
                   response_json, error_code, source_session_id, source_transition_id,
                   claim_generation,
                   created_at, updated_at
            FROM session_start_requests
            WHERE source_session_id = :source_session_id
              AND source_transition_id = :source_transition_id
              AND status IN ('in_progress', 'completed')
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
        },
    )
    row = result.mappings().first()
    if not row:
        return None
    data = dict(row)
    response_json = data.get("response_json")
    if isinstance(response_json, str):
        try:
            data["response_json"] = json.loads(response_json)
        except json.JSONDecodeError:
            data["response_json"] = None
    return data


async def reset_start_request(
    session: AsyncSession,
    user_id: str,
    client_start_id: str,
    request_hash: str,
    source_session_id: str | None = None,
    source_transition_id: str | None = None,
) -> dict:
    if source_session_id and source_transition_id:
        source_key = f"{source_session_id}:{source_transition_id}"
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:source_key)::bigint)"),
            {"source_key": source_key},
        )
        await session.execute(
            text(
                """
                UPDATE session_start_requests
                SET status = 'failed',
                    error_code = 'stale_in_progress',
                    updated_at = now()
                WHERE source_session_id = :source_session_id
                  AND source_transition_id = :source_transition_id
                  AND status = 'in_progress'
                  AND updated_at < now() - make_interval(secs => :stale_seconds)
                """
            ),
            {
                "source_session_id": source_session_id,
                "source_transition_id": source_transition_id,
                "stale_seconds": _REQUEST_STALE_SECONDS,
            },
        )
        consumed = await session.execute(
            text(
                """
                SELECT user_id, client_start_id, request_hash, status, session_id,
                       response_json, error_code, source_session_id, source_transition_id,
                       claim_generation, created_at, updated_at
                FROM session_start_requests
                WHERE source_session_id = :source_session_id
                  AND source_transition_id = :source_transition_id
                  AND status IN ('in_progress', 'completed')
                  AND NOT (user_id = :uid AND client_start_id = :client_start_id)
                ORDER BY updated_at DESC
                LIMIT 1
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "source_session_id": source_session_id,
                "source_transition_id": source_transition_id,
            },
        )
        consumed_row = consumed.mappings().first()
        if consumed_row:
            await session.rollback()
            data = dict(consumed_row)
            response_json = data.get("response_json")
            if isinstance(response_json, str):
                try:
                    data["response_json"] = json.loads(response_json)
                except json.JSONDecodeError:
                    data["response_json"] = None
            data["accepted"] = False
            data["request_mismatch"] = False
            data["consumed_status"] = data.get("status")
            data["status"] = "source_transition_consumed"
            data["accepted_client_start_id"] = data.get("client_start_id")
            return data

    lock_key = f"{user_id}:{client_start_id}"
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
        {"lock_key": lock_key},
    )
    result = await session.execute(
        text(
            """
            UPDATE session_start_requests
            SET request_hash = :request_hash,
                status = 'in_progress',
                session_id = NULL,
                response_json = NULL,
                error_code = NULL,
                source_session_id = :source_session_id,
                source_transition_id = :source_transition_id,
                claim_generation = claim_generation + 1,
                updated_at = now()
            WHERE user_id = :uid
              AND client_start_id = :client_start_id
              AND status = 'failed'
            RETURNING user_id, client_start_id, request_hash, status, session_id,
                      response_json, error_code, source_session_id, source_transition_id,
                      claim_generation,
                      created_at, updated_at
            """
        ),
        {
            "uid": user_id,
            "client_start_id": client_start_id,
            "request_hash": request_hash,
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
        },
    )
    row = result.mappings().first()
    if row is None:
        existing = await session.execute(
            text(
                """
                SELECT user_id, client_start_id, request_hash, status, session_id,
                       response_json, error_code, source_session_id, source_transition_id,
                       claim_generation,
                       created_at, updated_at
                FROM session_start_requests
                WHERE user_id = :uid AND client_start_id = :client_start_id
                """
            ),
            {"uid": user_id, "client_start_id": client_start_id},
        )
        row = existing.mappings().first()
    await session.commit()
    data = dict(row or {})
    data["accepted"] = bool(data) and data.get("status") == "in_progress" and data.get("updated_at") is not None and result.rowcount == 1
    data["request_mismatch"] = bool(data) and data.get("request_hash") != request_hash
    return data


async def complete_start_request(
    session: AsyncSession,
    user_id: str,
    client_start_id: str,
    status: str,
    session_id: str | None = None,
    response_json: dict | None = None,
    error_code: str | None = None,
    claim_generation: int = 1,
) -> bool:
    result = await session.execute(
        text(
            """
            UPDATE session_start_requests
            SET status = :status,
                session_id = :session_id,
                response_json = CAST(:response_json AS jsonb),
                error_code = :error_code,
                updated_at = now()
            WHERE user_id = :uid
              AND client_start_id = :client_start_id
              AND claim_generation = :claim_generation
              AND status = 'in_progress'
            RETURNING claim_generation
            """
        ),
        {
            "uid": user_id,
            "client_start_id": client_start_id,
            "status": status,
            "session_id": session_id,
            "response_json": json.dumps(response_json or {}),
            "error_code": error_code,
            "claim_generation": claim_generation,
        },
    )
    await session.commit()
    return result.mappings().first() is not None


async def renew_start_request_claim(
    session: AsyncSession,
    user_id: str,
    client_start_id: str,
    claim_generation: int,
) -> bool:
    result = await session.execute(
        text(
            """
            UPDATE session_start_requests
            SET updated_at = now()
            WHERE user_id = :uid
              AND client_start_id = :client_start_id
              AND claim_generation = :claim_generation
              AND status = 'in_progress'
            RETURNING claim_generation
            """
        ),
        {
            "uid": user_id,
            "client_start_id": client_start_id,
            "claim_generation": claim_generation,
        },
    )
    await session.commit()
    return result.mappings().first() is not None


async def commit_claimed_session_start(
    session: AsyncSession,
    *,
    user_id: str,
    client_start_id: str,
    claim_generation: int,
    session_record: dict,
    runtime_record: dict,
    messages: list[dict],
    response_json: dict,
) -> bool:
    """Publish a prepared session and complete its start latch in one transaction."""
    try:
        owned = await session.execute(
            text(
                """
                SELECT claim_generation
                FROM session_start_requests
                WHERE user_id = :uid
                  AND client_start_id = :client_start_id
                  AND claim_generation = :claim_generation
                  AND status = 'in_progress'
                FOR UPDATE
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "claim_generation": claim_generation,
            },
        )
        if owned.first() is None:
            await session.rollback()
            return False

        session_id = str(session_record["session_id"])
        await session.execute(
            text(
                """
                INSERT INTO sessions (
                    session_id, user_id, competency_node, task_type, module_id,
                    test_mode, career_context, scenario_config, persona_roster,
                    context_hash
                )
                VALUES (
                    :sid, :uid, :node, :task_type, :module_id, :test_mode,
                    CAST(:career_context AS jsonb), CAST(:scenario_config AS jsonb),
                    CAST(:persona_roster AS jsonb), :context_hash
                )
                ON CONFLICT (session_id) DO NOTHING
                """
            ),
            {
                "sid": session_id,
                "uid": user_id,
                "node": session_record["node_id"],
                "task_type": session_record["task_type"],
                "module_id": session_record["module_id"],
                "test_mode": bool(session_record.get("test_mode")),
                "career_context": json.dumps(session_record.get("career_context") or {}),
                "scenario_config": json.dumps(session_record.get("scenario_config") or {}),
                "persona_roster": json.dumps(session_record.get("persona_roster") or []),
                "context_hash": session_record.get("context_hash") or "default",
            },
        )
        await session.execute(
            text(
                """
                INSERT INTO session_runtime (
                    session_id, user_id, current_node, module_id, task_type,
                    test_mode, status, state_snapshot, pending_transition,
                    session_version, active_turn_id, active_opening_id, last_error,
                    lease_expires_at, updated_at
                )
                VALUES (
                    :sid, :uid, :node, :module_id, :task_type, :test_mode,
                    :status, CAST(:snapshot AS jsonb), CAST(:pending AS jsonb),
                    :version, :active_turn_id, :active_opening_id,
                    CAST(:last_error AS jsonb), NULL, now()
                )
                ON CONFLICT (session_id) DO UPDATE SET
                    user_id = EXCLUDED.user_id,
                    current_node = EXCLUDED.current_node,
                    module_id = EXCLUDED.module_id,
                    task_type = EXCLUDED.task_type,
                    test_mode = EXCLUDED.test_mode,
                    status = EXCLUDED.status,
                    state_snapshot = EXCLUDED.state_snapshot,
                    pending_transition = EXCLUDED.pending_transition,
                    session_version = EXCLUDED.session_version,
                    active_turn_id = EXCLUDED.active_turn_id,
                    active_opening_id = EXCLUDED.active_opening_id,
                    last_error = EXCLUDED.last_error,
                    lease_expires_at = EXCLUDED.lease_expires_at,
                    updated_at = now()
                """
            ),
            {
                "sid": session_id,
                "uid": user_id,
                "node": runtime_record["current_node"],
                "module_id": runtime_record.get("module_id"),
                "task_type": runtime_record.get("task_type"),
                "test_mode": bool(runtime_record.get("test_mode")),
                "status": runtime_record.get("status") or "active",
                "snapshot": json.dumps(runtime_record.get("state_snapshot") or {}),
                "pending": json.dumps(runtime_record.get("pending_transition"))
                if runtime_record.get("pending_transition")
                else None,
                "version": int(runtime_record.get("session_version") or 1),
                "active_turn_id": runtime_record.get("active_turn_id"),
                "active_opening_id": runtime_record.get("active_opening_id"),
                "last_error": json.dumps(runtime_record.get("last_error"))
                if runtime_record.get("last_error")
                else None,
            },
        )
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext('session_messages:' || :sid)::bigint)"),
            {"sid": session_id},
        )
        await session.execute(
            text("DELETE FROM session_messages WHERE session_id = :sid"),
            {"sid": session_id},
        )
        for index, message in enumerate(messages or []):
            await session.execute(
                text(
                    """
                    INSERT INTO session_messages (
                        message_id, session_id, sequence_index, turn_id, transition_id, node_id,
                        role, content, speaker_name, speaker_id, message_kind, status
                    )
                    VALUES (
                        :message_id, :sid, :sequence_index, :turn_id, :transition_id, :node_id,
                        :role, :content, :speaker_name, :speaker_id, :message_kind, :status
                    )
                    ON CONFLICT (message_id) DO UPDATE SET
                        sequence_index = EXCLUDED.sequence_index,
                        turn_id = EXCLUDED.turn_id,
                        transition_id = EXCLUDED.transition_id,
                        node_id = EXCLUDED.node_id,
                        role = EXCLUDED.role,
                        content = EXCLUDED.content,
                        speaker_name = EXCLUDED.speaker_name,
                        speaker_id = EXCLUDED.speaker_id,
                        message_kind = EXCLUDED.message_kind,
                        status = EXCLUDED.status
                    """
                ),
                {
                    "message_id": message.get("message_id") or f"{session_id}:{index}",
                    "sid": session_id,
                    "sequence_index": int(message.get("sequence_index") or index),
                    "turn_id": message.get("turn_id"),
                    "transition_id": message.get("transition_id"),
                    "node_id": message.get("node_id"),
                    "role": message.get("role") or "assistant",
                    "content": message.get("content") or "",
                    "speaker_name": message.get("speaker_name"),
                    "speaker_id": message.get("speaker_id"),
                    "message_kind": message.get("message_kind"),
                    "status": message.get("status") or "committed",
                },
            )
        completed = await session.execute(
            text(
                """
                UPDATE session_start_requests
                SET status = 'completed',
                    session_id = :sid,
                    response_json = CAST(:response_json AS jsonb),
                    error_code = NULL,
                    updated_at = now()
                WHERE user_id = :uid
                  AND client_start_id = :client_start_id
                  AND claim_generation = :claim_generation
                  AND status = 'in_progress'
                RETURNING claim_generation
                """
            ),
            {
                "sid": session_id,
                "uid": user_id,
                "client_start_id": client_start_id,
                "claim_generation": claim_generation,
                "response_json": json.dumps(response_json or {}),
            },
        )
        if completed.first() is None:
            raise RuntimeError("start_claim_lost_during_atomic_commit")
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def compensate_claimed_attempt_charge(
    session: AsyncSession,
    *,
    user_id: str,
    client_start_id: str,
    claim_generation: int,
    amount: int,
    charge_key: str,
    debit_reason: str,
    refund_reason: str,
    error_code: str,
) -> bool:
    """Reverse a failed metered attempt and fail its latch under one claim lock."""
    try:
        owned = await session.execute(
            text(
                """
                SELECT claim_generation
                FROM session_start_requests
                WHERE user_id = :uid
                  AND client_start_id = :client_start_id
                  AND claim_generation = :claim_generation
                  AND status = 'in_progress'
                FOR UPDATE
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "claim_generation": claim_generation,
            },
        )
        if owned.first() is None:
            await session.rollback()
            return False

        profile = await _lock_wallet_profile(session, user_id)
        if profile is None:
            await session.rollback()
            return False

        released = await session.execute(
            text(
                """
                UPDATE credit_transactions
                SET idempotency_key = NULL
                WHERE user_id = :uid
                  AND idempotency_key = :key
                  AND delta = :delta
                  AND reason = :debit_reason
                RETURNING id
                """
            ),
            {
                "uid": user_id,
                "key": charge_key,
                "delta": -amount,
                "debit_reason": debit_reason,
            },
        )
        transaction_id = released.scalar_one_or_none()
        if transaction_id is None:
            raise RuntimeError("claimed_start_charge_missing")
        await _restore_wallet_debit_allocations(
            session,
            user_id=user_id,
            transaction_id=int(transaction_id),
            amount=amount,
        )
        await session.execute(
            text(
                """
                INSERT INTO credit_transactions (user_id, delta, reason)
                VALUES (:uid, :amt, :reason)
                """
            ),
            {"uid": user_id, "amt": amount, "reason": refund_reason},
        )
        failed = await session.execute(
            text(
                """
                UPDATE session_start_requests
                SET status = 'failed',
                    session_id = NULL,
                    response_json = NULL,
                    error_code = :error_code,
                    updated_at = now()
                WHERE user_id = :uid
                  AND client_start_id = :client_start_id
                  AND claim_generation = :claim_generation
                  AND status = 'in_progress'
                RETURNING claim_generation
                """
            ),
            {
                "uid": user_id,
                "client_start_id": client_start_id,
                "claim_generation": claim_generation,
                "error_code": error_code,
            },
        )
        if failed.first() is None:
            raise RuntimeError("start_claim_lost_during_compensation")
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def end_session(
    session: AsyncSession,
    session_id: str,
    turn_count: int,
    final_mastery: float,
    summary: str,
) -> None:
    await session.execute(
        text(
            """
            UPDATE sessions
            SET status = 'ended', ended_at = now(), turn_count = :tc,
                final_mastery = :fm, summary = :sm
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id, "tc": turn_count, "fm": final_mastery, "sm": summary},
    )
    await session.commit()


async def record_turn(
    session: AsyncSession,
    session_id: str,
    user_id: str,
    node_id: str,
    score: float,
    on_task: bool = True,
    english: bool = True,
    affect: str = "neutral",
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO turns
                (session_id, user_id, node_id, score, on_task, english, affect, ts)
            VALUES (:sid, :uid, :node, :score, :on_task, :english, :affect, :ts)
            """
        ),
        {
            "sid": session_id,
            "uid": user_id,
            "node": node_id,
            "score": score,
            "on_task": on_task,
            "english": english,
            "affect": affect,
            "ts": time.time(),
        },
    )
    await session.commit()


async def record_turn_evaluation(
    session: AsyncSession,
    *,
    evaluation_id: str,
    session_id: str,
    user_id: str,
    node_id: str,
    turn_id: str | None,
    attempt_index: int,
    attempt_type: str,
    user_answer: str,
    rubric_version: str,
    raw_score: float,
    effective_score: float,
    criteria_json: list | dict,
    blockers: list,
    pass_eligible: bool,
    advance_eligible: bool,
    mastery_eligible: bool,
    tutor_plan_json: dict,
    context_json: dict | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO turn_evaluations
                (evaluation_id, session_id, user_id, node_id, turn_id,
                 attempt_index, attempt_type, user_answer, rubric_version,
                 raw_score, effective_score, criteria_json, blockers,
                 pass_eligible, advance_eligible, mastery_eligible,
                 tutor_plan_json, context_json, model_name, prompt_version)
            VALUES
                (:evaluation_id, :session_id, :user_id, :node_id, :turn_id,
                 :attempt_index, :attempt_type, :user_answer, :rubric_version,
                 :raw_score, :effective_score, CAST(:criteria_json AS jsonb),
                 CAST(:blockers AS jsonb), :pass_eligible, :advance_eligible,
                 :mastery_eligible, CAST(:tutor_plan_json AS jsonb),
                 CAST(:context_json AS jsonb), :model_name, :prompt_version)
            ON CONFLICT (evaluation_id) DO NOTHING
            """
        ),
        {
            "evaluation_id": evaluation_id,
            "session_id": session_id,
            "user_id": user_id,
            "node_id": node_id,
            "turn_id": turn_id,
            "attempt_index": attempt_index,
            "attempt_type": attempt_type,
            "user_answer": user_answer,
            "rubric_version": rubric_version,
            "raw_score": raw_score,
            "effective_score": effective_score,
            "criteria_json": json.dumps(criteria_json or []),
            "blockers": json.dumps(blockers or []),
            "pass_eligible": pass_eligible,
            "advance_eligible": advance_eligible,
            "mastery_eligible": mastery_eligible,
            "tutor_plan_json": json.dumps(tutor_plan_json or {}),
            "context_json": json.dumps(context_json or {}),
            "model_name": model_name,
            "prompt_version": prompt_version,
        },
    )
    await session.commit()


async def get_latest_passing_turn_evaluation(
    session: AsyncSession,
    user_id: str,
    node_id: str,
    attempt_type: str = "independent",
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT evaluation_id, session_id, user_id, node_id, turn_id,
                   attempt_index, attempt_type, user_answer, context_json,
                   effective_score, pass_eligible,
                   blockers, created_at
            FROM turn_evaluations
            WHERE user_id = :uid
              AND node_id = :node
              AND attempt_type = :attempt_type
              AND pass_eligible = TRUE
              AND jsonb_array_length(blockers) = 0
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id, "node": node_id, "attempt_type": attempt_type},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_turns(session: AsyncSession, session_id: str) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT session_id, user_id, node_id, score, on_task, english, affect, ts
            FROM turns
            WHERE session_id = :sid
            ORDER BY id
            """
        ),
        {"sid": session_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def record_learning_event(
    session: AsyncSession,
    *,
    commit: bool = True,
    source_event_key: str,
    user_id: str,
    domain: str,
    task_type: str,
    module_id: str = "",
    session_id: str | None = None,
    node_id: str = "",
    skill_id: str,
    source: str,
    attempt_type: str = "",
    score: float = 0.0,
    confidence: float = 0.0,
    criteria_json: list | dict | None = None,
    evidence_json: dict | None = None,
    blockers: list | None = None,
    gap: str = "",
    scenario_json: dict | None = None,
    caveats: list | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
) -> bool:
    _validate_learning_domain_task(domain, task_type)
    result = await session.execute(
        text(
            """
            INSERT INTO learning_events
                (source_event_key, user_id, domain, task_type, module_id,
                 session_id, node_id, skill_id, source, attempt_type, score,
                 confidence, criteria_json, evidence_json, blockers, gap,
                 scenario_json, caveats, model_name, prompt_version)
            VALUES
                (:source_event_key, :user_id, :domain, :task_type, :module_id,
                 :session_id, :node_id, :skill_id, :source, :attempt_type,
                 :score, :confidence, CAST(:criteria_json AS jsonb),
                 CAST(:evidence_json AS jsonb), CAST(:blockers AS jsonb),
                 :gap, CAST(:scenario_json AS jsonb), CAST(:caveats AS jsonb),
                 :model_name, :prompt_version)
            ON CONFLICT (source_event_key) DO NOTHING
            RETURNING source_event_key
            """
        ),
        {
            "source_event_key": source_event_key,
            "user_id": user_id,
            "domain": domain,
            "task_type": task_type,
            "module_id": module_id or "",
            "session_id": session_id,
            "node_id": node_id or "",
            "skill_id": skill_id,
            "source": source,
            "attempt_type": attempt_type or "",
            "score": float(score or 0.0),
            "confidence": float(confidence or 0.0),
            "criteria_json": json.dumps(criteria_json or []),
            "evidence_json": json.dumps(evidence_json or {}),
            "blockers": json.dumps(blockers or []),
            "gap": gap or "",
            "scenario_json": json.dumps(scenario_json or {}),
            "caveats": json.dumps(caveats or []),
            "model_name": model_name,
            "prompt_version": prompt_version,
        },
    )
    inserted = result.scalar_one_or_none() is not None
    if commit:
        await session.commit()
    return inserted


async def upsert_session_report(
    session: AsyncSession,
    *,
    report_id: str,
    session_id: str,
    user_id: str,
    report_type: str,
    task_type: str,
    module_id: str,
    status: str,
    score: float,
    readiness_score: float,
    summary: str,
    strengths_json: list | dict,
    gaps_json: list | dict,
    evidence_json: dict,
    recommended_actions_json: list | dict,
    validity_json: dict,
    public_context_json: dict,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO session_reports
                (report_id, session_id, user_id, report_type, task_type,
                 module_id, status, score, readiness_score, summary,
                 strengths_json, gaps_json, evidence_json,
                 recommended_actions_json, validity_json, public_context_json)
            VALUES
                (:report_id, :session_id, :user_id, :report_type, :task_type,
                 :module_id, :status, :score, :readiness_score, :summary,
                 CAST(:strengths_json AS jsonb), CAST(:gaps_json AS jsonb),
                 CAST(:evidence_json AS jsonb),
                 CAST(:recommended_actions_json AS jsonb),
                 CAST(:validity_json AS jsonb),
                 CAST(:public_context_json AS jsonb))
            ON CONFLICT (session_id) DO UPDATE SET
                status = EXCLUDED.status,
                score = EXCLUDED.score,
                readiness_score = EXCLUDED.readiness_score,
                summary = EXCLUDED.summary,
                strengths_json = EXCLUDED.strengths_json,
                gaps_json = EXCLUDED.gaps_json,
                evidence_json = EXCLUDED.evidence_json,
                recommended_actions_json = EXCLUDED.recommended_actions_json,
                validity_json = EXCLUDED.validity_json,
                public_context_json = EXCLUDED.public_context_json
            """
        ),
        {
            "report_id": report_id,
            "session_id": session_id,
            "user_id": user_id,
            "report_type": report_type,
            "task_type": task_type,
            "module_id": module_id or "",
            "status": status,
            "score": float(score or 0.0),
            "readiness_score": float(readiness_score or 0.0),
            "summary": summary or "",
            "strengths_json": json.dumps(strengths_json or []),
            "gaps_json": json.dumps(gaps_json or []),
            "evidence_json": json.dumps(evidence_json or {}),
            "recommended_actions_json": json.dumps(recommended_actions_json or []),
            "validity_json": json.dumps(validity_json or {}),
            "public_context_json": json.dumps(public_context_json or {}),
        },
    )
    await session.commit()


async def upsert_learner_skill_profile(
    session: AsyncSession,
    *,
    commit: bool = True,
    user_id: str,
    domain: str,
    skill_id: str,
    module_id: str,
    task_type: str,
    mastery: float,
    readiness: float,
    confidence: float,
    attempts: int,
    strengths_json: list | dict,
    gaps_json: list | dict,
    evidence_json: dict,
    recommended_next_action: str,
    source_summary: str,
) -> None:
    _validate_learning_domain_task(domain, task_type)
    await session.execute(
        text(
            """
            INSERT INTO learner_skill_profiles
                (user_id, domain, skill_id, module_id, task_type, mastery,
                 readiness, confidence, attempts, strengths_json, gaps_json,
                 evidence_json, recommended_next_action, source_summary)
            VALUES
                (:user_id, :domain, :skill_id, :module_id, :task_type,
                 :mastery, :readiness, :confidence, :attempts,
                 CAST(:strengths_json AS jsonb), CAST(:gaps_json AS jsonb),
                 CAST(:evidence_json AS jsonb), :recommended_next_action,
                 :source_summary)
            ON CONFLICT (user_id, domain, skill_id) DO UPDATE SET
                module_id = EXCLUDED.module_id,
                task_type = EXCLUDED.task_type,
                mastery = CASE
                    WHEN EXCLUDED.domain = 'school' THEN EXCLUDED.mastery
                    ELSE GREATEST(learner_skill_profiles.mastery, EXCLUDED.mastery)
                END,
                readiness = EXCLUDED.readiness,
                confidence = EXCLUDED.confidence,
                attempts = GREATEST(learner_skill_profiles.attempts, EXCLUDED.attempts),
                last_seen_at = now(),
                strengths_json = EXCLUDED.strengths_json,
                gaps_json = EXCLUDED.gaps_json,
                evidence_json = EXCLUDED.evidence_json,
                recommended_next_action = EXCLUDED.recommended_next_action,
                source_summary = EXCLUDED.source_summary,
                updated_at = now()
            """
        ),
        {
            "user_id": user_id,
            "domain": domain,
            "skill_id": skill_id,
            "module_id": module_id or "",
            "task_type": task_type or "",
            "mastery": float(mastery or 0.0),
            "readiness": float(readiness or 0.0),
            "confidence": float(confidence or 0.0),
            "attempts": int(attempts or 0),
            "strengths_json": json.dumps(strengths_json or []),
            "gaps_json": json.dumps(gaps_json or []),
            "evidence_json": json.dumps(evidence_json or {}),
            "recommended_next_action": recommended_next_action or "",
            "source_summary": source_summary or "",
        },
    )
    if commit:
        await session.commit()


async def reconcile_school_chapter_certification_projection(
    session: AsyncSession,
    *,
    user_id: str,
    projection_evidence: dict,
) -> list[dict]:
    """Atomically backfill reconciled chapter certifications for School profiles."""

    try:
        await session.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtext('zidd_school_answer:' || :uid))"
            ),
            {"uid": user_id},
        )
        existing_profiles = (
            await session.execute(
                text(
                    """
                    SELECT user_id, domain, skill_id, module_id, task_type,
                           mastery, readiness, confidence, attempts,
                           strengths_json, gaps_json, evidence_json,
                           recommended_next_action, source_summary
                    FROM learner_skill_profiles
                    WHERE user_id = :uid AND domain = 'school'
                    FOR UPDATE
                    """
                ),
                {"uid": user_id},
            )
        ).mappings().all()
        from app.services.school.projection import (
            SchoolAttemptEvidence,
            derive_school_projection_delta,
        )

        profile_upserts = derive_school_projection_delta(
            SchoolAttemptEvidence.from_dict(projection_evidence),
            [dict(profile) for profile in existing_profiles],
        )
        for profile in profile_upserts:
            profile["user_id"] = user_id
            await upsert_learner_skill_profile(session, **profile, commit=False)
        await session.commit()
        return profile_upserts
    except asyncio.CancelledError:
        await finish_cleanup(session.rollback())
        raise
    except Exception:
        await session.rollback()
        raise


async def record_learning_event_and_update_profile(
    session: AsyncSession,
    *,
    event: dict,
    profile: dict,
) -> bool:
    """Persist one prep event and projection using a dedicated store session."""
    try:
        inserted = await record_learning_event(session, commit=False, **event)
        if not inserted:
            return False
        await upsert_learner_skill_profile(session, commit=False, **profile)
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def reconcile_learner_skill_profiles_for_report(
    session: AsyncSession,
    *,
    user_id: str,
    domain: str,
    task_type: str,
    report_id: str,
    profiles: list[dict],
) -> None:
    latest_report = await session.execute(
        text(
            """
            SELECT report_id
            FROM session_reports
            WHERE user_id = :uid
              AND task_type = :task_type
              AND status NOT IN ('insufficient_evidence', 'invalid_simulation')
            ORDER BY created_at DESC, report_id DESC
            LIMIT 1
            """
        ),
        {"uid": user_id, "task_type": task_type},
    )
    if str(latest_report.scalar_one_or_none() or "") != report_id:
        await session.rollback()
        return
    await session.execute(
        text(
            """
            DELETE FROM learner_skill_profiles
            WHERE user_id = :uid
              AND domain = :domain
              AND task_type = :task_type
              AND LEFT(skill_id, char_length(:legacy_prefix)) = :legacy_prefix
            """
        ),
        {
            "uid": user_id,
            "domain": domain,
            "task_type": task_type,
            "legacy_prefix": f"{task_type}:",
        },
    )
    if profiles:
        statement = text(
            """
            INSERT INTO learner_skill_profiles
                (user_id, domain, skill_id, module_id, task_type, mastery,
                 readiness, confidence, attempts, strengths_json, gaps_json,
                 evidence_json, recommended_next_action, source_summary)
            VALUES
                (:user_id, :domain, :skill_id, :module_id, :task_type,
                 :mastery, :readiness, :confidence, :attempts,
                 CAST(:strengths_json AS jsonb), CAST(:gaps_json AS jsonb),
                 CAST(:evidence_json AS jsonb), :recommended_next_action,
                 :source_summary)
            ON CONFLICT (user_id, domain, skill_id) DO UPDATE SET
                module_id = EXCLUDED.module_id,
                task_type = EXCLUDED.task_type,
                mastery = GREATEST(learner_skill_profiles.mastery, EXCLUDED.mastery),
                readiness = EXCLUDED.readiness,
                confidence = EXCLUDED.confidence,
                attempts = CASE
                    WHEN learner_skill_profiles.evidence_json->>'latest_report' = :report_id
                    THEN learner_skill_profiles.attempts
                    ELSE GREATEST(learner_skill_profiles.attempts + 1, EXCLUDED.attempts)
                END,
                last_seen_at = now(),
                strengths_json = EXCLUDED.strengths_json,
                gaps_json = EXCLUDED.gaps_json,
                evidence_json = EXCLUDED.evidence_json,
                recommended_next_action = EXCLUDED.recommended_next_action,
                source_summary = EXCLUDED.source_summary,
                updated_at = now()
            """
        )
        params = [
            {
                "user_id": user_id,
                "domain": domain,
                "skill_id": str(profile.get("skill_id") or ""),
                "module_id": str(profile.get("module_id") or ""),
                "task_type": task_type,
                "report_id": report_id,
                "mastery": float(profile.get("mastery") or 0.0),
                "readiness": float(profile.get("readiness") or 0.0),
                "confidence": float(profile.get("confidence") or 0.0),
                "attempts": int(profile.get("attempts") or 0),
                "strengths_json": json.dumps(profile.get("strengths_json") or []),
                "gaps_json": json.dumps(profile.get("gaps_json") or []),
                "evidence_json": json.dumps(profile.get("evidence_json") or {}),
                "recommended_next_action": str(profile.get("recommended_next_action") or ""),
                "source_summary": str(profile.get("source_summary") or ""),
            }
            for profile in profiles
        ]
        await session.execute(statement, params)
    await session.commit()


async def replace_learner_skill_profiles_for_task(
    session: AsyncSession,
    **kwargs,
) -> None:
    """Backward-compatible alias for report reconciliation."""
    await reconcile_learner_skill_profiles_for_report(session, **kwargs)


async def get_learning_graph(session: AsyncSession, user_id: str) -> dict:
    """Return the Career learning graph; School has an explicit separate reader."""

    profiles = await session.execute(
        text(
            """
            SELECT user_id, domain, skill_id, module_id, task_type, mastery,
                   readiness, confidence, attempts, last_seen_at, strengths_json,
                   gaps_json, evidence_json, recommended_next_action, source_summary
            FROM learner_skill_profiles
            WHERE user_id = :uid AND domain = 'career'
            ORDER BY readiness ASC, last_seen_at DESC
            """
        ),
        {"uid": user_id},
    )
    reports = await session.execute(
        text(
            """
            SELECT report_id, session_id, report_type, task_type, module_id,
                   status, score, readiness_score, summary, strengths_json,
                   gaps_json, evidence_json, recommended_actions_json,
                   validity_json, public_context_json, created_at
            FROM session_reports
            WHERE user_id = :uid
            ORDER BY created_at DESC
            LIMIT 20
            """
        ),
        {"uid": user_id},
    )
    events = await session.execute(
        text(
            f"""
            SELECT source_event_key, domain, task_type, module_id, session_id,
                   node_id, skill_id, source, attempt_type, score, confidence,
                   jsonb_strip_nulls(jsonb_build_object(
                       'criteria', CASE
                           WHEN skill_id = 'int_03_weakness_framing'
                           THEN evidence_json->'criteria'
                           ELSE NULL
                       END,
                       'answer_excerpt', evidence_json->'answer_excerpt',
                       'latest_quote', COALESCE(
                           evidence_json->>'latest_quote',
                           (
                               SELECT criterion.value->>'evidence_quote'
                               FROM jsonb_array_elements(
                                   COALESCE(evidence_json->'criteria', '[]'::jsonb)
                               ) WITH ORDINALITY AS criterion(value, ordinality)
                               WHERE criterion.value->>'met' = 'true'
                                 AND NULLIF(BTRIM(criterion.value->>'evidence_quote'), '') IS NOT NULL
                                 AND POSITION(
                                     BTRIM(REGEXP_REPLACE(
                                         REGEXP_REPLACE(
                                             LOWER(criterion.value->>'evidence_quote'),
                                             '[^a-z0-9[:space:]]', ' ', 'g'
                                         ),
                                         '[[:space:]]+', ' ', 'g'
                                     ))
                                     IN BTRIM(REGEXP_REPLACE(
                                         REGEXP_REPLACE(
                                             LOWER(COALESCE(evidence_json->>'answer_excerpt', '')),
                                             '[^a-z0-9[:space:]]', ' ', 'g'
                                         ),
                                         '[[:space:]]+', ' ', 'g'
                                     ))
                                 ) > 0
                               ORDER BY CASE COALESCE(
                                   criterion.value->>'id',
                                   criterion.value->>'criterion_id'
                               )
                                   WHEN 'result' THEN 0
                                   WHEN 'progress_evidence' THEN 1
                                   WHEN 'quantified_before_after' THEN 2
                                   WHEN 'impact_signal' THEN 3
                                   WHEN 'impact_claim' THEN 4
                                   WHEN 'learner_contribution' THEN 5
                                   WHEN 'learner_action' THEN 6
                                   WHEN 'actions' THEN 7
                                   WHEN 'specific_evidence' THEN 8
                                   WHEN 'concrete_evidence' THEN 9
                                   WHEN 'evidence_defense' THEN 10
                                   WHEN 'pressure_response' THEN 11
                                   ELSE 12
                               END, criterion.ordinality
                               LIMIT 1
                           )
                       ),
                       'evidence_quote', evidence_json->'evidence_quote',
                       'gap_status', evidence_json->'gap_status',
                       'pass_eligible', evidence_json->'pass_eligible',
                       'required_missing', evidence_json->'required_missing',
                       'blockers', evidence_json->'blockers',
                       'proof', evidence_json->'proof',
                       'recommended_node_id', evidence_json->'recommended_node_id'
                   )) AS evidence_json,
                   gap, caveats, occurred_at
            FROM learning_events
            WHERE user_id = :uid AND domain = 'career'
            ORDER BY occurred_at DESC
            LIMIT {CAREER_LEARNING_EVENT_LIMIT}
            """
        ),
        {"uid": user_id},
    )
    progression = await get_progression(session, user_id)
    active_sessions = await get_active_career_session_runtimes(session, user_id)
    return {
        "profiles": [dict(row) for row in profiles.mappings().all()],
        "reports": [dict(row) for row in reports.mappings().all()],
        "events": [dict(row) for row in events.mappings().all()],
        "progression": progression,
        "active_sessions": active_sessions,
    }


async def get_school_learning_graph(session: AsyncSession, user_id: str) -> dict:
    """Return unredacted School evidence without crossing into Career memory."""

    profiles = await session.execute(
        text(
            """
            SELECT user_id, domain, skill_id, module_id, task_type, mastery,
                   readiness, confidence, attempts, last_seen_at, strengths_json,
                   gaps_json, evidence_json, recommended_next_action, source_summary
            FROM learner_skill_profiles
            WHERE user_id = :uid AND domain = 'school'
            ORDER BY readiness ASC, last_seen_at DESC
            """
        ),
        {"uid": user_id},
    )
    events = await session.execute(
        text(
            """
            SELECT source_event_key, domain, task_type, module_id, session_id,
                   node_id, skill_id, source, attempt_type, score, confidence,
                   criteria_json, evidence_json, blockers, gap, scenario_json,
                   caveats, model_name, prompt_version, occurred_at
            FROM learning_events
            WHERE user_id = :uid AND domain = 'school'
            ORDER BY occurred_at DESC
            LIMIT 200
            """
        ),
        {"uid": user_id},
    )
    school_sessions = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, user_id, api_version,
                   flow_type, subject_id, class_no, status, current_stage,
                   linked_session_id::text AS linked_session_id,
                   source_placement_report_id::text AS source_placement_report_id,
                   started_at, updated_at, completed_at
            FROM school_sessions
            WHERE user_id = :uid AND api_version = 'rebuild'
            ORDER BY updated_at DESC
            LIMIT 200
            """
        ),
        {"uid": user_id},
    )
    placement_reports = await session.execute(
        text(
            """
            SELECT report.report_id::text AS report_id, report.user_id,
                   report.profile_version_id::text AS profile_version_id,
                   report.placement_session_id::text AS placement_session_id,
                   report.placement_status, report.subject_id,
                   report.target_class_no, report.evaluated_class_no,
                   report.active_learning_class_no, report.unlock_state,
                   report.blocking_skills_json, report.watchlist_skills_json,
                   report.evidence_summary_json,
                   report.recommended_recap_modules_json,
                   report.learner_summary, report.parent_summary,
                   report.allowed_next_actions_json,
                   report.created_at, report.updated_at
            FROM school_placement_reports AS report
            JOIN school_sessions AS school_session
              ON school_session.session_id = report.placement_session_id
             AND school_session.user_id = report.user_id
            WHERE report.user_id = :uid
              AND school_session.api_version = 'rebuild'
            ORDER BY report.updated_at DESC
            LIMIT 50
            """
        ),
        {"uid": user_id},
    )
    return {
        "profiles": [dict(row) for row in profiles.mappings().all()],
        "reports": [
            _school_placement_report_from_row(dict(row))
            for row in placement_reports.mappings().all()
        ],
        "events": [dict(row) for row in events.mappings().all()],
        "sessions": [dict(row) for row in school_sessions.mappings().all()],
    }


async def get_active_career_session_runtimes(
    session: AsyncSession,
    user_id: str,
) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT DISTINCT ON (module_id, test_mode)
                session_id, current_node, module_id, task_type, test_mode,
                status, pending_transition, updated_at
            FROM session_runtime AS runtime
            WHERE runtime.user_id = :uid
              AND runtime.status = 'active'
              AND runtime.module_id IN ('interview', 'group_discussion')
              AND (runtime.lease_expires_at IS NULL OR runtime.lease_expires_at > now())
              AND runtime.updated_at > now() - interval '7 days'
              AND NOT (
                  runtime.test_mode
                  AND EXISTS (
                      SELECT 1
                      FROM session_reports AS report
                      WHERE report.user_id = runtime.user_id
                        AND report.module_id = runtime.module_id
                        AND report.created_at >= runtime.updated_at
                  )
              )
            ORDER BY module_id, test_mode, updated_at DESC
            """
        ),
        {"uid": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def upsert_session_runtime(
    session: AsyncSession,
    session_id: str,
    user_id: str,
    current_node: str,
    module_id: str | None,
    task_type: str | None,
    test_mode: bool,
    status: str,
    state_snapshot: dict,
    pending_transition: dict | None,
    session_version: int,
    active_turn_id: str | None = None,
    active_opening_id: str | None = None,
    last_error: dict | None = None,
    lease_expires_at: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO session_runtime (
                session_id, user_id, current_node, module_id, task_type,
                test_mode, status, state_snapshot, pending_transition,
                session_version, active_turn_id, active_opening_id, last_error,
                lease_expires_at, updated_at
            )
            VALUES (
                :sid, :uid, :node, :module_id, :task_type, :test_mode,
                :status, CAST(:snapshot AS jsonb), CAST(:pending AS jsonb),
                :version, :active_turn_id, :active_opening_id,
                CAST(:last_error AS jsonb), CAST(:lease_expires_at AS timestamptz),
                now()
            )
            ON CONFLICT (session_id) DO UPDATE SET
                user_id = EXCLUDED.user_id,
                current_node = EXCLUDED.current_node,
                module_id = EXCLUDED.module_id,
                task_type = EXCLUDED.task_type,
                test_mode = EXCLUDED.test_mode,
                status = EXCLUDED.status,
                state_snapshot = EXCLUDED.state_snapshot,
                pending_transition = EXCLUDED.pending_transition,
                session_version = EXCLUDED.session_version,
                active_turn_id = EXCLUDED.active_turn_id,
                active_opening_id = EXCLUDED.active_opening_id,
                last_error = EXCLUDED.last_error,
                lease_expires_at = EXCLUDED.lease_expires_at,
                updated_at = now()
            """
        ),
        {
            "sid": session_id,
            "uid": user_id,
            "node": current_node,
            "module_id": module_id,
            "task_type": task_type,
            "test_mode": bool(test_mode),
            "status": status,
            "snapshot": json.dumps(state_snapshot or {}),
            "pending": json.dumps(pending_transition) if pending_transition else None,
            "version": int(session_version or 1),
            "active_turn_id": active_turn_id,
            "active_opening_id": active_opening_id,
            "last_error": json.dumps(last_error) if last_error else None,
            "lease_expires_at": lease_expires_at,
        },
    )
    await session.commit()


async def get_session_runtime(
    session: AsyncSession, session_id: str
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT
                session_id, user_id, current_node, module_id, task_type,
                test_mode, status, state_snapshot, pending_transition,
                session_version, active_turn_id, active_opening_id, last_error,
                lease_expires_at, updated_at
            FROM session_runtime
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_active_session_runtime_for_node(
    session: AsyncSession,
    user_id: str,
    node_id: str,
    task_type: str,
    test_mode: bool,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT
                session_id, user_id, current_node, module_id, task_type,
                test_mode, status, state_snapshot, pending_transition,
                session_version, active_turn_id, active_opening_id, last_error,
                lease_expires_at, updated_at
            FROM session_runtime
            WHERE user_id = :uid
              AND current_node = :node_id
              AND task_type = :task_type
              AND test_mode = :test_mode
              AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "node_id": node_id,
            "task_type": task_type,
            "test_mode": bool(test_mode),
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_latest_active_session_runtime_for_module(
    session: AsyncSession,
    user_id: str,
    module_id: str,
    test_mode: bool,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT
                session_id, user_id, current_node, module_id, task_type,
                test_mode, status, state_snapshot, pending_transition,
                session_version, active_turn_id, active_opening_id, last_error,
                lease_expires_at, updated_at
            FROM session_runtime
            WHERE user_id = :uid
              AND module_id = :module_id
              AND test_mode = :test_mode
              AND status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "module_id": module_id,
            "test_mode": bool(test_mode),
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def touch_session_runtime(
    session: AsyncSession,
    session_id: str,
    status: str = "active",
    lease_expires_at: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE session_runtime
            SET status = :status,
                lease_expires_at = COALESCE(CAST(:lease_expires_at AS timestamptz), lease_expires_at),
                updated_at = now()
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id, "status": status, "lease_expires_at": lease_expires_at},
    )
    await session.execute(
        text(
            """
            UPDATE sessions
            SET status = :status, last_seen_at = now()
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id, "status": status},
    )
    await session.commit()


async def replace_session_messages(
    session: AsyncSession,
    session_id: str,
    messages: list[dict],
) -> None:
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext('session_messages:' || :sid)::bigint)"),
        {"sid": session_id},
    )
    await session.execute(
        text("DELETE FROM session_messages WHERE session_id = :sid"),
        {"sid": session_id},
    )
    for index, message in enumerate(messages or []):
        await session.execute(
            text(
                """
                INSERT INTO session_messages (
                    message_id, session_id, sequence_index, turn_id, transition_id, node_id,
                    role, content, speaker_name, speaker_id, message_kind, status
                )
                VALUES (
                    :message_id, :sid, :sequence_index, :turn_id, :transition_id, :node_id,
                    :role, :content, :speaker_name, :speaker_id, :message_kind, :status
                )
                ON CONFLICT (message_id) DO UPDATE SET
                    sequence_index = EXCLUDED.sequence_index,
                    turn_id = EXCLUDED.turn_id,
                    transition_id = EXCLUDED.transition_id,
                    node_id = EXCLUDED.node_id,
                    role = EXCLUDED.role,
                    content = EXCLUDED.content,
                    speaker_name = EXCLUDED.speaker_name,
                    speaker_id = EXCLUDED.speaker_id,
                    message_kind = EXCLUDED.message_kind,
                    status = EXCLUDED.status
                """
            ),
            {
                "message_id": message.get("message_id") or f"{session_id}:{index}",
                "sid": session_id,
                "sequence_index": int(message.get("sequence_index") or index),
                "turn_id": message.get("turn_id"),
                "transition_id": message.get("transition_id"),
                "node_id": message.get("node_id"),
                "role": message.get("role") or "assistant",
                "content": message.get("content") or "",
                "speaker_name": message.get("speaker_name"),
                "speaker_id": message.get("speaker_id"),
                "message_kind": message.get("message_kind"),
                "status": message.get("status") or "committed",
            },
        )
    await session.commit()


async def list_session_messages(
    session: AsyncSession, session_id: str
) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT message_id, session_id, sequence_index, turn_id, transition_id, node_id,
                   role, content, speaker_name, speaker_id, message_kind, status, created_at
            FROM session_messages
            WHERE session_id = :sid
            ORDER BY sequence_index
            """
        ),
        {"sid": session_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def begin_turn_request(
    session: AsyncSession,
    session_id: str,
    client_turn_id: str,
    request_hash: str,
    expected_version: int | None,
) -> dict:
    # Serialize turn-latch decisions per session. The unique client_turn_id key
    # handles exact replay, but a double-click/two-tab race often creates two
    # different client_turn_id values for the same rendered session_version. This
    # advisory lock makes the "one accepted turn per version" check atomic across
    # backend workers.
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:sid)::bigint)"),
        {"sid": session_id},
    )
    await session.execute(
        text(
            """
            UPDATE session_turn_requests
            SET status = 'failed',
                error_code = 'stale_in_progress',
                updated_at = now()
            WHERE session_id = :sid
              AND status = 'in_progress'
              AND updated_at < now() - make_interval(secs => :stale_seconds)
            """
        ),
        {"sid": session_id, "stale_seconds": _REQUEST_STALE_SECONDS},
    )

    existing = await session.execute(
        text(
            """
            SELECT status, transcript_delta, done_snapshot, error_code, request_hash
            FROM session_turn_requests
            WHERE session_id = :sid AND client_turn_id = :client_turn_id
            """
        ),
        {"sid": session_id, "client_turn_id": client_turn_id},
    )
    existing_row = existing.mappings().first()
    if existing_row:
        data = dict(existing_row)
        request_mismatch = data.get("request_hash") != request_hash
        if data.get("status") == "failed" and not request_mismatch:
            if expected_version is not None:
                consumed = await session.execute(
                    text(
                        """
                        SELECT client_turn_id, status, transcript_delta, done_snapshot, error_code,
                               EXTRACT(EPOCH FROM (now() - updated_at)) AS age_seconds
                        FROM session_turn_requests
                        WHERE session_id = :sid
                          AND expected_version = :expected_version
                          AND client_turn_id != :client_turn_id
                          AND status IN ('in_progress', 'completed')
                        ORDER BY created_at ASC
                        LIMIT 1
                        """
                    ),
                    {
                        "sid": session_id,
                        "expected_version": expected_version,
                        "client_turn_id": client_turn_id,
                    },
                )
                consumed_row = consumed.mappings().first()
                if consumed_row:
                    await session.rollback()
                    consumed_data = dict(consumed_row)
                    return {
                        "accepted": False,
                        "status": "version_consumed",
                        "accepted_client_turn_id": consumed_data.get("client_turn_id"),
                        "accepted_status": consumed_data.get("status"),
                        "accepted_age_seconds": float(consumed_data.get("age_seconds") or 0.0),
                        "transcript_delta": consumed_data.get("transcript_delta"),
                        "done_snapshot": consumed_data.get("done_snapshot"),
                        "error_code": consumed_data.get("error_code"),
                        "request_mismatch": False,
                    }
            retry = await session.execute(
                text(
                    """
                    UPDATE session_turn_requests
                    SET status = 'in_progress',
                        transcript_delta = '[]'::jsonb,
                        done_snapshot = NULL,
                        error_code = NULL,
                        updated_at = now()
                    WHERE session_id = :sid AND client_turn_id = :client_turn_id
                    RETURNING status, transcript_delta, done_snapshot, error_code
                    """
                ),
                {"sid": session_id, "client_turn_id": client_turn_id},
            )
            await session.commit()
            row = retry.mappings().first()
            return {"accepted": True, **dict(row or {})}
        await session.rollback()
        data["accepted"] = False
        data["request_mismatch"] = request_mismatch
        return data

    if expected_version is not None:
        consumed = await session.execute(
            text(
                """
                SELECT client_turn_id, status, transcript_delta, done_snapshot, error_code,
                       EXTRACT(EPOCH FROM (now() - updated_at)) AS age_seconds
                FROM session_turn_requests
                WHERE session_id = :sid
                  AND expected_version = :expected_version
                  AND client_turn_id != :client_turn_id
                  AND status IN ('in_progress', 'completed')
                ORDER BY created_at ASC
                LIMIT 1
                """
            ),
            {
                "sid": session_id,
                "expected_version": expected_version,
                "client_turn_id": client_turn_id,
            },
        )
        consumed_row = consumed.mappings().first()
        if consumed_row:
            await session.rollback()
            data = dict(consumed_row)
            return {
                "accepted": False,
                "status": "version_consumed",
                "accepted_client_turn_id": data.get("client_turn_id"),
                "accepted_status": data.get("status"),
                "accepted_age_seconds": float(data.get("age_seconds") or 0.0),
                "transcript_delta": data.get("transcript_delta"),
                "done_snapshot": data.get("done_snapshot"),
                "error_code": data.get("error_code"),
                "request_mismatch": False,
            }

    await session.execute(
        text(
            """
            INSERT INTO session_turn_requests (
                session_id, client_turn_id, request_hash, expected_version, status
            )
            VALUES (:sid, :client_turn_id, :request_hash, :expected_version, 'in_progress')
            """
        ),
        {
            "sid": session_id,
            "client_turn_id": client_turn_id,
            "request_hash": request_hash,
            "expected_version": expected_version,
        },
    )
    await session.commit()
    return {
        "accepted": True,
        "status": "in_progress",
        "transcript_delta": [],
        "done_snapshot": None,
        "error_code": None,
    }


async def complete_turn_request(
    session: AsyncSession,
    session_id: str,
    client_turn_id: str,
    status: str,
    transcript_delta: list[dict] | None = None,
    done_snapshot: dict | None = None,
    error_code: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE session_turn_requests
            SET status = :status,
                transcript_delta = CAST(:delta AS jsonb),
                done_snapshot = CAST(:done AS jsonb),
                error_code = :error_code,
                updated_at = now()
            WHERE session_id = :sid AND client_turn_id = :client_turn_id
            """
        ),
        {
            "sid": session_id,
            "client_turn_id": client_turn_id,
            "status": status,
            "delta": json.dumps(transcript_delta or []),
            "done": json.dumps(done_snapshot) if done_snapshot is not None else None,
            "error_code": error_code,
        },
    )
    await session.commit()


async def begin_opening_request(
    session: AsyncSession,
    session_id: str,
    transition_id: str,
) -> dict:
    result = await session.execute(
        text(
            """
            INSERT INTO session_opening_requests (
                session_id, transition_id, status, attempts
            )
            VALUES (:sid, :transition_id, 'in_progress', 1)
            ON CONFLICT (session_id, transition_id) DO NOTHING
            RETURNING status, message_id, attempts, last_error
            """
        ),
        {"sid": session_id, "transition_id": transition_id},
    )
    row = result.mappings().first()
    if row:
        await session.commit()
        return {"accepted": True, **dict(row)}

    existing = await session.execute(
        text(
            """
            SELECT status, message_id, attempts, last_error
            FROM session_opening_requests
            WHERE session_id = :sid AND transition_id = :transition_id
            """
        ),
        {"sid": session_id, "transition_id": transition_id},
    )
    existing_row = existing.mappings().first()
    if not existing_row:
        await session.rollback()
        return {"accepted": False, "status": "missing"}
    existing_data = dict(existing_row)
    if existing_data.get("status") == "in_progress":
        stale_retry = await session.execute(
            text(
                """
                UPDATE session_opening_requests
                SET status = 'in_progress',
                    attempts = attempts + 1,
                    last_error = NULL,
                    updated_at = now()
                WHERE session_id = :sid
                  AND transition_id = :transition_id
                  AND status = 'in_progress'
                  AND updated_at < now() - make_interval(secs => :stale_seconds)
                RETURNING status, message_id, attempts, last_error
                """
            ),
            {
                "sid": session_id,
                "transition_id": transition_id,
                "stale_seconds": _REQUEST_STALE_SECONDS,
            },
        )
        stale_row = stale_retry.mappings().first()
        if stale_row:
            await session.commit()
            return {"accepted": True, **dict(stale_row)}
    if existing_data.get("status") == "failed":
        retry = await session.execute(
            text(
                """
                UPDATE session_opening_requests
                SET status = 'in_progress',
                    attempts = attempts + 1,
                    last_error = NULL,
                    updated_at = now()
                WHERE session_id = :sid AND transition_id = :transition_id
                RETURNING status, message_id, attempts, last_error
                """
            ),
            {"sid": session_id, "transition_id": transition_id},
        )
        await session.commit()
        row = retry.mappings().first()
        return {"accepted": True, **dict(row or {})}
    await session.rollback()
    return {"accepted": False, **existing_data}


async def complete_opening_request(
    session: AsyncSession,
    session_id: str,
    transition_id: str,
    status: str,
    message_id: str | None = None,
    last_error: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            UPDATE session_opening_requests
            SET status = :status,
                message_id = COALESCE(:message_id, message_id),
                last_error = :last_error,
                updated_at = now()
            WHERE session_id = :sid AND transition_id = :transition_id
            """
        ),
        {
            "sid": session_id,
            "transition_id": transition_id,
            "status": status,
            "message_id": message_id,
            "last_error": last_error,
        },
    )
    await session.commit()


async def begin_end_request(session: AsyncSession, session_id: str) -> dict:
    result = await session.execute(
        text(
            """
            INSERT INTO session_end_requests (session_id, status, attempts)
            VALUES (:sid, 'in_progress', 1)
            ON CONFLICT (session_id) DO NOTHING
            RETURNING status, response_json, error_code, attempts
            """
        ),
        {"sid": session_id},
    )
    row = result.mappings().first()
    if row:
        await session.commit()
        return {"accepted": True, **dict(row)}

    existing = await session.execute(
        text(
            """
            SELECT status, response_json, error_code, attempts, updated_at
            FROM session_end_requests
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id},
    )
    existing_row = existing.mappings().first()
    if not existing_row:
        await session.rollback()
        return {"accepted": False, "status": "missing"}
    existing_data = dict(existing_row)
    if existing_data.get("status") == "in_progress":
        stale_retry = await session.execute(
            text(
                """
                UPDATE session_end_requests
                SET status = 'in_progress',
                    attempts = attempts + 1,
                    error_code = NULL,
                    updated_at = now()
                WHERE session_id = :sid
                  AND status = 'in_progress'
                  AND updated_at < now() - make_interval(secs => :stale_seconds)
                RETURNING status, response_json, error_code, attempts
                """
            ),
            {"sid": session_id, "stale_seconds": _REQUEST_STALE_SECONDS},
        )
        stale_row = stale_retry.mappings().first()
        if stale_row:
            await session.commit()
            return {"accepted": True, **dict(stale_row)}
    if existing_data.get("status") == "failed":
        retry = await session.execute(
            text(
                """
                UPDATE session_end_requests
                SET status = 'in_progress',
                    attempts = attempts + 1,
                    response_json = NULL,
                    error_code = NULL,
                    updated_at = now()
                WHERE session_id = :sid
                RETURNING status, response_json, error_code, attempts
                """
            ),
            {"sid": session_id},
        )
        await session.commit()
        row = retry.mappings().first()
        return {"accepted": True, **dict(row or {})}
    await session.rollback()
    existing_data["accepted"] = False
    return existing_data


async def complete_end_request(
    session: AsyncSession,
    session_id: str,
    status: str,
    response_json: dict | None = None,
    error_code: str | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO session_end_requests (
                session_id, status, response_json, error_code, attempts
            )
            VALUES (
                :sid, :status, CAST(:response_json AS jsonb), :error_code, 1
            )
            ON CONFLICT (session_id) DO UPDATE
            SET status = EXCLUDED.status,
                response_json = EXCLUDED.response_json,
                error_code = EXCLUDED.error_code,
                updated_at = now()
            """
        ),
        {
            "sid": session_id,
            "status": status,
            "response_json": json.dumps(response_json) if response_json is not None else None,
            "error_code": error_code,
        },
    )
    await session.commit()


async def get_end_request(session: AsyncSession, session_id: str) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT status, response_json, error_code, attempts, updated_at
            FROM session_end_requests
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


# ---------- competency mastery ----------

async def upsert_mastery(
    session: AsyncSession,
    user_id: str,
    node_id: str,
    mastery: float,
    attempts: int,
    clean_pass: bool,
    node_completed: bool = False,
    node_mastered: bool | None = None,
    display_status: str | None = None,
    best_independent_score: float = 0.0,
    independent_passes: int = 0,
    transfer_passes: int = 0,
    pressure_passes: int = 0,
    scaffold_successes: int = 0,
    last_gap: str = "",
    mastery_evidence: list[str] | None = None,
) -> None:
    mastered = bool(node_mastered) if node_mastered is not None else False
    status = display_status or ("mastered" if mastered else "ready_to_advance" if node_completed else "active")
    await session.execute(
        text(
            """
            INSERT INTO competency_nodes
                (user_id, competency_node, mastery, best_mastery, attempts, clean_pass,
                 node_completed, node_mastered, display_status, best_independent_score,
                 independent_passes, transfer_passes, pressure_passes, scaffold_successes,
                 last_gap, mastery_evidence, completed_at, completion_count, updated_at)
            VALUES
                (:uid, :node, :m, :m, :a, (:cp AND :nc), :nc, :nm, :display_status,
                 :best_independent_score, :independent_passes, :transfer_passes,
                 :pressure_passes, :scaffold_successes, :last_gap,
                 CAST(:mastery_evidence AS jsonb),
                 CASE WHEN :nc THEN now() ELSE NULL END, CASE WHEN :nc THEN 1 ELSE 0 END, now())
            ON CONFLICT (user_id, competency_node) DO UPDATE
            SET mastery = EXCLUDED.mastery,
                best_mastery = GREATEST(competency_nodes.best_mastery, EXCLUDED.best_mastery),
                attempts = EXCLUDED.attempts,
                clean_pass = competency_nodes.clean_pass OR (EXCLUDED.clean_pass AND EXCLUDED.node_completed),
                node_completed = competency_nodes.node_completed OR EXCLUDED.node_completed,
                node_mastered = competency_nodes.node_mastered OR EXCLUDED.node_mastered,
                display_status = CASE
                    WHEN competency_nodes.node_mastered OR EXCLUDED.node_mastered THEN 'mastered'
                    WHEN EXCLUDED.node_completed THEN EXCLUDED.display_status
                    WHEN competency_nodes.node_completed THEN competency_nodes.display_status
                    ELSE EXCLUDED.display_status
                END,
                best_independent_score = GREATEST(
                    competency_nodes.best_independent_score,
                    EXCLUDED.best_independent_score
                ),
                independent_passes = GREATEST(competency_nodes.independent_passes, EXCLUDED.independent_passes),
                transfer_passes = GREATEST(competency_nodes.transfer_passes, EXCLUDED.transfer_passes),
                pressure_passes = GREATEST(competency_nodes.pressure_passes, EXCLUDED.pressure_passes),
                scaffold_successes = GREATEST(competency_nodes.scaffold_successes, EXCLUDED.scaffold_successes),
                last_gap = COALESCE(NULLIF(EXCLUDED.last_gap, ''), competency_nodes.last_gap),
                mastery_evidence = CASE
                    WHEN jsonb_array_length(EXCLUDED.mastery_evidence) > 0 THEN EXCLUDED.mastery_evidence
                    ELSE competency_nodes.mastery_evidence
                END,
                completed_at = CASE
                    WHEN EXCLUDED.node_completed AND competency_nodes.completed_at IS NULL THEN EXCLUDED.completed_at
                    ELSE competency_nodes.completed_at
                END,
                completion_count = competency_nodes.completion_count + CASE
                    WHEN EXCLUDED.node_completed THEN 1 ELSE 0
                END,
                updated_at = now()
            """
        ),
        {
            "uid": user_id,
            "node": node_id,
            "m": mastery,
            "a": attempts,
            "cp": clean_pass,
            "nc": node_completed,
            "nm": mastered,
            "display_status": status,
            "best_independent_score": best_independent_score,
            "independent_passes": independent_passes,
            "transfer_passes": transfer_passes,
            "pressure_passes": pressure_passes,
            "scaffold_successes": scaffold_successes,
            "last_gap": last_gap or "",
            "mastery_evidence": json.dumps(mastery_evidence or []),
        },
    )
    await session.commit()


async def get_last_active_node(session: AsyncSession, user_id: str) -> str | None:
    result = await session.execute(
        text(
            """
            SELECT competency_node
            FROM competency_nodes
            WHERE user_id = :uid
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    row = result.first()
    return row[0] if row else None


async def get_progression(session: AsyncSession, user_id: str) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT competency_node as node_id, mastery as ema, best_mastery as best_ema,
                   attempts, clean_pass, node_completed, completed_at, completion_count,
                   last_completed_session_id, node_mastered, display_status,
                   best_independent_score, independent_passes, transfer_passes,
                   pressure_passes, scaffold_successes, last_gap, mastery_evidence,
                   COALESCE(independent_passes, 0)
                       + COALESCE(transfer_passes, 0)
                       + COALESCE(pressure_passes, 0) AS meaningful_attempts,
                   COALESCE((
                       SELECT (evidence.value->>'score')::double precision
                       FROM jsonb_array_elements(
                           COALESCE(competency_nodes.mastery_evidence, '[]'::jsonb)
                       ) WITH ORDINALITY AS evidence(value, ordinality)
                       WHERE evidence.value ? 'evidence_id'
                       ORDER BY evidence.ordinality DESC
                       LIMIT 1
                   ), mastery) AS readiness_score
            FROM competency_nodes
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_module_passrate(
    session: AsyncSession, user_id: str, node_ids: list[str]
) -> tuple[int, int]:
    """(clean_passes, total_attempted_nodes) for the module's text nodes.

    Pass-rate remediation (architecture-v3): if clean/total < 0.5 the service
    flags the module for a remediation pass.
    """
    result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE clean_pass) AS clean,
                COUNT(*) AS total
            FROM competency_nodes
            WHERE user_id = :uid AND competency_node = ANY(:nodes)
            """
        ),
        {"uid": user_id, "nodes": node_ids},
    )
    row = result.mappings().first()
    if not row:
        return (0, 0)
    return (int(row["clean"] or 0), int(row["total"] or 0))


async def bump_weakness(
    session: AsyncSession,
    user_id: str,
    task_type: str,
    skill_id: str,
    score: float,
    raw: str = "",
) -> None:
    sid = coerce_skill_id(skill_id)
    await session.execute(
        text(
            """
            INSERT INTO weaknesses
                (user_id, task_type, skill_id, hit_count, last_score, last_seen, last_raw)
            VALUES (:uid, :task, :skill, 1, :score, :seen, :raw)
            ON CONFLICT (user_id, task_type, skill_id) DO UPDATE SET
                hit_count = weaknesses.hit_count + 1,
                last_score = EXCLUDED.last_score,
                last_seen = EXCLUDED.last_seen,
                last_raw = EXCLUDED.last_raw
            """
        ),
        {
            "uid": user_id,
            "task": task_type,
            "skill": sid,
            "score": score,
            "seen": time.time(),
            "raw": raw,
        },
    )
    await session.commit()


async def get_weaknesses(
    session: AsyncSession, user_id: str, task_type: str | None = None
) -> list[dict]:
    cutoff = time.time() - _WEAKNESS_RECENCY_SECONDS
    if task_type is None:
        result = await session.execute(
            text(
                """
                SELECT user_id, task_type, skill_id, hit_count, last_score, last_seen, last_raw
                FROM weaknesses
                WHERE user_id = :uid AND last_seen >= :cutoff
                ORDER BY hit_count DESC, last_seen DESC
                LIMIT :limit
                """
            ),
            {"uid": user_id, "cutoff": cutoff, "limit": _WEAKNESS_SURFACE_CAP},
        )
    else:
        result = await session.execute(
            text(
                """
                SELECT user_id, task_type, skill_id, hit_count, last_score, last_seen, last_raw
                FROM weaknesses
                WHERE user_id = :uid AND task_type = :task AND last_seen >= :cutoff
                ORDER BY hit_count DESC, last_seen DESC
                LIMIT :limit
                """
            ),
            {
                "uid": user_id,
                "task": task_type,
                "cutoff": cutoff,
                "limit": _WEAKNESS_SURFACE_CAP,
            },
        )
    return [dict(row) for row in result.mappings().all()]


async def record_assessment_result(
    session: AsyncSession,
    user_id: str,
    test_id: str,
    class_no: int,
    kind: str,
    score: float,
    passed: bool,
    by_skill: list[dict],
) -> None:
    now = time.time()
    weak = sorted(
        item["skill"]
        for item in by_skill
        if int(item.get("total") or 0)
        and int(item.get("correct") or 0) / int(item["total"]) < _SCHOOL_PASS_MARK
    )
    try:
        existing_result = await session.execute(
            text(
                """
                SELECT score, passed, by_skill
                FROM school_results
                WHERE user_id = :uid AND test_id = :test
                """
            ),
            {"uid": user_id, "test": test_id},
        )
        existing = existing_result.mappings().first()
        duplicate_result = False
        if existing is not None:
            existing_by_skill = existing.get("by_skill") or []
            duplicate_result = (
                float(existing.get("score") or 0.0) == float(score)
                and bool(existing.get("passed")) == bool(passed)
                and list(existing_by_skill) == list(by_skill)
            )

        await session.execute(
            text(
                """
                INSERT INTO school_results
                    (user_id, test_id, class_no, kind, score, passed, by_skill, weak_skills, updated_at)
                VALUES (:uid, :test, :class_no, :kind, :score, :passed, CAST(:by_skill AS jsonb), CAST(:weak AS jsonb), :updated)
                ON CONFLICT (user_id, test_id) DO UPDATE SET
                    class_no = EXCLUDED.class_no,
                    kind = EXCLUDED.kind,
                    score = EXCLUDED.score,
                    passed = EXCLUDED.passed,
                    by_skill = EXCLUDED.by_skill,
                    weak_skills = EXCLUDED.weak_skills,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "uid": user_id,
                "test": test_id,
                "class_no": int(class_no),
                "kind": kind,
                "score": float(score),
                "passed": bool(passed),
                "by_skill": json.dumps(by_skill),
                "weak": json.dumps(weak),
                "updated": now,
            },
        )
        if duplicate_result:
            await session.commit()
            return
        for item in by_skill:
            total = int(item.get("total") or 0)
            if total <= 0:
                continue
            ratio = max(0.0, min(1.0, int(item.get("correct") or 0) / total))
            prev_result = await session.execute(
                text(
                    """
                    SELECT ema, attempts
                    FROM school_skill_mastery
                    WHERE user_id = :uid AND skill = :skill
                    """
                ),
                {"uid": user_id, "skill": item["skill"]},
            )
            prev = prev_result.mappings().first()
            if prev is None:
                ema, attempts = ratio, 1
            else:
                old = float(prev["ema"])
                ema = old + (ratio - old) * _SCHOOL_MASTERY_ALPHA
                attempts = int(prev["attempts"]) + 1
            await session.execute(
                text(
                    """
                    INSERT INTO school_skill_mastery (user_id, skill, ema, attempts, last_seen)
                    VALUES (:uid, :skill, :ema, :attempts, :seen)
                    ON CONFLICT (user_id, skill) DO UPDATE SET
                        ema = EXCLUDED.ema,
                        attempts = EXCLUDED.attempts,
                        last_seen = EXCLUDED.last_seen
                    """
                ),
                {
                    "uid": user_id,
                    "skill": item["skill"],
                    "ema": ema,
                    "attempts": attempts,
                    "seen": now,
                },
            )
        await session.commit()
    except Exception:
        await session.rollback()
        raise
        raise


async def get_school_skill_mastery(session: AsyncSession, user_id: str) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT skill, ema, attempts, last_seen
            FROM school_skill_mastery
            WHERE user_id = :uid
            ORDER BY ema ASC, attempts DESC
            """
        ),
        {"uid": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_school_weak_skills(
    session: AsyncSession,
    user_id: str,
    threshold: float = _SCHOOL_PASS_MARK,
    limit: int = _SCHOOL_WEAK_SURFACE_CAP,
) -> list[str]:
    result = await session.execute(
        text(
            """
            SELECT skill
            FROM school_skill_mastery
            WHERE user_id = :uid AND ema < :threshold
            ORDER BY ema ASC, attempts DESC
            LIMIT :limit
            """
        ),
        {"uid": user_id, "threshold": threshold, "limit": limit},
    )
    return [row[0] for row in result.all()]


async def get_school_results(
    session: AsyncSession, user_id: str, class_no: int | None = None
) -> list[dict]:
    if class_no is None:
        result = await session.execute(
            text(
                """
                SELECT test_id, class_no, kind, score, passed, by_skill, weak_skills, updated_at
                FROM school_results
                WHERE user_id = :uid
                ORDER BY updated_at
                """
            ),
            {"uid": user_id},
        )
    else:
        result = await session.execute(
            text(
                """
                SELECT test_id, class_no, kind, score, passed, by_skill, weak_skills, updated_at
                FROM school_results
                WHERE user_id = :uid AND class_no = :class_no
                ORDER BY updated_at
                """
            ),
            {"uid": user_id, "class_no": int(class_no)},
        )
    out = []
    for row in result.mappings().all():
        item = dict(row)
        item["passed"] = bool(item["passed"])
        item["by_skill"] = item.get("by_skill") or []
        item["weak_skills"] = item.get("weak_skills") or []
        out.append(item)
    return out


async def upsert_school_session(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: str,
    api_version: str,
    flow_type: str,
    subject_id: str,
    class_no: int,
    status: str,
    state_json: dict,
    current_stage: str = "",
    linked_session_id: str | None = None,
    profile_version_id: str | None = None,
    source_placement_report_id: str | None = None,
    _commit: bool = True,
    _profile_lineage_locked: bool = False,
    _locked_existing_session: dict | None = None,
) -> None:
    if api_version != "rebuild" and status in _SCHOOL_ACTIVE_SESSION_STATUSES:
        raise ValueError("archived_school_api_version")
    if api_version == "rebuild":
        if not _profile_lineage_locked:
            await _lock_school_profile_lineage(session, user_id)
        if _locked_existing_session is None:
            existing_result = await session.execute(
                text(
                    """
                    SELECT status,
                           profile_version_id::text AS profile_version_id,
                           source_placement_report_id::text AS source_placement_report_id
                    FROM school_sessions
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND user_id = :uid
                    LIMIT 1
                    FOR UPDATE
                    """
                ),
                {"session_id": session_id, "uid": user_id},
            )
            existing_row = existing_result.mappings().first()
            existing = dict(existing_row) if existing_row else None
        else:
            existing = dict(_locked_existing_session)
        effective_profile_version_id = profile_version_id
        if existing:
            existing_profile_version_id = existing.get("profile_version_id")
            if (
                effective_profile_version_id is not None
                and existing_profile_version_id is not None
                and str(effective_profile_version_id)
                != str(existing_profile_version_id)
            ):
                raise ValueError("school_session_lineage_conflict")
            effective_profile_version_id = (
                effective_profile_version_id or existing_profile_version_id
            )

        same_terminal_replay = bool(
            existing
            and status in _SCHOOL_TERMINAL_SESSION_STATUSES
            and existing.get("status") == status
        )
        requires_active_profile = False
        if status in _SCHOOL_ACTIVE_SESSION_STATUSES:
            if existing and existing.get("status") not in _SCHOOL_ACTIVE_SESSION_STATUSES:
                raise ValueError("stale_school_session_transition")
            requires_active_profile = True
        elif status in _SCHOOL_TERMINAL_SESSION_STATUSES:
            if not existing:
                raise ValueError("school_session_transition_requires_active")
            if not same_terminal_replay:
                if existing.get("status") not in _SCHOOL_ACTIVE_SESSION_STATUSES:
                    raise ValueError("stale_school_session_transition")
                requires_active_profile = True

        if requires_active_profile:
            if effective_profile_version_id is None:
                raise ValueError("active_school_session_profile_lineage_required")
            profile_result = await session.execute(
                text(
                    """
                    SELECT profile_version_id
                    FROM school_profile_versions
                    WHERE profile_version_id = CAST(:profile_version_id AS uuid)
                      AND user_id = :uid
                      AND status = 'active'
                    LIMIT 1
                    FOR SHARE
                    """
                ),
                {
                    "profile_version_id": str(effective_profile_version_id),
                    "uid": user_id,
                },
            )
            if profile_result.first() is None:
                raise ValueError("stale_school_profile_lineage")
        if effective_profile_version_id is not None:
            profile_version_id = str(effective_profile_version_id)
            embedded_profile_version_id = (state_json or {}).get(
                "profile_version_id"
            )
            if (
                embedded_profile_version_id not in (None, "")
                and str(embedded_profile_version_id) != profile_version_id
            ):
                raise ValueError("school_session_lineage_conflict")
        if linked_session_id is not None:
            linked_result = await session.execute(
                text(
                    """
                    SELECT session_id
                    FROM school_sessions
                    WHERE session_id = CAST(:linked_session_id AS uuid)
                      AND user_id = :uid
                    LIMIT 1
                    FOR SHARE
                    """
                ),
                {"linked_session_id": linked_session_id, "uid": user_id},
            )
            if linked_result.first() is None:
                raise ValueError("linked_school_session_not_found")

    await session.execute(
        text(
            """
            INSERT INTO school_sessions
                (session_id, user_id, api_version, flow_type, subject_id, class_no,
                 status, current_stage, linked_session_id, profile_version_id,
                 source_placement_report_id, state_json)
            VALUES
                (CAST(:session_id AS uuid), :uid, :api_version, :flow_type,
                 :subject_id, :class_no, :status, :current_stage,
                 CAST(:linked_session_id AS uuid), CAST(:profile_version_id AS uuid),
                 CAST(:source_placement_report_id AS uuid), CAST(:state_json AS jsonb))
            ON CONFLICT (session_id) DO UPDATE SET
                api_version = EXCLUDED.api_version,
                flow_type = EXCLUDED.flow_type,
                subject_id = EXCLUDED.subject_id,
                class_no = EXCLUDED.class_no,
                status = EXCLUDED.status,
                current_stage = EXCLUDED.current_stage,
                linked_session_id = EXCLUDED.linked_session_id,
                profile_version_id = COALESCE(EXCLUDED.profile_version_id, school_sessions.profile_version_id),
                source_placement_report_id = COALESCE(EXCLUDED.source_placement_report_id, school_sessions.source_placement_report_id),
                state_json = EXCLUDED.state_json,
                updated_at = now(),
                completed_at = CASE
                    WHEN EXCLUDED.status IN ('complete', 'abandoned', 'expired', 'insufficient_evidence')
                    THEN COALESCE(school_sessions.completed_at, now())
                    ELSE school_sessions.completed_at
                END
            """
        ),
        {
            "session_id": session_id,
            "uid": user_id,
            "api_version": api_version,
            "flow_type": flow_type,
            "subject_id": subject_id,
            "class_no": int(class_no),
            "status": status,
            "current_stage": current_stage or "",
            "linked_session_id": linked_session_id,
            "profile_version_id": profile_version_id,
            "source_placement_report_id": source_placement_report_id,
            "state_json": json.dumps(state_json or {}),
        },
    )
    if _commit:
        await session.commit()


async def get_or_create_school_session(
    session: AsyncSession,
    **school_session,
) -> dict:
    user_id = str(school_session["user_id"])
    try:
        if school_session.get("api_version") == "rebuild":
            await _lock_school_profile_lineage(session, user_id)
        winner = await get_active_school_session(
            session,
            user_id,
            str(school_session["api_version"]),
            str(school_session["flow_type"]),
            str(school_session["subject_id"]),
            int(school_session["class_no"]),
            profile_version_id=school_session.get("profile_version_id"),
            source_placement_report_id=school_session.get(
                "source_placement_report_id"
            ),
        )
        if winner:
            await session.commit()
            return winner
        await upsert_school_session(session, **school_session, _commit=False)
        created = await get_school_session(
            session,
            user_id,
            str(school_session["session_id"]),
        )
        if created is None:
            raise RuntimeError("school_session_create_failed")
        await session.commit()
        return created
    except IntegrityError as exc:
        constraint_name = getattr(getattr(exc, "orig", None), "constraint_name", None)
        if constraint_name is None:
            constraint_name = getattr(
                getattr(getattr(exc, "orig", None), "diag", None),
                "constraint_name",
                None,
            )
        await session.rollback()
        if constraint_name != "idx_school_sessions_one_active_flow":
            raise
        await _lock_school_profile_lineage(session, user_id)
        winner = await get_active_school_session(
            session,
            user_id,
            str(school_session["api_version"]),
            str(school_session["flow_type"]),
            str(school_session["subject_id"]),
            int(school_session["class_no"]),
            profile_version_id=school_session.get("profile_version_id"),
            source_placement_report_id=school_session.get(
                "source_placement_report_id"
            ),
        )
        if winner:
            await session.commit()
            return winner
        await session.rollback()
        raise ValueError("school_session_start_conflict") from exc
    except Exception:
        await session.rollback()
        raise


async def create_and_attach_school_masterclass(
    session: AsyncSession,
    *,
    parent_session: dict,
    expected_parent_state: dict,
    child_session: dict,
) -> dict | None:
    """Atomically create one linked masterclass and attach it to its parent.

    A paused curriculum session is the durable authority for a masterclass.
    Creating the child in a separate transaction leaves a learner stranded if
    the process stops before the parent receives the child ID, so both rows
    are committed together under the existing user-lineage lock.
    """

    user_id = str(parent_session["user_id"])
    parent_session_id = str(parent_session["session_id"])
    child_session_id = str(child_session["session_id"])
    if (
        str(child_session.get("user_id") or "") != user_id
        or str(child_session.get("linked_session_id") or "") != parent_session_id
        or child_session.get("flow_type") != "masterclass"
    ):
        raise ValueError("invalid_masterclass_parent_link")
    try:
        await _lock_school_profile_lineage(session, user_id)
        parent_result = await session.execute(
            text(
                """
                SELECT state_json
                FROM school_sessions
                WHERE session_id = CAST(:session_id AS uuid)
                  AND user_id = :uid
                FOR UPDATE
                """
            ),
            {"session_id": parent_session_id, "uid": user_id},
        )
        current_parent_state = parent_result.scalar_one_or_none()
        if isinstance(current_parent_state, str):
            current_parent_state = json.loads(current_parent_state)
        if (
            current_parent_state is None
            or dict(current_parent_state) != dict(expected_parent_state)
        ):
            await session.rollback()
            return None

        existing_child = await get_active_school_session(
            session,
            user_id,
            str(child_session["api_version"]),
            "masterclass",
            str(child_session["subject_id"]),
            int(child_session["class_no"]),
            profile_version_id=child_session.get("profile_version_id"),
            source_placement_report_id=child_session.get(
                "source_placement_report_id"
            ),
        )
        if (
            existing_child is not None
            and str(existing_child.get("session_id") or "") != child_session_id
        ):
            await session.rollback()
            return None

        await upsert_school_session(session, **child_session, _commit=False)
        await upsert_school_session(session, **parent_session, _commit=False)
        child = await get_school_session(session, user_id, child_session_id)
        if child is None:
            raise RuntimeError("masterclass_session_create_failed")
        await session.commit()
        return child
    except IntegrityError as exc:
        constraint_name = getattr(getattr(exc, "orig", None), "constraint_name", None)
        if constraint_name is None:
            constraint_name = getattr(
                getattr(getattr(exc, "orig", None), "diag", None),
                "constraint_name",
                None,
            )
        await session.rollback()
        if constraint_name == "idx_school_sessions_one_active_flow":
            return None
        raise
    except Exception:
        await session.rollback()
        raise


async def get_or_create_active_school_placement_session(
    session: AsyncSession,
    *,
    session_id: str,
    user_id: str,
    profile_version_id: str,
    subject_id: str,
    class_no: int,
    current_stage: str,
    state_json: dict,
) -> dict:
    async def authorize_expected_profile() -> None:
        active_result = await session.execute(
            text(
                """
                SELECT profile_version_id::text AS profile_version_id
                FROM school_profile_versions
                WHERE user_id = :uid AND status = 'active'
                ORDER BY activated_at DESC NULLS LAST, updated_at DESC
                LIMIT 1
                FOR SHARE
                """
            ),
            {"uid": user_id},
        )
        active_row = active_result.mappings().first()
        if (
            active_row is None
            or str(active_row["profile_version_id"]) != str(profile_version_id)
        ):
            raise ValueError("stale_school_profile_lineage")

    async def retire_legacy_conflicts() -> None:
        await _retire_conflicting_legacy_school_placement_sessions(
            session,
            user_id=user_id,
            subject_id=subject_id,
            class_no=class_no,
        )

    try:
        await _lock_school_profile_lineage(session, user_id)
        await authorize_expected_profile()
        await retire_legacy_conflicts()

        winner = await get_active_school_session(
            session,
            user_id,
            "rebuild",
            "placement",
            subject_id,
            class_no,
            profile_version_id=profile_version_id,
        )
        if winner:
            await session.commit()
            return winner

        await upsert_school_session(
            session,
            session_id=session_id,
            user_id=user_id,
            api_version="rebuild",
            flow_type="placement",
            subject_id=subject_id,
            class_no=class_no,
            status="active",
            current_stage=current_stage,
            profile_version_id=profile_version_id,
            source_placement_report_id=None,
            state_json=state_json,
            _commit=False,
        )
        winner = await get_school_session(session, user_id, session_id)
        if winner is None:
            raise RuntimeError("school_placement_session_create_failed")
        await session.commit()
        return winner
    except IntegrityError as exc:
        await session.rollback()
        try:
            await _lock_school_profile_lineage(session, user_id)
            await authorize_expected_profile()
            await retire_legacy_conflicts()
        except Exception:
            await session.rollback()
            raise
        winner = await get_active_school_session(
            session,
            user_id,
            "rebuild",
            "placement",
            subject_id,
            class_no,
            profile_version_id=profile_version_id,
        )
        if winner:
            await session.commit()
            return winner
        await session.rollback()
        raise ValueError("school_session_start_conflict") from exc
    except Exception:
        await session.rollback()
        raise


async def present_school_placement_item(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    item_id: str,
    force: bool = False,
) -> dict:
    """Stamp an item only after its placement row lock has been acquired."""

    try:
        from app.services.school_rebuild_placement import (
            PRIVATE_PLACEMENT_TIMING_KEY,
            envelope_from_json,
            next_item,
        )

        await _lock_school_profile_lineage(session, user_id)
        result = await session.execute(
            text(
                """
                SELECT session_id::text AS session_id, user_id, api_version,
                       flow_type, subject_id, class_no, status, current_stage,
                       linked_session_id::text AS linked_session_id, state_json,
                       profile_version_id::text AS profile_version_id,
                       source_placement_report_id::text AS source_placement_report_id,
                       started_at, updated_at, completed_at
                FROM school_sessions
                WHERE user_id = :uid
                  AND session_id = CAST(:session_id AS uuid)
                FOR UPDATE
                """
            ),
            {"uid": user_id, "session_id": session_id},
        )
        selected = result.mappings().first()
        if selected is None:
            raise ValueError("placement_session_not_found")
        row = dict(selected)
        if (
            row.get("api_version") != "rebuild"
            or row.get("flow_type") != "placement"
            or row.get("status") != "active"
        ):
            raise ValueError("placement_not_active")

        state_json = dict(row.get("state_json") or {})
        expected = next_item(envelope_from_json(state_json))
        if expected is None or expected.item_id != item_id:
            raise ValueError("unexpected_placement_item")
        current = state_json.get(PRIVATE_PLACEMENT_TIMING_KEY)
        if (
            not force
            and isinstance(current, dict)
            and str(current.get("item_id") or "") == item_id
            and current.get("presented_at")
        ):
            await session.commit()
            return row

        updated = await session.execute(
            text(
                """
                UPDATE school_sessions
                SET state_json = CAST(:state_json AS jsonb)
                        || jsonb_build_object(
                            CAST(:timing_key AS text),
                            jsonb_build_object(
                                'item_id', CAST(:item_id AS text),
                                'presented_at', clock_timestamp()
                            )
                        ),
                    updated_at = clock_timestamp()
                WHERE user_id = :uid
                  AND session_id = CAST(:session_id AS uuid)
                  AND status = 'active'
                RETURNING session_id::text AS session_id, user_id, api_version,
                          flow_type, subject_id, class_no, status, current_stage,
                          linked_session_id::text AS linked_session_id, state_json,
                          profile_version_id::text AS profile_version_id,
                          source_placement_report_id::text AS source_placement_report_id,
                          started_at, updated_at, completed_at
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "state_json": json.dumps(state_json),
                "timing_key": PRIVATE_PLACEMENT_TIMING_KEY,
                "item_id": item_id,
            },
        )
        presented = updated.mappings().first()
        if presented is None:
            raise ValueError("placement_presentation_conflict")
        await session.commit()
        return dict(presented)
    except Exception:
        await session.rollback()
        raise


async def _retire_conflicting_legacy_school_placement_sessions(
    session: AsyncSession,
    *,
    user_id: str,
    subject_id: str,
    class_no: int,
) -> int:
    """Terminalize an archived runtime that occupies the canonical flow slot."""

    result = await session.execute(
        text(
            """
            UPDATE school_sessions
            SET status = 'abandoned',
                completed_at = COALESCE(completed_at, now()),
                updated_at = now(),
                state_json = COALESCE(state_json, '{}'::jsonb)
                    || jsonb_build_object(
                        '_canonical_retirement',
                        jsonb_build_object(
                            'reason',
                            'legacy_runtime_retired_for_canonical_placement',
                            'retired_at',
                            now()
                        )
                    )
            WHERE user_id = :uid
              AND flow_type = 'placement'
              AND subject_id = :subject_id
              AND class_no = :class_no
              AND api_version <> 'rebuild'
              AND status IN ('active', 'paused_for_masterclass')
            """
        ),
        {
            "uid": user_id,
            "subject_id": subject_id,
            "class_no": int(class_no),
        },
    )
    return int(result.rowcount or 0)


async def resume_school_placement_session(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    profile_version_id: str,
    current_stage: str,
    state_json: dict,
) -> dict:
    """Reopen one insufficient placement row without changing its lineage."""

    try:
        from app.services.school_rebuild_placement import (
            validate_placement_resume_state_json,
        )

        await _lock_school_profile_lineage(session, user_id)
        result = await session.execute(
            text(
                """
                SELECT session_id::text AS session_id, user_id, api_version,
                       flow_type, subject_id, class_no, status, current_stage,
                       linked_session_id::text AS linked_session_id, state_json,
                       profile_version_id::text AS profile_version_id,
                       source_placement_report_id::text AS source_placement_report_id,
                       started_at, updated_at, completed_at
                FROM school_sessions
                WHERE user_id = :uid
                  AND session_id = CAST(:session_id AS uuid)
                FOR UPDATE
                """
            ),
            {"uid": user_id, "session_id": session_id},
        )
        row = result.mappings().first()
        if row is None:
            raise ValueError("placement_session_not_found")
        current = dict(row)
        if (
            current.get("api_version") != "rebuild"
            or current.get("flow_type") != "placement"
            or str(current.get("profile_version_id") or "")
            != str(profile_version_id)
        ):
            raise ValueError("placement_session_not_resumable")
        if current.get("status") == "active":
            await session.commit()
            return current
        if current.get("status") != "insufficient_evidence":
            raise ValueError("placement_session_not_resumable")

        profile_result = await session.execute(
            text(
                """
                SELECT profile_version_id
                FROM school_profile_versions
                WHERE user_id = :uid
                  AND profile_version_id = CAST(:profile_version_id AS uuid)
                  AND status = 'active'
                LIMIT 1
                FOR SHARE
                """
            ),
            {"uid": user_id, "profile_version_id": profile_version_id},
        )
        if profile_result.first() is None:
            raise ValueError("stale_school_profile_lineage")
        embedded_profile_version_id = (state_json or {}).get("profile_version_id")
        if (
            embedded_profile_version_id not in (None, "")
            and str(embedded_profile_version_id) != str(profile_version_id)
        ):
            raise ValueError("school_session_lineage_conflict")
        if str((state_json or {}).get("placement_state", {}).get("stage") or "") != str(
            current_stage
        ):
            raise ValueError("placement_session_resume_conflict")
        validate_placement_resume_state_json(
            current.get("state_json") or {},
            state_json or {},
            profile_version_id=profile_version_id,
        )

        await session.execute(
            text(
                """
                UPDATE school_sessions
                SET status = 'active',
                    current_stage = :current_stage,
                    state_json = CAST(:state_json AS jsonb),
                    completed_at = NULL,
                    updated_at = now()
                WHERE user_id = :uid
                  AND session_id = CAST(:session_id AS uuid)
                  AND status = 'insufficient_evidence'
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "current_stage": current_stage,
                "state_json": json.dumps(state_json or {}),
            },
        )
        await session.execute(
            text(
                """
                UPDATE school_placement_reports
                SET evidence_summary_json = COALESCE(
                        evidence_summary_json,
                        '{}'::jsonb
                    ) || jsonb_build_object(
                        'superseded_by_resume',
                        jsonb_build_object(
                            'placement_session_id', :session_id,
                            'resumed_at', now()
                        )
                    ),
                    updated_at = now()
                WHERE user_id = :uid
                  AND placement_session_id = CAST(:session_id AS uuid)
                  AND profile_version_id = CAST(:profile_version_id AS uuid)
                  AND placement_status = 'insufficient_evidence'
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "profile_version_id": profile_version_id,
            },
        )
        resumed = await get_school_session(session, user_id, session_id)
        if resumed is None or resumed.get("status") != "active":
            raise ValueError("placement_session_resume_conflict")
        await session.commit()
        return resumed
    except Exception:
        await session.rollback()
        raise


async def persist_school_answer_attempt(
    session: AsyncSession,
    *,
    learning_event: dict,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str | None = None,
    request_answer_hash: str | None = None,
    request_claim_token: str | None = None,
    request_claim_if_absent: bool = False,
    response_json: dict | None = None,
    placement_report: dict | None = None,
    projection_evidence: dict | None = None,
    language_evaluation: dict | None = None,
    evaluation_job_completion: dict | None = None,
    placement_presentation_item_id: str | None = None,
    placement_presentation_at: datetime | None = None,
) -> dict:
    """Commit one canonical School answer transition and its evidence atomically."""
    try:
        user_id = str(school_session["user_id"])
        await session.execute(
            text(
                "SELECT pg_advisory_xact_lock("
                "hashtext('zidd_school_answer:' || :uid))"
            ),
            {"uid": user_id},
        )
        if school_session.get("api_version") == "rebuild":
            await _lock_school_profile_lineage(session, user_id)
        if request_activity_id is not None:
            if (
                request_answer_hash is None
                or response_json is None
            ):
                raise ValueError("invalid_school_answer_request_completion")
            if request_claim_if_absent and request_claim_token is not None:
                raise ValueError("invalid_school_answer_request_claim_mode")
            if not request_claim_if_absent and request_claim_token is None:
                raise ValueError("invalid_school_answer_request_completion")
            request_row = (
                await session.execute(
                    text(
                        """
                        SELECT status, answer_hash, claim_token, response_json
                        FROM school_answer_requests
                        WHERE session_id = CAST(:session_id AS uuid)
                          AND activity_id = :activity_id
                          AND user_id = :uid
                        FOR UPDATE
                        """
                    ),
                    {
                        "session_id": school_session["session_id"],
                        "activity_id": request_activity_id,
                        "uid": user_id,
                    },
                )
            ).mappings().first()
            if request_claim_if_absent:
                if request_row is None:
                    request_claim_token = str(uuid4())
                    await session.execute(
                        text(
                            """
                            INSERT INTO school_answer_requests
                                (session_id, activity_id, user_id, answer_hash,
                                 claim_token, status, response_json)
                            VALUES
                                (CAST(:session_id AS uuid), :activity_id, :uid,
                                 :answer_hash, :claim_token, 'processing', NULL)
                            """
                        ),
                        {
                            "session_id": school_session["session_id"],
                            "activity_id": request_activity_id,
                            "uid": user_id,
                            "answer_hash": request_answer_hash,
                            "claim_token": request_claim_token,
                        },
                    )
                else:
                    existing_status = str(request_row["status"] or "")
                    existing_hash = str(request_row["answer_hash"] or "")
                    if existing_status == "completed":
                        if existing_hash != request_answer_hash:
                            raise ValueError("duplicate_evidence_conflict")
                        replay = request_row["response_json"]
                        if isinstance(replay, str):
                            replay = json.loads(replay)
                        await session.rollback()
                        return {
                            "outcome": "replayed",
                            "response_json": dict(replay or {}),
                        }
                    if existing_status == "processing":
                        raise ValueError("stale_school_answer_request")
                    if existing_status != "failed":
                        raise ValueError("stale_school_answer_request")
                    request_claim_token = str(uuid4())
                    reclaimed = await session.execute(
                        text(
                            """
                            UPDATE school_answer_requests
                            SET answer_hash = :answer_hash,
                                claim_token = :claim_token,
                                status = 'processing',
                                response_json = NULL,
                                updated_at = now()
                            WHERE session_id = CAST(:session_id AS uuid)
                              AND activity_id = :activity_id
                              AND user_id = :uid
                              AND status = 'failed'
                            RETURNING activity_id
                            """
                        ),
                        {
                            "session_id": school_session["session_id"],
                            "activity_id": request_activity_id,
                            "uid": user_id,
                            "answer_hash": request_answer_hash,
                            "claim_token": request_claim_token,
                        },
                    )
                    if reclaimed.scalar_one_or_none() is None:
                        raise ValueError("stale_school_answer_request")
            elif (
                request_row is None
                or request_row["status"] != "processing"
                or request_row["answer_hash"] != request_answer_hash
                or str(request_row["claim_token"] or "") != request_claim_token
            ):
                raise ValueError("stale_school_answer_request")
        elif evaluation_job_completion is not None:
            raise ValueError("invalid_school_evaluation_job_completion")

        normalized_job_completion: dict | None = None
        if evaluation_job_completion is not None:
            if not isinstance(evaluation_job_completion, dict):
                raise ValueError("invalid_school_evaluation_job_completion")
            required_identity = {
                "user_id": user_id,
                "session_id": str(school_session["session_id"]),
                "activity_id": str(request_activity_id),
                "answer_hash": str(request_answer_hash),
                "answer_claim_token": str(request_claim_token),
            }
            if any(
                str(evaluation_job_completion.get(key) or "") != value
                for key, value in required_identity.items()
            ):
                raise ValueError("invalid_school_evaluation_job_completion")
            lease_owner = str(evaluation_job_completion.get("lease_owner") or "").strip()
            lease_token = str(evaluation_job_completion.get("lease_token") or "").strip()
            try:
                lease_version = int(evaluation_job_completion.get("lease_version"))
            except (TypeError, ValueError):
                lease_version = 0
            job_response_json = evaluation_job_completion.get("response_json")
            job_result_data = evaluation_job_completion.get("result_data")
            if (
                not lease_owner
                or not lease_token
                or lease_version <= 0
                or not isinstance(job_response_json, dict)
                or not isinstance(job_result_data, dict)
                or job_response_json != response_json
            ):
                raise ValueError("invalid_school_evaluation_job_completion")
            normalized_job_completion = {
                **required_identity,
                "lease_owner": lease_owner,
                "lease_token": lease_token,
                "lease_version": lease_version,
                "response_json": job_response_json,
                "result_data": job_result_data,
            }
        result = await session.execute(
            text(
                """
                SELECT state_json,
                       status,
                       profile_version_id::text AS profile_version_id,
                       source_placement_report_id::text AS source_placement_report_id
                FROM school_sessions
                WHERE session_id = CAST(:session_id AS uuid) AND user_id = :uid
                FOR UPDATE
                """
            ),
            {
                "session_id": school_session["session_id"],
                "uid": user_id,
            },
        )
        locked_session_row = result.mappings().first()
        current_state = (
            locked_session_row.get("state_json")
            if locked_session_row is not None
            else None
        )
        if isinstance(current_state, str):
            current_state = json.loads(current_state)
        if current_state is None or dict(current_state) != dict(expected_state_json):
            raise ValueError("stale_school_answer_session")

        profile_upserts: list[dict] = []
        if projection_evidence is not None:
            from app.services.school.projection import (
                SchoolAttemptEvidence,
                derive_school_projection_delta,
                enrich_school_projection_evidence,
            )

            existing_profiles = (
                await session.execute(
                    text(
                        """
                        SELECT user_id, domain, skill_id, module_id, task_type,
                               mastery, readiness, confidence, attempts,
                               strengths_json, gaps_json, evidence_json,
                               recommended_next_action, source_summary
                        FROM learner_skill_profiles
                        WHERE user_id = :uid AND domain = 'school'
                        FOR UPDATE
                        """
                    ),
                    {"uid": user_id},
                )
            ).mappings().all()
            projection = SchoolAttemptEvidence.from_dict(
                enrich_school_projection_evidence(
                    projection_evidence,
                    learning_event=learning_event,
                    user_id=user_id,
                    session_id=str(school_session["session_id"]),
                    activity_id=request_activity_id,
                    answer_hash=request_answer_hash,
                )
            )
            profile_upserts = derive_school_projection_delta(
                projection,
                [dict(row) for row in existing_profiles],
            )
            for profile in profile_upserts:
                profile["user_id"] = user_id

        session_to_write = dict(school_session)
        if (placement_presentation_item_id is None) != (
            placement_presentation_at is None
        ):
            raise ValueError("invalid_school_placement_presentation")
        if placement_presentation_item_id is not None:
            if (
                placement_presentation_at is None
                or placement_presentation_at.tzinfo is None
                or placement_presentation_at.utcoffset() is None
            ):
                raise ValueError("invalid_school_placement_presentation")
            from app.services.school_rebuild_placement import (
                PRIVATE_PLACEMENT_TIMING_KEY,
            )

            placement_state_json = dict(session_to_write.get("state_json") or {})
            placement_state_json[PRIVATE_PLACEMENT_TIMING_KEY] = {
                "item_id": placement_presentation_item_id,
                "presented_at": placement_presentation_at.isoformat(),
            }
            session_to_write["state_json"] = placement_state_json
        if language_evaluation is not None:
            from app.services.school.language_confidence import (
                LanguageConfidenceState,
                apply_curriculum_language_signal,
            )

            language_row = (
                await session.execute(
                    text(
                        """
                        SELECT en_production_confidence, total_signals
                        FROM school_language_confidence
                        WHERE user_id = :uid
                        FOR UPDATE
                        """
                    ),
                    {"uid": user_id},
                )
            ).mappings().first()
            language_state = apply_curriculum_language_signal(
                LanguageConfidenceState(
                    user_id=user_id,
                    en_production_confidence=float(
                        (language_row or {}).get("en_production_confidence") or 0.0
                    ),
                    total_signals=int((language_row or {}).get("total_signals") or 0),
                ),
                language_evaluation,
            )
            state_json = dict(session_to_write.get("state_json") or {})
            state_json.update(
                en_production_confidence=language_state.en_production_confidence,
                language_signal_count=language_state.total_signals,
            )
            session_to_write["state_json"] = state_json
            await upsert_school_language_confidence(
                session,
                user_id=user_id,
                en_production_confidence=language_state.en_production_confidence,
                total_signals=language_state.total_signals,
                commit=False,
            )

        inserted = await record_learning_event(
            session,
            **learning_event,
            commit=False,
        )
        if not inserted:
            raise ValueError("duplicate_evidence_conflict")
        for profile in profile_upserts:
            await upsert_learner_skill_profile(session, **profile, commit=False)
        await upsert_school_session(
            session,
            **session_to_write,
            _commit=False,
            _profile_lineage_locked=(
                school_session.get("api_version") == "rebuild"
            ),
            _locked_existing_session=(
                dict(locked_session_row)
                if locked_session_row is not None
                and school_session.get("api_version") == "rebuild"
                else None
            ),
        )
        if placement_report is not None:
            await upsert_school_placement_report(
                session,
                **placement_report,
                _commit=False,
            )
        if normalized_job_completion is not None:
            completed_job = await session.execute(
                text(
                    """
                    UPDATE school_evaluation_jobs
                    SET status = 'completed',
                        response_json = CAST(:evaluation_job_response_json AS jsonb),
                        result_data = CAST(:evaluation_job_result_data AS jsonb),
                        last_error_code = NULL,
                        error_json = NULL,
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        completed_at = now(),
                        updated_at = now()
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND activity_id = :activity_id
                      AND user_id = :uid
                      AND answer_hash = :answer_hash
                      AND answer_claim_token = :answer_claim_token
                      AND lease_owner = :lease_owner
                      AND lease_token = :lease_token
                      AND lease_version = :lease_version
                      AND status = 'running'
                      AND lease_expires_at > now()
                      AND EXISTS (
                          SELECT 1
                          FROM school_answer_requests AS request
                          WHERE request.session_id = school_evaluation_jobs.session_id
                            AND request.activity_id = school_evaluation_jobs.activity_id
                            AND request.user_id = school_evaluation_jobs.user_id
                            AND request.answer_hash = school_evaluation_jobs.answer_hash
                            AND request.claim_token = school_evaluation_jobs.answer_claim_token
                            AND request.status = 'processing'
                      )
                    RETURNING activity_id
                    """
                ),
                {
                    "session_id": normalized_job_completion["session_id"],
                    "activity_id": normalized_job_completion["activity_id"],
                    "uid": normalized_job_completion["user_id"],
                    "answer_hash": normalized_job_completion["answer_hash"],
                    "answer_claim_token": normalized_job_completion[
                        "answer_claim_token"
                    ],
                    "lease_owner": normalized_job_completion["lease_owner"],
                    "lease_token": normalized_job_completion["lease_token"],
                    "lease_version": normalized_job_completion["lease_version"],
                    "evaluation_job_response_json": json.dumps(
                        normalized_job_completion["response_json"]
                    ),
                    "evaluation_job_result_data": json.dumps(
                        normalized_job_completion["result_data"]
                    ),
                },
            )
            if completed_job.scalar_one_or_none() is None:
                raise ValueError("stale_school_evaluation_job")
        if request_activity_id is not None:
            completed = await session.execute(
                text(
                    """
                    UPDATE school_answer_requests
                    SET status = 'completed',
                        response_json = CAST(:response_json AS jsonb),
                        updated_at = now()
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND activity_id = :activity_id
                      AND user_id = :uid
                      AND answer_hash = :answer_hash
                      AND claim_token = :claim_token
                      AND status = 'processing'
                    RETURNING activity_id
                    """
                ),
                {
                    "session_id": school_session["session_id"],
                    "activity_id": request_activity_id,
                    "uid": user_id,
                    "answer_hash": request_answer_hash,
                    "claim_token": request_claim_token,
                    "response_json": json.dumps(response_json),
                },
            )
            if completed.scalar_one_or_none() is None:
                raise ValueError("stale_school_answer_request")
        await session.commit()
        return {"outcome": "persisted"}
    except asyncio.CancelledError:
        await finish_cleanup(session.rollback())
        raise
    except Exception:
        await session.rollback()
        raise


async def compare_and_set_school_session(
    session: AsyncSession,
    *,
    school_session: dict,
    expected_state_json: dict,
) -> bool:
    """Persist a non-answer School transition only if its parent state is unchanged."""
    try:
        if school_session.get("api_version") == "rebuild":
            await _lock_school_profile_lineage(session, str(school_session["user_id"]))
        result = await session.execute(
            text(
                """
                SELECT state_json
                FROM school_sessions
                WHERE session_id = CAST(:session_id AS uuid) AND user_id = :uid
                FOR UPDATE
                """
            ),
            {
                "session_id": school_session["session_id"],
                "uid": school_session["user_id"],
            },
        )
        current_state = result.scalar_one_or_none()
        if isinstance(current_state, str):
            current_state = json.loads(current_state)
        if current_state is None or dict(current_state) != dict(expected_state_json):
            await session.rollback()
            return False
        await upsert_school_session(session, **school_session, _commit=False)
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def persist_school_curriculum_attempt(
    session: AsyncSession,
    *,
    learning_event: dict,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str | None = None,
    request_answer_hash: str | None = None,
    request_claim_token: str | None = None,
    request_claim_if_absent: bool = False,
    response_json: dict | None = None,
    projection_evidence: dict | None = None,
    language_evaluation: dict | None = None,
    evaluation_job_completion: dict | None = None,
) -> dict:
    return await persist_school_answer_attempt(
        session,
        learning_event=learning_event,
        school_session=school_session,
        expected_state_json=expected_state_json,
        request_activity_id=request_activity_id,
        request_answer_hash=request_answer_hash,
        request_claim_token=request_claim_token,
        request_claim_if_absent=request_claim_if_absent,
        response_json=response_json,
        projection_evidence=projection_evidence,
        language_evaluation=language_evaluation,
        evaluation_job_completion=evaluation_job_completion,
    )


async def persist_school_deterministic_curriculum_attempt(
    session: AsyncSession,
    *,
    learning_event: dict,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str,
    request_answer_hash: str,
    response_json: dict,
    projection_evidence: dict | None,
    language_evaluation: dict | None,
    evaluation_job_completion: dict | None = None,
) -> dict:
    """Persist a direct curriculum answer in one claim read and one bulk write.

    Deterministic answers do not need an evaluator job or a separate claim
    round trip. This keeps the same replay, profile-lineage, evidence, and
    compare-and-set guarantees as queued answers while avoiding the older
    serial generic persistence path.
    """

    user_id = str(school_session.get("user_id") or "")
    session_id = str(school_session.get("session_id") or "")
    profile_version_id = str(school_session.get("profile_version_id") or "")
    if (
        school_session.get("api_version") != "rebuild"
        or school_session.get("flow_type") != "curriculum"
        or not user_id
        or not session_id
        or not profile_version_id
        or not request_activity_id
        or not request_answer_hash
        or not isinstance(expected_state_json, dict)
        or not isinstance(response_json, dict)
        or evaluation_job_completion is not None
    ):
        raise ValueError("invalid_school_deterministic_curriculum_attempt")
    if (
        str(learning_event.get("user_id") or "") != user_id
        or str(learning_event.get("session_id") or "") != session_id
    ):
        raise ValueError("invalid_school_deterministic_curriculum_attempt")
    _validate_learning_domain_task(
        str(learning_event.get("domain") or ""),
        str(learning_event.get("task_type") or ""),
    )
    embedded_profile_version_id = (school_session.get("state_json") or {}).get(
        "profile_version_id"
    )
    if (
        embedded_profile_version_id not in (None, "")
        and str(embedded_profile_version_id) != profile_version_id
    ):
        raise ValueError("school_session_lineage_conflict")

    try:
        context_result = await session.execute(
            text(
                """
                WITH advisory_lock AS (
                    SELECT pg_advisory_xact_lock(
                        hashtext('zidd_school_answer:' || :uid)
                    )
                ),
                learner_lineage AS (
                    SELECT learner.user_id
                    FROM learner_profiles AS learner
                    CROSS JOIN advisory_lock
                    WHERE learner.user_id = :uid
                    FOR UPDATE
                ),
                active_profile AS (
                    SELECT profile.profile_version_id::text AS profile_version_id
                    FROM school_profile_versions AS profile
                    CROSS JOIN learner_lineage
                    WHERE profile.user_id = :uid
                      AND profile.profile_version_id = CAST(:profile_version_id AS uuid)
                      AND profile.status = 'active'
                    FOR SHARE
                ),
                locked_request AS (
                    SELECT request.status AS request_status,
                           request.answer_hash AS request_answer_hash,
                           request.claim_token AS request_claim_token,
                           request.response_json AS request_response_json
                    FROM school_answer_requests AS request
                    CROSS JOIN active_profile
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                    FOR UPDATE
                ),
                claimed_request AS (
                    INSERT INTO school_answer_requests
                        (session_id, activity_id, user_id, answer_hash,
                         claim_token, status, response_json)
                    SELECT CAST(:session_id AS uuid), :activity_id, :uid,
                           :answer_hash, :claim_token, 'processing', NULL
                    FROM active_profile
                    WHERE NOT EXISTS (SELECT 1 FROM locked_request)
                    RETURNING status AS request_status,
                              answer_hash AS request_answer_hash,
                              claim_token AS request_claim_token,
                              response_json AS request_response_json,
                              'claimed'::text AS request_origin
                ),
                reclaimed_request AS (
                    UPDATE school_answer_requests AS request
                    SET answer_hash = :answer_hash,
                        claim_token = :claim_token,
                        status = 'processing',
                        response_json = NULL,
                        updated_at = now()
                    FROM locked_request
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                      AND locked_request.request_status = 'failed'
                    RETURNING request.status AS request_status,
                              request.answer_hash AS request_answer_hash,
                              request.claim_token AS request_claim_token,
                              request.response_json AS request_response_json,
                              'reclaimed'::text AS request_origin
                ),
                request_resolution AS (
                    SELECT request_status, request_answer_hash,
                           request_claim_token, request_response_json,
                           'existing'::text AS request_origin
                    FROM locked_request
                    WHERE request_status <> 'failed'
                    UNION ALL
                    SELECT request_status, request_answer_hash,
                           request_claim_token, request_response_json,
                           request_origin
                    FROM claimed_request
                    UNION ALL
                    SELECT request_status, request_answer_hash,
                           request_claim_token, request_response_json,
                           request_origin
                    FROM reclaimed_request
                ),
                locked_session AS (
                    SELECT school.state_json AS session_state_json,
                           school.status AS session_status,
                           school.profile_version_id::text AS session_profile_version_id
                    FROM school_sessions AS school
                    CROSS JOIN active_profile
                    WHERE school.session_id = CAST(:session_id AS uuid)
                      AND school.user_id = :uid
                    FOR UPDATE
                ),
                locked_profiles AS (
                    SELECT profile.user_id, profile.domain, profile.skill_id,
                           profile.module_id, profile.task_type, profile.mastery,
                           profile.readiness, profile.confidence, profile.attempts,
                           profile.strengths_json, profile.gaps_json,
                           profile.evidence_json,
                           profile.recommended_next_action,
                           profile.source_summary
                    FROM learner_skill_profiles AS profile
                    CROSS JOIN active_profile
                    WHERE profile.user_id = :uid
                      AND profile.domain = 'school'
                    FOR UPDATE
                ),
                profile_snapshot AS (
                    SELECT COALESCE(
                        jsonb_agg(to_jsonb(locked_profiles)), '[]'::jsonb
                    ) AS profile_rows_json
                    FROM locked_profiles
                ),
                locked_language AS (
                    SELECT language.en_production_confidence AS language_confidence,
                           language.total_signals AS language_total_signals
                    FROM school_language_confidence AS language
                    CROSS JOIN active_profile
                    WHERE language.user_id = :uid
                    FOR UPDATE
                )
                SELECT
                    (SELECT profile_version_id FROM active_profile)
                        AS active_profile_version_id,
                    request_resolution.request_origin,
                    request_resolution.request_status,
                    request_resolution.request_answer_hash,
                    request_resolution.request_claim_token,
                    request_resolution.request_response_json,
                    (SELECT session_state_json FROM locked_session)
                        AS session_state_json,
                    (SELECT session_status FROM locked_session) AS session_status,
                    (SELECT session_profile_version_id FROM locked_session)
                        AS session_profile_version_id,
                    (SELECT profile_rows_json FROM profile_snapshot)
                        AS profile_rows_json,
                    (SELECT language_confidence FROM locked_language)
                        AS language_confidence,
                    (SELECT language_total_signals FROM locked_language)
                        AS language_total_signals
                FROM request_resolution
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "activity_id": request_activity_id,
                "profile_version_id": profile_version_id,
                "answer_hash": request_answer_hash,
                "claim_token": str(uuid4()),
            },
        )
        context = dict(context_result.mappings().first() or {})
        if str(context.get("active_profile_version_id") or "") != profile_version_id:
            raise ValueError("stale_school_profile_lineage")
        request_origin = str(context.get("request_origin") or "")
        request_status = str(context.get("request_status") or "")
        existing_hash = str(context.get("request_answer_hash") or "")
        request_claim_token = str(context.get("request_claim_token") or "")
        if request_origin == "existing":
            if request_status == "completed":
                if existing_hash != request_answer_hash:
                    raise ValueError("duplicate_evidence_conflict")
                replay = context.get("request_response_json")
                if isinstance(replay, str):
                    replay = json.loads(replay)
                await session.commit()
                return {
                    "outcome": "replayed",
                    "response_json": dict(replay or {}),
                }
            raise ValueError("stale_school_answer_request")
        if (
            request_origin not in {"claimed", "reclaimed"}
            or request_status != "processing"
            or existing_hash != request_answer_hash
            or not request_claim_token
        ):
            raise ValueError("stale_school_answer_request")
        if (
            str(context.get("session_profile_version_id") or "")
            != profile_version_id
            or str(context.get("session_status") or "")
            not in _SCHOOL_ACTIVE_SESSION_STATUSES
        ):
            raise ValueError("stale_school_session_transition")
        current_state = context.get("session_state_json")
        if isinstance(current_state, str):
            current_state = json.loads(current_state)
        if not isinstance(current_state, dict) or current_state != expected_state_json:
            raise ValueError("stale_school_answer_session")

        profile_rows = context.get("profile_rows_json") or []
        if isinstance(profile_rows, str):
            profile_rows = json.loads(profile_rows)
        if not isinstance(profile_rows, list):
            raise ValueError("invalid_school_projection_context")
        profile_upserts: list[dict] = []
        if projection_evidence is not None:
            from app.services.school.projection import (
                SchoolAttemptEvidence,
                derive_school_projection_delta,
                enrich_school_projection_evidence,
            )

            projection = SchoolAttemptEvidence.from_dict(
                enrich_school_projection_evidence(
                    projection_evidence,
                    learning_event=learning_event,
                    user_id=user_id,
                    session_id=session_id,
                    activity_id=request_activity_id,
                    answer_hash=request_answer_hash,
                )
            )
            profile_upserts = derive_school_projection_delta(
                projection,
                [dict(row) for row in profile_rows if isinstance(row, dict)],
            )
            for profile in profile_upserts:
                profile["user_id"] = user_id

        session_to_write = dict(school_session)
        language_update: dict | None = None
        if language_evaluation is not None:
            from app.services.school.language_confidence import (
                LanguageConfidenceState,
                apply_curriculum_language_signal,
            )

            language_state = apply_curriculum_language_signal(
                LanguageConfidenceState(
                    user_id=user_id,
                    en_production_confidence=float(
                        context.get("language_confidence") or 0.0
                    ),
                    total_signals=int(context.get("language_total_signals") or 0),
                ),
                language_evaluation,
            )
            state_json = dict(session_to_write.get("state_json") or {})
            state_json.update(
                en_production_confidence=language_state.en_production_confidence,
                language_signal_count=language_state.total_signals,
            )
            session_to_write["state_json"] = state_json
            language_update = {
                "user_id": user_id,
                "en_production_confidence": language_state.en_production_confidence,
                "total_signals": language_state.total_signals,
            }

        mutation_result = await session.execute(
            text(
                """
                WITH inserted_event AS (
                    INSERT INTO learning_events
                        (source_event_key, user_id, domain, task_type, module_id,
                         session_id, node_id, skill_id, source, attempt_type, score,
                         confidence, criteria_json, evidence_json, blockers, gap,
                         scenario_json, caveats, model_name, prompt_version)
                    VALUES
                        (:source_event_key, :uid, :event_domain, :event_task_type,
                         :event_module_id, :event_session_id, :event_node_id,
                         :event_skill_id, :event_source, :event_attempt_type,
                         :event_score, :event_confidence,
                         CAST(:event_criteria_json AS jsonb),
                         CAST(:event_evidence_json AS jsonb),
                         CAST(:event_blockers AS jsonb), :event_gap,
                         CAST(:event_scenario_json AS jsonb),
                         CAST(:event_caveats AS jsonb), :event_model_name,
                         :event_prompt_version)
                    ON CONFLICT (source_event_key) DO NOTHING
                    RETURNING source_event_key
                ),
                profile_input AS (
                    SELECT *
                    FROM jsonb_to_recordset(CAST(:profile_upserts_json AS jsonb))
                    AS profile(
                        user_id text, domain text, skill_id text, module_id text,
                        task_type text, mastery real, readiness real,
                        confidence real, attempts integer, strengths_json jsonb,
                        gaps_json jsonb, evidence_json jsonb,
                        recommended_next_action text, source_summary text
                    )
                ),
                upserted_profiles AS (
                    INSERT INTO learner_skill_profiles
                        (user_id, domain, skill_id, module_id, task_type, mastery,
                         readiness, confidence, attempts, strengths_json, gaps_json,
                         evidence_json, recommended_next_action, source_summary)
                    SELECT profile.user_id, profile.domain, profile.skill_id,
                           profile.module_id, profile.task_type, profile.mastery,
                           profile.readiness, profile.confidence, profile.attempts,
                           profile.strengths_json, profile.gaps_json,
                           profile.evidence_json,
                           profile.recommended_next_action, profile.source_summary
                    FROM profile_input AS profile
                    CROSS JOIN inserted_event
                    ON CONFLICT (user_id, domain, skill_id) DO UPDATE SET
                        module_id = EXCLUDED.module_id,
                        task_type = EXCLUDED.task_type,
                        mastery = CASE
                            WHEN EXCLUDED.domain = 'school' THEN EXCLUDED.mastery
                            ELSE GREATEST(
                                learner_skill_profiles.mastery, EXCLUDED.mastery
                            )
                        END,
                        readiness = EXCLUDED.readiness,
                        confidence = EXCLUDED.confidence,
                        attempts = GREATEST(
                            learner_skill_profiles.attempts, EXCLUDED.attempts
                        ),
                        last_seen_at = now(),
                        strengths_json = EXCLUDED.strengths_json,
                        gaps_json = EXCLUDED.gaps_json,
                        evidence_json = EXCLUDED.evidence_json,
                        recommended_next_action = EXCLUDED.recommended_next_action,
                        source_summary = EXCLUDED.source_summary,
                        updated_at = now()
                    RETURNING skill_id
                ),
                language_input AS (
                    SELECT CAST(:language_update_json AS jsonb) AS value
                    WHERE CAST(:language_update_json AS jsonb) <> 'null'::jsonb
                ),
                upserted_language AS (
                    INSERT INTO school_language_confidence
                        (user_id, en_production_confidence, total_signals)
                    SELECT value->>'user_id',
                           (value->>'en_production_confidence')::real,
                           (value->>'total_signals')::integer
                    FROM language_input
                    CROSS JOIN inserted_event
                    ON CONFLICT (user_id) DO UPDATE SET
                        en_production_confidence = EXCLUDED.en_production_confidence,
                        total_signals = EXCLUDED.total_signals,
                        updated_at = now()
                    RETURNING user_id
                ),
                transitioned_session AS (
                    UPDATE school_sessions AS school
                    SET status = :session_status,
                        current_stage = :session_current_stage,
                        state_json = CAST(:session_state_json AS jsonb),
                        updated_at = now(),
                        completed_at = CASE
                            WHEN :session_status IN (
                                'complete', 'abandoned', 'expired',
                                'insufficient_evidence'
                            ) THEN COALESCE(school.completed_at, now())
                            ELSE school.completed_at
                        END
                    FROM inserted_event
                    WHERE school.session_id = CAST(:session_id AS uuid)
                      AND school.user_id = :uid
                      AND school.profile_version_id = CAST(:profile_version_id AS uuid)
                      AND school.status IN ('active', 'paused_for_masterclass')
                      AND school.state_json = CAST(:expected_state_json AS jsonb)
                    RETURNING school.session_id
                ),
                completed_request AS (
                    UPDATE school_answer_requests AS request
                    SET status = 'completed',
                        response_json = CAST(:response_json AS jsonb),
                        updated_at = now()
                    FROM transitioned_session
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                      AND request.answer_hash = :answer_hash
                      AND request.claim_token = :answer_claim_token
                      AND request.status = 'processing'
                    RETURNING request.activity_id
                )
                SELECT
                    EXISTS (SELECT 1 FROM inserted_event) AS inserted,
                    EXISTS (SELECT 1 FROM transitioned_session)
                        AS session_transitioned,
                    EXISTS (SELECT 1 FROM completed_request) AS request_completed,
                    (SELECT COUNT(*) FROM upserted_profiles) AS profile_upsert_count,
                    (SELECT COUNT(*) FROM upserted_language) AS language_upsert_count
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "activity_id": request_activity_id,
                "profile_version_id": profile_version_id,
                "expected_state_json": json.dumps(expected_state_json),
                "session_status": str(session_to_write["status"]),
                "session_current_stage": str(
                    session_to_write.get("current_stage") or ""
                ),
                "session_state_json": json.dumps(
                    session_to_write.get("state_json") or {}
                ),
                "answer_hash": request_answer_hash,
                "answer_claim_token": request_claim_token,
                "response_json": json.dumps(response_json),
                "profile_upserts_json": json.dumps(profile_upserts),
                "language_update_json": json.dumps(language_update),
                "source_event_key": learning_event["source_event_key"],
                "event_domain": learning_event["domain"],
                "event_task_type": learning_event["task_type"],
                "event_module_id": learning_event.get("module_id") or "",
                "event_session_id": learning_event.get("session_id"),
                "event_node_id": learning_event.get("node_id") or "",
                "event_skill_id": learning_event["skill_id"],
                "event_source": learning_event["source"],
                "event_attempt_type": learning_event.get("attempt_type") or "",
                "event_score": float(learning_event.get("score") or 0.0),
                "event_confidence": float(learning_event.get("confidence") or 0.0),
                "event_criteria_json": json.dumps(
                    learning_event.get("criteria_json") or []
                ),
                "event_evidence_json": json.dumps(
                    learning_event.get("evidence_json") or {}
                ),
                "event_blockers": json.dumps(learning_event.get("blockers") or []),
                "event_gap": learning_event.get("gap") or "",
                "event_scenario_json": json.dumps(
                    learning_event.get("scenario_json") or {}
                ),
                "event_caveats": json.dumps(learning_event.get("caveats") or []),
                "event_model_name": learning_event.get("model_name"),
                "event_prompt_version": learning_event.get("prompt_version"),
            },
        )
        mutation = dict(mutation_result.mappings().first() or {})
        if not mutation.get("inserted"):
            raise ValueError("duplicate_evidence_conflict")
        if not mutation.get("session_transitioned"):
            raise ValueError("stale_school_answer_session")
        if not mutation.get("request_completed"):
            raise ValueError("stale_school_answer_request")
        await session.commit()
        return {"outcome": "persisted"}
    except asyncio.CancelledError:
        await finish_cleanup(session.rollback())
        raise
    except Exception:
        await session.rollback()
        raise


async def persist_school_evaluated_curriculum_attempt(
    session: AsyncSession,
    *,
    learning_event: dict,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str,
    request_answer_hash: str,
    request_claim_token: str,
    response_json: dict,
    projection_evidence: dict | None,
    language_evaluation: dict | None,
    evaluation_job_completion: dict,
) -> dict:
    """Persist a queued curriculum answer in one locked read plus one bulk write.

    This is deliberately narrower than ``persist_school_answer_attempt``. It
    is only valid after the evaluator worker owns a live lease, so it can keep
    all the existing fences while avoiding serial cross-region queries for
    every learner-profile projection.
    """

    user_id = str(school_session.get("user_id") or "")
    session_id = str(school_session.get("session_id") or "")
    profile_version_id = str(school_session.get("profile_version_id") or "")
    if (
        school_session.get("api_version") != "rebuild"
        or school_session.get("flow_type") != "curriculum"
        or not user_id
        or not session_id
        or not profile_version_id
        or not request_activity_id
        or not request_answer_hash
        or not request_claim_token
        or not isinstance(expected_state_json, dict)
        or not isinstance(response_json, dict)
        or not isinstance(evaluation_job_completion, dict)
    ):
        raise ValueError("invalid_school_evaluated_curriculum_attempt")
    if (
        str(learning_event.get("user_id") or "") != user_id
        or str(learning_event.get("session_id") or "") != session_id
    ):
        raise ValueError("invalid_school_evaluated_curriculum_attempt")
    _validate_learning_domain_task(
        str(learning_event.get("domain") or ""),
        str(learning_event.get("task_type") or ""),
    )
    if (
        (school_session.get("state_json") or {}).get("profile_version_id")
        not in (None, "", profile_version_id)
    ):
        raise ValueError("school_session_lineage_conflict")

    required_identity = {
        "user_id": user_id,
        "session_id": session_id,
        "activity_id": str(request_activity_id),
        "answer_hash": str(request_answer_hash),
        "answer_claim_token": str(request_claim_token),
    }
    if any(
        str(evaluation_job_completion.get(key) or "") != value
        for key, value in required_identity.items()
    ):
        raise ValueError("invalid_school_evaluation_job_completion")
    lease_owner = str(evaluation_job_completion.get("lease_owner") or "").strip()
    lease_token = str(evaluation_job_completion.get("lease_token") or "").strip()
    try:
        lease_version = int(evaluation_job_completion.get("lease_version"))
    except (TypeError, ValueError):
        lease_version = 0
    job_response_json = evaluation_job_completion.get("response_json")
    job_result_data = evaluation_job_completion.get("result_data")
    if (
        not lease_owner
        or not lease_token
        or lease_version <= 0
        or not isinstance(job_response_json, dict)
        or not isinstance(job_result_data, dict)
        or job_response_json != response_json
    ):
        raise ValueError("invalid_school_evaluation_job_completion")

    try:
        context_result = await session.execute(
            text(
                """
                WITH advisory_lock AS (
                    SELECT pg_advisory_xact_lock(
                        hashtext('zidd_school_answer:' || :uid)
                    )
                ),
                learner_lineage AS (
                    SELECT learner.user_id
                    FROM learner_profiles AS learner
                    CROSS JOIN advisory_lock
                    WHERE learner.user_id = :uid
                    FOR UPDATE
                ),
                active_profile AS (
                    SELECT profile.profile_version_id::text AS profile_version_id
                    FROM school_profile_versions AS profile
                    CROSS JOIN learner_lineage
                    WHERE profile.user_id = :uid
                      AND profile.profile_version_id = CAST(:profile_version_id AS uuid)
                      AND profile.status = 'active'
                    FOR SHARE
                ),
                locked_request AS (
                    SELECT request.status AS request_status,
                           request.answer_hash AS request_answer_hash,
                           request.claim_token AS request_claim_token,
                           request.response_json AS request_response_json
                    FROM school_answer_requests AS request
                    CROSS JOIN active_profile
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                    FOR UPDATE
                ),
                locked_session AS (
                    SELECT school.state_json AS session_state_json,
                           school.status AS session_status,
                           school.profile_version_id::text AS session_profile_version_id
                    FROM school_sessions AS school
                    CROSS JOIN active_profile
                    WHERE school.session_id = CAST(:session_id AS uuid)
                      AND school.user_id = :uid
                    FOR UPDATE
                ),
                locked_profiles AS (
                    SELECT profile.user_id, profile.domain, profile.skill_id,
                           profile.module_id, profile.task_type, profile.mastery,
                           profile.readiness, profile.confidence, profile.attempts,
                           profile.strengths_json, profile.gaps_json,
                           profile.evidence_json,
                           profile.recommended_next_action,
                           profile.source_summary
                    FROM learner_skill_profiles AS profile
                    CROSS JOIN active_profile
                    WHERE profile.user_id = :uid
                      AND profile.domain = 'school'
                    FOR UPDATE
                ),
                profile_snapshot AS (
                    SELECT COALESCE(
                        jsonb_agg(to_jsonb(locked_profiles)), '[]'::jsonb
                    ) AS profile_rows_json
                    FROM locked_profiles
                ),
                locked_language AS (
                    SELECT language.en_production_confidence AS language_confidence,
                           language.total_signals AS language_total_signals
                    FROM school_language_confidence AS language
                    CROSS JOIN active_profile
                    WHERE language.user_id = :uid
                    FOR UPDATE
                ),
                locked_job AS (
                    SELECT job.status AS job_status,
                           job.answer_hash AS job_answer_hash,
                           job.answer_claim_token AS job_answer_claim_token,
                           job.user_id AS job_user_id,
                           job.lease_owner AS job_lease_owner,
                           job.lease_token AS job_lease_token,
                           job.lease_version AS job_lease_version
                    FROM school_evaluation_jobs AS job
                    CROSS JOIN active_profile
                    WHERE job.session_id = CAST(:session_id AS uuid)
                      AND job.activity_id = :activity_id
                      AND job.user_id = :uid
                    FOR UPDATE
                )
                SELECT
                    (SELECT profile_version_id FROM active_profile)
                        AS active_profile_version_id,
                    (SELECT request_status FROM locked_request) AS request_status,
                    (SELECT request_answer_hash FROM locked_request)
                        AS request_answer_hash,
                    (SELECT request_claim_token FROM locked_request)
                        AS request_claim_token,
                    (SELECT request_response_json FROM locked_request)
                        AS request_response_json,
                    (SELECT session_state_json FROM locked_session)
                        AS session_state_json,
                    (SELECT session_status FROM locked_session) AS session_status,
                    (SELECT session_profile_version_id FROM locked_session)
                        AS session_profile_version_id,
                    (SELECT profile_rows_json FROM profile_snapshot)
                        AS profile_rows_json,
                    (SELECT language_confidence FROM locked_language)
                        AS language_confidence,
                    (SELECT language_total_signals FROM locked_language)
                        AS language_total_signals,
                    (SELECT job_status FROM locked_job) AS job_status,
                    (SELECT job_answer_hash FROM locked_job) AS job_answer_hash,
                    (SELECT job_answer_claim_token FROM locked_job)
                        AS job_answer_claim_token,
                    (SELECT job_user_id FROM locked_job) AS job_user_id,
                    (SELECT job_lease_owner FROM locked_job) AS job_lease_owner,
                    (SELECT job_lease_token FROM locked_job) AS job_lease_token,
                    (SELECT job_lease_version FROM locked_job) AS job_lease_version
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "activity_id": request_activity_id,
                "profile_version_id": profile_version_id,
            },
        )
        context = dict(context_result.mappings().first() or {})
        if str(context.get("active_profile_version_id") or "") != profile_version_id:
            raise ValueError("stale_school_profile_lineage")
        if (
            str(context.get("request_status") or "") != "processing"
            or str(context.get("request_answer_hash") or "") != request_answer_hash
            or str(context.get("request_claim_token") or "") != request_claim_token
        ):
            raise ValueError("stale_school_answer_request")
        if (
            str(context.get("session_profile_version_id") or "")
            != profile_version_id
            or str(context.get("session_status") or "")
            not in _SCHOOL_ACTIVE_SESSION_STATUSES
        ):
            raise ValueError("stale_school_session_transition")
        current_state = context.get("session_state_json")
        if isinstance(current_state, str):
            current_state = json.loads(current_state)
        if not isinstance(current_state, dict) or current_state != expected_state_json:
            raise ValueError("stale_school_answer_session")
        if (
            str(context.get("job_status") or "") != "running"
            or str(context.get("job_answer_hash") or "") != request_answer_hash
            or str(context.get("job_answer_claim_token") or "") != request_claim_token
            or str(context.get("job_user_id") or "") != user_id
            or str(context.get("job_lease_owner") or "") != lease_owner
            or str(context.get("job_lease_token") or "") != lease_token
            or int(context.get("job_lease_version") or 0) != lease_version
        ):
            raise ValueError("stale_school_evaluation_job")

        profile_rows = context.get("profile_rows_json") or []
        if isinstance(profile_rows, str):
            profile_rows = json.loads(profile_rows)
        if not isinstance(profile_rows, list):
            raise ValueError("invalid_school_projection_context")
        profile_upserts: list[dict] = []
        if projection_evidence is not None:
            from app.services.school.projection import (
                SchoolAttemptEvidence,
                derive_school_projection_delta,
                enrich_school_projection_evidence,
            )

            projection = SchoolAttemptEvidence.from_dict(
                enrich_school_projection_evidence(
                    projection_evidence,
                    learning_event=learning_event,
                    user_id=user_id,
                    session_id=session_id,
                    activity_id=request_activity_id,
                    answer_hash=request_answer_hash,
                )
            )
            profile_upserts = derive_school_projection_delta(
                projection,
                [dict(row) for row in profile_rows if isinstance(row, dict)],
            )
            for profile in profile_upserts:
                profile["user_id"] = user_id

        session_to_write = dict(school_session)
        language_update: dict | None = None
        if language_evaluation is not None:
            from app.services.school.language_confidence import (
                LanguageConfidenceState,
                apply_curriculum_language_signal,
            )

            language_state = apply_curriculum_language_signal(
                LanguageConfidenceState(
                    user_id=user_id,
                    en_production_confidence=float(
                        context.get("language_confidence") or 0.0
                    ),
                    total_signals=int(context.get("language_total_signals") or 0),
                ),
                language_evaluation,
            )
            state_json = dict(session_to_write.get("state_json") or {})
            state_json.update(
                en_production_confidence=language_state.en_production_confidence,
                language_signal_count=language_state.total_signals,
            )
            session_to_write["state_json"] = state_json
            language_update = {
                "user_id": user_id,
                "en_production_confidence": language_state.en_production_confidence,
                "total_signals": language_state.total_signals,
            }

        mutation_result = await session.execute(
            text(
                """
                WITH inserted_event AS (
                    INSERT INTO learning_events
                        (source_event_key, user_id, domain, task_type, module_id,
                         session_id, node_id, skill_id, source, attempt_type, score,
                         confidence, criteria_json, evidence_json, blockers, gap,
                         scenario_json, caveats, model_name, prompt_version)
                    VALUES
                        (:source_event_key, :uid, :event_domain, :event_task_type,
                         :event_module_id, :event_session_id, :event_node_id,
                         :event_skill_id, :event_source, :event_attempt_type,
                         :event_score, :event_confidence,
                         CAST(:event_criteria_json AS jsonb),
                         CAST(:event_evidence_json AS jsonb),
                         CAST(:event_blockers AS jsonb), :event_gap,
                         CAST(:event_scenario_json AS jsonb),
                         CAST(:event_caveats AS jsonb), :event_model_name,
                         :event_prompt_version)
                    ON CONFLICT (source_event_key) DO NOTHING
                    RETURNING source_event_key
                ),
                profile_input AS (
                    SELECT *
                    FROM jsonb_to_recordset(CAST(:profile_upserts_json AS jsonb))
                    AS profile(
                        user_id text, domain text, skill_id text, module_id text,
                        task_type text, mastery real, readiness real,
                        confidence real, attempts integer, strengths_json jsonb,
                        gaps_json jsonb, evidence_json jsonb,
                        recommended_next_action text, source_summary text
                    )
                ),
                upserted_profiles AS (
                    INSERT INTO learner_skill_profiles
                        (user_id, domain, skill_id, module_id, task_type, mastery,
                         readiness, confidence, attempts, strengths_json, gaps_json,
                         evidence_json, recommended_next_action, source_summary)
                    SELECT profile.user_id, profile.domain, profile.skill_id,
                           profile.module_id, profile.task_type, profile.mastery,
                           profile.readiness, profile.confidence, profile.attempts,
                           profile.strengths_json, profile.gaps_json,
                           profile.evidence_json,
                           profile.recommended_next_action, profile.source_summary
                    FROM profile_input AS profile
                    CROSS JOIN inserted_event
                    ON CONFLICT (user_id, domain, skill_id) DO UPDATE SET
                        module_id = EXCLUDED.module_id,
                        task_type = EXCLUDED.task_type,
                        mastery = CASE
                            WHEN EXCLUDED.domain = 'school' THEN EXCLUDED.mastery
                            ELSE GREATEST(
                                learner_skill_profiles.mastery, EXCLUDED.mastery
                            )
                        END,
                        readiness = EXCLUDED.readiness,
                        confidence = EXCLUDED.confidence,
                        attempts = GREATEST(
                            learner_skill_profiles.attempts, EXCLUDED.attempts
                        ),
                        last_seen_at = now(),
                        strengths_json = EXCLUDED.strengths_json,
                        gaps_json = EXCLUDED.gaps_json,
                        evidence_json = EXCLUDED.evidence_json,
                        recommended_next_action = EXCLUDED.recommended_next_action,
                        source_summary = EXCLUDED.source_summary,
                        updated_at = now()
                    RETURNING skill_id
                ),
                language_input AS (
                    SELECT CAST(:language_update_json AS jsonb) AS value
                    WHERE CAST(:language_update_json AS jsonb) <> 'null'::jsonb
                ),
                upserted_language AS (
                    INSERT INTO school_language_confidence
                        (user_id, en_production_confidence, total_signals)
                    SELECT value->>'user_id',
                           (value->>'en_production_confidence')::real,
                           (value->>'total_signals')::integer
                    FROM language_input
                    CROSS JOIN inserted_event
                    ON CONFLICT (user_id) DO UPDATE SET
                        en_production_confidence = EXCLUDED.en_production_confidence,
                        total_signals = EXCLUDED.total_signals,
                        updated_at = now()
                    RETURNING user_id
                ),
                transitioned_session AS (
                    UPDATE school_sessions AS school
                    SET status = :session_status,
                        current_stage = :session_current_stage,
                        state_json = CAST(:session_state_json AS jsonb),
                        updated_at = now(),
                        completed_at = CASE
                            WHEN :session_status IN (
                                'complete', 'abandoned', 'expired',
                                'insufficient_evidence'
                            ) THEN COALESCE(school.completed_at, now())
                            ELSE school.completed_at
                        END
                    FROM inserted_event
                    WHERE school.session_id = CAST(:session_id AS uuid)
                      AND school.user_id = :uid
                      AND school.profile_version_id = CAST(:profile_version_id AS uuid)
                      AND school.status IN ('active', 'paused_for_masterclass')
                      AND school.state_json = CAST(:expected_state_json AS jsonb)
                    RETURNING school.session_id
                ),
                completed_job AS (
                    UPDATE school_evaluation_jobs AS job
                    SET status = 'completed',
                        response_json = CAST(:evaluation_job_response_json AS jsonb),
                        result_data = CAST(:evaluation_job_result_data AS jsonb),
                        last_error_code = NULL,
                        error_json = NULL,
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        completed_at = now(),
                        updated_at = now()
                    FROM transitioned_session
                    WHERE job.session_id = CAST(:session_id AS uuid)
                      AND job.activity_id = :activity_id
                      AND job.user_id = :uid
                      AND job.answer_hash = :answer_hash
                      AND job.answer_claim_token = :answer_claim_token
                      AND job.lease_owner = :lease_owner
                      AND job.lease_token = :lease_token
                      AND job.lease_version = :lease_version
                      AND job.status = 'running'
                      AND job.lease_expires_at > now()
                      AND EXISTS (
                          SELECT 1
                          FROM school_answer_requests AS request
                          WHERE request.session_id = job.session_id
                            AND request.activity_id = job.activity_id
                            AND request.user_id = job.user_id
                            AND request.answer_hash = job.answer_hash
                            AND request.claim_token = job.answer_claim_token
                            AND request.status = 'processing'
                      )
                    RETURNING job.activity_id
                ),
                completed_request AS (
                    UPDATE school_answer_requests AS request
                    SET status = 'completed',
                        response_json = CAST(:response_json AS jsonb),
                        updated_at = now()
                    FROM completed_job
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                      AND request.answer_hash = :answer_hash
                      AND request.claim_token = :answer_claim_token
                      AND request.status = 'processing'
                    RETURNING request.activity_id
                )
                SELECT
                    EXISTS (SELECT 1 FROM inserted_event) AS inserted,
                    EXISTS (SELECT 1 FROM transitioned_session)
                        AS session_transitioned,
                    EXISTS (SELECT 1 FROM completed_job) AS job_completed,
                    EXISTS (SELECT 1 FROM completed_request) AS request_completed,
                    (SELECT COUNT(*) FROM upserted_profiles) AS profile_upsert_count,
                    (SELECT COUNT(*) FROM upserted_language) AS language_upsert_count
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "activity_id": request_activity_id,
                "profile_version_id": profile_version_id,
                "expected_state_json": json.dumps(expected_state_json),
                "session_status": str(session_to_write["status"]),
                "session_current_stage": str(
                    session_to_write.get("current_stage") or ""
                ),
                "session_state_json": json.dumps(
                    session_to_write.get("state_json") or {}
                ),
                "answer_hash": request_answer_hash,
                "answer_claim_token": request_claim_token,
                "lease_owner": lease_owner,
                "lease_token": lease_token,
                "lease_version": lease_version,
                "response_json": json.dumps(response_json),
                "evaluation_job_response_json": json.dumps(job_response_json),
                "evaluation_job_result_data": json.dumps(job_result_data),
                "profile_upserts_json": json.dumps(profile_upserts),
                "language_update_json": json.dumps(language_update),
                "source_event_key": learning_event["source_event_key"],
                "event_domain": learning_event["domain"],
                "event_task_type": learning_event["task_type"],
                "event_module_id": learning_event.get("module_id") or "",
                "event_session_id": learning_event.get("session_id"),
                "event_node_id": learning_event.get("node_id") or "",
                "event_skill_id": learning_event["skill_id"],
                "event_source": learning_event["source"],
                "event_attempt_type": learning_event.get("attempt_type") or "",
                "event_score": float(learning_event.get("score") or 0.0),
                "event_confidence": float(learning_event.get("confidence") or 0.0),
                "event_criteria_json": json.dumps(
                    learning_event.get("criteria_json") or []
                ),
                "event_evidence_json": json.dumps(
                    learning_event.get("evidence_json") or {}
                ),
                "event_blockers": json.dumps(learning_event.get("blockers") or []),
                "event_gap": learning_event.get("gap") or "",
                "event_scenario_json": json.dumps(
                    learning_event.get("scenario_json") or {}
                ),
                "event_caveats": json.dumps(learning_event.get("caveats") or []),
                "event_model_name": learning_event.get("model_name"),
                "event_prompt_version": learning_event.get("prompt_version"),
            },
        )
        mutation = dict(mutation_result.mappings().first() or {})
        if not mutation.get("inserted"):
            raise ValueError("duplicate_evidence_conflict")
        if not mutation.get("session_transitioned"):
            raise ValueError("stale_school_answer_session")
        if not mutation.get("job_completed"):
            raise ValueError("stale_school_evaluation_job")
        if not mutation.get("request_completed"):
            raise ValueError("stale_school_answer_request")
        await session.commit()
        return {"outcome": "persisted"}
    except asyncio.CancelledError:
        await finish_cleanup(session.rollback())
        raise
    except Exception:
        await session.rollback()
        raise


async def persist_school_curriculum_experience_step(
    session: AsyncSession,
    *,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str,
    request_answer_hash: str,
    response_json: dict,
) -> dict:
    """Advance an unscored curriculum acknowledgement without evidence writes.

    A ``continue`` activity changes the durable lesson position but does not
    measure a skill. Sending it through ``persist_school_answer_attempt``
    needlessly locks every School skill profile and records a zero-value
    learning event. This focused transaction keeps the same request replay,
    profile-lineage, and session CAS guarantees while avoiding those unrelated
    reads and writes.
    """

    user_id = str(school_session["user_id"])
    session_id = str(school_session["session_id"])
    profile_version_id = str(school_session.get("profile_version_id") or "")
    if (
        school_session.get("api_version") != "rebuild"
        or school_session.get("flow_type") != "curriculum"
        or not profile_version_id
        or not request_activity_id
        or not request_answer_hash
    ):
        raise ValueError("invalid_school_curriculum_experience_step")
    embedded_profile_version_id = (school_session.get("state_json") or {}).get(
        "profile_version_id"
    )
    if (
        embedded_profile_version_id not in (None, "")
        and str(embedded_profile_version_id) != profile_version_id
    ):
        raise ValueError("school_session_lineage_conflict")

    try:
        result = await session.execute(
            text(
                """
                WITH advisory_lock AS (
                    SELECT pg_advisory_xact_lock(
                        hashtext('zidd_school_answer:' || :uid)
                    )
                ),
                learner_lineage AS (
                    SELECT learner.user_id
                    FROM learner_profiles AS learner
                    CROSS JOIN advisory_lock
                    WHERE learner.user_id = :uid
                    FOR UPDATE
                ),
                active_profile AS (
                    SELECT profile.profile_version_id
                    FROM school_profile_versions AS profile
                    CROSS JOIN learner_lineage
                    WHERE profile.user_id = :uid
                      AND profile.profile_version_id = CAST(:profile_version_id AS uuid)
                      AND profile.status = 'active'
                    FOR SHARE
                ),
                locked_request AS (
                    SELECT request.status, request.answer_hash,
                           request.response_json, request.claim_token
                    FROM school_answer_requests AS request
                    CROSS JOIN active_profile
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                    FOR UPDATE
                ),
                claimed_request AS (
                    INSERT INTO school_answer_requests
                        (session_id, activity_id, user_id, answer_hash,
                         claim_token, status, response_json)
                    SELECT CAST(:session_id AS uuid), :activity_id, :uid,
                           :answer_hash, :claim_token, 'completed',
                           CAST(:response_json AS jsonb)
                    FROM active_profile
                    WHERE NOT EXISTS (SELECT 1 FROM locked_request)
                    RETURNING status, answer_hash, response_json, claim_token,
                              'claimed'::text AS origin
                ),
                reclaimed_request AS (
                    UPDATE school_answer_requests AS request
                    SET answer_hash = :answer_hash,
                        claim_token = :claim_token,
                        status = 'completed',
                        response_json = CAST(:response_json AS jsonb),
                        updated_at = now()
                    FROM locked_request
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                      AND request.user_id = :uid
                      AND locked_request.status = 'failed'
                    RETURNING request.status, request.answer_hash,
                              request.response_json, request.claim_token,
                              'reclaimed'::text AS origin
                ),
                request_resolution AS (
                    SELECT status, answer_hash, response_json, claim_token,
                           'existing'::text AS origin
                    FROM locked_request
                    WHERE status <> 'failed'
                    UNION ALL
                    SELECT status, answer_hash, response_json, claim_token, origin
                    FROM claimed_request
                    UNION ALL
                    SELECT status, answer_hash, response_json, claim_token, origin
                    FROM reclaimed_request
                ),
                transitioned_session AS (
                    UPDATE school_sessions AS school
                    SET status = :status,
                        current_stage = :current_stage,
                        state_json = CAST(:state_json AS jsonb),
                        updated_at = now(),
                        completed_at = CASE
                            WHEN :status IN (
                                'complete', 'abandoned', 'expired',
                                'insufficient_evidence'
                            ) THEN COALESCE(school.completed_at, now())
                            ELSE school.completed_at
                        END
                    FROM request_resolution
                    CROSS JOIN active_profile
                    WHERE request_resolution.origin IN ('claimed', 'reclaimed')
                      AND school.session_id = CAST(:session_id AS uuid)
                      AND school.user_id = :uid
                      AND school.api_version = 'rebuild'
                      AND school.flow_type = 'curriculum'
                      AND school.status = 'active'
                      AND school.profile_version_id = active_profile.profile_version_id
                      AND school.state_json = CAST(:expected_state_json AS jsonb)
                    RETURNING school.session_id
                )
                SELECT request_resolution.origin,
                       request_resolution.status,
                       request_resolution.answer_hash,
                       request_resolution.response_json,
                       EXISTS(
                           SELECT 1 FROM transitioned_session
                       ) AS session_transitioned
                FROM request_resolution
                """
            ),
            {
                "uid": user_id,
                "profile_version_id": profile_version_id,
                "session_id": session_id,
                "activity_id": request_activity_id,
                "answer_hash": request_answer_hash,
                "claim_token": str(uuid4()),
                "response_json": json.dumps(response_json),
                "status": str(school_session["status"]),
                "current_stage": str(school_session.get("current_stage") or ""),
                "state_json": json.dumps(school_session.get("state_json") or {}),
                "expected_state_json": json.dumps(expected_state_json or {}),
            },
        )
        row = result.mappings().first()
        if row is None:
            raise ValueError("stale_school_profile_lineage")
        origin = str(row["origin"] or "")
        status = str(row["status"] or "")
        existing_hash = str(row["answer_hash"] or "")
        if origin == "existing":
            if status == "completed":
                if existing_hash != request_answer_hash:
                    raise ValueError("duplicate_evidence_conflict")
                replay = row["response_json"]
                if isinstance(replay, str):
                    replay = json.loads(replay)
                await session.commit()
                return {
                    "outcome": "replayed",
                    "response_json": dict(replay or {}),
                }
            raise ValueError("stale_school_answer_request")
        if origin not in {"claimed", "reclaimed"} or not bool(
            row["session_transitioned"]
        ):
            raise ValueError("stale_school_answer_session")
        await session.commit()
        return {"outcome": "persisted"}
    except asyncio.CancelledError:
        await finish_cleanup(session.rollback())
        raise
    except Exception:
        await session.rollback()
        raise


async def get_school_answer_request(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT request.session_id::text AS session_id, request.activity_id,
                   request.user_id, request.answer_hash, request.claim_token,
                   request.status, request.response_json, request.created_at,
                   request.updated_at,
                   EXTRACT(EPOCH FROM (now() - request.updated_at)) AS age_seconds,
                   job.status AS evaluation_job_status,
                   (
                       job.status IN ('queued', 'running')
                       AND job.created_at > now() - (
                           CAST(:evaluation_deadline_seconds AS integer)
                           * INTERVAL '1 second'
                       )
                   ) AS evaluation_job_within_deadline
            FROM school_answer_requests AS request
            LEFT JOIN school_evaluation_jobs AS job
              ON job.session_id = request.session_id
             AND job.activity_id = request.activity_id
             AND job.user_id = request.user_id
             AND job.answer_hash = request.answer_hash
             AND job.answer_claim_token = request.claim_token
            WHERE request.session_id = CAST(:session_id AS uuid)
              AND request.activity_id = :activity_id
              AND request.user_id = :uid
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().first()
    if not row:
        return None
    data = dict(row)
    if isinstance(data.get("response_json"), str):
        data["response_json"] = json.loads(data["response_json"])
    data["stale"] = bool(
        data.get("status") == "processing"
        and float(data.get("age_seconds") or 0.0) >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
    )
    return data


async def get_school_placement_answer_context(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict:
    """Load the placement-answer preflight in one database round trip.

    School placement answers need three related values after authentication:
    the active School profile, exact session, and any prior idempotency
    request. Fetching them through independently
    pooled store calls made deterministic multiple-choice answers pay multiple
    cross-region round trips. The values are a read snapshot only; the claim
    and final answer transition remain their existing atomic operations.
    """

    result = await session.execute(
        text(
            """
            WITH active_profile AS (
                SELECT to_jsonb(profile) AS payload
                FROM school_profile_versions AS profile
                WHERE profile.user_id = :uid AND profile.status = 'active'
                ORDER BY profile.activated_at DESC NULLS LAST, profile.updated_at DESC
                LIMIT 1
            ),
            placement_session AS (
                SELECT to_jsonb(school_session) AS payload
                FROM school_sessions AS school_session
                WHERE school_session.user_id = :uid
                  AND school_session.session_id = CAST(:session_id AS uuid)
                LIMIT 1
            ),
            answer_request AS (
                SELECT
                    to_jsonb(request)
                    || jsonb_build_object(
                        'age_seconds', EXTRACT(EPOCH FROM (now() - request.updated_at)),
                        'evaluation_job_status', job.status,
                        'evaluation_job_within_deadline', (
                            job.status IN ('queued', 'running')
                            AND job.created_at > now() - (
                                CAST(:evaluation_deadline_seconds AS integer)
                                * INTERVAL '1 second'
                            )
                        )
                    ) AS payload
                FROM school_answer_requests AS request
                LEFT JOIN school_evaluation_jobs AS job
                  ON job.session_id = request.session_id
                 AND job.activity_id = request.activity_id
                 AND job.user_id = request.user_id
                 AND job.answer_hash = request.answer_hash
                 AND job.answer_claim_token = request.claim_token
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                LIMIT 1
            )
            SELECT
                (SELECT payload FROM active_profile) AS active_profile,
                (SELECT payload FROM placement_session) AS school_session,
                (SELECT payload FROM answer_request) AS answer_request
            """
        ),
        {
            "uid": user_id,
            "session_id": session_id,
            "activity_id": activity_id,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().one()

    def payload_dict(value: object) -> dict | None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        return dict(value) if isinstance(value, dict) else None

    request = payload_dict(row.get("answer_request"))
    if request is not None:
        request["stale"] = bool(
            request.get("status") == "processing"
            and float(request.get("age_seconds") or 0.0)
            >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
        )
    return {
        "active_profile": payload_dict(row.get("active_profile")),
        "school_session": payload_dict(row.get("school_session")),
        "answer_request": request,
    }


async def get_school_masterclass_answer_context(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict:
    """Load a masterclass-answer preflight from one database connection.

    This deliberately mirrors the placement preflight rather than moving the
    answer claim into a read query. The returned rows are only an authorization
    and idempotency snapshot; claim and answer persistence retain their
    existing fenced transactions.
    """

    result = await session.execute(
        text(
            """
            WITH active_profile AS (
                SELECT to_jsonb(profile) AS payload
                FROM school_profile_versions AS profile
                WHERE profile.user_id = :uid AND profile.status = 'active'
                ORDER BY profile.activated_at DESC NULLS LAST, profile.updated_at DESC
                LIMIT 1
            ),
            masterclass_session AS (
                SELECT to_jsonb(school_session) AS payload
                FROM school_sessions AS school_session
                WHERE school_session.user_id = :uid
                  AND school_session.session_id = CAST(:session_id AS uuid)
                LIMIT 1
            ),
            answer_request AS (
                SELECT
                    to_jsonb(request)
                    || jsonb_build_object(
                        'age_seconds', EXTRACT(EPOCH FROM (now() - request.updated_at)),
                        'evaluation_job_status', job.status,
                        'evaluation_job_within_deadline', (
                            job.status IN ('queued', 'running')
                            AND job.created_at > now() - (
                                CAST(:evaluation_deadline_seconds AS integer)
                                * INTERVAL '1 second'
                            )
                        )
                    ) AS payload
                FROM school_answer_requests AS request
                LEFT JOIN school_evaluation_jobs AS job
                  ON job.session_id = request.session_id
                 AND job.activity_id = request.activity_id
                 AND job.user_id = request.user_id
                 AND job.answer_hash = request.answer_hash
                 AND job.answer_claim_token = request.claim_token
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                LIMIT 1
            )
            SELECT
                (SELECT payload FROM active_profile) AS active_profile,
                (SELECT payload FROM masterclass_session) AS school_session,
                (SELECT payload FROM answer_request) AS answer_request
            """
        ),
        {
            "uid": user_id,
            "session_id": session_id,
            "activity_id": activity_id,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().one()

    def payload_dict(value: object) -> dict | None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        return dict(value) if isinstance(value, dict) else None

    request = payload_dict(row.get("answer_request"))
    if request is not None:
        request["stale"] = bool(
            request.get("status") == "processing"
            and float(request.get("age_seconds") or 0.0)
            >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
        )
    return {
        "active_profile": payload_dict(row.get("active_profile")),
        "school_session": payload_dict(row.get("school_session")),
        "answer_request": request,
    }


async def get_school_answer_status_context(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict:
    """Load the complete public-lineage snapshot for one pending School answer.

    This is intentionally narrower than the learner dashboard: a status poll
    needs exactly one session, its source report, optional linked parent, and
    the idempotency request.  It must never hydrate every profile, report, or
    active session merely to learn whether an evaluator has completed.
    """

    result = await session.execute(
        text(
            """
            WITH active_profile AS (
                SELECT to_jsonb(profile) AS payload
                FROM school_profile_versions AS profile
                WHERE profile.user_id = :uid AND profile.status = 'active'
                ORDER BY profile.activated_at DESC NULLS LAST, profile.updated_at DESC
                LIMIT 1
            ),
            target_session AS (
                SELECT school_session.*
                FROM school_sessions AS school_session
                WHERE school_session.user_id = :uid
                  AND school_session.session_id = CAST(:session_id AS uuid)
                LIMIT 1
            ),
            placement_report AS (
                SELECT to_jsonb(report) AS payload
                FROM school_placement_reports AS report
                JOIN target_session AS school_session
                  ON school_session.source_placement_report_id = report.report_id
                WHERE report.user_id = :uid
                LIMIT 1
            ),
            linked_parent AS (
                SELECT to_jsonb(parent_session) AS payload
                FROM school_sessions AS parent_session
                JOIN target_session AS child_session
                  ON parent_session.session_id = child_session.linked_session_id
                WHERE parent_session.user_id = :uid
                LIMIT 1
            ),
            answer_request AS (
                SELECT
                    to_jsonb(request)
                    || jsonb_build_object(
                        'age_seconds', EXTRACT(EPOCH FROM (now() - request.updated_at)),
                        'evaluation_job_status', job.status,
                        'evaluation_job_within_deadline', (
                            job.status IN ('queued', 'running')
                            AND job.created_at > now() - (
                                CAST(:evaluation_deadline_seconds AS integer)
                                * INTERVAL '1 second'
                            )
                        )
                    ) AS payload
                FROM school_answer_requests AS request
                LEFT JOIN school_evaluation_jobs AS job
                  ON job.session_id = request.session_id
                 AND job.activity_id = request.activity_id
                 AND job.user_id = request.user_id
                 AND job.answer_hash = request.answer_hash
                 AND job.answer_claim_token = request.claim_token
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                LIMIT 1
            )
            SELECT
                (SELECT payload FROM active_profile) AS active_profile,
                (SELECT to_jsonb(school_session) FROM target_session AS school_session)
                    AS school_session,
                (SELECT payload FROM placement_report) AS placement_report,
                (SELECT payload FROM linked_parent) AS linked_parent,
                (SELECT payload FROM answer_request) AS answer_request
            """
        ),
        {
            "uid": user_id,
            "session_id": session_id,
            "activity_id": activity_id,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().one()

    def payload_dict(value: object) -> dict | None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        return dict(value) if isinstance(value, dict) else None

    request = payload_dict(row.get("answer_request"))
    if request is not None:
        request["stale"] = bool(
            request.get("status") == "processing"
            and float(request.get("age_seconds") or 0.0)
            >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
        )
    report = payload_dict(row.get("placement_report"))
    return {
        "active_profile": payload_dict(row.get("active_profile")),
        "school_session": payload_dict(row.get("school_session")),
        "placement_report": (
            _school_placement_report_from_row(report) if report is not None else None
        ),
        "linked_parent": payload_dict(row.get("linked_parent")),
        "answer_request": request,
    }


async def get_school_curriculum_answer_context(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict:
    """Load a curriculum-answer preflight without hydrating School home state.

    A curriculum submission needs the exact persisted session, its source
    placement report, the active profile, and a possible idempotency request.
    The learner dashboard snapshot also materializes linked sessions and every
    School skill profile, which adds avoidable cross-region payload and query
    work to each answer. This read remains non-authoritative: the claim and
    final transition keep their existing fenced transactions.
    """

    result = await session.execute(
        text(
            """
            WITH active_profile AS (
                SELECT to_jsonb(profile) AS payload
                FROM school_profile_versions AS profile
                WHERE profile.user_id = :uid AND profile.status = 'active'
                ORDER BY profile.activated_at DESC NULLS LAST, profile.updated_at DESC
                LIMIT 1
            ),
            curriculum_session AS (
                SELECT school_session.*
                FROM school_sessions AS school_session
                WHERE school_session.user_id = :uid
                  AND school_session.session_id = CAST(:session_id AS uuid)
                LIMIT 1
            ),
            placement_report AS (
                SELECT to_jsonb(report) AS payload
                FROM school_placement_reports AS report
                JOIN curriculum_session AS school_session
                  ON school_session.source_placement_report_id = report.report_id
                WHERE report.user_id = :uid
                LIMIT 1
            ),
            answer_request AS (
                SELECT
                    to_jsonb(request)
                    || jsonb_build_object(
                        'age_seconds', EXTRACT(EPOCH FROM (now() - request.updated_at)),
                        'evaluation_job_status', job.status,
                        'evaluation_job_within_deadline', (
                            job.status IN ('queued', 'running')
                            AND job.created_at > now() - (
                                CAST(:evaluation_deadline_seconds AS integer)
                                * INTERVAL '1 second'
                            )
                        )
                    ) AS payload
                FROM school_answer_requests AS request
                LEFT JOIN school_evaluation_jobs AS job
                  ON job.session_id = request.session_id
                 AND job.activity_id = request.activity_id
                 AND job.user_id = request.user_id
                 AND job.answer_hash = request.answer_hash
                 AND job.answer_claim_token = request.claim_token
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                LIMIT 1
            )
            SELECT
                (SELECT payload FROM active_profile) AS active_profile,
                (SELECT to_jsonb(school_session) FROM curriculum_session AS school_session)
                    AS school_session,
                (SELECT payload FROM placement_report) AS placement_report,
                (SELECT payload FROM answer_request) AS answer_request
            """
        ),
        {
            "uid": user_id,
            "session_id": session_id,
            "activity_id": activity_id,
            "evaluation_deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
        },
    )
    row = result.mappings().one()

    def payload_dict(value: object) -> dict | None:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                return None
        return dict(value) if isinstance(value, dict) else None

    request = payload_dict(row.get("answer_request"))
    if request is not None:
        request["stale"] = bool(
            request.get("status") == "processing"
            and float(request.get("age_seconds") or 0.0)
            >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
        )
    report = payload_dict(row.get("placement_report"))
    return {
        "active_profile": payload_dict(row.get("active_profile")),
        "school_session": payload_dict(row.get("school_session")),
        "placement_report": (
            _school_placement_report_from_row(report) if report is not None else None
        ),
        "answer_request": request,
    }


async def claim_school_answer_request(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
) -> dict:
    lock_key = f"school-answer:{session_id}:{activity_id}"
    claim_token = str(uuid4())
    try:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {"lock_key": lock_key},
        )
        existing_result = await session.execute(
            text(
                """
                SELECT user_id, answer_hash, claim_token, status, response_json,
                       EXTRACT(EPOCH FROM (now() - updated_at)) AS age_seconds
                FROM school_answer_requests
                WHERE session_id = CAST(:session_id AS uuid)
                  AND activity_id = :activity_id
                FOR UPDATE
                """
            ),
            {"session_id": session_id, "activity_id": activity_id},
        )
        existing = existing_result.mappings().first()
        if existing:
            row = dict(existing)
            status = str(row.get("status") or "")
            if row.get("user_id") != user_id:
                await session.rollback()
                return {"outcome": "conflict"}
            if status != "failed" and row.get("answer_hash") != answer_hash:
                await session.rollback()
                return {"outcome": "conflict"}
            if status == "completed":
                await session.rollback()
                response = row.get("response_json")
                if isinstance(response, str):
                    response = json.loads(response)
                return {"outcome": "completed", "response_json": response}
            stale = (
                status == "processing"
                and float(row.get("age_seconds") or 0.0)
                >= _SCHOOL_ANSWER_REQUEST_STALE_SECONDS
            )
            if status == "processing" and not stale:
                await session.rollback()
                return {"outcome": "in_progress"}
            await session.execute(
                text(
                    """
                    UPDATE school_answer_requests
                    SET status = 'processing', response_json = NULL,
                        answer_hash = :answer_hash,
                        claim_token = :claim_token, updated_at = now()
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND activity_id = :activity_id
                    """
                ),
                {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "answer_hash": answer_hash,
                    "claim_token": claim_token,
                },
            )
            await session.commit()
            return {"outcome": "claimed", "claim_token": claim_token}

        await session.execute(
            text(
                """
                INSERT INTO school_answer_requests
                    (session_id, activity_id, user_id, answer_hash, claim_token, status)
                VALUES
                    (CAST(:session_id AS uuid), :activity_id, :uid, :answer_hash,
                     :claim_token, 'processing')
                """
            ),
            {
                "session_id": session_id,
                "activity_id": activity_id,
                "uid": user_id,
                "answer_hash": answer_hash,
                "claim_token": claim_token,
            },
        )
        await session.commit()
        return {"outcome": "claimed", "claim_token": claim_token}
    except Exception:
        await session.rollback()
        raise


async def fail_school_answer_request(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    claim_token: str,
    *,
    placement_retry_timing: dict | None = None,
) -> None:
    if placement_retry_timing is not None:
        await session.execute(
            text(
                """
                UPDATE school_sessions
                SET state_json = jsonb_set(
                        state_json,
                        '{_placement_item_timing}',
                        CAST(:placement_retry_timing AS jsonb),
                        true
                    ),
                    updated_at = now()
                WHERE user_id = :uid
                  AND session_id = CAST(:session_id AS uuid)
                  AND api_version = 'rebuild'
                  AND flow_type = 'placement'
                  AND status = 'active'
                  AND state_json #>> '{_placement_item_timing,item_id}' = :activity_id
                  AND EXISTS (
                      SELECT 1
                      FROM school_answer_requests request
                      WHERE request.session_id = school_sessions.session_id
                        AND request.activity_id = :activity_id
                        AND request.user_id = :uid
                        AND request.answer_hash = :answer_hash
                        AND request.claim_token = :claim_token
                        AND request.status = 'processing'
                  )
                """
            ),
            {
                "uid": user_id,
                "session_id": session_id,
                "activity_id": activity_id,
                "answer_hash": answer_hash,
                "claim_token": claim_token,
                "placement_retry_timing": json.dumps(placement_retry_timing),
            },
        )
    await session.execute(
        text(
            """
            UPDATE school_answer_requests
            SET status = 'failed', response_json = NULL, updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND claim_token = :claim_token
              AND status = 'processing'
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "claim_token": claim_token,
        },
    )
    await session.commit()


async def renew_school_answer_request(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    claim_token: str,
) -> bool:
    result = await session.execute(
        text(
            """
            UPDATE school_answer_requests
            SET updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND claim_token = :claim_token
              AND status = 'processing'
            RETURNING activity_id
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "claim_token": claim_token,
        },
    )
    renewed = result.scalar_one_or_none() is not None
    await session.commit()
    return renewed


def _school_evaluation_job_from_row(row) -> dict:
    data = dict(row)
    for key in (
        "expected_state_json",
        "request_metadata_json",
        "error_json",
        "response_json",
        "result_data",
    ):
        if isinstance(data.get(key), str):
            data[key] = json.loads(data[key])
    return data


def _school_evaluation_job_queue_view(job: dict) -> dict:
    """Return queue metadata suitable for route-level outcome handling."""
    return {
        key: job.get(key)
        for key in (
            "session_id",
            "activity_id",
            "status",
            "attempts",
            "max_attempts",
            "lease_version",
            "lease_expires_at",
            "next_attempt_at",
            "last_error_code",
            "error_json",
            "created_at",
            "updated_at",
            "started_at",
            "completed_at",
            "failed_at",
            "cancelled_at",
        )
    }


def _school_evaluation_job_expected_state_digest(expected_state_json: dict) -> str:
    encoded = json.dumps(
        expected_state_json,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _school_evaluation_job_request_metadata(
    request_metadata: dict | None,
) -> dict:
    if request_metadata is None:
        return {}
    if not isinstance(request_metadata, dict):
        raise ValueError("invalid_school_evaluation_job_request_metadata")
    return request_metadata


def _school_evaluation_job_lease_seconds(lease_seconds: int) -> int:
    normalized = int(lease_seconds)
    if normalized <= 0:
        raise ValueError("invalid_school_evaluation_job_lease_seconds")
    return normalized


def _school_evaluation_job_max_attempts(max_attempts: int) -> int:
    normalized = int(max_attempts)
    if normalized <= 0:
        raise ValueError("invalid_school_evaluation_job_max_attempts")
    return normalized


def _school_evaluation_job_lease_owner(lease_owner: str) -> str:
    normalized = str(lease_owner or "").strip()
    if not normalized:
        raise ValueError("invalid_school_evaluation_job_lease_owner")
    return normalized


def _school_evaluation_job_retry_after_seconds(
    retry_after_seconds: float | int | None,
) -> float:
    try:
        normalized = float(retry_after_seconds or 0)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_school_evaluation_job_retry_after_seconds") from exc
    if (
        not math.isfinite(normalized)
        or normalized < 0
        or normalized > _SCHOOL_EVALUATION_JOB_MAX_RETRY_DELAY_SECONDS
    ):
        raise ValueError("invalid_school_evaluation_job_retry_after_seconds")
    return normalized


async def get_school_evaluation_job(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, activity_id, user_id,
                   raw_answer, expected_state_json, request_metadata_json,
                   expected_state_digest,
                   answer_hash, answer_claim_token, flow_type, evaluation_mode,
                   status, attempts, max_attempts, lease_owner, lease_token,
                   lease_version, lease_expires_at, next_attempt_at, last_error_code, error_json,
                   response_json, result_data, created_at, updated_at, started_at,
                   completed_at, failed_at, cancelled_at
            FROM school_evaluation_jobs
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
            """
        ),
        {"session_id": session_id, "activity_id": activity_id, "uid": user_id},
    )
    row = result.mappings().first()
    return _school_evaluation_job_from_row(row) if row else None


async def get_school_evaluation_job_status(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict | None:
    """Return learner-safe evaluator metadata without its answer payload."""
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, activity_id, status,
                   attempts, max_attempts, next_attempt_at, last_error_code,
                   created_at, updated_at, started_at, completed_at,
                   failed_at, cancelled_at
            FROM school_evaluation_jobs
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
            """
        ),
        {"session_id": session_id, "activity_id": activity_id, "uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def claim_and_enqueue_school_evaluation_job_atomic(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    raw_answer: str,
    expected_state_json: dict,
    answer_hash: str,
    flow_type: str,
    evaluation_mode: str,
    max_attempts: int = 3,
    request_metadata: dict | None = None,
) -> dict:
    """Durably enqueue one semantic answer with one locked database mutation.

    The generic queue method remains the compatibility fallback for stores that
    do not have Postgres transaction support.  This path keeps its exact
    duplicate and fencing outcomes, but avoids serial cross-region round trips
    before the learner can receive the durable ``awaiting_evaluation`` response.
    """
    if not isinstance(raw_answer, str):
        raise ValueError("invalid_school_evaluation_job_answer")
    if not isinstance(expected_state_json, dict):
        raise ValueError("invalid_school_evaluation_job_expected_state")
    normalized_flow_type = str(flow_type or "").strip()
    normalized_evaluation_mode = str(evaluation_mode or "").strip()
    if not normalized_flow_type or not normalized_evaluation_mode:
        raise ValueError("invalid_school_evaluation_job_mode")

    normalized_max_attempts = _school_evaluation_job_max_attempts(max_attempts)
    normalized_request_metadata = _school_evaluation_job_request_metadata(
        request_metadata
    )
    expected_state_digest = _school_evaluation_job_expected_state_digest(
        expected_state_json
    )
    replacement_claim_token = str(uuid4())
    params = {
        "uid": user_id,
        "session_id": session_id,
        "activity_id": activity_id,
        "raw_answer": raw_answer,
        "expected_state_json": json.dumps(expected_state_json),
        "request_metadata_json": json.dumps(normalized_request_metadata),
        "expected_state_digest": expected_state_digest,
        "answer_hash": answer_hash,
        "flow_type": normalized_flow_type,
        "evaluation_mode": normalized_evaluation_mode,
        "max_attempts": normalized_max_attempts,
        "replacement_claim_token": replacement_claim_token,
        "answer_lock_key": f"school-answer:{session_id}:{activity_id}",
        "job_lock_key": f"school-evaluation-job:{session_id}:{activity_id}",
    }

    try:
        result = await session.execute(
            text(
                """
                WITH locks AS MATERIALIZED (
                    SELECT
                        pg_advisory_xact_lock(
                            hashtext(:answer_lock_key)::bigint
                        ) AS answer_lock,
                        pg_advisory_xact_lock(
                            hashtext(:job_lock_key)::bigint
                        ) AS job_lock
                ),
                request_row AS MATERIALIZED (
                    SELECT
                        request.user_id AS request_user_id,
                        request.answer_hash AS request_answer_hash,
                        request.claim_token AS request_claim_token,
                        request.status AS request_status,
                        request.response_json AS request_response_json
                    FROM school_answer_requests AS request
                    CROSS JOIN locks
                    WHERE request.session_id = CAST(:session_id AS uuid)
                      AND request.activity_id = :activity_id
                    FOR UPDATE OF request
                ),
                job_row AS MATERIALIZED (
                    SELECT
                        job.session_id::text AS queue_session_id,
                        job.activity_id AS queue_activity_id,
                        job.user_id AS job_user_id,
                        job.raw_answer AS job_raw_answer,
                        job.expected_state_digest AS job_expected_state_digest,
                        job.request_metadata_json AS job_request_metadata_json,
                        job.answer_hash AS job_answer_hash,
                        job.answer_claim_token AS job_answer_claim_token,
                        job.flow_type AS job_flow_type,
                        job.evaluation_mode AS job_evaluation_mode,
                        job.status AS queue_status,
                        job.attempts AS queue_attempts,
                        job.max_attempts AS queue_max_attempts,
                        job.lease_version AS queue_lease_version,
                        job.lease_expires_at AS queue_lease_expires_at,
                        job.next_attempt_at AS queue_next_attempt_at,
                        job.last_error_code AS queue_last_error_code,
                        job.error_json AS queue_error_json,
                        job.created_at AS queue_created_at,
                        job.updated_at AS queue_updated_at,
                        job.started_at AS queue_started_at,
                        job.completed_at AS queue_completed_at,
                        job.failed_at AS queue_failed_at,
                        job.cancelled_at AS queue_cancelled_at
                    FROM school_evaluation_jobs AS job
                    CROSS JOIN locks
                    WHERE job.session_id = CAST(:session_id AS uuid)
                      AND job.activity_id = :activity_id
                    FOR UPDATE OF job
                ),
                candidate AS MATERIALIZED (
                    SELECT
                        request_row.*,
                        job_row.*,
                        CASE
                            WHEN request_row.request_status = 'processing'
                                THEN request_row.request_claim_token
                            ELSE :replacement_claim_token
                        END AS claim_token
                    FROM locks
                    LEFT JOIN request_row ON TRUE
                    LEFT JOIN job_row ON TRUE
                ),
                decision AS MATERIALIZED (
                    SELECT
                        candidate.*,
                        CASE
                            WHEN candidate.request_user_id IS NOT NULL
                             AND candidate.request_user_id <> :uid
                                THEN 'conflict'
                            WHEN candidate.request_status = 'completed'
                                THEN 'completed'
                            WHEN candidate.request_user_id IS NOT NULL
                             AND candidate.request_status NOT IN ('processing', 'failed')
                                THEN 'conflict'
                            WHEN candidate.request_status = 'processing'
                             AND candidate.request_answer_hash <> :answer_hash
                                THEN 'conflict'
                            WHEN candidate.queue_session_id IS NOT NULL
                             AND candidate.job_user_id = :uid
                             AND candidate.job_answer_hash = :answer_hash
                             AND candidate.job_answer_claim_token = candidate.claim_token
                             AND candidate.job_raw_answer = :raw_answer
                             AND candidate.job_expected_state_digest = :expected_state_digest
                             AND candidate.job_request_metadata_json = CAST(:request_metadata_json AS jsonb)
                             AND candidate.job_flow_type = :flow_type
                             AND candidate.job_evaluation_mode = :evaluation_mode
                             AND candidate.queue_max_attempts = :max_attempts
                             AND candidate.queue_status IN ('queued', 'running')
                                THEN 'in_progress'
                            WHEN candidate.queue_session_id IS NOT NULL
                             AND candidate.queue_status NOT IN ('failed', 'cancelled')
                                THEN 'conflict'
                            ELSE 'queued'
                        END AS outcome
                    FROM candidate
                ),
                request_write AS (
                    INSERT INTO school_answer_requests (
                        session_id, activity_id, user_id, answer_hash, claim_token, status
                    )
                    SELECT
                        CAST(:session_id AS uuid), :activity_id, :uid,
                        :answer_hash, decision.claim_token, 'processing'
                    FROM decision
                    WHERE decision.outcome = 'queued'
                    ON CONFLICT (session_id, activity_id) DO UPDATE
                    SET status = 'processing',
                        response_json = NULL,
                        answer_hash = EXCLUDED.answer_hash,
                        claim_token = EXCLUDED.claim_token,
                        updated_at = now()
                    WHERE school_answer_requests.user_id = :uid
                      AND school_answer_requests.status = 'failed'
                    RETURNING session_id
                ),
                job_write AS (
                    INSERT INTO school_evaluation_jobs (
                        session_id, activity_id, user_id, raw_answer,
                        expected_state_json, request_metadata_json,
                        expected_state_digest, answer_hash, answer_claim_token,
                        flow_type, evaluation_mode, status, max_attempts
                    )
                    SELECT
                        CAST(:session_id AS uuid), :activity_id, :uid, :raw_answer,
                        CAST(:expected_state_json AS jsonb),
                        CAST(:request_metadata_json AS jsonb),
                        :expected_state_digest, :answer_hash, decision.claim_token,
                        :flow_type, :evaluation_mode, 'queued', :max_attempts
                    FROM decision
                    LEFT JOIN request_write ON TRUE
                    WHERE decision.outcome = 'queued'
                    ON CONFLICT (session_id, activity_id) DO UPDATE
                    SET user_id = EXCLUDED.user_id,
                        raw_answer = EXCLUDED.raw_answer,
                        expected_state_json = EXCLUDED.expected_state_json,
                        request_metadata_json = EXCLUDED.request_metadata_json,
                        expected_state_digest = EXCLUDED.expected_state_digest,
                        answer_hash = EXCLUDED.answer_hash,
                        answer_claim_token = EXCLUDED.answer_claim_token,
                        flow_type = EXCLUDED.flow_type,
                        evaluation_mode = EXCLUDED.evaluation_mode,
                        status = 'queued',
                        attempts = 0,
                        max_attempts = EXCLUDED.max_attempts,
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        next_attempt_at = now(),
                        last_error_code = NULL,
                        error_json = NULL,
                        response_json = NULL,
                        result_data = NULL,
                        created_at = now(),
                        updated_at = now(),
                        started_at = NULL,
                        completed_at = NULL,
                        failed_at = NULL,
                        cancelled_at = NULL
                    WHERE school_evaluation_jobs.status IN ('failed', 'cancelled')
                    RETURNING
                        session_id::text AS queue_session_id,
                        activity_id AS queue_activity_id,
                        status AS queue_status,
                        attempts AS queue_attempts,
                        max_attempts AS queue_max_attempts,
                        lease_version AS queue_lease_version,
                        lease_expires_at AS queue_lease_expires_at,
                        next_attempt_at AS queue_next_attempt_at,
                        last_error_code AS queue_last_error_code,
                        error_json AS queue_error_json,
                        created_at AS queue_created_at,
                        updated_at AS queue_updated_at,
                        started_at AS queue_started_at,
                        completed_at AS queue_completed_at,
                        failed_at AS queue_failed_at,
                        cancelled_at AS queue_cancelled_at
                )
                SELECT
                    decision.outcome,
                    decision.claim_token,
                    CASE
                        WHEN decision.outcome = 'completed'
                            THEN decision.request_response_json
                        ELSE NULL
                    END AS response_json,
                    COALESCE(job_write.queue_session_id, decision.queue_session_id)
                        AS queue_session_id,
                    COALESCE(job_write.queue_activity_id, decision.queue_activity_id)
                        AS queue_activity_id,
                    COALESCE(job_write.queue_status, decision.queue_status)
                        AS queue_status,
                    COALESCE(job_write.queue_attempts, decision.queue_attempts)
                        AS queue_attempts,
                    COALESCE(job_write.queue_max_attempts, decision.queue_max_attempts)
                        AS queue_max_attempts,
                    COALESCE(job_write.queue_lease_version, decision.queue_lease_version)
                        AS queue_lease_version,
                    COALESCE(job_write.queue_lease_expires_at, decision.queue_lease_expires_at)
                        AS queue_lease_expires_at,
                    COALESCE(job_write.queue_next_attempt_at, decision.queue_next_attempt_at)
                        AS queue_next_attempt_at,
                    COALESCE(job_write.queue_last_error_code, decision.queue_last_error_code)
                        AS queue_last_error_code,
                    COALESCE(job_write.queue_error_json, decision.queue_error_json)
                        AS queue_error_json,
                    COALESCE(job_write.queue_created_at, decision.queue_created_at)
                        AS queue_created_at,
                    COALESCE(job_write.queue_updated_at, decision.queue_updated_at)
                        AS queue_updated_at,
                    COALESCE(job_write.queue_started_at, decision.queue_started_at)
                        AS queue_started_at,
                    COALESCE(job_write.queue_completed_at, decision.queue_completed_at)
                        AS queue_completed_at,
                    COALESCE(job_write.queue_failed_at, decision.queue_failed_at)
                        AS queue_failed_at,
                    COALESCE(job_write.queue_cancelled_at, decision.queue_cancelled_at)
                        AS queue_cancelled_at
                FROM decision
                LEFT JOIN job_write ON TRUE
                """
            ),
            params,
        )
        row = result.mappings().first()
        if row is None:
            raise RuntimeError("school_evaluation_job_atomic_enqueue_missing")
        data = dict(row)
        outcome = str(data.get("outcome") or "")
        if outcome == "completed":
            await session.rollback()
            response = data.get("response_json")
            if isinstance(response, str):
                response = json.loads(response)
            return {"outcome": "completed", "response_json": response}
        if outcome == "conflict":
            await session.rollback()
            return {"outcome": "conflict"}

        queue_fields = {
            key.removeprefix("queue_"): value
            for key, value in data.items()
            if key.startswith("queue_")
        }
        if outcome == "queued":
            if not queue_fields.get("session_id"):
                await session.rollback()
                raise RuntimeError("school_evaluation_job_insert_missing")
            await session.commit()
            return {
                "outcome": "queued",
                "claim_token": str(data["claim_token"]),
                "job": queue_fields,
            }
        if outcome == "in_progress":
            await session.rollback()
            return {
                "outcome": "in_progress",
                "claim_token": str(data["claim_token"]),
                "job": queue_fields,
            }

        await session.rollback()
        raise RuntimeError("invalid_school_evaluation_job_atomic_enqueue_outcome")
    except Exception:
        await session.rollback()
        raise


async def claim_and_enqueue_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    raw_answer: str,
    expected_state_json: dict,
    answer_hash: str,
    flow_type: str,
    evaluation_mode: str,
    max_attempts: int = 3,
    request_metadata: dict | None = None,
) -> dict:
    """Atomically own one answer request and leave it with a matching job."""
    if not isinstance(raw_answer, str):
        raise ValueError("invalid_school_evaluation_job_answer")
    if not isinstance(expected_state_json, dict):
        raise ValueError("invalid_school_evaluation_job_expected_state")
    normalized_flow_type = str(flow_type or "").strip()
    normalized_evaluation_mode = str(evaluation_mode or "").strip()
    if not normalized_flow_type or not normalized_evaluation_mode:
        raise ValueError("invalid_school_evaluation_job_mode")
    normalized_max_attempts = _school_evaluation_job_max_attempts(max_attempts)
    normalized_request_metadata = _school_evaluation_job_request_metadata(
        request_metadata
    )
    expected_state_digest = _school_evaluation_job_expected_state_digest(
        expected_state_json
    )
    answer_lock_key = f"school-answer:{session_id}:{activity_id}"
    job_lock_key = f"school-evaluation-job:{session_id}:{activity_id}"
    replacement_claim_token = str(uuid4())
    try:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {"lock_key": answer_lock_key},
        )
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {"lock_key": job_lock_key},
        )
        request_result = await session.execute(
            text(
                """
                SELECT user_id, answer_hash, claim_token, status, response_json
                FROM school_answer_requests
                WHERE session_id = CAST(:session_id AS uuid)
                  AND activity_id = :activity_id
                FOR UPDATE
                """
            ),
            {"session_id": session_id, "activity_id": activity_id},
        )
        request_row = request_result.mappings().first()
        request = dict(request_row) if request_row else None
        if request is not None:
            if request.get("user_id") != user_id:
                await session.rollback()
                return {"outcome": "conflict"}
            if request.get("status") == "completed":
                await session.rollback()
                response = request.get("response_json")
                if isinstance(response, str):
                    response = json.loads(response)
                return {"outcome": "completed", "response_json": response}
            if request.get("status") not in {"processing", "failed"}:
                await session.rollback()
                return {"outcome": "conflict"}
            if (
                request.get("status") == "processing"
                and request.get("answer_hash") != answer_hash
            ):
                await session.rollback()
                return {"outcome": "conflict"}
            claim_token = (
                str(request.get("claim_token") or "")
                if request.get("status") == "processing"
                else replacement_claim_token
            )
        else:
            claim_token = replacement_claim_token

        existing_result = await session.execute(
            text(
                """
                SELECT session_id::text AS session_id, activity_id, user_id,
                       raw_answer, expected_state_json, request_metadata_json,
                       expected_state_digest,
                       answer_hash, answer_claim_token, flow_type, evaluation_mode,
                       status, attempts, max_attempts, lease_owner, lease_token,
                       lease_version, lease_expires_at, last_error_code, error_json,
                       response_json, result_data, created_at, updated_at, started_at,
                       completed_at, failed_at, cancelled_at
                FROM school_evaluation_jobs
                WHERE session_id = CAST(:session_id AS uuid)
                  AND activity_id = :activity_id
                FOR UPDATE
                """
            ),
            {"session_id": session_id, "activity_id": activity_id},
        )
        existing_row = existing_result.mappings().first()
        existing = (
            _school_evaluation_job_from_row(existing_row) if existing_row else None
        )
        if existing is not None:
            same_claim = (
                existing.get("user_id") == user_id
                and existing.get("answer_hash") == answer_hash
                and existing.get("answer_claim_token") == claim_token
            )
            same_payload = (
                existing.get("raw_answer") == raw_answer
                and existing.get("expected_state_digest") == expected_state_digest
                and existing.get("request_metadata_json")
                == normalized_request_metadata
                and existing.get("flow_type") == normalized_flow_type
                and existing.get("evaluation_mode") == normalized_evaluation_mode
                and existing.get("max_attempts") == normalized_max_attempts
            )
            if (
                same_claim
                and same_payload
                and existing.get("status") in {"queued", "running"}
            ):
                await session.rollback()
                return {
                    "outcome": "in_progress",
                    "claim_token": claim_token,
                    "job": _school_evaluation_job_queue_view(existing),
                }
            if existing.get("status") not in {"failed", "cancelled"}:
                await session.rollback()
                return {"outcome": "conflict"}

        if request is None:
            await session.execute(
                text(
                    """
                    INSERT INTO school_answer_requests
                        (session_id, activity_id, user_id, answer_hash, claim_token, status)
                    VALUES
                        (CAST(:session_id AS uuid), :activity_id, :uid, :answer_hash,
                         :claim_token, 'processing')
                    """
                ),
                {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "uid": user_id,
                    "answer_hash": answer_hash,
                    "claim_token": claim_token,
                },
            )
        else:
            await session.execute(
                text(
                    """
                    UPDATE school_answer_requests
                    SET status = 'processing',
                        response_json = NULL,
                        answer_hash = :answer_hash,
                        claim_token = :claim_token,
                        updated_at = now()
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND activity_id = :activity_id
                      AND user_id = :uid
                    """
                ),
                {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "uid": user_id,
                    "answer_hash": answer_hash,
                    "claim_token": claim_token,
                },
            )

        if existing is not None:
            reset_result = await session.execute(
                text(
                    """
                    UPDATE school_evaluation_jobs
                    SET user_id = :uid,
                        raw_answer = :raw_answer,
                        expected_state_json = CAST(:expected_state_json AS jsonb),
                        request_metadata_json = CAST(:request_metadata_json AS jsonb),
                        expected_state_digest = :expected_state_digest,
                        answer_hash = :answer_hash,
                        answer_claim_token = :answer_claim_token,
                        flow_type = :flow_type,
                        evaluation_mode = :evaluation_mode,
                        status = 'queued',
                        attempts = 0,
                        max_attempts = :max_attempts,
                        lease_owner = NULL,
                        lease_token = NULL,
                        lease_expires_at = NULL,
                        next_attempt_at = now(),
                        last_error_code = NULL,
                        error_json = NULL,
                        response_json = NULL,
                        result_data = NULL,
                        created_at = now(),
                        updated_at = now(),
                        started_at = NULL,
                        completed_at = NULL,
                        failed_at = NULL,
                        cancelled_at = NULL
                    WHERE session_id = CAST(:session_id AS uuid)
                      AND activity_id = :activity_id
                      AND status IN ('failed', 'cancelled')
                    RETURNING session_id::text AS session_id, activity_id, user_id,
                              raw_answer, expected_state_json, request_metadata_json,
                              expected_state_digest,
                              answer_hash, answer_claim_token, flow_type, evaluation_mode,
                              status, attempts, max_attempts, lease_owner, lease_token,
                              lease_version, lease_expires_at, last_error_code, error_json,
                              response_json, result_data, created_at, updated_at, started_at,
                              completed_at, failed_at, cancelled_at
                    """
                ),
                {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "uid": user_id,
                    "raw_answer": raw_answer,
                    "expected_state_json": json.dumps(expected_state_json),
                    "request_metadata_json": json.dumps(normalized_request_metadata),
                    "expected_state_digest": expected_state_digest,
                    "answer_hash": answer_hash,
                    "answer_claim_token": claim_token,
                    "flow_type": normalized_flow_type,
                    "evaluation_mode": normalized_evaluation_mode,
                    "max_attempts": normalized_max_attempts,
                },
            )
            queued_row = reset_result.mappings().first()
        else:
            inserted_result = await session.execute(
                text(
                    """
                    INSERT INTO school_evaluation_jobs (
                        session_id, activity_id, user_id, raw_answer,
                        expected_state_json, request_metadata_json,
                        expected_state_digest,
                        answer_hash, answer_claim_token, flow_type, evaluation_mode,
                        status, max_attempts
                    )
                    VALUES (
                        CAST(:session_id AS uuid), :activity_id, :uid, :raw_answer,
                        CAST(:expected_state_json AS jsonb),
                        CAST(:request_metadata_json AS jsonb), :expected_state_digest,
                        :answer_hash, :answer_claim_token, :flow_type, :evaluation_mode,
                        'queued', :max_attempts
                    )
                    RETURNING session_id::text AS session_id, activity_id, user_id,
                              raw_answer, expected_state_json, request_metadata_json,
                              expected_state_digest,
                              answer_hash, answer_claim_token, flow_type, evaluation_mode,
                              status, attempts, max_attempts, lease_owner, lease_token,
                              lease_version, lease_expires_at, last_error_code, error_json,
                              response_json, result_data, created_at, updated_at, started_at,
                              completed_at, failed_at, cancelled_at
                    """
                ),
                {
                    "session_id": session_id,
                    "activity_id": activity_id,
                    "uid": user_id,
                    "raw_answer": raw_answer,
                    "expected_state_json": json.dumps(expected_state_json),
                    "request_metadata_json": json.dumps(normalized_request_metadata),
                    "expected_state_digest": expected_state_digest,
                    "answer_hash": answer_hash,
                    "answer_claim_token": claim_token,
                    "flow_type": normalized_flow_type,
                    "evaluation_mode": normalized_evaluation_mode,
                    "max_attempts": normalized_max_attempts,
                },
            )
            queued_row = inserted_result.mappings().first()
        if queued_row is None:
            raise RuntimeError("school_evaluation_job_insert_missing")
        job = _school_evaluation_job_from_row(queued_row)
        await session.commit()
        return {
            "outcome": "queued",
            "claim_token": claim_token,
            "job": _school_evaluation_job_queue_view(job),
        }
    except Exception:
        await session.rollback()
        raise


async def enqueue_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    raw_answer: str,
    expected_state_json: dict,
    answer_hash: str,
    answer_claim_token: str,
    flow_type: str,
    evaluation_mode: str,
    max_attempts: int = 3,
    request_metadata: dict | None = None,
) -> dict:
    """Queue one evaluator job only while its School answer claim is current."""
    if not isinstance(expected_state_json, dict):
        raise ValueError("invalid_school_evaluation_job_expected_state")
    normalized_flow_type = str(flow_type or "").strip()
    normalized_evaluation_mode = str(evaluation_mode or "").strip()
    if not normalized_flow_type or not normalized_evaluation_mode:
        raise ValueError("invalid_school_evaluation_job_mode")
    normalized_max_attempts = _school_evaluation_job_max_attempts(max_attempts)
    normalized_request_metadata = _school_evaluation_job_request_metadata(
        request_metadata
    )

    expected_state_digest = _school_evaluation_job_expected_state_digest(
        expected_state_json
    )
    lock_key = f"school-evaluation-job:{session_id}:{activity_id}"
    try:
        await session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key)::bigint)"),
            {"lock_key": lock_key},
        )
        claimed_request_result = await session.execute(
            text(
                """
                SELECT session_id, activity_id
                FROM school_answer_requests
                WHERE session_id = CAST(:session_id AS uuid)
                  AND activity_id = :activity_id
                  AND user_id = :uid
                  AND answer_hash = :answer_hash
                  AND claim_token = :answer_claim_token
                  AND status = 'processing'
                FOR UPDATE
                """
            ),
            {
                "session_id": session_id,
                "activity_id": activity_id,
                "uid": user_id,
                "answer_hash": answer_hash,
                "answer_claim_token": answer_claim_token,
            },
        )
        if claimed_request_result.mappings().first() is None:
            await session.rollback()
            return {"outcome": "conflict"}

        existing_result = await session.execute(
            text(
                """
                SELECT session_id::text AS session_id, activity_id, user_id,
                       raw_answer, expected_state_json, request_metadata_json,
                       expected_state_digest,
                       answer_hash, answer_claim_token, flow_type, evaluation_mode,
                       status, attempts, max_attempts, lease_owner, lease_token,
                       lease_version, lease_expires_at, last_error_code, error_json,
                       response_json, result_data, created_at, updated_at, started_at,
                       completed_at, failed_at, cancelled_at
                FROM school_evaluation_jobs
                WHERE session_id = CAST(:session_id AS uuid)
                  AND activity_id = :activity_id
                FOR UPDATE
                """
            ),
            {"session_id": session_id, "activity_id": activity_id},
        )
        existing_row = existing_result.mappings().first()
        if existing_row is not None:
            existing = _school_evaluation_job_from_row(existing_row)
            same_claim = (
                existing.get("user_id") == user_id
                and existing.get("answer_hash") == answer_hash
                and existing.get("answer_claim_token") == answer_claim_token
            )
            same_payload = (
                existing.get("raw_answer") == raw_answer
                and existing.get("expected_state_digest") == expected_state_digest
                and existing.get("request_metadata_json")
                == normalized_request_metadata
                and existing.get("flow_type") == normalized_flow_type
                and existing.get("evaluation_mode") == normalized_evaluation_mode
                and existing.get("max_attempts") == normalized_max_attempts
            )
            if same_claim and same_payload:
                await session.commit()
                return {"outcome": "existing", "job": existing}
            if existing.get("status") in {"failed", "cancelled"}:
                reset_result = await session.execute(
                    text(
                        """
                        UPDATE school_evaluation_jobs
                        SET user_id = :uid,
                            raw_answer = :raw_answer,
                            expected_state_json = CAST(:expected_state_json AS jsonb),
                            request_metadata_json = CAST(:request_metadata_json AS jsonb),
                            expected_state_digest = :expected_state_digest,
                            answer_hash = :answer_hash,
                            answer_claim_token = :answer_claim_token,
                            flow_type = :flow_type,
                            evaluation_mode = :evaluation_mode,
                            status = 'queued',
                            attempts = 0,
                            max_attempts = :max_attempts,
                            lease_owner = NULL,
                            lease_token = NULL,
                            lease_expires_at = NULL,
                            next_attempt_at = now(),
                            last_error_code = NULL,
                            error_json = NULL,
                            response_json = NULL,
                            result_data = NULL,
                            created_at = now(),
                            updated_at = now(),
                            started_at = NULL,
                            completed_at = NULL,
                            failed_at = NULL,
                            cancelled_at = NULL
                        WHERE session_id = CAST(:session_id AS uuid)
                          AND activity_id = :activity_id
                          AND status IN ('failed', 'cancelled')
                        RETURNING session_id::text AS session_id, activity_id, user_id,
                                  raw_answer, expected_state_json, request_metadata_json,
                                  expected_state_digest,
                                  answer_hash, answer_claim_token, flow_type, evaluation_mode,
                                  status, attempts, max_attempts, lease_owner, lease_token,
                                  lease_version, lease_expires_at, last_error_code, error_json,
                                  response_json, result_data, created_at, updated_at, started_at,
                                  completed_at, failed_at, cancelled_at
                        """
                    ),
                    {
                        "session_id": session_id,
                        "activity_id": activity_id,
                        "uid": user_id,
                        "raw_answer": raw_answer,
                        "expected_state_json": json.dumps(expected_state_json),
                        "request_metadata_json": json.dumps(normalized_request_metadata),
                        "expected_state_digest": expected_state_digest,
                        "answer_hash": answer_hash,
                        "answer_claim_token": answer_claim_token,
                        "flow_type": normalized_flow_type,
                        "evaluation_mode": normalized_evaluation_mode,
                        "max_attempts": normalized_max_attempts,
                    },
                )
                reset = reset_result.mappings().first()
                if reset is None:
                    await session.rollback()
                    return {"outcome": "conflict"}
                await session.commit()
                return {"outcome": "queued", "job": _school_evaluation_job_from_row(reset)}
            await session.rollback()
            return {"outcome": "conflict"}

        inserted_result = await session.execute(
            text(
                """
                INSERT INTO school_evaluation_jobs (
                    session_id, activity_id, user_id, raw_answer,
                    expected_state_json, request_metadata_json,
                    expected_state_digest,
                    answer_hash, answer_claim_token, flow_type, evaluation_mode,
                    status, max_attempts
                )
                VALUES (
                    CAST(:session_id AS uuid), :activity_id, :uid, :raw_answer,
                    CAST(:expected_state_json AS jsonb),
                    CAST(:request_metadata_json AS jsonb), :expected_state_digest,
                    :answer_hash, :answer_claim_token, :flow_type, :evaluation_mode,
                    'queued', :max_attempts
                )
                RETURNING session_id::text AS session_id, activity_id, user_id,
                          raw_answer, expected_state_json, request_metadata_json,
                          expected_state_digest,
                          answer_hash, answer_claim_token, flow_type, evaluation_mode,
                          status, attempts, max_attempts, lease_owner, lease_token,
                          lease_version, lease_expires_at, last_error_code, error_json,
                          response_json, result_data, created_at, updated_at, started_at,
                          completed_at, failed_at, cancelled_at
                """
            ),
            {
                "session_id": session_id,
                "activity_id": activity_id,
                "uid": user_id,
                "raw_answer": raw_answer,
                "expected_state_json": json.dumps(expected_state_json),
                "request_metadata_json": json.dumps(normalized_request_metadata),
                "expected_state_digest": expected_state_digest,
                "answer_hash": answer_hash,
                "answer_claim_token": answer_claim_token,
                "flow_type": normalized_flow_type,
                "evaluation_mode": normalized_evaluation_mode,
                "max_attempts": normalized_max_attempts,
            },
        )
        inserted = inserted_result.mappings().first()
        if inserted is None:
            raise RuntimeError("school_evaluation_job_insert_missing")
        await session.commit()
        return {"outcome": "queued", "job": _school_evaluation_job_from_row(inserted)}
    except Exception:
        await session.rollback()
        raise


async def _terminalize_expired_school_evaluation_jobs(session: AsyncSession) -> int:
    """Release expired exhausted jobs before issuing another evaluator lease."""
    result = await session.execute(
        text(
            """
            WITH terminal_request_candidates AS (
                SELECT
                    request.session_id,
                    request.activity_id,
                    CASE
                        WHEN job.created_at <= now() - (
                            CAST(:deadline_seconds AS integer) * INTERVAL '1 second'
                        ) THEN 'evaluation_deadline_exceeded'
                        ELSE 'evaluation_recovery_lease_expired'
                    END AS error_code
                FROM school_answer_requests AS request
                JOIN school_evaluation_jobs AS job
                  ON job.session_id = request.session_id
                 AND job.activity_id = request.activity_id
                 AND job.user_id = request.user_id
                 AND job.answer_hash = request.answer_hash
                 AND job.answer_claim_token = request.claim_token
                WHERE job.status IN ('queued', 'running')
                  AND request.status = 'processing'
                  AND (
                      job.created_at <= now() - (
                          CAST(:deadline_seconds AS integer) * INTERVAL '1 second'
                      )
                      OR (
                          job.status = 'running'
                          AND job.lease_expires_at IS NOT NULL
                          AND job.lease_expires_at <= now()
                          AND job.attempts > job.max_attempts
                      )
                  )
                ORDER BY job.created_at ASC
                FOR UPDATE OF request SKIP LOCKED
            ),
            terminal_candidates AS (
                SELECT
                    job.session_id,
                    job.activity_id,
                    request.error_code
                FROM school_evaluation_jobs AS job
                JOIN terminal_request_candidates AS request
                  ON request.session_id = job.session_id
                 AND request.activity_id = job.activity_id
                FOR UPDATE OF job SKIP LOCKED
            ),
            terminalized_jobs AS (
                UPDATE school_evaluation_jobs AS job
                SET status = 'failed',
                    last_error_code = candidate.error_code,
                    error_json = jsonb_build_object('reason', candidate.error_code),
                    response_json = NULL,
                    result_data = NULL,
                    lease_owner = NULL,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    failed_at = now(),
                    updated_at = now()
                FROM terminal_candidates AS candidate
                WHERE job.session_id = candidate.session_id
                  AND job.activity_id = candidate.activity_id
                RETURNING job.session_id, job.activity_id, job.user_id,
                          job.answer_hash, job.answer_claim_token
            ),
            released_requests AS (
                UPDATE school_answer_requests AS request
                SET status = 'failed',
                    response_json = NULL,
                    updated_at = now()
                FROM terminalized_jobs AS job
                WHERE request.session_id = job.session_id
                  AND request.activity_id = job.activity_id
                  AND request.user_id = job.user_id
                  AND request.answer_hash = job.answer_hash
                  AND request.claim_token = job.answer_claim_token
                  AND request.status = 'processing'
                RETURNING request.session_id, request.activity_id
            )
            SELECT COUNT(*) FROM released_requests
            """
        ),
        {"deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS},
    )
    return int(result.scalar_one_or_none() or 0)


async def reconcile_expired_school_evaluation_jobs(session: AsyncSession) -> int:
    """Release only durable evaluator jobs that have crossed their server deadline."""

    try:
        released = await _terminalize_expired_school_evaluation_jobs(session)
        await session.commit()
        return released
    except Exception:
        await session.rollback()
        raise


async def claim_school_evaluation_job(
    session: AsyncSession,
    *,
    lease_owner: str = _SCHOOL_EVALUATION_JOB_DEFAULT_LEASE_OWNER,
    lease_seconds: int = _SCHOOL_EVALUATION_JOB_LEASE_SECONDS,
) -> dict | None:
    """Claim one queued or expired job, including one bounded recovery lease."""
    normalized_lease_owner = _school_evaluation_job_lease_owner(lease_owner)
    normalized_lease_seconds = _school_evaluation_job_lease_seconds(lease_seconds)
    lease_token = str(uuid4())
    try:
        await _terminalize_expired_school_evaluation_jobs(session)
        result = await session.execute(
            text(
                """
                WITH candidate AS (
                    SELECT job.session_id, job.activity_id
                    FROM school_evaluation_jobs AS job
                    JOIN school_answer_requests AS request
                      ON request.session_id = job.session_id
                     AND request.activity_id = job.activity_id
                     AND request.user_id = job.user_id
                     AND request.answer_hash = job.answer_hash
                     AND request.claim_token = job.answer_claim_token
                     AND request.status = 'processing'
                    WHERE job.created_at > now() - (
                              CAST(:deadline_seconds AS integer) * INTERVAL '1 second'
                          )
                      AND (
                          (
                              job.status = 'queued'
                              AND job.attempts < job.max_attempts
                              AND job.next_attempt_at <= now()
                          )
                          OR (
                              job.status = 'running'
                              AND job.lease_expires_at IS NOT NULL
                              AND job.lease_expires_at <= now()
                              AND job.attempts <= job.max_attempts
                          )
                      )
                    ORDER BY job.next_attempt_at ASC, job.created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE school_evaluation_jobs AS job
                SET status = 'running',
                    attempts = job.attempts + 1,
                    lease_owner = :lease_owner,
                    lease_token = :lease_token,
                    lease_version = job.lease_version + 1,
                    lease_expires_at = now() + (
                        CAST(:lease_seconds AS integer) * INTERVAL '1 second'
                    ),
                    started_at = COALESCE(job.started_at, now()),
                    updated_at = now()
                FROM candidate
                WHERE job.session_id = candidate.session_id
                  AND job.activity_id = candidate.activity_id
                RETURNING job.session_id::text AS session_id, job.activity_id, job.user_id,
                          job.raw_answer, job.expected_state_json,
                          job.request_metadata_json,
                          job.expected_state_digest, job.answer_hash,
                          job.answer_claim_token, job.flow_type, job.evaluation_mode,
                          job.status, job.attempts, job.max_attempts,
                          job.lease_owner, job.lease_token, job.lease_version,
                          job.lease_expires_at, job.last_error_code, job.error_json,
                          job.response_json, job.result_data, job.created_at,
                          job.updated_at, job.started_at, job.completed_at, job.failed_at,
                          job.cancelled_at
                """
            ),
            {
                "lease_owner": normalized_lease_owner,
                "lease_token": lease_token,
                "lease_seconds": normalized_lease_seconds,
                "deadline_seconds": _SCHOOL_EVALUATION_JOB_DEADLINE_SECONDS,
            },
        )
        row = result.mappings().first()
        await session.commit()
        return _school_evaluation_job_from_row(row) if row else None
    except Exception:
        await session.rollback()
        raise


async def heartbeat_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
    lease_seconds: int = _SCHOOL_EVALUATION_JOB_LEASE_SECONDS,
) -> bool:
    normalized_lease_seconds = _school_evaluation_job_lease_seconds(lease_seconds)
    result = await session.execute(
        text(
            """
            WITH locked_request AS (
                SELECT request.session_id, request.activity_id
                FROM school_answer_requests AS request
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                  AND request.answer_hash = :answer_hash
                  AND request.claim_token = :answer_claim_token
                  AND request.status = 'processing'
                FOR UPDATE
            ),
            renewed_job AS (
                UPDATE school_evaluation_jobs AS job
                SET lease_expires_at = now() + (
                        CAST(:lease_seconds AS integer) * INTERVAL '1 second'
                    ),
                    updated_at = now()
                FROM locked_request AS request
                WHERE job.session_id = request.session_id
                  AND job.activity_id = request.activity_id
                  AND job.user_id = :uid
                  AND job.answer_hash = :answer_hash
                  AND job.answer_claim_token = :answer_claim_token
                  AND job.lease_owner = :lease_owner
                  AND job.lease_token = :lease_token
                  AND job.lease_version = :lease_version
                  AND job.status = 'running'
                  AND job.lease_expires_at > now()
                RETURNING job.session_id, job.activity_id, job.user_id,
                          job.answer_hash, job.answer_claim_token
            ),
            renewed_request AS (
                UPDATE school_answer_requests AS request
                SET updated_at = now()
                FROM renewed_job AS job
                WHERE request.session_id = job.session_id
                  AND request.activity_id = job.activity_id
                  AND request.user_id = job.user_id
                  AND request.answer_hash = job.answer_hash
                  AND request.claim_token = job.answer_claim_token
                  AND request.status = 'processing'
                RETURNING request.activity_id
            )
            SELECT activity_id FROM renewed_request
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": _school_evaluation_job_lease_owner(lease_owner),
            "lease_token": lease_token,
            "lease_version": int(lease_version),
            "lease_seconds": normalized_lease_seconds,
        },
    )
    renewed = result.scalar_one_or_none() is not None
    await session.commit()
    return renewed


async def terminalize_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
    last_error_code: str,
    error_json: dict | None = None,
    placement_retry_timing: dict | None = None,
) -> dict | None:
    """Fail a fenced running job and release its exact answer request atomically."""
    normalized_error_code = str(last_error_code or "").strip()
    if not normalized_error_code:
        raise ValueError("invalid_school_evaluation_job_error_code")
    normalized_placement_retry_timing = _validated_placement_retry_timing(
        placement_retry_timing,
        activity_id=activity_id,
    )
    result = await session.execute(
        text(
            """
            WITH locked_request AS (
                SELECT request.session_id, request.activity_id
                FROM school_answer_requests AS request
                WHERE request.session_id = CAST(:session_id AS uuid)
                  AND request.activity_id = :activity_id
                  AND request.user_id = :uid
                  AND request.answer_hash = :answer_hash
                  AND request.claim_token = :answer_claim_token
                  AND request.status = 'processing'
                FOR UPDATE
            ),
            locked_placement_session AS (
                SELECT school_session.session_id
                FROM school_sessions AS school_session
                WHERE CAST(:placement_retry_timing AS jsonb) IS NOT NULL
                  AND school_session.user_id = :uid
                  AND school_session.session_id = CAST(:session_id AS uuid)
                  AND school_session.api_version = 'rebuild'
                  AND school_session.flow_type = 'placement'
                  AND school_session.status = 'active'
                  AND school_session.state_json #>> '{_placement_item_timing,item_id}' = :activity_id
                  AND EXISTS (
                      SELECT 1
                      FROM locked_request AS request
                      WHERE request.session_id = school_session.session_id
                        AND request.activity_id = :activity_id
                  )
                FOR UPDATE
            ),
            terminalized_job AS (
                UPDATE school_evaluation_jobs AS job
                SET status = 'failed',
                    last_error_code = :last_error_code,
                    error_json = CAST(:error_json AS jsonb),
                    response_json = NULL,
                    result_data = NULL,
                    lease_owner = NULL,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    failed_at = now(),
                    updated_at = now()
                FROM locked_request AS request
                WHERE job.session_id = request.session_id
                  AND job.activity_id = request.activity_id
                  AND job.user_id = :uid
                  AND job.answer_hash = :answer_hash
                  AND job.answer_claim_token = :answer_claim_token
                  AND job.lease_owner = :lease_owner
                  AND job.lease_token = :lease_token
                  AND job.lease_version = :lease_version
                  AND job.status = 'running'
                  AND job.lease_expires_at > now()
                  AND (
                      CAST(:placement_retry_timing AS jsonb) IS NULL
                      OR (
                          job.flow_type = 'placement'
                          AND EXISTS (
                              SELECT 1 FROM locked_placement_session
                          )
                      )
                  )
                RETURNING job.session_id::text AS session_id, job.activity_id,
                          job.user_id, job.answer_hash, job.answer_claim_token,
                          job.status, job.attempts, job.max_attempts,
                          job.lease_owner, job.lease_token, job.lease_version,
                          job.lease_expires_at, job.last_error_code, job.error_json,
                          job.created_at, job.updated_at, job.started_at,
                          job.failed_at, job.cancelled_at
            ),
            patched_placement_session AS (
                UPDATE school_sessions AS school_session
                SET state_json = jsonb_set(
                        school_session.state_json,
                        '{_placement_item_timing}',
                        CAST(:placement_retry_timing AS jsonb),
                        true
                    ),
                    updated_at = now()
                FROM terminalized_job AS job
                WHERE CAST(:placement_retry_timing AS jsonb) IS NOT NULL
                  AND school_session.user_id = job.user_id
                  AND school_session.session_id = CAST(job.session_id AS uuid)
                  AND EXISTS (
                      SELECT 1
                      FROM locked_placement_session AS locked_session
                      WHERE locked_session.session_id = school_session.session_id
                  )
                RETURNING school_session.session_id
            ),
            released_request AS (
                UPDATE school_answer_requests AS request
                SET status = 'failed',
                    response_json = NULL,
                    updated_at = now()
                FROM terminalized_job AS job
                WHERE request.session_id = CAST(job.session_id AS uuid)
                  AND request.activity_id = job.activity_id
                  AND request.user_id = job.user_id
                  AND request.answer_hash = job.answer_hash
                  AND request.claim_token = job.answer_claim_token
                  AND request.status = 'processing'
                  AND (
                      CAST(:placement_retry_timing AS jsonb) IS NULL
                      OR EXISTS (SELECT 1 FROM patched_placement_session)
                  )
                RETURNING request.session_id, request.activity_id
            )
            SELECT terminalized_job.*
            FROM terminalized_job
            JOIN released_request ON TRUE
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": _school_evaluation_job_lease_owner(lease_owner),
            "lease_token": lease_token,
            "lease_version": int(lease_version),
            "last_error_code": normalized_error_code,
            "error_json": json.dumps(error_json) if error_json is not None else None,
            "placement_retry_timing": (
                json.dumps(normalized_placement_retry_timing)
                if normalized_placement_retry_timing is not None
                else None
            ),
        },
    )
    row = result.mappings().first()
    await session.commit()
    return _school_evaluation_job_from_row(row) if row else None


async def complete_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
    response_json: dict,
    result_data: dict,
) -> dict | None:
    """Store a worker result only when its lease and answer identity are current."""
    result = await session.execute(
        text(
            """
            UPDATE school_evaluation_jobs
            SET status = 'completed',
                response_json = CAST(:response_json AS jsonb),
                result_data = CAST(:result_data AS jsonb),
                last_error_code = NULL,
                error_json = NULL,
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                completed_at = now(),
                updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND answer_claim_token = :answer_claim_token
              AND lease_owner = :lease_owner
              AND lease_token = :lease_token
              AND lease_version = :lease_version
              AND status = 'running'
              AND lease_expires_at > now()
              AND EXISTS (
                  SELECT 1
                  FROM school_answer_requests AS request
                  WHERE request.session_id = school_evaluation_jobs.session_id
                    AND request.activity_id = school_evaluation_jobs.activity_id
                    AND request.user_id = school_evaluation_jobs.user_id
                    AND request.answer_hash = school_evaluation_jobs.answer_hash
                    AND request.claim_token = school_evaluation_jobs.answer_claim_token
                    AND request.status = 'processing'
              )
            RETURNING session_id::text AS session_id, activity_id, user_id,
                      raw_answer, expected_state_json, request_metadata_json,
                      expected_state_digest,
                      answer_hash, answer_claim_token, flow_type, evaluation_mode,
                      status, attempts, max_attempts, lease_owner, lease_token,
                      lease_version, lease_expires_at, next_attempt_at, last_error_code, error_json,
                      response_json, result_data, created_at, updated_at, started_at,
                      completed_at, failed_at, cancelled_at
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": _school_evaluation_job_lease_owner(lease_owner),
            "lease_token": lease_token,
            "lease_version": int(lease_version),
            "response_json": json.dumps(response_json),
            "result_data": json.dumps(result_data),
        },
    )
    row = result.mappings().first()
    await session.commit()
    return _school_evaluation_job_from_row(row) if row else None


async def fail_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
    last_error_code: str,
    error_json: dict | None = None,
    response_json: dict | None = None,
    result_data: dict | None = None,
) -> dict | None:
    """Persist a terminal worker failure only for the worker that owns the lease."""
    normalized_error_code = str(last_error_code or "").strip()
    if not normalized_error_code:
        raise ValueError("invalid_school_evaluation_job_error_code")
    result = await session.execute(
        text(
            """
            UPDATE school_evaluation_jobs
                SET status = 'failed',
                last_error_code = :last_error_code,
                error_json = CAST(:error_json AS jsonb),
                response_json = CAST(:response_json AS jsonb),
                result_data = CAST(:result_data AS jsonb),
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                failed_at = now(),
                updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND answer_claim_token = :answer_claim_token
              AND lease_owner = :lease_owner
              AND lease_token = :lease_token
              AND lease_version = :lease_version
              AND status = 'running'
              AND lease_expires_at > now()
              AND EXISTS (
                  SELECT 1
                  FROM school_answer_requests AS request
                  WHERE request.session_id = school_evaluation_jobs.session_id
                    AND request.activity_id = school_evaluation_jobs.activity_id
                    AND request.user_id = school_evaluation_jobs.user_id
                    AND request.answer_hash = school_evaluation_jobs.answer_hash
                    AND request.claim_token = school_evaluation_jobs.answer_claim_token
                    AND request.status = 'processing'
              )
            RETURNING session_id::text AS session_id, activity_id, user_id,
                      raw_answer, expected_state_json, request_metadata_json,
                      expected_state_digest,
                      answer_hash, answer_claim_token, flow_type, evaluation_mode,
                      status, attempts, max_attempts, lease_owner, lease_token,
                      lease_version, lease_expires_at, next_attempt_at, last_error_code, error_json,
                      response_json, result_data, created_at, updated_at, started_at,
                      completed_at, failed_at, cancelled_at
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": _school_evaluation_job_lease_owner(lease_owner),
            "lease_token": lease_token,
            "lease_version": int(lease_version),
            "last_error_code": normalized_error_code,
            "error_json": json.dumps(error_json) if error_json is not None else None,
            "response_json": json.dumps(response_json)
            if response_json is not None
            else None,
            "result_data": json.dumps(result_data) if result_data is not None else None,
        },
    )
    row = result.mappings().first()
    await session.commit()
    return _school_evaluation_job_from_row(row) if row else None


async def retry_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str,
    lease_token: str,
    lease_version: int,
    last_error_code: str,
    retry_after_seconds: float | int | None = None,
    error_json: dict | None = None,
) -> dict | None:
    """Release one current worker lease so the same claimed answer can retry."""
    normalized_error_code = str(last_error_code or "").strip()
    if not normalized_error_code:
        raise ValueError("invalid_school_evaluation_job_error_code")
    normalized_retry_after_seconds = _school_evaluation_job_retry_after_seconds(
        retry_after_seconds
    )
    result = await session.execute(
        text(
            """
            UPDATE school_evaluation_jobs
            SET status = 'queued',
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                next_attempt_at = now() + (
                    CAST(:retry_after_seconds AS double precision) * INTERVAL '1 second'
                ),
                last_error_code = :last_error_code,
                error_json = CAST(:error_json AS jsonb),
                response_json = NULL,
                result_data = NULL,
                failed_at = NULL,
                updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND answer_claim_token = :answer_claim_token
              AND lease_owner = :lease_owner
              AND lease_token = :lease_token
              AND lease_version = :lease_version
              AND status = 'running'
              AND lease_expires_at > now()
              AND attempts < max_attempts
              AND EXISTS (
                  SELECT 1
                  FROM school_answer_requests AS request
                  WHERE request.session_id = school_evaluation_jobs.session_id
                    AND request.activity_id = school_evaluation_jobs.activity_id
                    AND request.user_id = school_evaluation_jobs.user_id
                    AND request.answer_hash = school_evaluation_jobs.answer_hash
                    AND request.claim_token = school_evaluation_jobs.answer_claim_token
                    AND request.status = 'processing'
              )
            RETURNING session_id::text AS session_id, activity_id, user_id,
                      raw_answer, expected_state_json, request_metadata_json,
                      expected_state_digest,
                      answer_hash, answer_claim_token, flow_type, evaluation_mode,
                      status, attempts, max_attempts, lease_owner, lease_token,
                      lease_version, lease_expires_at, next_attempt_at, last_error_code, error_json,
                      response_json, result_data, created_at, updated_at, started_at,
                      completed_at, failed_at, cancelled_at
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": _school_evaluation_job_lease_owner(lease_owner),
            "lease_token": lease_token,
            "lease_version": int(lease_version),
            "last_error_code": normalized_error_code,
            "retry_after_seconds": normalized_retry_after_seconds,
            "error_json": json.dumps(error_json) if error_json is not None else None,
        },
    )
    row = result.mappings().first()
    await session.commit()
    return _school_evaluation_job_from_row(row) if row else None


async def cancel_school_evaluation_job(
    session: AsyncSession,
    *,
    user_id: str,
    session_id: str,
    activity_id: str,
    answer_hash: str,
    answer_claim_token: str,
    lease_owner: str | None = None,
    lease_token: str | None = None,
    lease_version: int | None = None,
    last_error_code: str = "evaluation_cancelled",
    error_json: dict | None = None,
) -> dict | None:
    """Cancel queued jobs by identity and running jobs only by current lease."""
    normalized_error_code = str(last_error_code or "").strip()
    if not normalized_error_code:
        raise ValueError("invalid_school_evaluation_job_error_code")
    normalized_lease_owner = (
        _school_evaluation_job_lease_owner(lease_owner)
        if lease_owner is not None
        else None
    )
    result = await session.execute(
        text(
            """
            UPDATE school_evaluation_jobs
            SET status = 'cancelled',
                last_error_code = :last_error_code,
                error_json = CAST(:error_json AS jsonb),
                response_json = NULL,
                result_data = NULL,
                lease_owner = NULL,
                lease_token = NULL,
                lease_expires_at = NULL,
                cancelled_at = now(),
                updated_at = now()
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
              AND answer_hash = :answer_hash
              AND answer_claim_token = :answer_claim_token
              AND (
                  status = 'queued'
                  OR (
                      status = 'running'
                      AND lease_owner = :lease_owner
                      AND lease_token = :lease_token
                      AND lease_version = :lease_version
                      AND lease_expires_at > now()
                  )
              )
              AND EXISTS (
                  SELECT 1
                  FROM school_answer_requests AS request
                  WHERE request.session_id = school_evaluation_jobs.session_id
                    AND request.activity_id = school_evaluation_jobs.activity_id
                    AND request.user_id = school_evaluation_jobs.user_id
                    AND request.answer_hash = school_evaluation_jobs.answer_hash
                    AND request.claim_token = school_evaluation_jobs.answer_claim_token
                    AND request.status = 'processing'
              )
            RETURNING session_id::text AS session_id, activity_id, user_id,
                      raw_answer, expected_state_json, request_metadata_json,
                      expected_state_digest,
                      answer_hash, answer_claim_token, flow_type, evaluation_mode,
                      status, attempts, max_attempts, lease_owner, lease_token,
                      lease_version, lease_expires_at, last_error_code, error_json,
                      response_json, result_data, created_at, updated_at, started_at,
                      completed_at, failed_at, cancelled_at
            """
        ),
        {
            "session_id": session_id,
            "activity_id": activity_id,
            "uid": user_id,
            "answer_hash": answer_hash,
            "answer_claim_token": answer_claim_token,
            "lease_owner": normalized_lease_owner,
            "lease_token": lease_token,
            "lease_version": int(lease_version) if lease_version is not None else None,
            "last_error_code": normalized_error_code,
            "error_json": json.dumps(error_json) if error_json is not None else None,
        },
    )
    row = result.mappings().first()
    await session.commit()
    return _school_evaluation_job_from_row(row) if row else None


async def get_school_session(
    session: AsyncSession,
    user_id: str,
    session_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, user_id, api_version, flow_type,
                   subject_id, class_no, status, current_stage,
                   linked_session_id::text AS linked_session_id, state_json,
                   profile_version_id::text AS profile_version_id,
                   source_placement_report_id::text AS source_placement_report_id,
                   started_at, updated_at, completed_at
            FROM school_sessions
            WHERE user_id = :uid AND session_id = CAST(:session_id AS uuid)
            """
        ),
        {"uid": user_id, "session_id": session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_active_school_session(
    session: AsyncSession,
    user_id: str,
    api_version: str,
    flow_type: str,
    subject_id: str,
    class_no: int,
    *,
    profile_version_id: str | None = None,
    source_placement_report_id: str | None = None,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, user_id, api_version, flow_type,
                   subject_id, class_no, status, current_stage,
                   linked_session_id::text AS linked_session_id, state_json,
                   profile_version_id::text AS profile_version_id,
                   source_placement_report_id::text AS source_placement_report_id,
                   started_at, updated_at, completed_at
            FROM school_sessions
            WHERE user_id = :uid
              AND api_version = :api_version
              AND flow_type = :flow_type
              AND subject_id = :subject_id
              AND class_no = :class_no
              AND (
                  CAST(:profile_version_id AS uuid) IS NULL
                  OR profile_version_id = CAST(:profile_version_id AS uuid)
              )
              AND (
                  CAST(:source_placement_report_id AS uuid) IS NULL
                  OR source_placement_report_id = CAST(:source_placement_report_id AS uuid)
              )
              AND status IN ('active', 'paused_for_masterclass')
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "api_version": api_version,
            "flow_type": flow_type,
            "subject_id": subject_id,
            "class_no": int(class_no),
            "profile_version_id": profile_version_id,
            "source_placement_report_id": source_placement_report_id,
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_latest_school_session(
    session: AsyncSession,
    user_id: str,
    api_version: str,
    flow_type: str,
    subject_id: str,
    class_no: int,
    *,
    profile_version_id: str | None = None,
    source_placement_report_id: str | None = None,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, user_id, api_version, flow_type,
                   subject_id, class_no, status, current_stage,
                   linked_session_id::text AS linked_session_id, state_json,
                   profile_version_id::text AS profile_version_id,
                   source_placement_report_id::text AS source_placement_report_id,
                   started_at, updated_at, completed_at
            FROM school_sessions
            WHERE user_id = :uid
              AND api_version = :api_version
              AND flow_type = :flow_type
              AND subject_id = :subject_id
              AND class_no = :class_no
              AND (
                  CAST(:profile_version_id AS uuid) IS NULL
                  OR profile_version_id = CAST(:profile_version_id AS uuid)
              )
              AND (
                  CAST(:source_placement_report_id AS uuid) IS NULL
                  OR source_placement_report_id = CAST(:source_placement_report_id AS uuid)
              )
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "api_version": api_version,
            "flow_type": flow_type,
            "subject_id": subject_id,
            "class_no": int(class_no),
            "profile_version_id": profile_version_id,
            "source_placement_report_id": source_placement_report_id,
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_school_sessions_linked_to(
    session: AsyncSession,
    user_id: str,
    linked_session_id: str,
) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, user_id, api_version, flow_type,
                   subject_id, class_no, status, current_stage,
                   linked_session_id::text AS linked_session_id, state_json,
                   profile_version_id::text AS profile_version_id,
                   source_placement_report_id::text AS source_placement_report_id,
                   started_at, updated_at, completed_at
            FROM school_sessions
            WHERE user_id = :uid
              AND linked_session_id = CAST(:linked_session_id AS uuid)
            ORDER BY updated_at DESC
            """
        ),
        {"uid": user_id, "linked_session_id": linked_session_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def expire_active_school_sessions_from_other_profiles(
    session: AsyncSession,
    user_id: str,
    current_profile_version_id: str,
) -> int:
    result = await session.execute(
        text(
            """
            UPDATE school_sessions
            SET status = 'expired', updated_at = now(),
                completed_at = COALESCE(completed_at, now())
            WHERE user_id = :uid
              AND status IN ('active', 'paused_for_masterclass')
              AND profile_version_id IS DISTINCT FROM CAST(:profile_version_id AS uuid)
            """
        ),
        {"uid": user_id, "profile_version_id": current_profile_version_id},
    )
    await session.commit()
    return int(result.rowcount or 0)


async def upsert_school_placement_report(
    session: AsyncSession,
    *,
    report_id: str,
    user_id: str,
    profile_version_id: str,
    placement_session_id: str,
    placement_status: str,
    subject_id: str,
    target_class_no: int,
    evaluated_class_no: int | None,
    active_learning_class_no: int | None,
    unlock_state: str,
    blocking_skills: list[dict],
    watchlist_skills: list[dict],
    deviation_note: str = "",
    evidence_summary: dict,
    recommended_recap_modules: list[dict],
    learner_summary: str,
    parent_summary: str,
    allowed_next_actions: list[str],
    _commit: bool = True,
) -> dict:
    await session.execute(
        text(
            """
            INSERT INTO school_placement_reports
                (report_id, user_id, profile_version_id, placement_session_id,
                 placement_status, subject_id, target_class_no, evaluated_class_no,
                 active_learning_class_no, unlock_state, blocking_skills_json,
                 watchlist_skills_json, deviation_note, evidence_summary_json,
                 recommended_recap_modules_json, learner_summary, parent_summary,
                 allowed_next_actions_json)
            VALUES
                (CAST(:report_id AS uuid), :uid, CAST(:profile_version_id AS uuid),
                 CAST(:placement_session_id AS uuid), :placement_status, :subject_id,
                 :target_class_no, :evaluated_class_no, :active_learning_class_no,
                 :unlock_state, CAST(:blocking_skills AS jsonb),
                 CAST(:watchlist_skills AS jsonb), :deviation_note, CAST(:evidence_summary AS jsonb),
                 CAST(:recommended_recap_modules AS jsonb), :learner_summary,
                 :parent_summary, CAST(:allowed_next_actions AS jsonb))
            ON CONFLICT (user_id, placement_session_id) DO UPDATE SET
                placement_status = EXCLUDED.placement_status,
                subject_id = EXCLUDED.subject_id,
                target_class_no = EXCLUDED.target_class_no,
                evaluated_class_no = EXCLUDED.evaluated_class_no,
                active_learning_class_no = EXCLUDED.active_learning_class_no,
                unlock_state = EXCLUDED.unlock_state,
                blocking_skills_json = EXCLUDED.blocking_skills_json,
                watchlist_skills_json = EXCLUDED.watchlist_skills_json,
                deviation_note = EXCLUDED.deviation_note,
                evidence_summary_json = EXCLUDED.evidence_summary_json,
                recommended_recap_modules_json = EXCLUDED.recommended_recap_modules_json,
                learner_summary = EXCLUDED.learner_summary,
                parent_summary = EXCLUDED.parent_summary,
                allowed_next_actions_json = EXCLUDED.allowed_next_actions_json,
                updated_at = now()
            """
        ),
        {
            "report_id": report_id,
            "uid": user_id,
            "profile_version_id": profile_version_id,
            "placement_session_id": placement_session_id,
            "placement_status": placement_status,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "evaluated_class_no": (
                int(evaluated_class_no)
                if evaluated_class_no is not None
                else None
            ),
            "active_learning_class_no": (
                int(active_learning_class_no)
                if active_learning_class_no is not None
                else None
            ),
            "unlock_state": unlock_state,
            "blocking_skills": json.dumps(blocking_skills or []),
            "watchlist_skills": json.dumps(watchlist_skills or []),
            "deviation_note": deviation_note or "",
            "evidence_summary": json.dumps(evidence_summary or {}),
            "recommended_recap_modules": json.dumps(recommended_recap_modules or []),
            "learner_summary": learner_summary or "",
            "parent_summary": parent_summary or "",
            "allowed_next_actions": json.dumps(allowed_next_actions or []),
        },
    )
    if _commit:
        await session.commit()
    row = await get_school_placement_report(session, user_id, placement_session_id)
    if not row:
        raise RuntimeError("school_placement_report_upsert_failed")
    return row


async def get_school_placement_report(
    session: AsyncSession,
    user_id: str,
    placement_session_id: str,
    *,
    profile_version_id: str | None = None,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT report_id::text AS report_id, user_id,
                   profile_version_id::text AS profile_version_id,
                   placement_session_id::text AS placement_session_id,
                   placement_status, subject_id, target_class_no,
                   evaluated_class_no, active_learning_class_no, unlock_state,
                   blocking_skills_json, watchlist_skills_json,
                   deviation_note, evidence_summary_json, recommended_recap_modules_json,
                   learner_summary, parent_summary, allowed_next_actions_json,
                   created_at, updated_at
            FROM school_placement_reports
            WHERE user_id = :uid
              AND placement_session_id = CAST(:placement_session_id AS uuid)
              AND (
                  CAST(:profile_version_id AS uuid) IS NULL
                  OR profile_version_id = CAST(:profile_version_id AS uuid)
              )
            """
        ),
        {
            "uid": user_id,
            "placement_session_id": placement_session_id,
            "profile_version_id": profile_version_id,
        },
    )
    row = result.mappings().first()
    if not row:
        return None
    return _school_placement_report_from_row(dict(row))


def _school_placement_report_from_row(row: dict) -> dict:
    return {
        "report_id": row["report_id"],
        "user_id": row["user_id"],
        "profile_version_id": row["profile_version_id"],
        "placement_session_id": row["placement_session_id"],
        "placement_status": row["placement_status"],
        "subject_id": row["subject_id"],
        "target_class_no": row["target_class_no"],
        "evaluated_class_no": row["evaluated_class_no"],
        "active_learning_class_no": row["active_learning_class_no"],
        "unlock_state": row["unlock_state"],
        "blocking_skills": row.get("blocking_skills_json") or [],
        "watchlist_skills": row.get("watchlist_skills_json") or [],
        "deviation_note": row.get("deviation_note") or "",
        "evidence_summary": row.get("evidence_summary_json") or {},
        "recommended_recap_modules": row.get("recommended_recap_modules_json") or [],
        "learner_summary": row.get("learner_summary") or "",
        "parent_summary": row.get("parent_summary") or "",
        "allowed_next_actions": row.get("allowed_next_actions_json") or [],
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


async def get_school_placement_report_by_id(
    session: AsyncSession,
    user_id: str,
    report_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT report_id::text AS report_id, user_id,
                   profile_version_id::text AS profile_version_id,
                   placement_session_id::text AS placement_session_id,
                   placement_status, subject_id, target_class_no,
                   evaluated_class_no, active_learning_class_no, unlock_state,
                   blocking_skills_json, watchlist_skills_json,
                   deviation_note, evidence_summary_json, recommended_recap_modules_json,
                   learner_summary, parent_summary, allowed_next_actions_json,
                   created_at, updated_at
            FROM school_placement_reports
            WHERE user_id = :uid
              AND report_id = CAST(:report_id AS uuid)
            """
        ),
        {"uid": user_id, "report_id": report_id},
    )
    row = result.mappings().first()
    if not row:
        return None
    return _school_placement_report_from_row(dict(row))


async def get_latest_compatible_school_placement_report(
    session: AsyncSession,
    user_id: str,
    profile_version_id: str,
    subject_id: str,
    target_class_no: int,
) -> dict | None:
    lineage_result = await session.execute(
        text(
            """
            WITH RECURSIVE profile_lineage AS (
                SELECT profile_version_id, source_profile_version_id,
                       board_id, target_class_no, subject_ids,
                       preferred_teaching_language, english_comfort,
                       prior_difficulty_signals, 0 AS depth,
                       ARRAY[profile_version_id] AS visited
                FROM school_profile_versions
                WHERE user_id = :uid
                  AND profile_version_id = CAST(:profile_version_id AS uuid)
                  AND status = 'active'

                UNION ALL

                SELECT source.profile_version_id, source.source_profile_version_id,
                       source.board_id, source.target_class_no, source.subject_ids,
                       source.preferred_teaching_language, source.english_comfort,
                       source.prior_difficulty_signals, current.depth + 1,
                       current.visited || source.profile_version_id
                FROM profile_lineage AS current
                JOIN school_profile_versions AS source
                  ON source.user_id = :uid
                 AND source.profile_version_id = current.source_profile_version_id
                WHERE NOT source.profile_version_id = ANY(current.visited)
            )
            SELECT profile_version_id::text AS profile_version_id,
                   source_profile_version_id::text AS source_profile_version_id,
                   board_id, target_class_no, subject_ids,
                   preferred_teaching_language, english_comfort,
                   prior_difficulty_signals, depth
            FROM profile_lineage
            ORDER BY depth
            """
        ),
        {"uid": user_id, "profile_version_id": profile_version_id},
    )
    lineage = [dict(row) for row in lineage_result.mappings().all()]
    if not lineage:
        return None

    compatible_profile_ids = [str(lineage[0]["profile_version_id"])]
    for current, source in zip(lineage, lineage[1:]):
        if str(current.get("source_profile_version_id") or "") != str(
            source["profile_version_id"]
        ):
            break
        if _school_profile_compatibility_values(
            current
        ) != _school_profile_compatibility_values(source):
            break
        compatible_profile_ids.append(str(source["profile_version_id"]))

    report_result = await session.execute(
        text(
            """
            SELECT report_id::text AS report_id, user_id,
                   profile_version_id::text AS profile_version_id,
                   placement_session_id::text AS placement_session_id,
                   placement_status, subject_id, target_class_no,
                   evaluated_class_no, active_learning_class_no, unlock_state,
                   blocking_skills_json, watchlist_skills_json,
                   evidence_summary_json, recommended_recap_modules_json,
                   learner_summary, parent_summary, allowed_next_actions_json,
                   created_at, updated_at
            FROM school_placement_reports
            WHERE user_id = :uid
              AND subject_id = :subject_id
              AND target_class_no = :target_class_no
            ORDER BY updated_at DESC
            """
        ),
        {
            "uid": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
        },
    )
    reports_by_profile: dict[str, dict] = {}
    for row in report_result.mappings().all():
        report = dict(row)
        reports_by_profile.setdefault(str(report["profile_version_id"]), report)
    for compatible_profile_id in compatible_profile_ids:
        report = reports_by_profile.get(compatible_profile_id)
        if report:
            return _school_placement_report_from_row(report)
    return None


async def upsert_school_language_confidence(
    session: AsyncSession,
    *,
    user_id: str,
    en_production_confidence: float,
    total_signals: int,
    commit: bool = True,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO school_language_confidence
                (user_id, en_production_confidence, total_signals)
            VALUES (:uid, :confidence, :signals)
            ON CONFLICT (user_id) DO UPDATE SET
                en_production_confidence = EXCLUDED.en_production_confidence,
                total_signals = EXCLUDED.total_signals,
                updated_at = now()
            """
        ),
        {
            "uid": user_id,
            "confidence": max(0.0, min(1.0, float(en_production_confidence))),
            "signals": max(0, int(total_signals)),
        },
    )
    if commit:
        await session.commit()


async def get_school_language_confidence(
    session: AsyncSession,
    user_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT user_id, en_production_confidence, total_signals, updated_at
            FROM school_language_confidence
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def upsert_school_v2_placement_session(
    session: AsyncSession,
    *,
    placement_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    preferred_language: str,
    status: str,
    state_json: dict,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO school_v2_placement_sessions
                (placement_session_id, user_id, subject_id, target_class_no,
                 preferred_language, status, state_json, updated_at,
                 completed_at)
            VALUES
                (:placement_session_id, :user_id, :subject_id, :target_class_no,
                 :preferred_language, :status, CAST(:state_json AS jsonb),
                 now(), CASE WHEN :status IN ('complete', 'insufficient_evidence')
                            THEN now() ELSE NULL END)
            ON CONFLICT (placement_session_id) DO UPDATE SET
                subject_id = EXCLUDED.subject_id,
                target_class_no = EXCLUDED.target_class_no,
                preferred_language = EXCLUDED.preferred_language,
                status = EXCLUDED.status,
                state_json = EXCLUDED.state_json,
                updated_at = now(),
                completed_at = CASE
                    WHEN EXCLUDED.status IN ('complete', 'insufficient_evidence')
                    THEN COALESCE(school_v2_placement_sessions.completed_at, now())
                    ELSE NULL
                END
            """
        ),
        {
            "placement_session_id": placement_session_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "preferred_language": preferred_language or "",
            "status": status,
            "state_json": json.dumps(state_json or {}),
        },
    )
    await session.commit()


async def get_school_v2_placement_session(
    session: AsyncSession,
    user_id: str,
    placement_session_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT placement_session_id, user_id, subject_id, target_class_no,
                   preferred_language, status, state_json, started_at,
                   updated_at, completed_at
            FROM school_v2_placement_sessions
            WHERE user_id = :uid AND placement_session_id = :sid
            """
        ),
        {"uid": user_id, "sid": placement_session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_active_school_v2_placement_session(
    session: AsyncSession,
    user_id: str,
    subject_id: str,
    target_class_no: int,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT placement_session_id, user_id, subject_id, target_class_no,
                   preferred_language, status, state_json, started_at,
                   updated_at, completed_at
            FROM school_v2_placement_sessions
            WHERE user_id = :uid
              AND subject_id = :subject_id
              AND target_class_no = :target_class_no
              AND status = 'in_progress'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {"uid": user_id, "subject_id": subject_id, "target_class_no": int(target_class_no)},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def upsert_school_v2_practice_session(
    session: AsyncSession,
    *,
    practice_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    skill_id: str,
    status: str,
    state_json: dict,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO school_v2_practice_sessions
                (practice_session_id, user_id, subject_id, target_class_no,
                 skill_id, status, state_json, updated_at, completed_at)
            VALUES
                (:practice_session_id, :user_id, :subject_id, :target_class_no,
                 :skill_id, :status, CAST(:state_json AS jsonb), now(),
                 CASE WHEN :status = 'complete' THEN now() ELSE NULL END)
            ON CONFLICT (practice_session_id) DO UPDATE SET
                subject_id = EXCLUDED.subject_id,
                target_class_no = EXCLUDED.target_class_no,
                skill_id = EXCLUDED.skill_id,
                status = EXCLUDED.status,
                state_json = EXCLUDED.state_json,
                updated_at = now(),
                completed_at = CASE
                    WHEN EXCLUDED.status = 'complete'
                    THEN COALESCE(school_v2_practice_sessions.completed_at, now())
                    ELSE NULL
                END
            """
        ),
        {
            "practice_session_id": practice_session_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "skill_id": skill_id,
            "status": status,
            "state_json": json.dumps(state_json or {}),
        },
    )
    await session.commit()


async def get_school_v2_practice_session(
    session: AsyncSession,
    user_id: str,
    practice_session_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT practice_session_id, user_id, subject_id, target_class_no,
                   skill_id, status, state_json, started_at, updated_at,
                   completed_at
            FROM school_v2_practice_sessions
            WHERE user_id = :uid AND practice_session_id = :sid
            """
        ),
        {"uid": user_id, "sid": practice_session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_active_school_v2_practice_session(
    session: AsyncSession,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    skill_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT practice_session_id, user_id, subject_id, target_class_no,
                   skill_id, status, state_json, started_at, updated_at,
                   completed_at
            FROM school_v2_practice_sessions
            WHERE user_id = :uid
              AND subject_id = :subject_id
              AND target_class_no = :target_class_no
              AND skill_id = :skill_id
              AND status = 'in_progress'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "skill_id": skill_id,
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def upsert_school_v2_curriculum_session(
    session: AsyncSession,
    *,
    curriculum_session_id: str,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    chapter_id: str,
    status: str,
    state_json: dict,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO school_v2_curriculum_sessions
                (curriculum_session_id, user_id, subject_id, target_class_no,
                 chapter_id, status, state_json, updated_at, completed_at)
            VALUES
                (:curriculum_session_id, :user_id, :subject_id, :target_class_no,
                 :chapter_id, :status, CAST(:state_json AS jsonb), now(),
                 CASE WHEN :status = 'complete' THEN now() ELSE NULL END)
            ON CONFLICT (curriculum_session_id) DO UPDATE SET
                subject_id = EXCLUDED.subject_id,
                target_class_no = EXCLUDED.target_class_no,
                chapter_id = EXCLUDED.chapter_id,
                status = EXCLUDED.status,
                state_json = EXCLUDED.state_json,
                updated_at = now(),
                completed_at = CASE
                    WHEN EXCLUDED.status = 'complete'
                    THEN COALESCE(school_v2_curriculum_sessions.completed_at, now())
                    ELSE NULL
                END
            """
        ),
        {
            "curriculum_session_id": curriculum_session_id,
            "user_id": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "chapter_id": chapter_id,
            "status": status,
            "state_json": json.dumps(state_json or {}),
        },
    )
    await session.commit()


async def get_school_v2_curriculum_session(
    session: AsyncSession,
    user_id: str,
    curriculum_session_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT curriculum_session_id, user_id, subject_id, target_class_no,
                   chapter_id, status, state_json, started_at, updated_at,
                   completed_at
            FROM school_v2_curriculum_sessions
            WHERE user_id = :uid AND curriculum_session_id = :sid
            """
        ),
        {"uid": user_id, "sid": curriculum_session_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_active_school_v2_curriculum_session(
    session: AsyncSession,
    user_id: str,
    subject_id: str,
    target_class_no: int,
    chapter_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT curriculum_session_id, user_id, subject_id, target_class_no,
                   chapter_id, status, state_json, started_at, updated_at,
                   completed_at
            FROM school_v2_curriculum_sessions
            WHERE user_id = :uid
              AND subject_id = :subject_id
              AND target_class_no = :target_class_no
              AND chapter_id = :chapter_id
              AND status = 'in_progress'
            ORDER BY updated_at DESC
            LIMIT 1
            """
        ),
        {
            "uid": user_id,
            "subject_id": subject_id,
            "target_class_no": int(target_class_no),
            "chapter_id": chapter_id,
        },
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_activity_snapshot(session: AsyncSession, user_id: str) -> dict:
    cutoff = time.time() - _WEAKNESS_RECENCY_SECONDS
    result = await session.execute(
        text(
            """
            SELECT
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(r) ORDER BY r.updated_at)
                    FROM (
                        SELECT test_id, class_no, kind, score, passed, by_skill, weak_skills, updated_at
                        FROM school_results
                        WHERE user_id = :uid
                    ) r
                ), '[]'::jsonb) AS school_results,
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(m) ORDER BY m.ema ASC, m.attempts DESC)
                    FROM (
                        SELECT skill, ema, attempts, last_seen
                        FROM school_skill_mastery
                        WHERE user_id = :uid
                    ) m
                ), '[]'::jsonb) AS school_skill_mastery,
                COALESCE((
                    SELECT jsonb_agg(w.skill)
                    FROM (
                        SELECT skill
                        FROM school_skill_mastery
                        WHERE user_id = :uid AND ema < :school_threshold
                        ORDER BY ema ASC, attempts DESC
                        LIMIT :school_limit
                    ) w
                ), '[]'::jsonb) AS school_weak_skills,
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(p))
                    FROM (
                        SELECT competency_node as node_id, mastery as ema, best_mastery as best_ema,
                               attempts, clean_pass, node_completed, completed_at, completion_count,
                               last_completed_session_id
                        FROM competency_nodes
                        WHERE user_id = :uid
                    ) p
                ), '[]'::jsonb) AS progression,
                COALESCE((
                    SELECT jsonb_agg(to_jsonb(x) ORDER BY x.hit_count DESC, x.last_seen DESC)
                    FROM (
                        SELECT user_id, task_type, skill_id, hit_count, last_score, last_seen, last_raw
                        FROM weaknesses
                        WHERE user_id = :uid AND last_seen >= :cutoff
                        ORDER BY hit_count DESC, last_seen DESC
                        LIMIT :weakness_limit
                    ) x
                ), '[]'::jsonb) AS weaknesses
            """
        ),
        {
            "uid": user_id,
            "cutoff": cutoff,
            "school_threshold": _SCHOOL_PASS_MARK,
            "school_limit": _SCHOOL_WEAK_SURFACE_CAP,
            "weakness_limit": _WEAKNESS_SURFACE_CAP,
        },
    )
    row = result.mappings().first() or {}
    return {
        "school_results": list(row.get("school_results") or []),
        "school_skill_mastery": list(row.get("school_skill_mastery") or []),
        "school_weak_skills": list(row.get("school_weak_skills") or []),
        "progression": list(row.get("progression") or []),
        "weaknesses": list(row.get("weaknesses") or []),
    }


async def get_school_review_skills(
    session: AsyncSession,
    user_id: str,
    mastered_threshold: float = _SCHOOL_MASTERED_THRESHOLD,
    stale_seconds: float = _SCHOOL_REVIEW_STALE_SECONDS,
    limit: int = 3,
) -> list[str]:
    cutoff = time.time() - stale_seconds
    result = await session.execute(
        text(
            """
            SELECT skill
            FROM school_skill_mastery
            WHERE user_id = :uid AND ema >= :threshold AND last_seen < :cutoff
            ORDER BY last_seen ASC
            LIMIT :limit
            """
        ),
        {
            "uid": user_id,
            "threshold": mastered_threshold,
            "cutoff": cutoff,
            "limit": limit,
        },
    )
    return [row[0] for row in result.all()]


async def cache_test_items(
    session: AsyncSession,
    user_id: str,
    task_type: str,
    items: list[dict],
    context_hash: str = "default",
    ts: float | None = None,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO test_items (user_id, task_type, context_hash, items, cached_at)
            VALUES (:uid, :task, :context_hash, CAST(:items AS jsonb), :cached)
            ON CONFLICT (user_id, task_type, context_hash) DO UPDATE SET
                items = EXCLUDED.items,
                cached_at = EXCLUDED.cached_at
            """
        ),
        {
            "uid": user_id,
            "task": task_type,
            "context_hash": context_hash or "default",
            "items": json.dumps(items),
            "cached": ts if ts is not None else time.time(),
        },
    )
    await session.commit()


async def get_cached_test_items(
    session: AsyncSession,
    user_id: str,
    task_type: str,
    context_hash: str = "default",
    max_age: float | None = None,
) -> list[dict] | None:
    result = await session.execute(
        text(
            """
            SELECT items, cached_at
            FROM test_items
            WHERE user_id = :uid AND task_type = :task AND context_hash = :context_hash
            """
        ),
        {"uid": user_id, "task": task_type, "context_hash": context_hash or "default"},
    )
    row = result.mappings().first()
    if not row:
        return None
    if max_age is not None and (time.time() - float(row["cached_at"])) > max_age:
        return None
    items = row["items"]
    return list(items) if isinstance(items, list) else None


# ---------- billing: credits ----------

async def get_credits(session: AsyncSession, user_id: str) -> int:
    summary = await get_wallet_summary(session, user_id)
    return int(summary["credits"])


async def get_wallet_summary(session: AsyncSession, user_id: str) -> dict:
    """Return the spendable balance, separating beta credit from paid credit."""
    try:
        profile = await _lock_wallet_profile(session, user_id)
        if profile is None:
            return {
                "credits": 0,
                "beta_credits": 0,
                "paid_credits": 0,
                "promo_credits": 0,
                "beta_expires_at": None,
            }
        await _ensure_legacy_credit_lot(session, user_id)
        await _expire_wallet_lots(session, user_id)
        result = await session.execute(
            text(
                """
                SELECT id, source, remaining_credits, expires_at
                FROM credit_lots
                WHERE user_id = :uid
                ORDER BY id
                """
            ),
            {"uid": user_id},
        )
        lots = [
            CreditLot(
                lot_id=int(row["id"]),
                source=str(row["source"]),
                remaining_credits=int(row["remaining_credits"]),
                expires_at=row["expires_at"],
            )
            for row in result.mappings().all()
        ]
        summary = wallet_summary(lots, now=datetime.now(timezone.utc))
        await _sync_cached_wallet_balance(session, user_id)
        await session.commit()
        return summary
    except Exception:
        await session.rollback()
        raise


async def set_demo_unlimited(
    session: AsyncSession, user_id: str, enabled: bool
) -> None:
    await session.execute(
        text("UPDATE learner_profiles SET demo_unlimited = :e WHERE user_id = :u"),
        {"e": enabled, "u": user_id},
    )
    await session.commit()


async def grant_credits(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    *,
    source: str = "promo",
    grant_key: str | None = None,
    expires_at: datetime | None = None,
) -> int:
    """Grant a non-purchase lot, retaining the legacy public signature."""
    try:
        key = grant_key or f"{source}:{reason}:{uuid4()}"
        await _grant_credit_lot(
            session,
            user_id=user_id,
            amount=amount,
            reason=reason,
            source=source,
            grant_key=key,
            expires_at=expires_at,
        )
        await session.commit()
        return await get_credits(session, user_id)
    except Exception:
        await session.rollback()
        raise


# ---------- billing: content unlocks ----------

async def has_unlock(
    session: AsyncSession, user_id: str, scope: str, ref_id: str
) -> bool:
    result = await session.execute(
        text(
            "SELECT 1 FROM content_unlocks "
            "WHERE user_id = :u AND scope = :s AND ref_id = :r"
        ),
        {"u": user_id, "s": scope, "r": ref_id},
    )
    return result.first() is not None


async def add_unlock(
    session: AsyncSession,
    user_id: str,
    scope: str,
    ref_id: str,
    credits_spent: int,
) -> None:
    await session.execute(
        text(
            "INSERT INTO content_unlocks (user_id, scope, ref_id, credits_spent) "
            "VALUES (:u, :s, :r, :c) "
            "ON CONFLICT (user_id, scope, ref_id) DO NOTHING"
        ),
        {"u": user_id, "s": scope, "r": ref_id, "c": credits_spent},
    )
    await session.commit()


async def remove_unlock(
    session: AsyncSession, user_id: str, scope: str, ref_id: str
) -> None:
    await session.execute(
        text(
            "DELETE FROM content_unlocks "
            "WHERE user_id = :u AND scope = :s AND ref_id = :r"
        ),
        {"u": user_id, "s": scope, "r": ref_id},
    )
    await session.commit()


async def list_unlocks(session: AsyncSession, user_id: str) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT scope, ref_id, credits_spent FROM content_unlocks "
            "WHERE user_id = :u"
        ),
        {"u": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def record_node_attempt(
    session: AsyncSession,
    *,
    attempt_id: str,
    session_id: str,
    user_id: str,
    node_id: str,
    starting_mastery: float = 0.0,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO node_attempts (
                attempt_id, session_id, user_id, competency_node, status, starting_mastery
            )
            VALUES (
                :attempt_id, :session_id, :user_id, :node_id, 'active', :starting_mastery
            )
            ON CONFLICT (attempt_id) DO NOTHING
            """
        ),
        {
            "attempt_id": attempt_id,
            "session_id": session_id,
            "user_id": user_id,
            "node_id": node_id,
            "starting_mastery": starting_mastery,
        },
    )
    await session.commit()


async def list_node_attempt_nodes(session: AsyncSession, user_id: str) -> list[str]:
    result = await session.execute(
        text(
            """
            SELECT competency_node
            FROM node_attempts
            WHERE user_id = :u
              AND status IN ('active', 'completed')
            ORDER BY started_at ASC
            """
        ),
        {"u": user_id},
    )
    return [row[0] for row in result.all()]


# ---------- billing: purchases ----------

async def record_purchase(
    session: AsyncSession,
    order_id: str,
    user_id: str,
    pack_id: str,
    credits: int,
    amount_paise: int,
    status: str = "created",
) -> None:
    await session.execute(
        text(
            "INSERT INTO purchases "
            "(order_id, user_id, pack_id, credits, amount_paise, status) "
            "VALUES (:o, :u, :p, :c, :a, :st) "
            "ON CONFLICT (order_id) DO NOTHING"
        ),
        {
            "o": order_id,
            "u": user_id,
            "p": pack_id,
            "c": credits,
            "a": amount_paise,
            "st": status,
        },
    )
    await session.commit()


async def get_purchase(session: AsyncSession, order_id: str) -> dict | None:
    result = await session.execute(
        text("SELECT * FROM purchases WHERE order_id = :o"),
        {"o": order_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def mark_purchase_paid(session: AsyncSession, order_id: str) -> bool:
    result = await session.execute(
        text(
            "UPDATE purchases SET status = 'paid' "
            "WHERE order_id = :o AND status != 'paid'"
        ),
        {"o": order_id},
    )
    await session.commit()
    return result.rowcount > 0


async def mark_paid_and_grant(
    session: AsyncSession,
    order_id: str,
    user_id: str,
    credits: int,
    reason: str,
) -> bool:
    """Latch a purchase to 'paid' AND grant its credits in ONE transaction.

    Folds the idempotency latch and the credit grant into a single committed
    unit. The old PgStore two-step (mark_purchase_paid committed in one txn,
    then grant_credits committed in a SECOND txn) had a fatal hole: an error
    BETWEEN them left the order
    permanently 'paid' while credits were never granted, and Razorpay's retry
    then hit `WHERE status != 'paid'` -> 0 rows -> grant skipped forever
    (customer paid, no credits). Here either both land under one commit() or
    neither does.

    Returns True only on the FIRST captured webhook for this order (granted
    once); False on a retry where it is already paid (no double grant). Rolls the
    whole unit back and raises KeyError if the buyer's profile is missing,
    leaving the order UNPAID so a later retry or reconciliation can still grant.
    """
    if credits < 0:
        raise ValueError("grant amount must be non-negative")
    try:
        latch = await session.execute(
            text(
                "UPDATE purchases SET status = 'paid' "
                "WHERE order_id = :o AND status != 'paid'"
            ),
            {"o": order_id},
        )
        if latch.rowcount == 0:
            # Already paid (idempotent retry) — nothing to grant.
            await session.rollback()
            return False
        granted = await _grant_credit_lot(
            session,
            user_id=user_id,
            amount=credits,
            reason=reason,
            source="paid_purchase",
            grant_key=f"purchase:{order_id}",
        )
        if not granted:
            raise RuntimeError("paid_purchase_credit_lot_already_exists")
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise
