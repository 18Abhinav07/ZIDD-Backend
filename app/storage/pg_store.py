"""Postgres/Supabase storage backend.

This is the product runtime store. PgStore must not silently no-op when
Supabase is unavailable, because that loses auth profiles, credits, progress,
and session history while making the product look functional.
"""
from contextlib import asynccontextmanager

from app.db.cancellation import finish_cleanup


@asynccontextmanager
async def _session():
    """Yield an AsyncSession, raising if Supabase cannot be reached/configured."""
    from app.db.engine import get_sessionmaker

    maker = get_sessionmaker()
    sess = maker()
    try:
        yield sess
    finally:
        try:
            await finish_cleanup(sess.close())
        except Exception:
            pass


def _parse_context_rows(rows: list[dict]) -> list[dict]:
    """Turn pgvector (node_id, content) rows into the app context shape.

    Each row's `content` is a raw session summary (the 3-line Strengths/Watch/
    Next focus format write_memory persists). Parse the named lines and stamp
    the REAL competency node_id the row carries so a caller matching a summary
    to a node (the welcome-back recap) works without a second lookup.
    """
    result: list[dict] = []
    for row in rows or []:
        node_id = row.get("node_id", "") if isinstance(row, dict) else ""
        chunk = ((row.get("content", "") if isinstance(row, dict) else "") or "").strip()
        if not chunk:
            continue
        parsed: dict[str, str] = {}
        for line in chunk.splitlines():
            if line.startswith("Strengths:"):
                parsed["strengths"] = line[len("Strengths:"):].strip()
            elif line.startswith("Watch:"):
                parsed["watch"] = line[len("Watch:"):].strip()
            elif line.startswith("Next focus:"):
                parsed["next_focus"] = line[len("Next focus:"):].strip()
        result.append({
            "node_id": node_id, "score": 0.0,
            "session_id": str(row.get("session_id") or "") if isinstance(row, dict) else "",
            "task_type": str(row.get("task_type") or "") if isinstance(row, dict) else "",
            "module_id": str(row.get("module_id") or "") if isinstance(row, dict) else "",
            "strengths": parsed.get("strengths", ""),
            "watch": parsed.get("watch", ""),
            "next_focus": parsed.get("next_focus", ""),
            "date": "", "raw": chunk,
        })
    return result


class PgStore:
    async def ping_writable(self) -> bool:
        """Confirm the pooled Postgres connection answers a trivial query."""
        from sqlalchemy import text

        try:
            async with _session() as s:
                try:
                    result = await s.execute(text("SELECT 1"))
                    return result.scalar() == 1
                except Exception:
                    return False
        except Exception:
            return False

    async def ensure_profile(
        self,
        user_id: str,
        name: str = "",
        email: str | None = None,
        google_sub: str | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.ensure_profile(s, user_id, name, email, google_sub)

    async def get_profile(self, user_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_profile(s, user_id)

    async def get_profile_by_email(self, email: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_profile_by_email(s, email)

    async def get_profile_by_google_sub(self, google_sub: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_profile_by_google_sub(s, google_sub)

    async def resolve_google_login(
        self,
        google_sub: str,
        email: str,
        name: str,
        welcome_credits: int,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.resolve_google_login(
                s, google_sub, email, name, welcome_credits
            )

    async def get_preferences(self, user_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_preferences(s, user_id)

    async def update_preferences(self, user_id: str, patch: dict) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.update_preferences(s, user_id, patch)

    async def update_onboarding_state(self, user_id: str, draft: dict) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.update_onboarding_state(s, user_id, draft)

    async def complete_onboarding(
        self,
        user_id: str,
        display_name: str,
        primary_motive: str,
        school_profile: dict,
        career_profile: dict,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.complete_onboarding(
                s, user_id, display_name, primary_motive, school_profile, career_profile
            )

    async def get_active_school_profile_version(self, user_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_school_profile_version(s, user_id)

    async def get_school_state_snapshot(self, user_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_state_snapshot(s, user_id)

    async def get_school_profile_draft(self, user_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_profile_draft(s, user_id)

    async def get_school_profile_version(
        self,
        user_id: str,
        profile_version_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_profile_version(s, user_id, profile_version_id)

    async def save_school_profile_draft(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.save_school_profile_draft(s, **kwargs)

    async def activate_school_profile_draft(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.activate_school_profile_draft(s, **kwargs)

    async def create_session(
        self,
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
        from app.db import repo

        async with _session() as s:
            await repo.create_session(
                s,
                session_id,
                user_id,
                task_type,
                module_id,
                node_id,
                test_mode=test_mode,
                career_context=career_context or {},
                scenario_config=scenario_config or {},
                persona_roster=persona_roster or [],
                context_hash=context_hash,
            )

    async def begin_start_request(
        self,
        user_id: str,
        client_start_id: str,
        request_hash: str,
        source_session_id: str | None = None,
        source_transition_id: str | None = None,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.begin_start_request(
                s,
                user_id,
                client_start_id,
                request_hash,
                source_session_id=source_session_id,
                source_transition_id=source_transition_id,
            )

    async def get_start_request(
        self,
        user_id: str,
        client_start_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_start_request(s, user_id, client_start_id)

    async def get_start_request_for_source_transition(
        self,
        source_session_id: str,
        source_transition_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_start_request_for_source_transition(
                s,
                source_session_id,
                source_transition_id,
            )

    async def reset_start_request(
        self,
        user_id: str,
        client_start_id: str,
        request_hash: str,
        source_session_id: str | None = None,
        source_transition_id: str | None = None,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.reset_start_request(
                s,
                user_id,
                client_start_id,
                request_hash,
                source_session_id=source_session_id,
                source_transition_id=source_transition_id,
            )

    async def complete_start_request(
        self,
        user_id: str,
        client_start_id: str,
        status: str,
        session_id: str | None = None,
        response_json: dict | None = None,
        error_code: str | None = None,
        claim_generation: int = 1,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.complete_start_request(
                s,
                user_id,
                client_start_id,
                status,
                session_id=session_id,
                response_json=response_json or {},
                error_code=error_code,
                claim_generation=claim_generation,
            )

    async def renew_start_request_claim(
        self,
        user_id: str,
        client_start_id: str,
        claim_generation: int,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.renew_start_request_claim(
                s,
                user_id,
                client_start_id,
                claim_generation,
            )

    async def commit_claimed_session_start(
        self,
        *,
        user_id: str,
        client_start_id: str,
        claim_generation: int,
        session_record: dict,
        runtime_record: dict,
        messages: list[dict],
        response_json: dict,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.commit_claimed_session_start(
                s,
                user_id=user_id,
                client_start_id=client_start_id,
                claim_generation=claim_generation,
                session_record=session_record,
                runtime_record=runtime_record,
                messages=messages,
                response_json=response_json,
            )

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
        from app.db import repo

        async with _session() as s:
            return await repo.compensate_claimed_attempt_charge(
                s,
                user_id=user_id,
                client_start_id=client_start_id,
                claim_generation=claim_generation,
                amount=amount,
                charge_key=charge_key,
                debit_reason=debit_reason,
                refund_reason=refund_reason,
                error_code=error_code,
            )

    async def end_session(
        self, session_id: str, final_summary: str = "", avg_score: float = 0.0
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.end_session(s, session_id, 0, avg_score, final_summary)

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
        from app.db import repo

        async with _session() as s:
            await repo.record_turn(
                s, session_id, user_id, node_id, score, on_task, english, affect
            )

    async def get_turns(self, session_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_turns(s, session_id)

    async def record_turn_evaluation(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.record_turn_evaluation(s, **kwargs)

    async def get_latest_passing_turn_evaluation(
        self,
        user_id: str,
        node_id: str,
        attempt_type: str = "independent",
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_latest_passing_turn_evaluation(
                s,
                user_id,
                node_id,
                attempt_type,
            )

    async def record_learning_event(self, **kwargs) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.record_learning_event(s, **kwargs)

    async def record_learning_event_and_update_profile(
        self,
        *,
        event: dict,
        profile: dict,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.record_learning_event_and_update_profile(
                s,
                event=event,
                profile=profile,
            )

    async def upsert_session_report(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_session_report(s, **kwargs)

    async def upsert_learner_skill_profile(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_learner_skill_profile(s, **kwargs)

    async def reconcile_school_chapter_certification_projection(
        self,
        **kwargs,
    ) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.reconcile_school_chapter_certification_projection(
                s,
                **kwargs,
            )

    async def replace_learner_skill_profiles_for_task(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.replace_learner_skill_profiles_for_task(s, **kwargs)

    async def reconcile_learner_skill_profiles_for_report(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.reconcile_learner_skill_profiles_for_report(s, **kwargs)

    async def get_learning_graph(self, user_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_learning_graph(s, user_id)

    async def get_school_learning_graph(self, user_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_learning_graph(s, user_id)

    async def get_active_career_session_runtimes(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_career_session_runtimes(s, user_id)

    async def upsert_session_runtime(
        self,
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
        from app.db import repo

        async with _session() as s:
            await repo.upsert_session_runtime(
                s,
                session_id,
                user_id,
                current_node,
                module_id,
                task_type,
                test_mode,
                status,
                state_snapshot,
                pending_transition,
                session_version,
                active_turn_id=active_turn_id,
                active_opening_id=active_opening_id,
                last_error=last_error,
                lease_expires_at=lease_expires_at,
            )

    async def get_session_runtime(self, session_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            row = await repo.get_session_runtime(s, session_id)
            if row:
                messages = await repo.list_session_messages(s, session_id)
                if messages:
                    snapshot = dict(row.get("state_snapshot") or {})
                    snapshot["messages"] = messages
                    row["state_snapshot"] = snapshot
            return row

    async def get_active_session_runtime_for_node(
        self,
        user_id: str,
        node_id: str,
        task_type: str,
        test_mode: bool,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            row = await repo.get_active_session_runtime_for_node(
                s, user_id, node_id, task_type, test_mode
            )
            if row:
                messages = await repo.list_session_messages(s, row["session_id"])
                if messages:
                    snapshot = dict(row.get("state_snapshot") or {})
                    snapshot["messages"] = messages
                    row["state_snapshot"] = snapshot
            return row

    async def get_latest_active_session_runtime_for_module(
        self,
        user_id: str,
        module_id: str,
        test_mode: bool,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            row = await repo.get_latest_active_session_runtime_for_module(
                s, user_id, module_id, test_mode
            )
            if row:
                messages = await repo.list_session_messages(s, row["session_id"])
                if messages:
                    snapshot = dict(row.get("state_snapshot") or {})
                    snapshot["messages"] = messages
                    row["state_snapshot"] = snapshot
            return row

    async def touch_session_runtime(
        self,
        session_id: str,
        status: str = "active",
        lease_expires_at: str | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.touch_session_runtime(s, session_id, status, lease_expires_at)

    async def replace_session_messages(
        self, session_id: str, messages: list[dict]
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.replace_session_messages(s, session_id, messages)

    async def begin_turn_request(
        self,
        session_id: str,
        client_turn_id: str,
        request_hash: str,
        expected_version: int | None,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.begin_turn_request(
                s, session_id, client_turn_id, request_hash, expected_version
            )

    async def complete_turn_request(
        self,
        session_id: str,
        client_turn_id: str,
        status: str,
        transcript_delta: list[dict] | None = None,
        done_snapshot: dict | None = None,
        error_code: str | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.complete_turn_request(
                s,
                session_id,
                client_turn_id,
                status,
                transcript_delta,
                done_snapshot,
                error_code,
            )

    async def begin_opening_request(
        self,
        session_id: str,
        transition_id: str,
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.begin_opening_request(s, session_id, transition_id)

    async def complete_opening_request(
        self,
        session_id: str,
        transition_id: str,
        status: str,
        message_id: str | None = None,
        last_error: str | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.complete_opening_request(
                s,
                session_id,
                transition_id,
                status,
                message_id,
                last_error,
            )

    async def begin_end_request(self, session_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.begin_end_request(s, session_id)

    async def complete_end_request(
        self,
        session_id: str,
        status: str,
        response_json: dict | None = None,
        error_code: str | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.complete_end_request(
                s,
                session_id,
                status,
                response_json,
                error_code,
            )

    async def get_end_request(self, session_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_end_request(s, session_id)

    async def upsert_mastery(
        self,
        user_id: str,
        node_id: str,
        ema: float,
        attempts: int,
        clean_pass: bool = False,
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
        from app.db import repo

        async with _session() as s:
            await repo.upsert_mastery(
                s,
                user_id,
                node_id,
                ema,
                attempts,
                clean_pass,
                node_completed,
                node_mastered=node_mastered,
                display_status=display_status,
                best_independent_score=best_independent_score,
                independent_passes=independent_passes,
                transfer_passes=transfer_passes,
                pressure_passes=pressure_passes,
                scaffold_successes=scaffold_successes,
                last_gap=last_gap,
                mastery_evidence=mastery_evidence,
            )

    async def get_last_active_node(self, user_id: str) -> str | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_last_active_node(s, user_id)

    async def get_progression(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_progression(s, user_id)

    async def get_module_passrate(
        self, user_id: str, node_ids: list[str]
    ) -> tuple[int, int]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_module_passrate(s, user_id, node_ids)

    async def bump_weakness(
        self,
        user_id: str,
        task_type: str,
        skill_id: str,
        score: float,
        raw: str = "",
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.bump_weakness(s, user_id, task_type, skill_id, score, raw)

    async def get_weaknesses(
        self, user_id: str, task_type: str | None = None
    ) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_weaknesses(s, user_id, task_type)

    # ---------- school progress + per-skill mastery ----------

    async def record_assessment_result(
        self, user_id: str, test_id: str, class_no: int, kind: str,
        score: float, passed: bool, by_skill: list[dict],
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.record_assessment_result(
                s, user_id, test_id, class_no, kind, score, passed, by_skill
            )

    async def get_school_skill_mastery(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_skill_mastery(s, user_id)

    async def get_school_weak_skills(
        self, user_id: str, threshold: float = 0.6, limit: int = 5
    ) -> list[str]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_weak_skills(s, user_id, threshold, limit)

    async def get_school_results(
        self, user_id: str, class_no: int | None = None
    ) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_results(s, user_id, class_no)

    async def upsert_school_session(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_school_session(s, **kwargs)

    async def get_or_create_school_session(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_or_create_school_session(s, **kwargs)

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
        projection_evidence: dict | None = None,
        language_evaluation: dict | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.persist_school_curriculum_attempt(
                s,
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

    async def persist_school_answer_attempt(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.persist_school_answer_attempt(s, **kwargs)

    async def compare_and_set_school_session(
        self,
        *,
        school_session: dict,
        expected_state_json: dict,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.compare_and_set_school_session(
                s,
                school_session=school_session,
                expected_state_json=expected_state_json,
            )

    async def get_school_answer_request(
        self, user_id: str, session_id: str, activity_id: str
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_answer_request(s, user_id, session_id, activity_id)

    async def claim_school_answer_request(
        self, user_id: str, session_id: str, activity_id: str, answer_hash: str
    ) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.claim_school_answer_request(
                s, user_id, session_id, activity_id, answer_hash
            )

    async def fail_school_answer_request(
        self,
        user_id: str,
        session_id: str,
        activity_id: str,
        answer_hash: str,
        claim_token: str,
        placement_retry_timing: dict | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.fail_school_answer_request(
                s,
                user_id,
                session_id,
                activity_id,
                answer_hash,
                claim_token,
                placement_retry_timing=placement_retry_timing,
            )

    async def renew_school_answer_request(
        self,
        user_id: str,
        session_id: str,
        activity_id: str,
        answer_hash: str,
        claim_token: str,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.renew_school_answer_request(
                s,
                user_id,
                session_id,
                activity_id,
                answer_hash,
                claim_token,
            )

    async def get_school_session(
        self,
        user_id: str,
        session_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_session(s, user_id, session_id)

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
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_school_session(
                s,
                user_id,
                api_version,
                flow_type,
                subject_id,
                class_no,
                profile_version_id=profile_version_id,
                source_placement_report_id=source_placement_report_id,
            )

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
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_latest_school_session(
                s,
                user_id,
                api_version,
                flow_type,
                subject_id,
                class_no,
                profile_version_id=profile_version_id,
                source_placement_report_id=source_placement_report_id,
            )

    async def get_or_create_active_school_placement_session(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_or_create_active_school_placement_session(s, **kwargs)

    async def present_school_placement_item(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.present_school_placement_item(s, **kwargs)

    async def resume_school_placement_session(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.resume_school_placement_session(s, **kwargs)

    async def get_school_sessions_linked_to(
        self,
        user_id: str,
        linked_session_id: str,
    ) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_sessions_linked_to(s, user_id, linked_session_id)

    async def expire_active_school_sessions_from_other_profiles(
        self,
        user_id: str,
        current_profile_version_id: str,
    ) -> int:
        from app.db import repo

        async with _session() as s:
            return await repo.expire_active_school_sessions_from_other_profiles(
                s,
                user_id,
                current_profile_version_id,
            )

    async def upsert_school_placement_report(self, **kwargs) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.upsert_school_placement_report(s, **kwargs)

    async def get_school_placement_report(
        self,
        user_id: str,
        placement_session_id: str,
        *,
        profile_version_id: str | None = None,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_placement_report(
                s,
                user_id,
                placement_session_id,
                profile_version_id=profile_version_id,
            )

    async def get_school_placement_report_by_id(
        self,
        user_id: str,
        report_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_placement_report_by_id(
                s,
                user_id,
                report_id,
            )

    async def get_latest_compatible_school_placement_report(
        self,
        user_id: str,
        profile_version_id: str,
        subject_id: str,
        target_class_no: int,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_latest_compatible_school_placement_report(
                s,
                user_id,
                profile_version_id,
                subject_id,
                target_class_no,
            )

    async def upsert_school_language_confidence(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_school_language_confidence(s, **kwargs)

    async def get_school_language_confidence(self, user_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_language_confidence(s, user_id)

    async def upsert_school_v2_placement_session(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_school_v2_placement_session(s, **kwargs)

    async def get_school_v2_placement_session(
        self,
        user_id: str,
        placement_session_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_v2_placement_session(
                s,
                user_id,
                placement_session_id,
            )

    async def get_active_school_v2_placement_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_school_v2_placement_session(
                s,
                user_id,
                subject_id,
                target_class_no,
            )

    async def upsert_school_v2_practice_session(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_school_v2_practice_session(s, **kwargs)

    async def get_school_v2_practice_session(
        self,
        user_id: str,
        practice_session_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_v2_practice_session(
                s,
                user_id,
                practice_session_id,
            )

    async def get_active_school_v2_practice_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
        skill_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_school_v2_practice_session(
                s,
                user_id,
                subject_id,
                target_class_no,
                skill_id,
            )

    async def upsert_school_v2_curriculum_session(self, **kwargs) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.upsert_school_v2_curriculum_session(s, **kwargs)

    async def get_school_v2_curriculum_session(
        self,
        user_id: str,
        curriculum_session_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_v2_curriculum_session(
                s,
                user_id,
                curriculum_session_id,
            )

    async def get_active_school_v2_curriculum_session(
        self,
        user_id: str,
        subject_id: str,
        target_class_no: int,
        chapter_id: str,
    ) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_active_school_v2_curriculum_session(
                s,
                user_id,
                subject_id,
                target_class_no,
                chapter_id,
            )

    async def get_activity_snapshot(self, user_id: str) -> dict:
        from app.db import repo

        async with _session() as s:
            return await repo.get_activity_snapshot(s, user_id)

    async def get_school_review_skills(
        self, user_id: str, mastered_threshold: float = 0.8,
        stale_seconds: float = 5 * 24 * 60 * 60, limit: int = 3,
    ) -> list[str]:
        from app.db import repo

        async with _session() as s:
            return await repo.get_school_review_skills(
                s, user_id, mastered_threshold, stale_seconds, limit
            )

    async def write_memory(
        self,
        user_id: str,
        session_id: str,
        node_id: str,
        content: str,
        task_type: str = "",
        score: float = 0.0,
    ) -> bool:
        # Keep `score` in the method signature so session_service's end_session
        # call `write_memory(..., score=avg_score)` does not raise a
        # TypeError under the cloud backend (which a bare `except Exception: pass`
        # at the call site would have silently swallowed, dropping the memory).
        # The pgvector store keys on content, so score is not forwarded.
        from app.memory import store as memory_store

        async with _session() as s:
            return await memory_store.write_memory(
                s, user_id, session_id, node_id, content
            )

    async def load_context(self, user_id: str, task_type: str, k: int = 3) -> list[dict]:
        """Most recent k session summaries as structured dicts, newest-first.

        Returns list[dict] with keys node_id, score, strengths, watch,
        next_focus, date, raw. The pgvector store hands back (node_id, content)
        rows; each carries the REAL competency node that produced the summary,
        so the node-level match in start_session works. Empty/offline -> []."""
        from app.memory import store as memory_store

        async with _session() as s:
            # task_type biases the semantic query; each row carries its true
            # competency node_id (see memory_store.load_context).
            rows = await memory_store.load_context(s, user_id, task_type, k)
        return _parse_context_rows(rows)

    # ---------- test-item cache ----------

    async def cache_test_items(
        self,
        user_id: str,
        task_type: str,
        items: list[dict],
        context_hash: str = "default",
        ts: float | None = None,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.cache_test_items(s, user_id, task_type, items, context_hash, ts)

    async def get_cached_test_items(
        self,
        user_id: str,
        task_type: str,
        context_hash: str = "default",
        max_age: float | None = None,
    ) -> list[dict] | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_cached_test_items(
                s, user_id, task_type, context_hash, max_age
            )

    # ---------- billing: credits ----------

    async def get_credits(self, user_id: str) -> int:
        from app.db import repo

        async with _session() as s:
            return await repo.get_credits(s, user_id)

    async def is_demo(self, user_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            profile = await repo.get_profile(s, user_id)
            if profile is None:
                return False
            return bool(profile["demo_unlimited"])

    async def set_demo_unlimited(self, user_id: str, enabled: bool = True) -> None:
        from app.db import repo

        async with _session() as s:
            return await repo.set_demo_unlimited(s, user_id, enabled)

    async def grant_credits(self, user_id: str, amount: int, reason: str) -> int:
        from app.db import repo

        async with _session() as s:
            return await repo.grant_credits(s, user_id, amount, reason)

    async def deduct_credits(self, user_id: str, amount: int, reason: str) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.deduct_credit(s, user_id, amount, reason)

    async def deduct_credits_once(
        self,
        user_id: str,
        amount: int,
        reason: str,
        idempotency_key: str,
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.deduct_credit_once(
                s,
                user_id,
                amount,
                reason,
                idempotency_key,
            )

    async def refund_idempotent_charge(
        self,
        user_id: str,
        amount: int,
        idempotency_key: str,
        reason: str = "refund",
    ) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.refund_idempotent_charge(
                s,
                user_id,
                amount,
                idempotency_key,
                reason,
            )

    async def charge_and_unlock(
        self,
        user_id: str,
        amount: int,
        reason: str,
        scope: str,
        ref_id: str,
    ) -> tuple[bool, bool]:
        """Return (allowed, charged) for one atomic ACCESS unlock attempt."""
        from app.db import repo

        async with _session() as s:
            return await repo.charge_and_unlock(
                s, user_id, amount, reason, scope, ref_id
            )

    # ---------- billing: content unlocks ----------

    async def has_unlock(self, user_id: str, scope: str, ref_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.has_unlock(s, user_id, scope, ref_id)

    async def add_unlock(
        self, user_id: str, scope: str, ref_id: str, credits_spent: int
    ) -> None:
        from app.db import repo

        async with _session() as s:
            return await repo.add_unlock(
                s, user_id, scope, ref_id, credits_spent
            )

    async def remove_unlock(self, user_id: str, scope: str, ref_id: str) -> None:
        from app.db import repo

        async with _session() as s:
            return await repo.remove_unlock(s, user_id, scope, ref_id)

    async def list_unlocks(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            return await repo.list_unlocks(s, user_id)

    async def count_attempts(self, user_id: str, module_id: str) -> int:
        from app.content import registry
        from app.db import repo

        async with _session() as s:
            nodes = await repo.list_node_attempt_nodes(s, user_id)
            count = 0
            for node_id in nodes:
                try:
                    if registry.module_of(node_id) == module_id:
                        count += 1
                except KeyError:
                    continue
            return count

    async def record_node_attempt(
        self,
        session_id: str,
        user_id: str,
        node_id: str,
        starting_mastery: float = 0.0,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            await repo.record_node_attempt(
                s,
                attempt_id=session_id,
                session_id=session_id,
                user_id=user_id,
                node_id=node_id,
                starting_mastery=starting_mastery,
            )

    # ---------- billing: purchases ----------

    async def record_purchase(
        self,
        order_id: str,
        user_id: str,
        pack_id: str,
        credits: int,
        amount_paise: int,
        status: str = "created",
    ) -> None:
        from app.db import repo

        async with _session() as s:
            return await repo.record_purchase(
                s, order_id, user_id, pack_id, credits, amount_paise, status=status
            )

    async def get_purchase(self, order_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            return await repo.get_purchase(s, order_id)

    async def mark_purchase_paid(self, order_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            return await repo.mark_purchase_paid(s, order_id)

    async def mark_paid_and_grant(
        self, order_id: str, user_id: str, credits: int, reason: str
    ) -> bool:
        """Latch a purchase to 'paid' AND grant its credits in ONE transaction.

        Delegates to repo.mark_paid_and_grant, which folds the latch + grant +
        ledger row under a SINGLE commit() with rollback-on-failure. The old
        body committed the latch and the grant in TWO
        separate transactions (mark_purchase_paid then grant_credits): an error
        between them left the order permanently 'paid' with credits never
        granted, and Razorpay's retry then skipped the grant forever.

        Exceptions are intentionally NOT swallowed here. The repo helper rolls
        the whole unit back before raising, so the order stays UNPAID on failure
        and the grant is never lost: a missing-profile KeyError is handled by the
        webhook route (deferred for reconciliation), and a transient DB error
        propagates to a 5xx so Razorpay retries. Returns True on the first
        captured webhook (granted once); False on a retry (already paid).
        """
        from app.db import repo

        async with _session() as s:
            return await repo.mark_paid_and_grant(
                s, order_id, user_id, credits, reason
            )
