from __future__ import annotations

import copy
import hashlib
from uuid import uuid4

import pytest

from app.api import school_rebuild_routes
from app.content.school_v3_schema import (
    SchoolV3RubricCriterion,
    SchoolV3RubricEvaluation,
)
from app.services import school_rebuild_curriculum as curriculum
from app.services import school_rebuild_masterclass as masterclass
from app.services import school_rebuild_placement as placement
from app.services import school_rebuild_recap as recap
from app.services.school import evaluation_jobs
from tests.conftest import InMemoryStore


USER_ID = "evaluation-worker-learner"


def test_curriculum_worker_timing_log_is_safe_and_phase_specific(monkeypatch):
    """Worker telemetry may identify a slow boundary but never learner text."""

    captured_logs: list[tuple[object, tuple[object, ...]]] = []

    class Logger:
        def warning(self, message, *args):
            captured_logs.append((message, args))

    class Settings:
        app_env = "dev"

    monkeypatch.setattr(school_rebuild_routes, "get_settings", lambda: Settings())
    monkeypatch.setattr(school_rebuild_routes, "logger", Logger())

    school_rebuild_routes._log_school_evaluation_job_timing(
        flow_type="curriculum",
        activity_id="poem_story:independent:1",
        preflight_ms=12.5,
        evaluation_ms=1950.8,
        finalization_ms=834.2,
        total_ms=2810.1,
    )

    assert len(captured_logs) == 1
    message, args = captured_logs[0]
    assert message == "school_evaluation_job_timing %s"
    telemetry = args[0]
    assert telemetry == {
        "flow_type": "curriculum",
        "activity_id": "poem_story:independent:1",
        "preflight_ms": 12.5,
        "evaluation_ms": 1950.8,
        "finalization_ms": 834.2,
        "total_ms": 2810.1,
    }
    assert "raw_answer" not in telemetry


def _semantic_curriculum_state() -> tuple[dict, str, str]:
    chapter = copy.deepcopy(
        next(
            candidate
            for candidate in curriculum.CLASS_5_CURRICULUM_CHAPTERS
            if candidate["chapter_id"] == "eng_c5_ch05"
        )
    )
    level_id = "frog_poem_meaning"
    levels = copy.deepcopy(chapter["levels"])
    level_index = next(
        index for index, level in enumerate(levels) if level["level_id"] == level_id
    )
    for index, level in enumerate(levels):
        level["status"] = "complete" if index < level_index else "not_started"
        level["current_step"] = "complete" if index < level_index else "guided_check"
        level["attempts"] = []
    active_level = levels[level_index]
    active_level["status"] = "in_progress"
    independent_index = next(
        index
        for index, step in enumerate(active_level["teaching_steps"])
        if step["phase"] == "independent_application"
    )
    active_level["v2_step_index"] = independent_index
    active_level["current_step"] = "independent_application"
    state = curriculum.normalize_curriculum_state(
        {
            "engine_version": curriculum.ENGINE_VERSION,
            "profile_version_id": "worker-profile",
            "status": "active",
            "phase": "learning",
            "subject_id": "english",
            "target_class_no": 5,
            "active_learning_class_no": 5,
            "preferred_teaching_language": "en",
            "source_recap_session_id": None,
            "source_placement_report_id": "worker-placement",
            "chapter": {
                key: value
                for key, value in chapter.items()
                if key != "levels"
            },
            "chapter_assessment": copy.deepcopy(chapter["chapter_assessment"]),
            "completed_chapter_ids": [],
            "completed_chapter_versions": {},
            "completed_chapter_certification_versions": {},
            "carry_forward_focuses": [],
            "learner_memory": {},
            "current_level_index": level_index,
            "levels": levels,
            "last_feedback": None,
            "feedback_v2": None,
            "hot_session_memory": {},
            "active_interrupt": None,
            "interrupt_history": [],
            "interrupt_counts": {},
        }
    )
    activity_id = (
        "frog_poem_meaning:frog_poem_meaning:independent_application:"
        "frog_poem_meaning:independent:1:1"
    )
    answer = (
        "The jump feels very high and exciting, but the frog does not reach clouds; "
        "this is not a scientific height claim."
    )
    return state, activity_id, answer


async def _seed_queued_curriculum_job() -> tuple[InMemoryStore, dict, dict, str, str]:
    store = InMemoryStore()
    state, activity_id, answer = _semantic_curriculum_state()
    session_id = str(uuid4())
    store.school_profile_versions[(USER_ID, "worker-profile")] = {
        "user_id": USER_ID,
        "profile_version_id": "worker-profile",
        "status": "active",
    }
    await store.upsert_school_session(
        session_id=session_id,
        user_id=USER_ID,
        api_version="rebuild",
        flow_type="curriculum",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="2",
        linked_session_id=None,
        profile_version_id="worker-profile",
        source_placement_report_id="worker-placement",
        state_json=state,
    )
    answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    claim = await store.claim_school_answer_request(
        USER_ID, session_id, activity_id, answer_hash
    )
    queued = await store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=session_id,
        activity_id=activity_id,
        raw_answer=answer,
        expected_state_json=state,
        answer_hash=answer_hash,
        answer_claim_token=claim["claim_token"],
        flow_type="curriculum",
        evaluation_mode="llm_rubric",
        max_attempts=2,
    )
    assert queued["outcome"] == "queued"
    return store, state, queued["job"], session_id, answer


async def _seed_queued_masterclass_job() -> tuple[
    InMemoryStore,
    dict,
    dict,
    str,
    str,
]:
    chapter = copy.deepcopy(
        next(
            candidate
            for candidate in curriculum._available_chapters("english", 5)
            if candidate["chapter_id"] == "eng_c5_ch02"
        )
    )
    level = next(
        candidate
        for candidate in chapter["levels"]
        if candidate["level_id"] == "scooter_dialogue_and_speaker"
    )
    parent_session_id = str(uuid4())
    child_session_id = str(uuid4())
    parent_state = {
        "status": "paused_for_masterclass",
        "phase": "paused_for_masterclass",
        "chapter": {
            key: value
            for key, value in chapter.items()
            if key != "levels"
        },
        "preferred_teaching_language": "en",
        "hot_session_memory": {
            "used_variant_ids": [
                "scooter_dialogue_and_speaker:guided:1",
                "scooter_dialogue_and_speaker:independent:1",
                "scooter_dialogue_and_speaker:transfer:1",
            ]
        },
        "active_interrupt": {
            "interrupt_id": "scooter_dialogue_and_speaker:masterclass:1",
            "level_id": level["level_id"],
            "focus": level["focus"],
            "skill_ids": list(level["skill_ids"]),
            "trigger_count": 1,
            "runtime_contract": "v2",
        },
        "levels": [level],
    }
    child_state = masterclass.new_masterclass_state(
        curriculum_session_id=parent_session_id,
        curriculum_state=parent_state,
    )
    # Exercise the semantic independent phase rather than the deterministic
    # first support activity.
    child_state["phase_index"] = 2
    activity = masterclass.current_activity(child_state)
    assert activity is not None
    assert activity["evaluation_mode"] == "llm_rubric"
    answer = (
        "Priya asks how to find the cart. The guard says to note the number and "
        "call the depot. Priya says she can see the number. The guard tells her "
        "to write it down."
    )

    store = InMemoryStore()
    store.school_profile_versions[(USER_ID, "worker-profile")] = {
        "user_id": USER_ID,
        "profile_version_id": "worker-profile",
        "status": "active",
    }
    await store.upsert_school_session(
        session_id=parent_session_id,
        user_id=USER_ID,
        api_version="rebuild",
        flow_type="curriculum",
        subject_id="english",
        class_no=5,
        status="paused_for_masterclass",
        current_stage="2",
        linked_session_id=None,
        profile_version_id="worker-profile",
        source_placement_report_id="worker-placement",
        state_json=parent_state,
    )
    await store.upsert_school_session(
        session_id=child_session_id,
        user_id=USER_ID,
        api_version="rebuild",
        flow_type="masterclass",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="focused_practice",
        linked_session_id=parent_session_id,
        profile_version_id="worker-profile",
        source_placement_report_id="worker-placement",
        state_json=child_state,
    )
    answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    claim = await store.claim_school_answer_request(
        USER_ID,
        child_session_id,
        activity["activity_id"],
        answer_hash,
    )
    queued = await store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=child_session_id,
        activity_id=activity["activity_id"],
        raw_answer=answer,
        expected_state_json=child_state,
        answer_hash=answer_hash,
        answer_claim_token=claim["claim_token"],
        flow_type="masterclass",
        evaluation_mode="llm_rubric",
        max_attempts=2,
    )
    assert queued["outcome"] == "queued"
    return store, child_state, queued["job"], child_session_id, answer


async def _seed_queued_recap_job() -> tuple[
    InMemoryStore,
    dict,
    dict,
    str,
    str,
]:
    report = {
        "profile_version_id": "worker-profile",
        "report_id": "worker-placement",
        "placement_session_id": "worker-placement-session",
        "subject_id": "english",
        "target_class_no": 5,
        "active_learning_class_no": 4,
        "recommended_recap_modules": [
            {
                "module_id": "worker-inference-recap",
                "title": "Use a clue to infer",
                "focus": "Use a clue to infer",
                "source_class_no": 4,
                "target_class_no": 5,
                "placement_track_id": "english.c5.inference",
                "primary_skill_id": "reading.inference_reason",
            }
        ],
    }
    state = recap.new_recap_state(report)
    activity = recap.recap_activity_for_answer(
        state,
        activity_id="worker-inference-recap:guided_check:attempt:1",
    )
    assert activity["evaluation_mode"] == "strict_rubric"
    answer = (
        "It probably rained because Rohan has drops on his hair and folded a wet "
        "raincoat beside the door."
    )
    session_id = str(uuid4())
    store = InMemoryStore()
    store.school_profile_versions[(USER_ID, "worker-profile")] = {
        "user_id": USER_ID,
        "profile_version_id": "worker-profile",
        "status": "active",
    }
    await store.upsert_school_session(
        session_id=session_id,
        user_id=USER_ID,
        api_version="rebuild",
        flow_type="recap",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="0",
        linked_session_id=None,
        profile_version_id="worker-profile",
        source_placement_report_id="worker-placement",
        state_json=state,
    )
    answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    claim = await store.claim_school_answer_request(
        USER_ID,
        session_id,
        activity["activity_id"],
        answer_hash,
    )
    queued = await store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=session_id,
        activity_id=activity["activity_id"],
        raw_answer=answer,
        expected_state_json=state,
        answer_hash=answer_hash,
        answer_claim_token=claim["claim_token"],
        flow_type="recap",
        evaluation_mode="llm_rubric",
        max_attempts=2,
    )
    assert queued["outcome"] == "queued"
    return store, state, queued["job"], session_id, answer


async def _seed_queued_placement_job() -> tuple[
    InMemoryStore,
    dict,
    dict,
    str,
    str,
]:
    profile = {
        "profile_version_id": "worker-profile",
        "target_class_no": 5,
        "subject_ids": ["english"],
        "preferred_teaching_language": "en",
        "prior_difficulty_signals": [],
    }
    envelope = placement.new_placement_envelope(profile)
    while envelope.state.stage == "snapshot":
        snapshot_item = placement.next_item(envelope)
        assert snapshot_item is not None
        envelope = placement.apply_evaluated_attempt(
            envelope,
            snapshot_item,
            evaluator_score=(
                0.7
                if snapshot_item.track_id == "english.c5.inference"
                else 1.0
            ),
            evaluator_confidence=1.0,
        )
    item = placement.next_item(envelope)
    assert item is not None
    assert item.track_id == "english.c5.inference"
    assert item.evaluation_mode == "strict_rubric"
    state = placement.envelope_to_json(envelope)
    state["_placement_item_timing"] = {
        "item_id": item.item_id,
        "presented_at": "2026-07-19T00:00:00+00:00",
        "retry_pending": False,
        "accrued_learner_seconds": 0.0,
    }
    answer = (
        "The team became quiet because the bowler began, and every player leaned "
        "forward for the final run."
    )
    session_id = str(uuid4())
    store = InMemoryStore()
    store.school_profile_versions[(USER_ID, "worker-profile")] = {
        "user_id": USER_ID,
        "profile_version_id": "worker-profile",
        "status": "active",
    }
    await store.upsert_school_session(
        session_id=session_id,
        user_id=USER_ID,
        api_version="rebuild",
        flow_type="placement",
        subject_id="english",
        class_no=5,
        status="active",
        current_stage="targeted_diagnostic",
        linked_session_id=None,
        profile_version_id="worker-profile",
        source_placement_report_id=None,
        state_json=state,
    )
    answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
    claim = await store.claim_school_answer_request(
        USER_ID,
        session_id,
        item.item_id,
        answer_hash,
    )
    queued = await store.enqueue_school_evaluation_job(
        user_id=USER_ID,
        session_id=session_id,
        activity_id=item.item_id,
        raw_answer=answer,
        expected_state_json=state,
        answer_hash=answer_hash,
        answer_claim_token=claim["claim_token"],
        flow_type="placement",
        evaluation_mode="strict_rubric",
        max_attempts=2,
        request_metadata={"learner_elapsed_seconds": 17.0},
    )
    assert queued["outcome"] == "queued"
    return store, state, queued["job"], session_id, answer


@pytest.mark.asyncio
async def test_queued_curriculum_evaluation_advances_once_in_its_atomic_commit(
    monkeypatch,
):
    store, original_state, _queued, session_id, answer = (
        await _seed_queued_curriculum_job()
    )
    observed_activity: dict | None = None

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        nonlocal observed_activity
        assert learner_answer == answer
        observed_activity = dict(activity)
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.92,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.92,
                    evidence_quote=answer[:80],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    )

    assert processed is True
    assert observed_activity is not None
    assert observed_activity["evaluation_mode"] == "llm_rubric"
    stored = await store.get_school_session(USER_ID, session_id)
    job = await store.get_school_evaluation_job(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    request = await store.get_school_answer_request(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    assert stored["state_json"] != original_state
    assert stored["state_json"]["last_feedback"]["correct"] is True
    assert job["status"] == "completed"
    assert request["status"] == "completed"
    assert request["response_json"] == job["response_json"]
    assert len(store.learning_events) == 1

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is False
    assert len(store.learning_events) == 1


@pytest.mark.asyncio
async def test_queued_curriculum_worker_prefers_the_bulk_evaluated_persister(
    monkeypatch,
):
    """A leased open answer uses the low-round-trip finalizer when available."""

    store, _state, _queued, _session_id, answer = await _seed_queued_curriculum_job()
    generic_persist = store.persist_school_curriculum_attempt
    optimized_calls: list[dict] = []

    async def optimized_persist(**kwargs):
        optimized_calls.append(kwargs)
        return await generic_persist(**kwargs)

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        assert learner_answer == answer
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.92,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.92,
                    evidence_quote=answer[:80],
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The response meets the authored criteria.",
        )

    store.persist_school_evaluated_curriculum_attempt = optimized_persist
    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is True

    assert len(optimized_calls) == 1
    assert optimized_calls[0]["evaluation_job_completion"]["lease_owner"]


@pytest.mark.asyncio
async def test_queued_masterclass_evaluation_advances_child_once_in_its_atomic_commit(
    monkeypatch,
):
    store, original_state, _queued, session_id, answer = (
        await _seed_queued_masterclass_job()
    )
    observed_activity: dict | None = None

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        nonlocal observed_activity
        assert learner_answer == answer
        observed_activity = dict(activity)
        evidence_quotes = [
            "Priya asks how to find the cart.",
            "The guard says to note the number and call the depot.",
            "Priya says she can see the number.",
            "The guard tells her to write it down.",
        ]
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.92,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.92,
                    evidence_quote=evidence_quotes[index],
                )
                for index, criterion in enumerate(activity["rubric_criteria"])
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The dialogue meets the authored criteria.",
        )

    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    )

    assert processed is True
    assert observed_activity is not None
    assert observed_activity["remediation_phase"] == "independent_check"
    stored = await store.get_school_session(USER_ID, session_id)
    job = await store.get_school_evaluation_job(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    request = await store.get_school_answer_request(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    assert stored["state_json"] != original_state
    assert stored["state_json"]["phase_index"] == 3
    assert stored["state_json"]["last_feedback"]["correct"] is True
    assert job["status"] == "completed"
    assert request["status"] == "completed"
    assert request["response_json"] == job["response_json"]
    assert [event["task_type"] for event in store.learning_events] == [
        "school_rebuild_masterclass"
    ]
    assert [event["attempt_type"] for event in store.learning_events] == [
        "independent_check"
    ]

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is False
    assert len(store.learning_events) == 1


@pytest.mark.asyncio
async def test_queued_recap_evaluation_advances_once_in_its_atomic_commit(monkeypatch):
    store, original_state, _queued, session_id, answer = await _seed_queued_recap_job()
    observed_activity: dict | None = None

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        nonlocal observed_activity
        assert learner_answer == answer
        observed_activity = dict(activity)
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.92,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.92,
                    evidence_quote=(
                        "It probably rained" if index == 0 else "drops on his hair"
                    ),
                )
                for index, criterion in enumerate(activity["rubric_criteria"])
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The explanation uses a clue from the passage.",
        )

    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    )

    assert processed is True
    assert observed_activity is not None
    assert observed_activity["evaluation_mode"] == "llm_rubric"
    stored = await store.get_school_session(USER_ID, session_id)
    job = await store.get_school_evaluation_job(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    request = await store.get_school_answer_request(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    assert stored["state_json"] != original_state
    assert stored["state_json"]["last_feedback"]["correct"] is True
    assert job["status"] == "completed"
    assert request["status"] == "completed"
    assert request["response_json"] == job["response_json"]
    assert [event["task_type"] for event in store.learning_events] == [
        "school_rebuild_recap"
    ]

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is False
    assert len(store.learning_events) == 1


@pytest.mark.asyncio
async def test_queued_placement_evaluation_advances_once_with_arrival_time(
    monkeypatch,
):
    store, original_state, _queued, session_id, answer = (
        await _seed_queued_placement_job()
    )
    observed_activity: dict | None = None

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        nonlocal observed_activity
        assert learner_answer == answer
        observed_activity = dict(activity)
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.92,
            confidence=0.95,
            language_detected="en",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=True,
                    quality=0.92,
                    evidence_quote=answer,
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=[],
            needs_human_review=False,
            feedback_to_learner="The explanation uses evidence from the passage.",
        )

    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    processed = await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    )

    assert processed is True
    assert observed_activity is not None
    stored = await store.get_school_session(USER_ID, session_id)
    job = await store.get_school_evaluation_job(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    request = await store.get_school_answer_request(
        USER_ID, session_id, observed_activity["activity_id"]
    )
    updated = placement.envelope_from_json(stored["state_json"])
    assert stored["state_json"] != original_state
    assert updated.state.elapsed_seconds == 17.0
    assert job["status"] == "completed"
    assert request["status"] == "completed"
    assert request["response_json"] == job["response_json"]
    assert [event["task_type"] for event in store.learning_events][-1:] == [
        "school_rebuild_placement"
    ]

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is False
    # The snapshot evidence above creates the placement state directly; only
    # the queued strict diagnostic is a persisted worker transition here.
    assert len(store.learning_events) == 1


@pytest.mark.asyncio
async def test_queued_placement_language_mismatch_releases_the_same_item_with_saved_time(
    monkeypatch,
):
    store, original_state, _queued, session_id, answer = (
        await _seed_queued_placement_job()
    )

    async def evaluate(activity: dict, learner_answer: str, **_kwargs):
        assert learner_answer == answer
        return SchoolV3RubricEvaluation(
            schema_version="school.open.v1",
            item_id=activity["activity_id"],
            skill_ids=list(activity["skill_ids"]),
            score=0.0,
            confidence=0.95,
            language_detected="hi",
            criteria=[
                SchoolV3RubricCriterion(
                    id=criterion["id"],
                    met=False,
                    quality=0.0,
                    evidence_quote=answer,
                )
                for criterion in activity["rubric_criteria"]
            ],
            misconception_tags=[],
            blockers=["language_mismatch"],
            needs_human_review=False,
            feedback_to_learner="Please try this check in English.",
        )

    monkeypatch.setattr(school_rebuild_routes, "get_storage", lambda: store)
    monkeypatch.setattr(school_rebuild_routes, "evaluate_school_open_answer", evaluate)

    assert await evaluation_jobs.run_one_school_evaluation_job(
        store=store,
        processor=school_rebuild_routes.process_school_evaluation_job,
        max_attempts=2,
    ) is True

    stored = await store.get_school_session(USER_ID, session_id)
    job = await store.get_school_evaluation_job(
        USER_ID,
        session_id,
        _queued["activity_id"],
    )
    request = await store.get_school_answer_request(
        USER_ID,
        session_id,
        _queued["activity_id"],
    )

    expected_state = copy.deepcopy(original_state)
    expected_state["_placement_item_timing"] = {
        "item_id": _queued["activity_id"],
        "presented_at": stored["state_json"]["_placement_item_timing"]["presented_at"],
        "retry_pending": True,
        "accrued_learner_seconds": 17.0,
    }
    assert stored["state_json"] == expected_state
    assert job["status"] == "failed"
    assert job["last_error_code"] == "placement_english_response_required"
    assert request["status"] == "failed"
    assert store.learning_events == []
