"""Hardening-test fixtures.

Tests must not create a local product database. Endpoint tests patch the route
modules to use this process-local fake store; runtime code still resolves only
to PgStore/Supabase.
"""
from __future__ import annotations

import importlib
import os
import time
from typing import Any

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

    def __init__(self) -> None:
        self.profiles: dict[str, dict[str, Any]] = {}
        self.mastery: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_results: dict[tuple[str, str], dict[str, Any]] = {}
        self.school_mastery: dict[tuple[str, str], dict[str, Any]] = {}
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
        self.unlocks: set[tuple[str, str, str]] = set()
        self.idempotent_charges: dict[tuple[str, str], dict[str, Any]] = {}
        self.credit_transactions: list[dict[str, Any]] = []
        self.google_login_resolutions = 0
        self.activity_snapshot_calls = 0

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
            "claim_generation": 1,
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
        if source_session_id and source_transition_id:
            for (_uid, existing_client_start_id), candidate in self.start_requests.items():
                if self._is_stale_request(candidate):
                    self._mark_stale_failed(candidate)
                if (
                    existing_client_start_id != client_start_id
                    and candidate.get("source_session_id") == source_session_id
                    and candidate.get("source_transition_id") == source_transition_id
                    and candidate.get("status") in {"in_progress", "completed"}
                ):
                    consumed = dict(candidate)
                    consumed["accepted"] = False
                    consumed["request_mismatch"] = False
                    consumed["consumed_status"] = consumed.get("status")
                    consumed["status"] = "source_transition_consumed"
                    consumed["accepted_client_start_id"] = existing_client_start_id
                    return consumed
        existing = self.start_requests.get((user_id, client_start_id))
        if existing and existing.get("status") != "failed":
            row = dict(existing)
            row["accepted"] = False
            row["request_mismatch"] = row.get("request_hash") != request_hash
            return row
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
            "claim_generation": int((existing or {}).get("claim_generation") or 0) + 1,
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
        claim_generation: int = 1,
    ) -> bool:
        key = (user_id, client_start_id)
        row = self.start_requests.get(key)
        if (
            row is None
            or int(row.get("claim_generation") or 1) != int(claim_generation)
            or row.get("status") != "in_progress"
        ):
            return False
        row["status"] = status
        row["session_id"] = session_id
        row["response_json"] = dict(response_json or {})
        row["error_code"] = error_code
        row["updated_at"] = time.time()
        return True

    async def renew_start_request_claim(
        self,
        user_id: str,
        client_start_id: str,
        claim_generation: int,
    ) -> bool:
        row = self.start_requests.get((user_id, client_start_id))
        if (
            row is None
            or int(row.get("claim_generation") or 1) != int(claim_generation)
            or row.get("status") != "in_progress"
        ):
            return False
        row["updated_at"] = time.time()
        return True

    async def commit_claimed_session_start(
        self,
        *,
        user_id: str,
        client_start_id: str,
        claim_generation: int,
        session_record: dict[str, Any],
        runtime_record: dict[str, Any],
        messages: list[dict[str, Any]],
        response_json: dict[str, Any],
    ) -> bool:
        row = self.start_requests.get((user_id, client_start_id))
        if (
            row is None
            or row.get("status") != "in_progress"
            or int(row.get("claim_generation") or 1) != int(claim_generation)
        ):
            return False
        session_id = str(session_record["session_id"])
        self.sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "task_type": session_record["task_type"],
            "module_id": session_record["module_id"],
            "competency_node": session_record["node_id"],
            "test_mode": bool(session_record.get("test_mode")),
            "career_context": dict(session_record.get("career_context") or {}),
            "scenario_config": dict(session_record.get("scenario_config") or {}),
            "persona_roster": list(session_record.get("persona_roster") or []),
            "context_hash": session_record.get("context_hash") or "default",
            "status": "active",
        }
        runtime = dict(runtime_record)
        runtime["state_snapshot"] = dict(runtime_record.get("state_snapshot") or {})
        runtime["pending_transition"] = (
            dict(runtime_record["pending_transition"])
            if runtime_record.get("pending_transition")
            else None
        )
        self.session_runtime[session_id] = runtime
        self.session_messages[session_id] = [dict(message) for message in messages]
        row["status"] = "completed"
        row["session_id"] = session_id
        row["response_json"] = dict(response_json or {})
        row["error_code"] = None
        row["updated_at"] = time.time()
        return True

    async def compensate_claimed_attempt_charge(
        self,
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
        row = self.start_requests.get((user_id, client_start_id))
        if (
            row is None
            or row.get("status") != "in_progress"
            or int(row.get("claim_generation") or 1) != int(claim_generation)
        ):
            return False
        charge = self.idempotent_charges.get((user_id, charge_key))
        if (
            charge is None
            or int(charge.get("amount") or 0) != int(amount)
            or str(charge.get("reason") or "") != debit_reason
        ):
            raise RuntimeError("claimed_start_charge_missing")
        self.idempotent_charges.pop((user_id, charge_key), None)
        profile = self._profile(user_id)
        profile["credits"] = int(profile.get("credits") or 0) + amount
        self.credit_transactions.append({
            "user_id": user_id,
            "delta": amount,
            "reason": refund_reason,
            "idempotency_key": None,
        })
        row["status"] = "failed"
        row["session_id"] = None
        row["response_json"] = None
        row["error_code"] = error_code
        row["updated_at"] = time.time()
        return True

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

    async def record_learning_event(self, **kwargs) -> bool:
        key = kwargs.get("source_event_key")
        if key and any(row.get("source_event_key") == key for row in self.learning_events):
            return False
        self.learning_events.append(dict(kwargs))
        return True

    async def record_learning_event_and_update_profile(
        self,
        *,
        event: dict,
        profile: dict,
    ) -> bool:
        inserted = await self.record_learning_event(**event)
        if not inserted:
            return False
        try:
            await self.upsert_learner_skill_profile(**profile)
        except Exception:
            self.learning_events = [
                row
                for row in self.learning_events
                if row.get("source_event_key") != event.get("source_event_key")
            ]
            raise
        return True

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

    async def deduct_credits_once(
        self,
        user_id: str,
        amount: int,
        reason: str,
        idempotency_key: str,
    ) -> bool:
        key = (user_id, idempotency_key)
        if key in self.idempotent_charges:
            return True
        if not await self.deduct_credits(user_id, amount, reason):
            return False
        self.idempotent_charges[key] = {"amount": amount, "reason": reason}
        self.credit_transactions.append({
            "user_id": user_id,
            "delta": -amount,
            "reason": reason,
            "idempotency_key": idempotency_key,
        })
        return True

    async def refund_idempotent_charge(
        self,
        user_id: str,
        amount: int,
        idempotency_key: str,
        reason: str = "refund",
    ) -> bool:
        row = self.idempotent_charges.pop((user_id, idempotency_key), None)
        if row is None:
            return False
        profile = self._profile(user_id)
        profile["credits"] = int(profile.get("credits") or 0) + amount
        self.credit_transactions.append({
            "user_id": user_id,
            "delta": amount,
            "reason": reason,
            "idempotency_key": None,
        })
        return True

    async def charge_and_unlock(
        self, user_id: str, amount: int, reason: str, scope: str, ref_id: str
    ) -> tuple[bool, bool]:
        unlock_key = (user_id, scope, ref_id)
        if unlock_key in self.unlocks:
            return True, False
        if not await self.deduct_credits(user_id, amount, reason):
            return False, False
        self.unlocks.add(unlock_key)
        self.credit_transactions.append({
            "user_id": user_id,
            "delta": -amount,
            "reason": reason,
            "idempotency_key": None,
        })
        return True, True

    async def get_progression(self, user_id: str) -> list[dict[str, Any]]:
        rows = [
            dict(row)
            for (uid, _node_id), row in self.mastery.items()
            if uid == user_id
        ]
        rows.sort(key=lambda row: row["node_id"])
        return rows

    async def get_latest_passing_turn_evaluation(
        self,
        user_id: str,
        node_id: str,
        attempt_type: str = "independent",
    ) -> dict[str, Any] | None:
        rows = [
            row
            for row in self.turn_evaluations
            if row.get("user_id") == user_id
            and row.get("node_id") == node_id
            and row.get("attempt_type") == attempt_type
            and row.get("pass_eligible") is True
            and not row.get("blockers")
        ]
        return dict(rows[-1]) if rows else None

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
