"""Persistence repository — thin async SQL over the product data tables.

Pure data access: no pedagogy, no AI. The service layer owns flow; this owns
rows. Every function takes an AsyncSession so the caller controls the txn
boundary. Product runtime must use Supabase/Postgres; storage failures should
surface to callers instead of silently losing learner state.
"""
import json
import time
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.content.skills import coerce_skill_id

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
) -> dict:
    """Resolve/link/create a Google learner in one DB transaction.

    The old route opened separate Supabase connections for sub lookup, email
    lookup, profile upsert, welcome credit grant, and balance read. Over the
    transaction pooler that made first login painfully slow. Keep this path on
    one AsyncSession and one commit.
    """
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
        await session.commit()
        if row:
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
                school_profile = CAST(:school_profile AS jsonb),
                career_profile = CAST(:career_profile AS jsonb),
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
                                    >= :stale_seconds
                            )
                            ORDER BY a.updated_at DESC
                        )
                        FROM school_answer_requests AS a
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
                         draft_revision, last_save_request_id, last_save_payload_hash,
                         source_profile_version_id)
                    VALUES
                        (CAST(:profile_version_id AS uuid), :uid, 'draft', :display_name,
                         :school_name, :board_id, :target_class_no,
                         CAST(:subject_ids AS jsonb), :preferred_teaching_language,
                         :english_comfort, :learner_goal, :parent_goal,
                         CAST(:prior_difficulty_signals AS jsonb), :current_step, 1,
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


async def deduct_credit(
    session: AsyncSession, user_id: str, amount: int, reason: str
) -> bool:
    """Spend `amount` credits. Returns True if allowed/charged.

    Judge/demo bypass (architecture-v3 §621): demo_unlimited profiles are
    NEVER charged and ALWAYS allowed — zero paywalls for XPRIZE judges.
    """
    profile = await get_profile(session, user_id)
    if profile is None:
        return False
    if profile["demo_unlimited"]:
        return True
    # Atomic spend: the balance check and the decrement are a single guarded
    # UPDATE (`credits >= :amt`). A Python-side read-then-write (TOCTOU) lets two
    # concurrent spends both pass the check and both subtract — double-spend. The
    # WHERE guard makes the row engine arbitrate: at most one wins, and
    # rowcount == 0 means insufficient funds at write time.
    result = await session.execute(
        text(
            "UPDATE learner_profiles SET credits = credits - :amt "
            "WHERE user_id = :uid AND credits >= :amt"
        ),
        {"amt": amount, "uid": user_id},
    )
    if result.rowcount == 0:
        return False
    await session.execute(
        text(
            "INSERT INTO credit_transactions (user_id, delta, reason) "
            "VALUES (:uid, :delta, :reason)"
        ),
        {"uid": user_id, "delta": -amount, "reason": reason},
    )
    await session.commit()
    return True


async def deduct_credit_once(
    session: AsyncSession,
    user_id: str,
    amount: int,
    reason: str,
    idempotency_key: str,
) -> bool:
    """Atomically debit one metered action at most once per user/key."""
    profile = await get_profile(session, user_id)
    if profile is None:
        return False
    if profile["demo_unlimited"]:
        return True
    try:
        inserted = await session.execute(
            text(
                """
                INSERT INTO credit_transactions (user_id, delta, reason, idempotency_key)
                VALUES (:uid, :delta, :reason, :key)
                ON CONFLICT (user_id, idempotency_key)
                    WHERE idempotency_key IS NOT NULL
                DO NOTHING
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
        if inserted.first() is None:
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
            await session.rollback()
            if not row or int(row["delta"]) != -amount or str(row["reason"]) != reason:
                raise ValueError("credit_idempotency_key_reused_with_different_payload")
            return True
        debited = await session.execute(
            text(
                "UPDATE learner_profiles SET credits = credits - :amt "
                "WHERE user_id = :uid AND credits >= :amt"
            ),
            {"amt": amount, "uid": user_id},
        )
        if debited.rowcount == 0:
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
        if released.first() is None:
            await session.rollback()
            return False
        await session.execute(
            text("UPDATE learner_profiles SET credits = credits + :amt WHERE user_id = :uid"),
            {"amt": amount, "uid": user_id},
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
    profile = await get_profile(session, user_id)
    if profile is None:
        return False, False
    if profile["demo_unlimited"]:
        return True, False
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
            # Already owned: discard the no-op insert and do not charge again.
            await session.rollback()
            return True, False
        # Fresh unlock — now debit. The balance check and decrement are one
        # statement so concurrent spends cannot both pass. rowcount == 0 =>
        # insufficient funds: roll back the unlock too.
        result = await session.execute(
            text(
                "UPDATE learner_profiles SET credits = credits - :amt "
                "WHERE user_id = :uid AND credits >= :amt"
            ),
            {"amt": amount, "uid": user_id},
        )
        if result.rowcount == 0:
            await session.rollback()
            return False, False
        await session.execute(
            text(
                "INSERT INTO credit_transactions (user_id, delta, reason) "
                "VALUES (:uid, :delta, :reason)"
            ),
            {"uid": user_id, "delta": -amount, "reason": reason},
        )
        await session.commit()
        return True, True
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
        if released.first() is None:
            raise RuntimeError("claimed_start_charge_missing")

        credited = await session.execute(
            text("UPDATE learner_profiles SET credits = credits + :amt WHERE user_id = :uid"),
            {"amt": amount, "uid": user_id},
        )
        if credited.rowcount != 1:
            raise RuntimeError("claimed_start_profile_missing")
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
    return {
        "profiles": [dict(row) for row in profiles.mappings().all()],
        "reports": [],
        "events": [dict(row) for row in events.mappings().all()],
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
) -> None:
    if api_version != "rebuild" and status in _SCHOOL_ACTIVE_SESSION_STATUSES:
        raise ValueError("archived_school_api_version")
    if api_version == "rebuild":
        await _lock_school_profile_lineage(session, user_id)
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

    try:
        await _lock_school_profile_lineage(session, user_id)
        await authorize_expected_profile()

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


async def persist_school_answer_attempt(
    session: AsyncSession,
    *,
    learning_event: dict,
    school_session: dict,
    expected_state_json: dict,
    request_activity_id: str | None = None,
    request_answer_hash: str | None = None,
    request_claim_token: str | None = None,
    response_json: dict | None = None,
    placement_report: dict | None = None,
    projection_evidence: dict | None = None,
    language_evaluation: dict | None = None,
) -> None:
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
                or request_claim_token is None
                or response_json is None
            ):
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
            if (
                request_row is None
                or request_row["status"] != "processing"
                or request_row["answer_hash"] != request_answer_hash
                or str(request_row["claim_token"] or "") != request_claim_token
            ):
                raise ValueError("stale_school_answer_request")
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
                "uid": user_id,
            },
        )
        current_state = result.scalar_one_or_none()
        if isinstance(current_state, str):
            current_state = json.loads(current_state)
        if current_state is None or dict(current_state) != dict(expected_state_json):
            raise ValueError("stale_school_answer_session")

        profile_upserts: list[dict] = []
        if projection_evidence is not None:
            from app.services.school.projection import (
                SchoolAttemptEvidence,
                derive_school_projection_delta,
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
            projection = SchoolAttemptEvidence.from_dict(projection_evidence)
            profile_upserts = derive_school_projection_delta(
                projection,
                [dict(row) for row in existing_profiles],
            )
            for profile in profile_upserts:
                profile["user_id"] = user_id

        session_to_write = dict(school_session)
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
        await upsert_school_session(session, **session_to_write, _commit=False)
        if placement_report is not None:
            await upsert_school_placement_report(
                session,
                **placement_report,
                _commit=False,
            )
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
    response_json: dict | None = None,
    projection_evidence: dict | None = None,
    language_evaluation: dict | None = None,
) -> None:
    await persist_school_answer_attempt(
        session,
        learning_event=learning_event,
        school_session=school_session,
        expected_state_json=expected_state_json,
        request_activity_id=request_activity_id,
        request_answer_hash=request_answer_hash,
        request_claim_token=request_claim_token,
        response_json=response_json,
        projection_evidence=projection_evidence,
        language_evaluation=language_evaluation,
    )


async def get_school_answer_request(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    activity_id: str,
) -> dict | None:
    result = await session.execute(
        text(
            """
            SELECT session_id::text AS session_id, activity_id, user_id, answer_hash,
                   claim_token,
                   status, response_json, created_at, updated_at,
                   EXTRACT(EPOCH FROM (now() - updated_at)) AS age_seconds
            FROM school_answer_requests
            WHERE session_id = CAST(:session_id AS uuid)
              AND activity_id = :activity_id
              AND user_id = :uid
            """
        ),
        {"session_id": session_id, "activity_id": activity_id, "uid": user_id},
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
) -> None:
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
    evaluated_class_no: int,
    active_learning_class_no: int,
    unlock_state: str,
    blocking_skills: list[dict],
    watchlist_skills: list[dict],
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
                 watchlist_skills_json, evidence_summary_json,
                 recommended_recap_modules_json, learner_summary, parent_summary,
                 allowed_next_actions_json)
            VALUES
                (CAST(:report_id AS uuid), :uid, CAST(:profile_version_id AS uuid),
                 CAST(:placement_session_id AS uuid), :placement_status, :subject_id,
                 :target_class_no, :evaluated_class_no, :active_learning_class_no,
                 :unlock_state, CAST(:blocking_skills AS jsonb),
                 CAST(:watchlist_skills AS jsonb), CAST(:evidence_summary AS jsonb),
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
            "evaluated_class_no": int(evaluated_class_no),
            "active_learning_class_no": int(active_learning_class_no),
            "unlock_state": unlock_state,
            "blocking_skills": json.dumps(blocking_skills or []),
            "watchlist_skills": json.dumps(watchlist_skills or []),
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
                   evidence_summary_json, recommended_recap_modules_json,
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
                   evidence_summary_json, recommended_recap_modules_json,
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
    result = await session.execute(
        text("SELECT credits FROM learner_profiles WHERE user_id = :u"),
        {"u": user_id},
    )
    row = result.mappings().first()
    return int(row["credits"]) if row else 0


async def set_demo_unlimited(
    session: AsyncSession, user_id: str, enabled: bool
) -> None:
    await session.execute(
        text("UPDATE learner_profiles SET demo_unlimited = :e WHERE user_id = :u"),
        {"e": enabled, "u": user_id},
    )
    await session.commit()


async def grant_credits(
    session: AsyncSession, user_id: str, amount: int, reason: str
) -> int:
    await session.execute(
        text(
            "UPDATE learner_profiles SET credits = credits + :amount "
            "WHERE user_id = :u"
        ),
        {"amount": amount, "u": user_id},
    )
    await session.execute(
        text(
            "INSERT INTO credit_transactions (user_id, delta, reason) "
            "VALUES (:u, :delta, :reason)"
        ),
        {"u": user_id, "delta": amount, "reason": reason},
    )
    await session.commit()
    return await get_credits(session, user_id)


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
        grant = await session.execute(
            text(
                "UPDATE learner_profiles SET credits = credits + :amt "
                "WHERE user_id = :u"
            ),
            {"amt": credits, "u": user_id},
        )
        if grant.rowcount == 0:
            # No such profile: undo the latch too so the grant is not lost.
            await session.rollback()
            raise KeyError(user_id)
        await session.execute(
            text(
                "INSERT INTO credit_transactions (user_id, delta, reason) "
                "VALUES (:u, :delta, :reason)"
            ),
            {"u": user_id, "delta": credits, "reason": reason},
        )
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise
