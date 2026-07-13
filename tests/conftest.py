"""Hardening-test fixtures.

Tests must not create a local product database. Endpoint tests patch the route
modules to use this process-local fake store; runtime code still resolves only
to PgStore/Supabase.
"""
from __future__ import annotations

import asyncio
import copy
import importlib
import os
import time
from typing import Any
from uuid import uuid4

import pytest

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("AI_BACKEND", "local")
os.environ.setdefault("ZIDD_ALLOW_TEST_AUTH", "1")
os.environ.setdefault("ZIDD_JWT_SECRET", "test-jwt-secret-do-not-use-in-prod")
os.environ.setdefault("CORS_ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)
os.environ.setdefault("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")


class InMemoryStore:
    REQUEST_STALE_SECONDS = 120
    SCHOOL_ANSWER_REQUEST_STALE_SECONDS = 120

    def __init__(self) -> None:
        self.profiles: dict[str, dict[str, Any]] = {}
        self.school_profile_versions: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_profile_draft_requests: dict[tuple[str, str], dict[str, Any]] = {}
        self.mastery: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_results: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_mastery: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_sessions: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_answer_requests: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_placement_reports: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_language_confidence: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, dict[str, Any]] = {}
        self.session_runtime: dict[str, dict[str, Any]] = {}
        self.session_messages: dict[str, list[dict[str, Any]]] = {}
        self.node_attempts: dict[str, dict[str, Any]] = {}
        self.turn_evaluations: list[dict[str, Any]] = []
        self.turn_requests: dict[tuple[str, str], dict[str, Any]] = {}
        self.start_requests: dict[tuple[str, str], dict[str, Any]] = {}
        self.opening_requests: dict[tuple[str, str], dict[str, Any]] = {}
        self.end_requests: dict[str, dict[str, Any]] = {}
        self.learning_events: list[dict[str, Any]] = []
        self.session_reports: dict[tuple[str, str], dict[str, Any]] = {}
        self.learner_skill_profiles: dict[tuple[str, str, str], dict[str, Any]] = {}
        self.school_v2_placement_sessions: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_v2_practice_sessions: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_v2_curriculum_sessions: dict[tuple[str, str], dict[str, Any]] = {}
        self.unlocks: set[tuple[str, str, str]] = set()
        self.google_login_resolutions = 0
        self.activity_snapshot_calls = 0
        self._school_curriculum_attempt_lock = asyncio.Lock()
        self._school_lineage_locks: dict[str, asyncio.Lock] = {}

    def _school_lineage_lock(self, user_id: str) -> asyncio.Lock:
        return self._school_lineage_locks.setdefault(user_id, asyncio.Lock())

    def _is_stale_request(self, row: dict[str, Any]) -> bool:
        if row.get("status") != "in_progress":
            return False
        updated_at = row.get("updated_at") or row.get("created_at")
        if updated_at is None:
            return False
        return time.time() - float(updated_at) > self.REQUEST_STALE_SECONDS

    def _mark_stale_failed(self, row: dict[str, Any]) -> None:
        row["status"] = "failed"
        row["error_code"] = "stale_in_progress"
        row["updated_at"] = time.time()

    async def ping_writable(self) -> bool:
        return True

    def _profile(self, user_id: str) -> dict[str, Any]:
        return self.profiles.setdefault(
            user_id,
            {
                "user_id": user_id,
                "name": "",
                "email": None,
                "google_sub": None,
                "credits": 0,
                "demo_unlimited": False,
                "preferences": {},
                "primary_motive": None,
                "onboarding_completed_at": None,
                "school_profile": {},
                "career_profile": {},
                "onboarding_state": {},
            },
        )

    async def ensure_profile(
        self,
        user_id: str,
        name: str = "",
        email: str | None = None,
        google_sub: str | None = None,
    ) -> None:
        profile = self._profile(user_id)
        if name.strip():
            profile["name"] = name.strip()
        if email is not None:
            profile["email"] = email
        if google_sub is not None:
            profile["google_sub"] = google_sub

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        profile = self.profiles.get(user_id)
        return dict(profile) if profile else None

    async def get_profile_by_email(self, email: str) -> dict[str, Any] | None:
        for profile in self.profiles.values():
            if profile.get("email") == email:
                return dict(profile)
        return None

    async def get_profile_by_google_sub(self, google_sub: str) -> dict[str, Any] | None:
        for profile in self.profiles.values():
            if profile.get("google_sub") == google_sub:
                return dict(profile)
        return None

    async def resolve_google_login(
        self,
        google_sub: str,
        email: str,
        name: str,
        welcome_credits: int,
    ) -> dict[str, Any]:
        self.google_login_resolutions += 1
        profile = await self.get_profile_by_google_sub(google_sub)
        if profile:
            return {"user_id": profile["user_id"], "is_new_user": False}

        profile = await self.get_profile_by_email(email)
        if profile:
            await self.ensure_profile(profile["user_id"], email=email, google_sub=google_sub)
            return {"user_id": profile["user_id"], "is_new_user": False}

        user_id = f"google:{google_sub}"
        await self.ensure_profile(user_id, name=name, email=email, google_sub=google_sub)
        await self.grant_credits(user_id, welcome_credits, "welcome")
        return {"user_id": user_id, "is_new_user": True}

    async def get_preferences(self, user_id: str) -> dict[str, Any]:
        return dict(self._profile(user_id).get("preferences") or {})

    async def update_preferences(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        profile = self._profile(user_id)
        prefs = dict(profile.get("preferences") or {})
        prefs.update(patch)
        profile["preferences"] = prefs
        return dict(prefs)

    async def update_onboarding_state(self, user_id: str, draft: dict[str, Any]) -> dict[str, Any]:
        clean = dict(draft or {})
        self._profile(user_id)["onboarding_state"] = clean
        return dict(clean)

    async def complete_onboarding(
        self,
        user_id: str,
        display_name: str,
        primary_motive: str,
        school_profile: dict[str, Any],
        career_profile: dict[str, Any],
    ) -> dict[str, Any]:
        profile = self._profile(user_id)
        if display_name.strip():
            profile["name"] = display_name.strip()
        profile["primary_motive"] = primary_motive
        profile["onboarding_completed_at"] = time.time()
        profile["school_profile"] = dict(school_profile or {})
        profile["career_profile"] = dict(career_profile or {})
        profile["onboarding_state"] = {}
        return dict(profile)

    async def get_active_school_profile_version(self, user_id: str) -> dict[str, Any] | None:
        rows = [
            row
            for (uid, _version_id), row in self.school_profile_versions.items()
            if uid == user_id and row.get("status") == "active"
        ]
        rows.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        return dict(rows[0]) if rows else None

    async def get_school_state_snapshot(self, user_id: str) -> dict[str, Any]:
        self.school_state_snapshot_calls = int(
            getattr(self, "school_state_snapshot_calls", 0)
        ) + 1
        learner = self.profiles.get(user_id)
        profile_rows = [
            row
            for (uid, _version_id), row in self.school_profile_versions.items()
            if uid == user_id and row.get("status") == "active"
        ]
        profile_rows.sort(
            key=lambda row: float(row.get("updated_at") or 0),
            reverse=True,
        )
        profile = profile_rows[0] if profile_rows else None
        if not profile:
            return {
                "learner_profile": copy.deepcopy(learner),
                "school_profile": None,
                "placement_session": None,
                "placement_report": None,
                "recap_session": None,
                "curriculum_session": None,
                "linked_sessions": [],
                "processing_answer_requests": [],
                "school_skill_profiles": [],
            }

        profile_version_id = str(profile["profile_version_id"])
        subject_id = str((profile.get("subject_ids") or [""])[0])
        class_no = int(profile.get("target_class_no") or 0)
        rows = [
            row
            for (uid, _session_id), row in self.school_sessions.items()
            if uid == user_id
            and row.get("api_version") == "rebuild"
            and str(row.get("profile_version_id") or "") == profile_version_id
            and row.get("subject_id") == subject_id
            and int(row.get("class_no") or 0) == class_no
        ]

        def latest(flow_type: str, report_id: str | None = None) -> dict | None:
            candidates = [
                row
                for row in rows
                if row.get("flow_type") == flow_type
                and (
                    report_id is None
                    or str(row.get("source_placement_report_id") or "")
                    == str(report_id)
                )
            ]
            candidates.sort(
                key=lambda row: (
                    row.get("status") in {"active", "paused_for_masterclass"},
                    float(row.get("updated_at") or 0),
                ),
                reverse=True,
            )
            return candidates[0] if candidates else None

        placement_session = latest("placement")
        placement_session_id = (
            str(placement_session.get("session_id") or "")
            if placement_session
            else ""
        )
        reports = [
            row
            for (report_user_id, report_placement_id), row in self.school_placement_reports.items()
            if report_user_id == user_id
            and str(row.get("profile_version_id") or "") == profile_version_id
            and (
                str(report_placement_id) == placement_session_id
                or (
                    row.get("subject_id") == subject_id
                    and int(row.get("target_class_no") or 0) == class_no
                )
            )
        ]
        reports.sort(
            key=lambda row: (
                bool(
                    placement_session
                    and str(row.get("placement_session_id") or "")
                    == str(placement_session.get("session_id") or "")
                ),
                float(row.get("updated_at") or 0),
            ),
            reverse=True,
        )
        placement_report = reports[0] if reports else None
        report_id = (
            str(placement_report.get("report_id") or "")
            if placement_report
            else None
        )
        recap_session = latest("recap", report_id) if report_id else None
        curriculum_session = latest("curriculum", report_id) if report_id else None
        parent = curriculum_session or recap_session
        linked_sessions = [
            row
            for row in rows
            if parent
            and str(row.get("linked_session_id") or "")
            == str(parent.get("session_id") or "")
        ]
        processing_requests = [
            row
            for (session_id, _activity_id), row in self.school_answer_requests.items()
            if curriculum_session
            and str(session_id) == str(curriculum_session.get("session_id") or "")
            and row.get("status") == "processing"
        ]
        skill_profiles = [
            row
            for (uid, domain, _skill_id), row in self.learner_skill_profiles.items()
            if uid == user_id and domain == "school"
        ]
        return {
            "learner_profile": copy.deepcopy(learner),
            "school_profile": copy.deepcopy(profile),
            "placement_session": copy.deepcopy(placement_session),
            "placement_report": copy.deepcopy(placement_report),
            "recap_session": copy.deepcopy(recap_session),
            "curriculum_session": copy.deepcopy(curriculum_session),
            "linked_sessions": copy.deepcopy(linked_sessions),
            "processing_answer_requests": copy.deepcopy(processing_requests),
            "school_skill_profiles": copy.deepcopy(skill_profiles),
        }

    async def get_school_profile_draft(self, user_id: str) -> dict[str, Any] | None:
        rows = [
            row
            for (uid, _version_id), row in self.school_profile_versions.items()
            if uid == user_id and row.get("status") == "draft"
        ]
        rows.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        return dict(rows[0]) if rows else None

    async def get_school_profile_version(
        self,
        user_id: str,
        profile_version_id: str,
    ) -> dict[str, Any] | None:
        row = self.school_profile_versions.get((user_id, str(profile_version_id)))
        return dict(row) if row else None

    @staticmethod
    def _school_profile_values(
        row: dict[str, Any],
        fields: tuple[str, ...],
    ) -> tuple[Any, ...]:
        values: list[Any] = []
        for field in fields:
            value = row.get(field)
            if isinstance(value, list):
                value = tuple(sorted(set(value)))
            values.append(value)
        return tuple(values)

    @classmethod
    def _school_profile_all_values(cls, row: dict[str, Any]) -> tuple[Any, ...]:
        return cls._school_profile_values(
            row,
            (
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
            ),
        )

    @classmethod
    def _school_profile_compatibility_values(
        cls,
        row: dict[str, Any],
    ) -> tuple[Any, ...]:
        return cls._school_profile_values(
            row,
            (
                "board_id",
                "target_class_no",
                "subject_ids",
                "preferred_teaching_language",
                "english_comfort",
                "prior_difficulty_signals",
            ),
        )

    @staticmethod
    def _school_profile_draft_snapshot(row: dict[str, Any]) -> dict[str, Any]:
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
            "subject_ids": copy.deepcopy(row.get("subject_ids")),
            "preferred_teaching_language": row.get("preferred_teaching_language"),
            "english_comfort": row.get("english_comfort"),
            "learner_goal": row.get("learner_goal"),
            "parent_goal": row.get("parent_goal"),
            "prior_difficulty_signals": copy.deepcopy(
                row.get("prior_difficulty_signals")
            ),
        }

    async def save_school_profile_draft(
        self,
        *,
        user_id: str,
        profile_version_id: str | None,
        expected_revision: int | None,
        current_step: int,
        request_id: str,
        payload_hash: str,
        patch: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._school_lineage_lock(user_id):
            request_key = (user_id, str(request_id))
            saved_request = self.school_profile_draft_requests.get(request_key)
            if saved_request:
                if saved_request["payload_hash"] != payload_hash:
                    raise ValueError("school_draft_request_conflict")
                return copy.deepcopy(saved_request["response_json"])

            existing = await self.get_school_profile_draft(user_id)
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
                row = self.school_profile_versions[
                    (user_id, str(existing["profile_version_id"]))
                ]
                row.update(copy.deepcopy(patch))
                row["current_step"] = int(current_step)
                row["draft_revision"] = int(row.get("draft_revision") or 1) + 1
                row["last_save_request_id"] = str(request_id)
                row["last_save_payload_hash"] = payload_hash
                row["updated_at"] = time.time()
                snapshot = self._school_profile_draft_snapshot(row)
                self.school_profile_draft_requests[request_key] = {
                    "user_id": user_id,
                    "request_id": str(request_id),
                    "profile_version_id": str(row["profile_version_id"]),
                    "payload_hash": payload_hash,
                    "response_json": copy.deepcopy(snapshot),
                    "created_at": time.time(),
                    "updated_at": time.time(),
                }
                return snapshot

            if profile_version_id is not None or expected_revision is not None:
                raise ValueError("school_draft_not_found")
            active = await self.get_active_school_profile_version(user_id)
            draft_id = str(uuid4())
            now = time.time()
            row = {
                "profile_version_id": draft_id,
                "user_id": user_id,
                "status": "draft",
                "display_name": None,
                "school_name": None,
                "board_id": None,
                "target_class_no": None,
                "subject_ids": None,
                "preferred_teaching_language": None,
                "english_comfort": None,
                "learner_goal": None,
                "parent_goal": None,
                "prior_difficulty_signals": None,
                "current_step": int(current_step),
                "draft_revision": 1,
                "last_save_request_id": str(request_id),
                "last_save_payload_hash": payload_hash,
                "source_profile_version_id": (
                    str(active["profile_version_id"]) if active else None
                ),
                "activation_request_id": None,
                "activation_payload_hash": None,
                "activation_result_profile_version_id": None,
                "created_at": now,
                "updated_at": now,
                "activated_at": None,
                "archived_at": None,
            }
            if active:
                for field in (
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
                ):
                    row[field] = copy.deepcopy(active.get(field))
            row.update(copy.deepcopy(patch))
            self.school_profile_versions[(user_id, draft_id)] = row
            snapshot = self._school_profile_draft_snapshot(row)
            self.school_profile_draft_requests[request_key] = {
                "user_id": user_id,
                "request_id": str(request_id),
                "profile_version_id": draft_id,
                "payload_hash": payload_hash,
                "response_json": copy.deepcopy(snapshot),
                "created_at": now,
                "updated_at": now,
            }
            return snapshot

    async def activate_school_profile_draft(
        self,
        *,
        user_id: str,
        profile_version_id: str,
        expected_revision: int,
        request_id: str,
        payload_hash: str,
    ) -> dict[str, Any]:
        async with self._school_lineage_lock(user_id):
            versions_before = copy.deepcopy(self.school_profile_versions)
            sessions_before = copy.deepcopy(self.school_sessions)
            reports_before = copy.deepcopy(self.school_placement_reports)
            profiles_before = copy.deepcopy(self.profiles)
            try:
                replay = next(
                    (
                        row
                        for (uid, _version_id), row in self.school_profile_versions.items()
                        if uid == user_id
                        and str(row.get("activation_request_id") or "")
                        == str(request_id)
                    ),
                    None,
                )
                if replay:
                    if replay.get("activation_payload_hash") != payload_hash:
                        raise ValueError("school_activation_request_conflict")
                    result_profile_id = (
                        replay.get("activation_result_profile_version_id")
                        or replay["profile_version_id"]
                    )
                    result = self.school_profile_versions.get(
                        (user_id, str(result_profile_id))
                    )
                    if result is None:
                        raise ValueError("school_activation_result_missing")
                    return copy.deepcopy(result)

                target = self.school_profile_versions.get(
                    (user_id, str(profile_version_id))
                )
                if target is None:
                    raise ValueError("school_profile_not_found")
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
                    candidate = self.school_profile_versions.get(
                        (user_id, str(source_profile_version_id))
                    )
                    if candidate and candidate.get("status") == "active":
                        source = candidate
                now = time.time()
                if (
                    source
                    and self._school_profile_all_values(source)
                    == self._school_profile_all_values(target)
                ):
                    target["status"] = "archived"
                    target["archived_at"] = now
                    target["activation_request_id"] = str(request_id)
                    target["activation_payload_hash"] = payload_hash
                    target["activation_result_profile_version_id"] = str(
                        source["profile_version_id"]
                    )
                    target["updated_at"] = now
                    return copy.deepcopy(source)

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

                for (uid, _version_id), row in self.school_profile_versions.items():
                    if uid == user_id and row.get("status") == "active":
                        row["status"] = "archived"
                        row["archived_at"] = now
                        row["updated_at"] = now
                target["status"] = "active"
                target["activated_at"] = now
                target["archived_at"] = None
                target.update(coach_identity)
                target["activation_request_id"] = str(request_id)
                target["activation_payload_hash"] = payload_hash
                target["activation_result_profile_version_id"] = str(
                    profile_version_id
                )
                target["updated_at"] = now
                compatible_edit = bool(
                    source
                    and self._school_profile_compatibility_values(source)
                    == self._school_profile_compatibility_values(target)
                )
                if compatible_edit:
                    for row in self.school_sessions.values():
                        if (
                            row.get("user_id") == user_id
                            and str(row.get("profile_version_id") or "")
                            == str(source["profile_version_id"])
                            and row.get("status")
                            in {"active", "paused_for_masterclass"}
                        ):
                            row["profile_version_id"] = str(profile_version_id)
                            row.setdefault("state_json", {})[
                                "profile_version_id"
                            ] = str(profile_version_id)
                            row["updated_at"] = now
                await self.expire_active_school_sessions_from_other_profiles(
                    user_id,
                    str(profile_version_id),
                )
                learner = self._profile(user_id)
                learner["name"] = str(target["display_name"])
                learner["primary_motive"] = "school"
                learner["school_profile"] = {
                    field: copy.deepcopy(target.get(field))
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
                learner["onboarding_completed_at"] = now
                learner["onboarding_state"] = {}
                return copy.deepcopy(target)
            except Exception:
                self.school_profile_versions = versions_before
                self.school_sessions = sessions_before
                self.school_placement_reports = reports_before
                self.profiles = profiles_before
                raise

    async def grant_credits(self, user_id: str, amount: int, reason: str = "grant") -> int:
        profile = self._profile(user_id)
        profile["credits"] = int(profile.get("credits") or 0) + amount
        return int(profile["credits"])

    async def get_credits(self, user_id: str) -> int:
        return int(self._profile(user_id).get("credits") or 0)

    async def set_demo_unlimited(self, user_id: str, enabled: bool) -> None:
        self._profile(user_id)["demo_unlimited"] = bool(enabled)

    async def is_demo(self, user_id: str) -> bool:
        return bool(self._profile(user_id).get("demo_unlimited"))

    async def has_unlock(self, user_id: str, scope: str, ref_id: str) -> bool:
        return (user_id, scope, ref_id) in self.unlocks

    async def remove_unlock(self, user_id: str, scope: str, ref_id: str) -> None:
        self.unlocks.discard((user_id, scope, ref_id))

    async def count_attempts(self, user_id: str, module_id: str) -> int:
        from app.content import registry

        count = 0
        for attempt in self.node_attempts.values():
            if attempt.get("user_id") != user_id:
                continue
            if attempt.get("status") not in ("active", "completed"):
                continue
            node_id = attempt.get("competency_node")
            try:
                if registry.module_of(node_id) != module_id:
                    continue
            except KeyError:
                continue
            count += 1
        return count

    async def record_node_attempt(
        self,
        session_id: str,
        user_id: str,
        node_id: str,
        starting_mastery: float = 0.0,
    ) -> None:
        self.node_attempts.setdefault(
            session_id,
            {
                "attempt_id": session_id,
                "session_id": session_id,
                "user_id": user_id,
                "competency_node": node_id,
                "status": "active",
                "started_at": time.time(),
                "starting_mastery": float(starting_mastery or 0.0),
                "ending_mastery": 0.0,
            },
        )

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        task_type: str,
        module_id: str,
        node_id: str,
        test_mode: bool = False,
        career_context: dict[str, Any] | None = None,
        scenario_config: dict[str, Any] | None = None,
        persona_roster: list[dict[str, Any]] | None = None,
        context_hash: str = "default",
    ) -> None:
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "task_type": task_type,
            "module_id": module_id,
            "competency_node": node_id,
            "test_mode": bool(test_mode),
            "career_context": dict(career_context or {}),
            "scenario_config": dict(scenario_config or {}),
            "persona_roster": list(persona_roster or []),
            "context_hash": context_hash,
            "status": "active",
        }

    async def begin_start_request(
        self,
        user_id: str,
        client_start_id: str,
        request_hash: str,
        source_session_id: str | None = None,
        source_transition_id: str | None = None,
    ) -> dict[str, Any]:
        key = (user_id, client_start_id)
        existing = self.start_requests.get(key)
        if existing:
            if self._is_stale_request(existing):
                self._mark_stale_failed(existing)
            copy = dict(existing)
            copy["accepted"] = False
            copy["request_mismatch"] = copy.get("request_hash") != request_hash
            return copy
        if source_session_id and source_transition_id:
            for (_existing_user_id, existing_client_start_id), existing_row in self.start_requests.items():
                if self._is_stale_request(existing_row):
                    self._mark_stale_failed(existing_row)
                if (
                    existing_row.get("source_session_id") == source_session_id
                    and existing_row.get("source_transition_id") == source_transition_id
                    and existing_row.get("status") in {"in_progress", "completed"}
                ):
                    return {
                        "accepted": False,
                        "status": "source_transition_consumed",
                        "consumed_status": existing_row.get("status"),
                        "accepted_client_start_id": existing_client_start_id,
                        "request_mismatch": False,
                        "session_id": existing_row.get("session_id"),
                        "response_json": existing_row.get("response_json"),
                        "error_code": existing_row.get("error_code"),
                        "source_session_id": source_session_id,
                        "source_transition_id": source_transition_id,
                    }
        now = time.time()
        row = {
            "user_id": user_id,
            "client_start_id": client_start_id,
            "request_hash": request_hash,
            "status": "in_progress",
            "session_id": None,
            "response_json": None,
            "error_code": None,
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
            "accepted": True,
            "request_mismatch": False,
            "created_at": now,
            "updated_at": now,
        }
        self.start_requests[key] = row
        return dict(row)

    async def get_start_request_for_source_transition(
        self,
        source_session_id: str,
        source_transition_id: str,
    ) -> dict[str, Any] | None:
        candidates = [
            dict(row)
            for row in self.start_requests.values()
            if row.get("source_session_id") == source_session_id
            and row.get("source_transition_id") == source_transition_id
            and row.get("status") in {"in_progress", "completed"}
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda row: row.get("updated_at", 0), reverse=True)
        return candidates[0]

    async def get_start_request(
        self,
        user_id: str,
        client_start_id: str,
    ) -> dict[str, Any] | None:
        row = self.start_requests.get((user_id, client_start_id))
        if row and self._is_stale_request(row):
            self._mark_stale_failed(row)
        return dict(row) if row else None

    async def reset_start_request(
        self,
        user_id: str,
        client_start_id: str,
        request_hash: str,
        source_session_id: str | None = None,
        source_transition_id: str | None = None,
    ) -> dict[str, Any]:
        now = time.time()
        row = {
            "user_id": user_id,
            "client_start_id": client_start_id,
            "request_hash": request_hash,
            "status": "in_progress",
            "session_id": None,
            "response_json": None,
            "error_code": None,
            "source_session_id": source_session_id,
            "source_transition_id": source_transition_id,
            "accepted": True,
            "request_mismatch": False,
            "created_at": self.start_requests.get((user_id, client_start_id), {}).get("created_at", now),
            "updated_at": now,
        }
        self.start_requests[(user_id, client_start_id)] = row
        return dict(row)

    async def complete_start_request(
        self,
        user_id: str,
        client_start_id: str,
        status: str,
        session_id: str | None = None,
        response_json: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        key = (user_id, client_start_id)
        row = self.start_requests.setdefault(
            key,
            {
                "user_id": user_id,
                "client_start_id": client_start_id,
                "request_hash": "",
            },
        )
        row["status"] = status
        row["session_id"] = session_id
        row["response_json"] = dict(response_json or {})
        row["error_code"] = error_code
        row["updated_at"] = time.time()

    async def end_session(
        self,
        session_id: str,
        final_summary: str = "",
        avg_score: float = 0.0,
    ) -> None:
        session = self.sessions.get(session_id)
        if session:
            session["status"] = "ended"
            session["summary"] = final_summary
            session["final_mastery"] = avg_score

    async def record_turn(
        self,
        session_id: str,
        user_id: str,
        node_id: str,
        score: float,
        on_task: bool = True,
        english: bool = True,
        affect: str = "neutral",
    ) -> None:
        void = (session_id, user_id, node_id, score, on_task, english, affect)
        _ = void

    async def get_turns(self, session_id: str) -> list[dict[str, Any]]:
        return []

    async def record_turn_evaluation(self, **kwargs) -> None:
        self.turn_evaluations.append(dict(kwargs))

    async def record_learning_event(self, **kwargs) -> None:
        key = kwargs.get("source_event_key")
        if key and any(row.get("source_event_key") == key for row in self.learning_events):
            return
        self.learning_events.append(dict(kwargs))

    async def upsert_session_report(self, **kwargs) -> None:
        self.session_reports[(kwargs["user_id"], kwargs["session_id"])] = dict(kwargs)

    async def upsert_learner_skill_profile(self, **kwargs) -> None:
        key = (kwargs["user_id"], kwargs["domain"], kwargs["skill_id"])
        prev = self.learner_skill_profiles.get(key, {})
        attempts = max(int(prev.get("attempts") or 0), int(kwargs.get("attempts") or 0))
        self.learner_skill_profiles[key] = {**prev, **dict(kwargs), "attempts": attempts}

    async def get_learning_graph(self, user_id: str) -> dict[str, Any]:
        return {
            "profiles": [
                row
                for (uid, _domain, _skill), row in self.learner_skill_profiles.items()
                if uid == user_id
            ],
            "reports": [
                row
                for (uid, _session_id), row in self.session_reports.items()
                if uid == user_id
            ],
            "events": [
                row
                for row in self.learning_events
                if row.get("user_id") == user_id
            ],
        }

    async def upsert_session_runtime(
        self,
        session_id: str,
        user_id: str,
        current_node: str,
        module_id: str | None,
        task_type: str | None,
        test_mode: bool,
        status: str,
        state_snapshot: dict[str, Any],
        pending_transition: dict[str, Any] | None,
        session_version: int,
        active_turn_id: str | None = None,
        active_opening_id: str | None = None,
        last_error: dict[str, Any] | None = None,
        lease_expires_at: str | None = None,
    ) -> None:
        self.session_runtime[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "current_node": current_node,
            "module_id": module_id,
            "task_type": task_type,
            "test_mode": bool(test_mode),
            "status": status,
            "state_snapshot": dict(state_snapshot or {}),
            "pending_transition": dict(pending_transition) if pending_transition else None,
            "session_version": int(session_version or 1),
            "active_turn_id": active_turn_id,
            "active_opening_id": active_opening_id,
            "last_error": dict(last_error) if last_error else None,
            "lease_expires_at": lease_expires_at,
        }

    async def get_session_runtime(self, session_id: str) -> dict[str, Any] | None:
        row = self.session_runtime.get(session_id)
        if not row:
            return None
        copy = dict(row)
        snapshot = dict(copy.get("state_snapshot") or {})
        messages = self.session_messages.get(session_id)
        if messages is not None:
            snapshot["messages"] = [dict(m) for m in messages]
        copy["state_snapshot"] = snapshot
        return copy

    async def get_active_session_runtime_for_node(
        self,
        user_id: str,
        node_id: str,
        task_type: str,
        test_mode: bool,
    ) -> dict[str, Any] | None:
        matches = [
            row
            for row in self.session_runtime.values()
            if row.get("user_id") == user_id
            and row.get("current_node") == node_id
            and row.get("task_type") == task_type
            and bool(row.get("test_mode")) == bool(test_mode)
            and row.get("status") == "active"
        ]
        if not matches:
            return None
        latest = matches[-1]
        return await self.get_session_runtime(str(latest.get("session_id") or ""))

    async def get_latest_active_session_runtime_for_module(
        self,
        user_id: str,
        module_id: str,
        test_mode: bool,
    ) -> dict[str, Any] | None:
        matches = [
            row
            for row in self.session_runtime.values()
            if row.get("user_id") == user_id
            and row.get("module_id") == module_id
            and bool(row.get("test_mode")) == bool(test_mode)
            and row.get("status") == "active"
        ]
        if not matches:
            return None
        matches.sort(key=lambda row: float(row.get("updated_at") or 0.0), reverse=True)
        return await self.get_session_runtime(str(matches[0].get("session_id") or ""))

    async def touch_session_runtime(
        self,
        session_id: str,
        status: str = "active",
        lease_expires_at: str | None = None,
    ) -> None:
        if session_id in self.session_runtime:
            self.session_runtime[session_id]["status"] = status
            self.session_runtime[session_id]["lease_expires_at"] = lease_expires_at

    async def replace_session_messages(
        self, session_id: str, messages: list[dict[str, Any]]
    ) -> None:
        self.session_messages[session_id] = [dict(message) for message in messages or []]

    async def begin_turn_request(
        self,
        session_id: str,
        client_turn_id: str,
        request_hash: str,
        expected_version: int | None,
    ) -> dict[str, Any]:
        key = (session_id, client_turn_id)
        for (existing_session_id, _existing_turn_id), existing_row in self.turn_requests.items():
            if existing_session_id == session_id and self._is_stale_request(existing_row):
                self._mark_stale_failed(existing_row)
        existing = self.turn_requests.get(key)
        if existing:
            request_mismatch = existing.get("request_hash") != request_hash
            if existing.get("status") == "failed" and not request_mismatch:
                if expected_version is not None:
                    for (existing_session_id, existing_turn_id), existing_row in self.turn_requests.items():
                        if (
                            existing_session_id == session_id
                            and existing_turn_id != client_turn_id
                            and existing_row.get("expected_version") == expected_version
                            and existing_row.get("status") in {"in_progress", "completed"}
                        ):
                            return {
                                "accepted": False,
                                "status": "version_consumed",
                                "accepted_client_turn_id": existing_turn_id,
                                "accepted_status": existing_row.get("status"),
                                "accepted_age_seconds": max(
                                    0.0,
                                    time.time() - float(existing_row.get("updated_at") or time.time()),
                                ),
                                "transcript_delta": list(existing_row.get("transcript_delta") or []),
                                "done_snapshot": existing_row.get("done_snapshot"),
                                "error_code": existing_row.get("error_code"),
                                "request_mismatch": False,
                            }
                existing["status"] = "in_progress"
                existing["transcript_delta"] = []
                existing["done_snapshot"] = None
                existing["error_code"] = None
                existing["updated_at"] = time.time()
                copy = dict(existing)
                copy["accepted"] = True
                copy["request_mismatch"] = False
                return copy
            copy = dict(existing)
            copy["accepted"] = False
            copy["request_mismatch"] = request_mismatch
            return copy
        if expected_version is not None:
            for (existing_session_id, existing_turn_id), existing_row in self.turn_requests.items():
                if (
                    existing_session_id == session_id
                    and existing_turn_id != client_turn_id
                    and existing_row.get("expected_version") == expected_version
                    and existing_row.get("status") in {"in_progress", "completed"}
                ):
                    return {
                        "accepted": False,
                        "status": "version_consumed",
                        "accepted_client_turn_id": existing_turn_id,
                        "accepted_status": existing_row.get("status"),
                        "accepted_age_seconds": max(
                            0.0,
                            time.time() - float(existing_row.get("updated_at") or time.time()),
                        ),
                        "transcript_delta": list(existing_row.get("transcript_delta") or []),
                        "done_snapshot": existing_row.get("done_snapshot"),
                        "error_code": existing_row.get("error_code"),
                        "request_mismatch": False,
                    }
        now = time.time()
        row = {
            "session_id": session_id,
            "client_turn_id": client_turn_id,
            "request_hash": request_hash,
            "expected_version": expected_version,
            "status": "in_progress",
            "transcript_delta": [],
            "done_snapshot": None,
            "error_code": None,
            "accepted": True,
            "created_at": now,
            "updated_at": now,
        }
        self.turn_requests[key] = row
        return dict(row)

    async def complete_turn_request(
        self,
        session_id: str,
        client_turn_id: str,
        status: str,
        transcript_delta: list[dict[str, Any]] | None = None,
        done_snapshot: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        key = (session_id, client_turn_id)
        row = self.turn_requests.setdefault(
            key,
            {
                "session_id": session_id,
                "client_turn_id": client_turn_id,
                "request_hash": "",
                "expected_version": None,
            },
        )
        row["status"] = status
        row["transcript_delta"] = list(transcript_delta or [])
        row["done_snapshot"] = done_snapshot
        row["error_code"] = error_code
        row["updated_at"] = time.time()

    async def begin_opening_request(
        self,
        session_id: str,
        transition_id: str,
    ) -> dict[str, Any]:
        key = (session_id, transition_id)
        existing = self.opening_requests.get(key)
        if existing:
            if self._is_stale_request(existing):
                existing["status"] = "failed"
                existing["last_error"] = "stale_in_progress"
                existing["updated_at"] = time.time()
            if existing.get("status") == "failed":
                existing["status"] = "in_progress"
                existing["attempts"] = int(existing.get("attempts") or 0) + 1
                existing["last_error"] = None
                existing["updated_at"] = time.time()
                copy = dict(existing)
                copy["accepted"] = True
                return copy
            copy = dict(existing)
            copy["accepted"] = False
            return copy
        now = time.time()
        row = {
            "session_id": session_id,
            "transition_id": transition_id,
            "status": "in_progress",
            "message_id": None,
            "attempts": 1,
            "last_error": None,
            "accepted": True,
            "created_at": now,
            "updated_at": now,
        }
        self.opening_requests[key] = row
        return dict(row)

    async def complete_opening_request(
        self,
        session_id: str,
        transition_id: str,
        status: str,
        message_id: str | None = None,
        last_error: str | None = None,
    ) -> None:
        key = (session_id, transition_id)
        row = self.opening_requests.setdefault(
            key,
            {
                "session_id": session_id,
                "transition_id": transition_id,
                "attempts": 0,
            },
        )
        row["status"] = status
        row["message_id"] = message_id or row.get("message_id")
        row["last_error"] = last_error
        row["updated_at"] = time.time()

    async def begin_end_request(self, session_id: str) -> dict[str, Any]:
        existing = self.end_requests.get(session_id)
        if existing:
            if self._is_stale_request(existing):
                existing["status"] = "failed"
                existing["error_code"] = "stale_in_progress"
                existing["updated_at"] = time.time()
            if existing.get("status") == "failed":
                existing["status"] = "in_progress"
                existing["response_json"] = None
                existing["error_code"] = None
                existing["attempts"] = int(existing.get("attempts") or 0) + 1
                existing["updated_at"] = time.time()
                copy = dict(existing)
                copy["accepted"] = True
                return copy
            copy = dict(existing)
            copy["accepted"] = False
            return copy
        now = time.time()
        row = {
            "session_id": session_id,
            "status": "in_progress",
            "response_json": None,
            "error_code": None,
            "attempts": 1,
            "accepted": True,
            "created_at": now,
            "updated_at": now,
        }
        self.end_requests[session_id] = row
        return dict(row)

    async def complete_end_request(
        self,
        session_id: str,
        status: str,
        response_json: dict[str, Any] | None = None,
        error_code: str | None = None,
    ) -> None:
        row = self.end_requests.setdefault(
            session_id,
            {
                "session_id": session_id,
                "attempts": 0,
                "created_at": time.time(),
            },
        )
        row["status"] = status
        row["response_json"] = response_json
        row["error_code"] = error_code
        row["updated_at"] = time.time()

    async def get_end_request(self, session_id: str) -> dict[str, Any] | None:
        row = self.end_requests.get(session_id)
        return dict(row) if row else None

    async def load_context(self, user_id: str, task_type: str, k: int = 3) -> list[dict[str, Any]]:
        return []

    async def write_memory(
        self,
        user_id: str,
        session_id: str,
        node_id: str,
        raw: str,
        task_type: str,
        score: float = 0.0,
    ) -> None:
        void = (user_id, session_id, node_id, raw, task_type, score)
        _ = void

    async def get_school_review_skills(
        self,
        user_id: str,
        mastered_threshold: float = 0.8,
        stale_seconds: float = 5 * 24 * 60 * 60,
        limit: int = 3,
    ) -> list[str]:
        return []

    async def deduct_credits(self, user_id: str, amount: int, reason: str) -> bool:
        profile = self._profile(user_id)
        credits = int(profile.get("credits") or 0)
        if credits < amount:
            return False
        profile["credits"] = credits - amount
        return True

    async def charge_and_unlock(
        self, user_id: str, amount: int, reason: str, scope: str, ref_id: str
    ) -> bool:
        if not await self.deduct_credits(user_id, amount, reason):
            return False
        self.unlocks.add((user_id, scope, ref_id))
        return True

    async def get_progression(self, user_id: str) -> list[dict[str, Any]]:
        rows = [
            dict(row)
            for (uid, _node_id), row in self.mastery.items()
            if uid == user_id
        ]
        rows.sort(key=lambda row: row["node_id"])
        return rows

    async def upsert_mastery(
        self,
        user_id: str,
        node_id: str,
        ema: float,
        attempts: int,
        clean_pass: bool = False,
        node_completed: bool = False,
        session_id: str | None = None,
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
        key = (user_id, node_id)
        prev = self.mastery.get(key, {})
        completed = bool(prev.get("node_completed")) or bool(node_completed)
        mastered = bool(node_mastered) if node_mastered is not None else False
        mastered = bool(prev.get("node_mastered")) or mastered
        clean = bool(prev.get("clean_pass")) or (bool(clean_pass) and bool(node_completed))
        best = max(float(prev.get("best_ema") or 0.0), float(ema))
        best_independent = max(
            float(prev.get("best_independent_score") or 0.0),
            float(best_independent_score or 0.0),
        )
        completion_count = int(prev.get("completion_count") or 0)
        completed_at = prev.get("completed_at")
        if node_completed and not prev.get("node_completed"):
            completion_count += 1
            completed_at = time.time()
        self.mastery[key] = {
            "user_id": user_id,
            "node_id": node_id,
            "competency_node": node_id,
            "ema": float(ema),
            "mastery": float(ema),
            "best_ema": best,
            "attempts": int(attempts),
            "clean_pass": clean,
            "node_completed": completed,
            "node_mastered": mastered,
            "display_status": display_status or ("mastered" if mastered else "ready_to_advance" if completed else "active"),
            "best_independent_score": best_independent,
            "independent_passes": max(int(prev.get("independent_passes") or 0), int(independent_passes or 0)),
            "transfer_passes": max(int(prev.get("transfer_passes") or 0), int(transfer_passes or 0)),
            "pressure_passes": max(int(prev.get("pressure_passes") or 0), int(pressure_passes or 0)),
            "scaffold_successes": max(int(prev.get("scaffold_successes") or 0), int(scaffold_successes or 0)),
            "last_gap": last_gap or prev.get("last_gap", ""),
            "mastery_evidence": list(mastery_evidence or prev.get("mastery_evidence") or []),
            "completed_at": completed_at,
            "completion_count": completion_count,
            "last_completed_session_id": session_id or prev.get("last_completed_session_id"),
        }

    async def record_assessment_result(
        self,
        user_id: str,
        test_id: str,
        class_no: int,
        kind: str,
        score: float,
        passed: bool,
        by_skill: list[dict[str, Any]],
    ) -> None:
        existing = self.school_results.get((user_id, test_id))
        if existing and existing.get("score") == score and existing.get("passed") == passed and existing.get("by_skill") == by_skill:
            self.school_results[(user_id, test_id)] = {
                **existing,
                "class_no": class_no,
                "kind": kind,
                "score": score,
                "passed": passed,
                "by_skill": by_skill,
            }
            return
        weak_skills: list[str] = []
        for item in by_skill:
            skill = str(item.get("skill") or "")
            total = int(item.get("total") or 0)
            correct = int(item.get("correct") or 0)
            ratio = correct / total if total else 0.0
            if ratio < 0.6:
                weak_skills.append(skill)
            prev = self.school_mastery.get((user_id, skill))
            attempts = int(prev.get("attempts") or 0) + 1 if prev else 1
            ema = ratio if not prev else float(prev.get("ema") or 0.0) + (ratio - float(prev.get("ema") or 0.0)) * 0.35
            self.school_mastery[(user_id, skill)] = {
                "skill": skill,
                "ema": ema,
                "attempts": attempts,
                "last_seen": time.time(),
            }
        self.school_results[(user_id, test_id)] = {
            "user_id": user_id,
            "test_id": test_id,
            "class_no": class_no,
            "kind": kind,
            "score": score,
            "passed": passed,
            "by_skill": by_skill,
            "weak_skills": weak_skills,
        }

    async def get_school_results(
        self, user_id: str, class_no: int | None = None
    ) -> list[dict[str, Any]]:
        rows = [
            dict(row)
            for (uid, _test_id), row in self.school_results.items()
            if uid == user_id and (class_no is None or row.get("class_no") == class_no)
        ]
        rows.sort(key=lambda row: row["test_id"])
        return rows

    async def get_school_skill_mastery(self, user_id: str) -> list[dict[str, Any]]:
        return [
            dict(row)
            for (uid, _skill), row in self.school_mastery.items()
            if uid == user_id
        ]

    async def get_school_weak_skills(self, user_id: str) -> list[str]:
        rows = await self.get_school_skill_mastery(user_id)
        return [row["skill"] for row in rows if float(row.get("ema") or 0.0) < 0.6]

    async def upsert_school_session(self, **kwargs) -> None:
        lineage_lock_held = bool(kwargs.pop("_school_lineage_lock_held", False))
        row = dict(kwargs)
        user_id = str(row["user_id"])
        if row.get("api_version") == "rebuild" and not lineage_lock_held:
            async with self._school_lineage_lock(user_id):
                self._upsert_school_session(row)
            return
        self._upsert_school_session(row)

    async def get_or_create_school_session(self, **kwargs) -> dict[str, Any]:
        row = dict(kwargs)
        user_id = str(row["user_id"])
        async with self._school_lineage_lock(user_id):
            winner = await self.get_active_school_session(
                user_id,
                str(row["api_version"]),
                str(row["flow_type"]),
                str(row["subject_id"]),
                int(row["class_no"]),
                profile_version_id=row.get("profile_version_id"),
                source_placement_report_id=row.get("source_placement_report_id"),
            )
            if winner:
                return winner
            self._upsert_school_session(row)
            return copy.deepcopy(
                self.school_sessions[(user_id, str(row["session_id"]))]
            )

    async def get_or_create_active_school_placement_session(
        self,
        **kwargs,
    ) -> dict[str, Any]:
        row = {
            **dict(kwargs),
            "api_version": "rebuild",
            "flow_type": "placement",
            "status": "active",
            "source_placement_report_id": None,
        }
        user_id = str(row["user_id"])
        profile_version_id = str(row["profile_version_id"])
        async with self._school_lineage_lock(user_id):
            active = await self.get_active_school_profile_version(user_id)
            if (
                not active
                or str(active["profile_version_id"]) != profile_version_id
            ):
                raise ValueError("stale_school_profile_lineage")
            winner = await self.get_active_school_session(
                user_id,
                "rebuild",
                "placement",
                str(row["subject_id"]),
                int(row["class_no"]),
                profile_version_id=profile_version_id,
            )
            if winner:
                return winner
            self._upsert_school_session(row)
            return copy.deepcopy(
                self.school_sessions[(user_id, str(row["session_id"]))]
            )

    def _upsert_school_session(self, row: dict[str, Any]) -> None:
        session_id = str(row["session_id"])
        user_id = str(row["user_id"])
        status = str(row.get("status") or "active")
        active_statuses = {"active", "paused_for_masterclass"}
        terminal_statuses = {
            "complete",
            "insufficient_evidence",
            "abandoned",
            "expired",
        }
        if row.get("api_version") != "rebuild" and status in active_statuses:
            raise ValueError("archived_school_api_version")
        previous = self.school_sessions.get((user_id, session_id), {})
        for lineage_key in ("profile_version_id", "source_placement_report_id"):
            if row.get(lineage_key) is None and previous.get(lineage_key) is not None:
                row[lineage_key] = previous[lineage_key]
            elif (
                row.get("api_version") == "rebuild"
                and row.get(lineage_key) is not None
                and previous.get(lineage_key) is not None
                and str(row[lineage_key]) != str(previous[lineage_key])
            ):
                raise ValueError("school_session_lineage_conflict")
        same_terminal_replay = bool(
            previous
            and status in terminal_statuses
            and previous.get("status") == status
        )
        requires_active_profile = False
        if row.get("api_version") == "rebuild" and status in active_statuses:
            if previous and previous.get("status") not in active_statuses:
                raise ValueError("stale_school_session_transition")
            requires_active_profile = True
        elif row.get("api_version") == "rebuild" and status in terminal_statuses:
            if not previous:
                raise ValueError("school_session_transition_requires_active")
            if not same_terminal_replay:
                if previous.get("status") not in active_statuses:
                    raise ValueError("stale_school_session_transition")
                requires_active_profile = True
        if (
            row.get("api_version") == "rebuild"
            and requires_active_profile
            and not row.get("profile_version_id")
        ):
            raise ValueError("active_school_session_profile_lineage_required")
        if row.get("api_version") == "rebuild" and requires_active_profile:
            profile = self.school_profile_versions.get(
                (user_id, str(row["profile_version_id"]))
            )
            if not profile or profile.get("status") != "active":
                raise ValueError("stale_school_profile_lineage")
        if row.get("api_version") == "rebuild" and row.get("profile_version_id"):
            profile_version_id = str(row["profile_version_id"])
            state_json = dict(row.get("state_json") or {})
            embedded_profile_version_id = state_json.get("profile_version_id")
            if (
                embedded_profile_version_id not in (None, "")
                and str(embedded_profile_version_id) != profile_version_id
            ):
                raise ValueError("school_session_lineage_conflict")
        if status in active_statuses:
            for (uid, sid), existing in self.school_sessions.items():
                if uid != user_id or sid == session_id:
                    continue
                if existing.get("status") not in active_statuses:
                    continue
                if (
                    existing.get("flow_type") == row.get("flow_type")
                    and existing.get("subject_id") == row.get("subject_id")
                    and int(existing.get("class_no") or 0) == int(row.get("class_no") or 0)
                ):
                    raise ValueError("duplicate_active_school_session")
        linked_session_id = row.get("linked_session_id")
        if linked_session_id:
            linked_key = (user_id, str(linked_session_id))
            if linked_key not in self.school_sessions:
                raise ValueError("linked_school_session_not_found")
        now = time.time()
        merged = {
            **previous,
            **row,
            "session_id": session_id,
            "user_id": user_id,
            "status": status,
            "state_json": dict(row.get("state_json") or previous.get("state_json") or {}),
            "updated_at": now,
        }
        merged.setdefault("started_at", previous.get("started_at", now))
        if status in {"complete", "abandoned", "expired", "insufficient_evidence"}:
            merged.setdefault("completed_at", now)
        self.school_sessions[(user_id, session_id)] = merged

    async def persist_school_curriculum_attempt(
        self,
        *,
        learning_event: dict,
        school_session: dict,
        expected_state_json: dict,
        request_activity_id: str | None = None,
        request_answer_hash: str | None = None,
        request_claim_token: str | None = None,
        response_json: dict | None = None,
    ) -> None:
        await self.persist_school_answer_attempt(
            learning_event=learning_event,
            school_session=school_session,
            expected_state_json=expected_state_json,
            request_activity_id=request_activity_id,
            request_answer_hash=request_answer_hash,
            request_claim_token=request_claim_token,
            response_json=response_json,
        )

    async def compare_and_set_school_session(
        self,
        *,
        school_session: dict,
        expected_state_json: dict,
    ) -> bool:
        user_id = str(school_session["user_id"])
        session_id = str(school_session["session_id"])
        async with self._school_lineage_lock(user_id):
            async with self._school_curriculum_attempt_lock:
                current = self.school_sessions.get((user_id, session_id))
                if current is None or current.get("state_json") != expected_state_json:
                    return False
                self._upsert_school_session(dict(school_session))
                return True

    async def persist_school_answer_attempt(
        self,
        *,
        learning_event: dict,
        school_session: dict,
        expected_state_json: dict,
        request_activity_id: str | None = None,
        request_answer_hash: str | None = None,
        request_claim_token: str | None = None,
        response_json: dict | None = None,
        placement_report: dict | None = None,
    ) -> None:
        kwargs = {
            "learning_event": learning_event,
            "school_session": school_session,
            "expected_state_json": expected_state_json,
            "request_activity_id": request_activity_id,
            "request_answer_hash": request_answer_hash,
            "request_claim_token": request_claim_token,
            "response_json": response_json,
            "placement_report": placement_report,
        }
        if school_session.get("api_version") == "rebuild":
            async with self._school_lineage_lock(str(school_session["user_id"])):
                await self._persist_school_answer_attempt(**kwargs)
            return
        await self._persist_school_answer_attempt(**kwargs)

    async def _persist_school_answer_attempt(
        self,
        *,
        learning_event: dict,
        school_session: dict,
        expected_state_json: dict,
        request_activity_id: str | None = None,
        request_answer_hash: str | None = None,
        request_claim_token: str | None = None,
        response_json: dict | None = None,
        placement_report: dict | None = None,
    ) -> None:
        async with self._school_curriculum_attempt_lock:
            key = (str(school_session["user_id"]), str(school_session["session_id"]))
            current = self.school_sessions.get(key)
            if current is None or current.get("state_json") != expected_state_json:
                raise ValueError("stale_school_answer_session")
            previous_session = copy.deepcopy(current)
            request_key = (str(school_session["session_id"]), str(request_activity_id))
            previous_request = copy.deepcopy(self.school_answer_requests.get(request_key))
            report_key = None
            previous_report = None
            if placement_report is not None:
                report_key = (
                    str(placement_report["user_id"]),
                    str(placement_report["placement_session_id"]),
                )
                previous_report = copy.deepcopy(
                    self.school_placement_reports.get(report_key)
                )
            event_key = learning_event.get("source_event_key")
            event_already_existed = bool(
                event_key
                and any(row.get("source_event_key") == event_key for row in self.learning_events)
            )
            try:
                await self.record_learning_event(**learning_event)
                await self.upsert_school_session(
                    _school_lineage_lock_held=True,
                    **school_session,
                )
                if placement_report is not None:
                    await self.upsert_school_placement_report(**placement_report)
                if request_activity_id is not None:
                    request_row = self.school_answer_requests.get(request_key)
                    if (
                        request_answer_hash is None
                        or request_claim_token is None
                        or response_json is None
                        or request_row is None
                        or request_row.get("user_id") != school_session["user_id"]
                        or request_row.get("answer_hash") != request_answer_hash
                        or request_row.get("claim_token") != request_claim_token
                        or request_row.get("status") != "processing"
                    ):
                        raise ValueError("stale_school_answer_request")
                    request_row.update(
                        status="completed",
                        response_json=copy.deepcopy(response_json),
                        updated_at=time.time(),
                    )
            except Exception:
                self.school_sessions[key] = previous_session
                if request_activity_id is not None:
                    if previous_request is None:
                        self.school_answer_requests.pop(request_key, None)
                    else:
                        self.school_answer_requests[request_key] = previous_request
                if report_key is not None:
                    if previous_report is None:
                        self.school_placement_reports.pop(report_key, None)
                    else:
                        self.school_placement_reports[report_key] = previous_report
                if event_key and not event_already_existed:
                    self.learning_events = [
                        row
                        for row in self.learning_events
                        if row.get("source_event_key") != event_key
                    ]
                raise

    async def get_school_answer_request(
        self, user_id: str, session_id: str, activity_id: str
    ) -> dict[str, Any] | None:
        row = self.school_answer_requests.get((str(session_id), str(activity_id)))
        if not row or row.get("user_id") != user_id:
            return None
        result = copy.deepcopy(row)
        result["stale"] = bool(
            result.get("status") == "processing"
            and time.time() - float(result.get("updated_at") or 0.0)
            >= self.SCHOOL_ANSWER_REQUEST_STALE_SECONDS
        )
        return result

    async def claim_school_answer_request(
        self, user_id: str, session_id: str, activity_id: str, answer_hash: str
    ) -> dict[str, Any]:
        async with self._school_curriculum_attempt_lock:
            key = (str(session_id), str(activity_id))
            existing = self.school_answer_requests.get(key)
            now = time.time()
            claim_token = str(uuid4())
            if existing:
                status = str(existing.get("status") or "")
                if existing.get("user_id") != user_id:
                    return {"outcome": "conflict"}
                if status != "failed" and existing.get("answer_hash") != answer_hash:
                    return {"outcome": "conflict"}
                if status == "completed":
                    return {
                        "outcome": "completed",
                        "response_json": copy.deepcopy(existing.get("response_json")),
                    }
                stale = (
                    status == "processing"
                    and now - float(existing.get("updated_at") or 0.0)
                    >= self.SCHOOL_ANSWER_REQUEST_STALE_SECONDS
                )
                if status == "processing" and not stale:
                    return {"outcome": "in_progress"}
                existing.update(
                    answer_hash=answer_hash,
                    status="processing",
                    response_json=None,
                    claim_token=claim_token,
                    updated_at=now,
                )
                return {"outcome": "claimed", "claim_token": claim_token}
            if (user_id, str(session_id)) not in self.school_sessions:
                raise ValueError("school_session_not_found")
            self.school_answer_requests[key] = {
                "session_id": str(session_id),
                "activity_id": str(activity_id),
                "user_id": user_id,
                "answer_hash": answer_hash,
                "claim_token": claim_token,
                "status": "processing",
                "response_json": None,
                "created_at": now,
                "updated_at": now,
            }
            return {"outcome": "claimed", "claim_token": claim_token}

    async def fail_school_answer_request(
        self,
        user_id: str,
        session_id: str,
        activity_id: str,
        answer_hash: str,
        claim_token: str,
    ) -> None:
        async with self._school_curriculum_attempt_lock:
            row = self.school_answer_requests.get((str(session_id), str(activity_id)))
            if (
                row
                and row.get("user_id") == user_id
                and row.get("answer_hash") == answer_hash
                and row.get("claim_token") == claim_token
                and row.get("status") == "processing"
            ):
                row.update(status="failed", response_json=None, updated_at=time.time())

    async def renew_school_answer_request(
        self,
        user_id: str,
        session_id: str,
        activity_id: str,
        answer_hash: str,
        claim_token: str,
    ) -> bool:
        async with self._school_curriculum_attempt_lock:
            row = self.school_answer_requests.get((str(session_id), str(activity_id)))
            if not (
                row
                and row.get("user_id") == user_id
                and row.get("answer_hash") == answer_hash
                and row.get("claim_token") == claim_token
                and row.get("status") == "processing"
            ):
                return False
            row["updated_at"] = time.time()
            return True

    async def get_school_session(
        self,
        user_id: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        row = self.school_sessions.get((user_id, str(session_id)))
        return dict(row) if row else None

    async def get_active_school_session(
        self,
        user_id: str,
        api_version: str,
        flow_type: str,
        subject_id: str,
        class_no: int,
        *,
        profile_version_id: str | None = None,
        source_placement_report_id: str | None = None,
    ) -> dict[str, Any] | None:
        for (uid, _session_id), row in self.school_sessions.items():
            if (
                uid == user_id
                and row.get("api_version") == api_version
                and row.get("flow_type") == flow_type
                and row.get("subject_id") == subject_id
                and int(row.get("class_no") or 0) == int(class_no)
                and (
                    profile_version_id is None
                    or str(row.get("profile_version_id") or "")
                    == str(profile_version_id)
                )
                and (
                    source_placement_report_id is None
                    or str(row.get("source_placement_report_id") or "")
                    == str(source_placement_report_id)
                )
                and row.get("status") in {"active", "paused_for_masterclass"}
            ):
                return dict(row)
        return None

    async def get_latest_school_session(
        self,
        user_id: str,
        api_version: str,
        flow_type: str,
        subject_id: str,
        class_no: int,
        *,
        profile_version_id: str | None = None,
        source_placement_report_id: str | None = None,
    ) -> dict[str, Any] | None:
        rows = [
            dict(row)
            for (uid, _session_id), row in self.school_sessions.items()
            if (
                uid == user_id
                and row.get("api_version") == api_version
                and row.get("flow_type") == flow_type
                and row.get("subject_id") == subject_id
                and int(row.get("class_no") or 0) == int(class_no)
                and (
                    profile_version_id is None
                    or str(row.get("profile_version_id") or "")
                    == str(profile_version_id)
                )
                and (
                    source_placement_report_id is None
                    or str(row.get("source_placement_report_id") or "")
                    == str(source_placement_report_id)
                )
            )
        ]
        rows.sort(key=lambda row: float(row.get("updated_at") or 0.0), reverse=True)
        return rows[0] if rows else None

    async def get_school_sessions_linked_to(
        self,
        user_id: str,
        linked_session_id: str,
    ) -> list[dict[str, Any]]:
        rows = [
            dict(row)
            for (uid, _session_id), row in self.school_sessions.items()
            if uid == user_id and str(row.get("linked_session_id") or "") == str(linked_session_id)
        ]
        rows.sort(key=lambda row: float(row.get("updated_at") or 0.0), reverse=True)
        return rows

    async def expire_active_school_sessions_from_other_profiles(
        self,
        user_id: str,
        current_profile_version_id: str,
    ) -> int:
        expired = 0
        now = time.time()
        for (uid, _session_id), row in self.school_sessions.items():
            if uid != user_id:
                continue
            if row.get("status") not in {"active", "paused_for_masterclass"}:
                continue
            if str(row.get("profile_version_id") or "") == str(current_profile_version_id):
                continue
            row.update(status="expired", updated_at=now)
            row.setdefault("completed_at", now)
            expired += 1
        return expired

    async def upsert_school_placement_report(self, **kwargs) -> dict[str, Any]:
        user_id = str(kwargs["user_id"])
        placement_session_id = str(kwargs["placement_session_id"])
        key = (user_id, placement_session_id)
        now = time.time()
        previous = self.school_placement_reports.get(key, {})
        row = {
            **previous,
            **dict(kwargs),
            "user_id": user_id,
            "placement_session_id": placement_session_id,
            "updated_at": now,
        }
        row.setdefault("created_at", previous.get("created_at", now))
        self.school_placement_reports[key] = row
        return dict(row)

    async def get_school_placement_report(
        self,
        user_id: str,
        placement_session_id: str,
        *,
        profile_version_id: str | None = None,
    ) -> dict[str, Any] | None:
        row = self.school_placement_reports.get((str(user_id), str(placement_session_id)))
        if not row:
            return None
        if (
            profile_version_id is not None
            and str(row.get("profile_version_id") or "") != str(profile_version_id)
        ):
            return None
        return dict(row)

    async def get_school_placement_report_by_id(
        self,
        user_id: str,
        report_id: str,
    ) -> dict[str, Any] | None:
        for (report_user_id, _session_id), row in self.school_placement_reports.items():
            if report_user_id == str(user_id) and str(row.get("report_id")) == str(
                report_id
            ):
                return dict(row)
        return None

    async def get_latest_compatible_school_placement_report(
        self,
        user_id: str,
        profile_version_id: str,
        subject_id: str,
        target_class_no: int,
    ) -> dict[str, Any] | None:
        current = self.school_profile_versions.get((user_id, str(profile_version_id)))
        if not current or current.get("status") != "active":
            return None
        compatible_profile_ids: list[str] = []
        visited: set[str] = set()
        while current:
            current_id = str(current["profile_version_id"])
            if current_id in visited:
                break
            visited.add(current_id)
            compatible_profile_ids.append(current_id)
            source_id = str(current.get("source_profile_version_id") or "")
            if not source_id:
                break
            source = self.school_profile_versions.get((user_id, source_id))
            if not source or self._school_profile_compatibility_values(
                current
            ) != self._school_profile_compatibility_values(source):
                break
            current = source

        reports = [
            row
            for (report_user_id, _session_id), row in self.school_placement_reports.items()
            if report_user_id == user_id
            and row.get("subject_id") == subject_id
            and int(row.get("target_class_no") or 0) == int(target_class_no)
        ]
        reports.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        for compatible_profile_id in compatible_profile_ids:
            report = next(
                (
                    row
                    for row in reports
                    if str(row.get("profile_version_id") or "")
                    == compatible_profile_id
                ),
                None,
            )
            if report:
                return dict(report)
        return None

    async def upsert_school_language_confidence(self, **kwargs) -> None:
        user_id = str(kwargs["user_id"])
        self.school_language_confidence[user_id] = {
            "user_id": user_id,
            "en_production_confidence": max(
                0.0,
                min(1.0, float(kwargs.get("en_production_confidence") or 0.0)),
            ),
            "total_signals": max(0, int(kwargs.get("total_signals") or 0)),
            "updated_at": time.time(),
        }

    async def get_school_language_confidence(self, user_id: str) -> dict[str, Any] | None:
        row = self.school_language_confidence.get(user_id)
        return dict(row) if row else None

    async def upsert_school_v2_placement_session(self, **kwargs) -> None:
        key = (kwargs["user_id"], kwargs["placement_session_id"])
        previous = self.school_v2_placement_sessions.get(key, {})
        self.school_v2_placement_sessions[key] = {**previous, **dict(kwargs)}

    async def get_school_v2_placement_session(
        self,
        user_id: str,
        placement_session_id: str,
    ) -> dict[str, Any] | None:
        row = self.school_v2_placement_sessions.get((user_id, placement_session_id))
        return dict(row) if row else None

    async def get_active_school_v2_placement_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
    ) -> dict[str, Any] | None:
        for (uid, _session_id), row in self.school_v2_placement_sessions.items():
            if (
                uid == user_id
                and row.get("subject_id") == subject_id
                and int(row.get("target_class_no") or 0) == int(target_class_no)
                and row.get("status") == "in_progress"
            ):
                return dict(row)
        return None

    async def upsert_school_v2_practice_session(self, **kwargs) -> None:
        key = (kwargs["user_id"], kwargs["practice_session_id"])
        previous = self.school_v2_practice_sessions.get(key, {})
        self.school_v2_practice_sessions[key] = {**previous, **dict(kwargs)}

    async def get_school_v2_practice_session(
        self,
        user_id: str,
        practice_session_id: str,
    ) -> dict[str, Any] | None:
        row = self.school_v2_practice_sessions.get((user_id, practice_session_id))
        return dict(row) if row else None

    async def get_active_school_v2_practice_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
        skill_id: str,
    ) -> dict[str, Any] | None:
        for (uid, _session_id), row in self.school_v2_practice_sessions.items():
            if (
                uid == user_id
                and row.get("subject_id") == subject_id
                and int(row.get("target_class_no") or 0) == int(target_class_no)
                and row.get("skill_id") == skill_id
                and row.get("status") == "in_progress"
            ):
                return dict(row)
        return None

    async def upsert_school_v2_curriculum_session(self, **kwargs) -> None:
        key = (kwargs["user_id"], kwargs["curriculum_session_id"])
        previous = self.school_v2_curriculum_sessions.get(key, {})
        self.school_v2_curriculum_sessions[key] = {**previous, **dict(kwargs)}

    async def get_school_v2_curriculum_session(
        self,
        user_id: str,
        curriculum_session_id: str,
    ) -> dict[str, Any] | None:
        row = self.school_v2_curriculum_sessions.get((user_id, curriculum_session_id))
        return dict(row) if row else None

    async def get_active_school_v2_curriculum_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
        chapter_id: str,
    ) -> dict[str, Any] | None:
        for (uid, _session_id), row in self.school_v2_curriculum_sessions.items():
            if (
                uid == user_id
                and row.get("subject_id") == subject_id
                and int(row.get("target_class_no") or 0) == int(target_class_no)
                and row.get("chapter_id") == chapter_id
                and row.get("status") == "in_progress"
            ):
                return dict(row)
        return None

    async def get_weaknesses(self, user_id: str, task_type: str | None = None) -> list[dict[str, Any]]:
        return []

    async def get_activity_snapshot(self, user_id: str) -> dict[str, Any]:
        self.activity_snapshot_calls += 1
        return {
            "school_results": await self.get_school_results(user_id),
            "school_skill_mastery": await self.get_school_skill_mastery(user_id),
            "school_weak_skills": await self.get_school_weak_skills(user_id),
            "progression": await self.get_progression(user_id),
            "weaknesses": await self.get_weaknesses(user_id),
        }


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture(autouse=True)
def hardening_test_env(monkeypatch, store: InMemoryStore):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("AI_BACKEND", "local")
    monkeypatch.setenv("ZIDD_ALLOW_TEST_AUTH", "1")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com")

    from app.config import get_jwt_secret, get_settings
    from app.middleware.rate_limit import auth_ip_counts, turn_counts
    from app.services import session_service as svc
    from app.storage import reset_storage

    get_settings.cache_clear()
    get_jwt_secret.cache_clear()
    reset_storage()

    def _fake_get_storage() -> InMemoryStore:
        return store

    for module_name in (
        "app.api.auth",
        "app.api.routes",
        "app.api.health",
        "app.api.school_routes",
        "app.api.school_rebuild_routes",
        "app.api.onboarding_routes",
        "app.api.me_routes",
        "app.api.billing_routes",
        "app.services.session_service",
    ):
        module = importlib.import_module(module_name)
        if hasattr(module, "get_storage"):
            monkeypatch.setattr(module, "get_storage", _fake_get_storage)

    svc.SessionStore.clear()
    auth_ip_counts.clear()
    turn_counts.clear()
    yield
    svc.SessionStore.clear()
    auth_ip_counts.clear()
    turn_counts.clear()
    reset_storage()
    get_settings.cache_clear()
    get_jwt_secret.cache_clear()
