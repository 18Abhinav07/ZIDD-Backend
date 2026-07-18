import asyncio

import pytest

from app.db import repo
from app.services import school_rebuild_curriculum as curriculum
from app.services.school_rebuild_learning import (
    SCHOOL_DOMAIN,
    SchoolLearningProfileService,
    build_school_memory_context,
)
from app.services.school.projection import (
    SchoolAttemptEvidence,
    derive_school_projection_delta,
    enrich_school_projection_evidence,
)
from app.services.school_core.readiness import (
    SkillReadinessState,
    to_profile_upsert,
)


class MemoryStore:
    def __init__(self):
        self.profiles: dict[str, dict] = {}

    async def get_learning_graph(self, user_id: str) -> dict:
        return {
            "profiles": list(self.profiles.values()),
            "reports": [],
            "events": [],
        }

    async def get_school_learning_graph(self, user_id: str) -> dict:
        return await self.get_learning_graph(user_id)

    async def upsert_learner_skill_profile(self, **row) -> None:
        self.profiles[row["skill_id"]] = {**row, "domain": row["domain"]}


def _record(
    service: SchoolLearningProfileService,
    *,
    score: float,
    kind: str = "transfer_check",
) -> None:
    asyncio.run(service.record_curriculum_attempt(
        user_id="learner-1",
        session_id="curriculum-1",
        chapter_id="eng_c3_ch01",
        level_id="colour_sharing_reason",
        focus="answer with a reason",
        skill_ids=["reading.inference_reason", "writing.reason_answer"],
        attempt_type=kind,
        score=score,
        confidence=1.0,
        criteria=[{"id": "answer_match", "met": score >= 0.8}],
        blockers=[] if score >= 0.8 else ["curriculum_gap"],
        answer_excerpt="They should share because both need more colours.",
        attempt_passed=score >= 0.8,
        chapter_certified=False,
    ))


def test_school_attempts_update_each_taxonomy_skill_without_granting_mastery():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)

    _record(service, score=0.0)
    _record(service, score=1.0)

    assert set(store.profiles) == {
        "reading.inference_reason",
        "writing.reason_answer",
    }
    for profile in store.profiles.values():
        assert profile["domain"] == SCHOOL_DOMAIN
        assert profile["attempts"] == 2
        assert 0.4 <= profile["readiness"] <= 0.5
        assert profile["mastery"] == 0.0
        assert profile["evidence_json"]["attempt_type"] == "transfer_check"


def test_chapter_certification_records_evidence_but_not_readiness_or_mastery():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)
    _record(service, score=1.0, kind="bridge")
    assert all(profile["mastery"] == 0.0 for profile in store.profiles.values())

    asyncio.run(service.record_curriculum_attempt(
        user_id="learner-1",
        session_id="curriculum-1",
        chapter_id="eng_c3_ch01",
        level_id="chapter_check",
        focus="chapter evidence",
        skill_ids=["reading.inference_reason"],
        attempt_type="chapter_check",
        score=1.0,
        confidence=1.0,
        criteria=[{"id": "chapter_check", "met": True}],
        blockers=[],
        answer_excerpt="because both children need colours",
        attempt_passed=True,
        chapter_certified=True,
    ))
    profile = store.profiles["reading.inference_reason"]
    assert profile["readiness"] == 1.0
    assert profile["mastery"] == 0.0
    assert profile["evidence_json"]["skill_status"] == "practice_ready"


def test_supported_revision_success_improves_but_cannot_clear_or_strengthen_a_gap():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)

    _record(service, score=0.0, kind="transfer_check")
    _record(service, score=1.0, kind="revision_level_1")

    profile = store.profiles["reading.inference_reason"]
    context = build_school_memory_context({"profiles": [profile]})
    assert profile["gaps_json"] == ["answer with a reason"]
    assert profile["strengths_json"] == []
    assert profile["readiness"] < 0.85
    assert context["strong_skills"] == []

    for _ in range(3):
        _record(service, score=1.0, kind="independent_check")
    profile = store.profiles["reading.inference_reason"]
    assert profile["gaps_json"] == []
    assert profile["strengths_json"] == ["answer with a reason"]


def test_gated_high_score_remains_a_gap_instead_of_becoming_a_strength():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)

    asyncio.run(service.record_curriculum_attempt(
        user_id="learner-1",
        session_id="curriculum-1",
        chapter_id="eng_c5_ch01",
        level_id="chapter_assessment",
        focus="summarise without inventing details",
        skill_ids=["writing.summary_own_words"],
        attempt_type="chapter_check",
        score=0.88,
        confidence=0.95,
        criteria=[{
            "id": "summary_source_accuracy",
            "met": False,
            "quality": 0.5,
        }],
        blockers=["needs_human_review"],
        answer_excerpt="A teacher rewarded Renu before she returned the notebook.",
        attempt_passed=False,
        chapter_certified=False,
    ))

    profile = store.profiles["writing.summary_own_words"]
    context = build_school_memory_context({"profiles": [profile]})
    assert context["strong_skills"] == []
    assert [item["skill_id"] for item in context["active_gaps"]] == [
        "writing.summary_own_words"
    ]
    assert profile["gaps_json"] == ["summarise without inventing details"]
    assert profile["recommended_next_action"] == (
        "Rebuild this skill: summarise without inventing details."
    )


def test_chapter_certification_projects_every_assessed_skill_not_only_last_item():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)

    asyncio.run(service.record_chapter_certification(
        user_id="learner-1",
        session_id="curriculum-1",
        chapter_id="eng_c3_ch01",
        skill_scores={
            "reading.inference_reason": 0.9,
            "writing.reason_answer": 0.85,
            "grammar.connectors_because_and_but": 0.65,
        },
    ))

    assert set(store.profiles) == {
        "reading.inference_reason",
        "writing.reason_answer",
        "grammar.connectors_because_and_but",
    }
    assert store.profiles["reading.inference_reason"]["mastery"] == 0.0
    assert store.profiles["writing.reason_answer"]["mastery"] == 0.0
    assert store.profiles["grammar.connectors_because_and_but"]["mastery"] == 0.0
    assert all(
        profile["evidence_json"]["attempt_type"] == "chapter_check"
        for profile in store.profiles.values()
    )


def test_chapter_certification_preserves_latest_real_learner_answer():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)
    _record(service, score=1.0, kind="transfer_check")

    asyncio.run(service.record_chapter_certification(
        user_id="learner-1",
        session_id="curriculum-1",
        chapter_id="eng_c3_ch01",
        skill_scores={"reading.inference_reason": 0.9},
    ))

    profile = store.profiles["reading.inference_reason"]
    evidence = profile["evidence_json"]
    assert evidence["latest_quote"] == (
        "They should share because both need more colours."
    )
    assert evidence["attempt_type"] == "transfer_check"
    assert evidence["latest_certification"] == {
        "session_id": "curriculum-1",
        "chapter_id": "eng_c3_ch01",
        "score": 0.9,
    }
    assert profile["mastery"] == 0.0
    assert evidence["skill_status"] == "practice_ready"


def test_reconciliation_certification_ledger_preserves_newer_latest_certification():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)
    _record(service, score=1.0, kind="transfer_check")
    profile = store.profiles["reading.inference_reason"]
    profile["evidence_json"]["latest_certification"] = {
        "session_id": "newer-session",
        "chapter_id": "eng_c3_ch02",
        "score": 0.97,
    }

    for _ in range(2):
        asyncio.run(service.record_chapter_certification(
            user_id="learner-1",
            session_id="historic-repair-session",
            chapter_id="eng_c3_ch01",
            skill_scores={"reading.inference_reason": 0.9},
        ))

    evidence = store.profiles["reading.inference_reason"]["evidence_json"]
    assert evidence["latest_certification"] == {
        "session_id": "newer-session",
        "chapter_id": "eng_c3_ch02",
        "score": 0.97,
    }
    assert evidence["reconciliation_certification_ledger"] == {
        "historic-repair-session:eng_c3_ch01": {
            "session_id": "historic-repair-session",
            "chapter_id": "eng_c3_ch01",
            "score": 0.9,
        }
    }


def test_reconciliation_certification_ledger_keeps_release_sized_history():
    store = MemoryStore()
    service = SchoolLearningProfileService(store)

    for chapter_no in range(65):
        asyncio.run(service.record_chapter_certification(
            user_id="learner-1",
            session_id=f"historic-session-{chapter_no}",
            chapter_id=f"eng_c5_ch{chapter_no:02d}",
            skill_scores={"reading.inference_reason": 0.9},
        ))

    ledger = store.profiles["reading.inference_reason"]["evidence_json"][
        "reconciliation_certification_ledger"
    ]
    assert len(ledger) == 64
    assert "historic-session-0:eng_c5_ch00" not in ledger
    assert "historic-session-64:eng_c5_ch64" in ledger


def test_postgres_reconciliation_certification_projection_uses_answer_lock_and_one_commit():
    class ProfileRows:
        def mappings(self):
            return self

        def all(self):
            return [{
                "user_id": "learner-1",
                "domain": "school",
                "skill_id": "reading.inference_reason",
                "module_id": "eng_c3_ch01",
                "task_type": "school_rebuild_curriculum",
                "mastery": 0.0,
                "readiness": 0.0,
                "confidence": 1.0,
                "attempts": 0,
                "strengths_json": [],
                "gaps_json": [],
                "evidence_json": {},
                "recommended_next_action": "",
                "source_summary": "",
            }]

    class EmptyResult:
        pass

    class FakeSession:
        def __init__(self):
            self.calls: list[tuple[str, dict]] = []
            self.commits = 0
            self.rollbacks = 0

        async def execute(self, statement, params):
            sql = str(statement)
            self.calls.append((sql, dict(params)))
            if "FROM learner_skill_profiles" in sql:
                return ProfileRows()
            return EmptyResult()

        async def commit(self):
            self.commits += 1

        async def rollback(self):
            self.rollbacks += 1

    session = FakeSession()
    asyncio.run(repo.reconcile_school_chapter_certification_projection(
        session,
        user_id="learner-1",
        projection_evidence={
            "session_id": "historic-session",
            "chapter_id": "eng_c3_ch01",
            "level_id": "chapter_assessment",
            "module_id": "eng_c3_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "chapter assessment reconciliation",
            "skill_ids": [],
            "attempt_type": "chapter_check",
            "score": 0.0,
            "confidence": 1.0,
            "criteria": [],
            "blockers": [],
            "answer_excerpt": "",
            "attempt_passed": False,
            "certified_skill_scores": {"reading.inference_reason": 0.9},
            "preserve_latest_evidence": True,
            "reconciliation_certification": True,
        },
    ))

    lock_sql, lock_params = session.calls[0]
    assert "zidd_school_answer:" in lock_sql
    assert lock_params == {"uid": "learner-1"}
    profile_lock_sql = next(
        sql for sql, _params in session.calls if "FROM learner_skill_profiles" in sql
    )
    assert "domain = 'school'" in profile_lock_sql
    assert "FOR UPDATE" in profile_lock_sql
    assert sum(
        "INSERT INTO learner_skill_profiles" in sql
        for sql, _params in session.calls
    ) == 1
    assert session.commits == 1
    assert session.rollbacks == 0


def test_chapter_certification_uses_atomic_storage_projection_when_available():
    class AtomicStore(MemoryStore):
        def __init__(self):
            super().__init__()
            self.calls: list[dict] = []

        async def reconcile_school_chapter_certification_projection(self, **kwargs):
            self.calls.append(kwargs)

    store = AtomicStore()
    asyncio.run(SchoolLearningProfileService(store).record_chapter_certification(
        user_id="learner-1",
        session_id="historic-session",
        chapter_id="eng_c3_ch01",
        skill_scores={"reading.inference_reason": 0.9},
    ))

    assert store.calls == [{
        "user_id": "learner-1",
        "projection_evidence": {
            "session_id": "historic-session",
            "chapter_id": "eng_c3_ch01",
            "level_id": "chapter_assessment",
            "module_id": "eng_c3_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "chapter assessment reconciliation",
            "skill_ids": [],
            "attempt_type": "chapter_check",
            "score": 0.0,
            "confidence": 1.0,
            "criteria": [],
            "blockers": [],
            "answer_excerpt": "",
            "attempt_passed": False,
            "certified_skill_scores": {"reading.inference_reason": 0.9},
            "preserve_latest_evidence": True,
            "reconciliation_certification": True,
        },
    }]


@pytest.mark.parametrize(
    ("certification_score", "expected_mastery", "expected_readiness"),
    [(0.65, 0.0, 0.72), (0.90, 0.0, 0.72)],
)
def test_chapter_certification_preserves_unrelated_skill_metadata(
    certification_score,
    expected_mastery,
    expected_readiness,
):
    prior = {
        "domain": SCHOOL_DOMAIN,
        "skill_id": "reading.inference_reason",
        "module_id": "eng_c3_ch01",
        "task_type": "school_rebuild_curriculum",
        "mastery": 0.4,
        "readiness": 0.72,
        "confidence": 0.95,
        "attempts": 4,
        "strengths_json": ["infer from clues"],
        "gaps_json": [],
        "evidence_json": {
            "session_id": "prior-session",
            "chapter_id": "eng_c3_ch01",
            "attempt_type": "transfer_check",
            "latest_quote": "The clue shows why the character shared.",
        },
        "recommended_next_action": "Explain one more inference independently.",
        "source_summary": "Strong inference evidence in eng_c3_ch01.",
    }
    evidence = SchoolAttemptEvidence.from_dict({
        "session_id": "current-session",
        "chapter_id": "eng_c3_ch02",
        "level_id": "chapter_check",
        "module_id": "eng_c3_ch02",
        "task_type": "school_rebuild_curriculum",
        "focus": "use past-tense verbs",
        "skill_ids": ["grammar.past_tense"],
        "attempt_type": "chapter_check",
        "score": 0.85,
        "confidence": 0.61,
        "criteria": [{"id": "past_tense", "met": True}],
        "blockers": [],
        "answer_excerpt": "She walked home after school.",
        "attempt_passed": True,
        "certified_skill_scores": {
            "grammar.past_tense": 0.85,
            "reading.inference_reason": certification_score,
        },
    })

    projected = derive_school_projection_delta(evidence, [prior])
    reading = next(
        row for row in projected
        if row["skill_id"] == "reading.inference_reason"
    )

    assert reading["mastery"] == expected_mastery
    assert reading["readiness"] == expected_readiness
    assert reading["evidence_json"] == {
        **prior["evidence_json"],
        "latest_certification": {
            "session_id": "current-session",
            "chapter_id": "eng_c3_ch02",
            "score": certification_score,
        },
    }
    for field in (
        "module_id",
        "task_type",
        "confidence",
        "attempts",
        "strengths_json",
        "gaps_json",
        "recommended_next_action",
        "source_summary",
    ):
        assert reading[field] == prior[field]


def test_public_curriculum_memory_includes_mastered_skills_as_confirmed_strengths():
    summary = curriculum._public_memory_summary({
        "active_gaps": [],
        "improving_gaps": [],
        "strong_skills": [],
        "mastered_skills": [{
            "skill_id": "reading.inference_reason",
            "skill_status": "mastered",
            "readiness": 0.96,
            "mastery": 0.96,
            "confidence": 1.0,
            "latest_evidence": "I used the clue and explained the reason.",
            "last_attempt_type": "transfer_check",
            "last_chapter_id": "eng_c5_ch01",
            "attempts": 4,
            "certifying_attempts": 4,
            "independent_passes": 3,
            "transfer_passes": 1,
            "review_passes": 1,
            "chapter_passes": 1,
            "active_blockers": [],
        }],
    })

    assert summary["strong_skill_ids"] == ["reading.inference_reason"]
    assert summary["strong_skills"] == [{
        "skill_id": "reading.inference_reason",
        "skill_label": "Infer a reason",
        "skill_status": "mastered",
        "readiness": 0.96,
        "mastery": 0.96,
        "confidence": 1.0,
        "latest_evidence": "I used the clue and explained the reason.",
        "last_attempt_type": "transfer_check",
        "last_chapter_id": "eng_c5_ch01",
        "attempts": 4,
        "certifying_attempts": 4,
        "independent_passes": 3,
        "transfer_passes": 1,
        "review_passes": 1,
        "chapter_passes": 1,
        "active_blockers": [],
    }]


def test_public_curriculum_memory_exposes_truthful_attempt_breakdown_for_reports():
    practice_ready = to_profile_upsert(SkillReadinessState(
        skill_id="reading.sentence_comprehension",
        practice_readiness=0.96,
        certified_readiness=0.99,
        total_attempts=14,
        certified_attempts=4,
        independent_passes=1,
        transfer_passes=1,
        review_passes=1,
        chapter_passes=1,
        recent_hint_flags=(False, False, False, False, False),
        last_confidence=1.0,
    ))
    memory = build_school_memory_context({
        "profiles": [{
            "domain": SCHOOL_DOMAIN,
            "skill_id": "reading.sentence_comprehension",
            "readiness": practice_ready["readiness"],
            "mastery": practice_ready["mastery"],
            "confidence": 1.0,
            "attempts": 14,
            "gaps_json": ["understand events and explain the clue"],
            "evidence_json": {
                "attempt_type": "chapter_check",
                "latest_quote": "beside the library lamp",
                "school_readiness_state": practice_ready["school_readiness_state"],
                "skill_status": practice_ready["skill_status"],
            },
            "recommended_next_action": "Try one more independent example.",
        }],
    })

    summary = curriculum._public_memory_summary(memory)

    [skill] = summary["improving_skills"]
    assert skill == {
        "skill_id": "reading.sentence_comprehension",
        "skill_label": "Understand sentence meaning",
        "skill_status": "practice_ready",
        "readiness": 0.96,
        "mastery": 0.0,
        "confidence": 1.0,
        "latest_evidence": "beside the library lamp",
        "last_attempt_type": "chapter_check",
        "last_chapter_id": "",
        "attempts": 14,
        "certifying_attempts": 4,
        "independent_passes": 1,
        "transfer_passes": 1,
        "review_passes": 1,
        "chapter_passes": 1,
        "active_blockers": [],
    }


def test_school_memory_context_excludes_career_profiles_and_surfaces_active_gaps():
    context = build_school_memory_context({
        "profiles": [
            {
                "domain": SCHOOL_DOMAIN,
                "skill_id": "reading.inference_reason",
                "readiness": 0.3,
                "mastery": 0.0,
                "confidence": 0.8,
                "attempts": 3,
                "gaps_json": ["answer with a reason"],
                "evidence_json": {"latest_quote": "The learner omitted the reason."},
                "recommended_next_action": "Use because and a passage clue.",
            },
            {
                "domain": "career",
                "skill_id": "int_04_star_behavioral",
                "readiness": 0.1,
            },
        ]
    })

    assert [item["skill_id"] for item in context["active_gaps"]] == [
        "reading.inference_reason"
    ]
    assert context["active_gaps"][0]["latest_evidence"] == (
        "The learner omitted the reason."
    )


def test_school_memory_context_preserves_misconceptions_for_next_session():
    context = build_school_memory_context({
        "profiles": [{
            "domain": SCHOOL_DOMAIN,
            "skill_id": "reading.inference_reason",
            "readiness": 0.3,
            "mastery": 0.0,
            "confidence": 0.8,
            "attempts": 3,
            "gaps_json": ["support a reason with a passage clue"],
            "evidence_json": {
                "latest_quote": "I think the character was worried.",
                "misconception_tags": ["reason_without_clue"],
                "criteria": [
                    {"id": "passage_clue", "met": False, "quality": 0.2},
                ],
                "support_used": ["bridge"],
            },
            "recommended_next_action": "Use one visible clue with the reason.",
        }]
    })

    [gap] = context["active_gaps"]
    assert gap["misconception_tags"] == ["reason_without_clue"]
    assert gap["criterion_gap_ids"] == ["passage_clue"]
    assert gap["support_used"] == ["bridge"]


def test_next_chapter_seeds_prior_misconception_for_variant_targeting(monkeypatch):
    chapter = curriculum.CLASS_5_CURRICULUM_CHAPTERS[0]
    skill_id = chapter["levels"][0]["skill_ids"][0]
    target_tag = "reason_without_clue"
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )

    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 5},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
        learning_memory={
            "active_gaps": [{
                "skill_id": skill_id,
                "gap": "support a reason with a passage clue",
                "misconception_tags": [target_tag],
                "criterion_gap_ids": ["passage_clue"],
            }],
            "improving_gaps": [],
            "strong_skills": [],
            "mastered_skills": [],
        },
    )

    assert state["hot_session_memory"]["unresolved_misconception_tags"] == [
        target_tag,
        "criterion:passage_clue",
    ]
    selected, variant_id, fresh = curriculum._v2_step_activity(
        state,
        {"used_variant_ids": []},
        {
            "variant_pool": [
                {
                    "variant_id": "neutral-first",
                    "passage": "A neutral fresh passage.",
                    "prompt": "Answer the neutral question.",
                    "target_misconception_tags": ["different_gap"],
                },
                {
                    "variant_id": "prior-gap-second",
                    "passage": "A second fresh passage.",
                    "prompt": "Use one visible clue to explain your reason.",
                    "target_misconception_tags": [target_tag],
                },
            ]
        },
    )
    assert fresh is True
    assert variant_id == "prior-gap-second"
    assert selected["target_misconception_tags"] == [target_tag]


def test_legacy_mastery_scalar_is_only_a_historical_hint():
    context = build_school_memory_context({
        "profiles": [{
            "domain": SCHOOL_DOMAIN,
            "skill_id": "reading.inference_reason",
            "readiness": 0.3,
            "mastery": 0.96,
            "confidence": 0.8,
            "attempts": 3,
            "gaps_json": ["answer with a reason"],
            "evidence_json": {},
        }]
    })

    assert context["mastered_skills"] == []
    assert context["active_gaps"][0]["skill_id"] == "reading.inference_reason"


def test_school_memory_context_prefers_latest_ledger_answer_over_cached_summary():
    mastered = to_profile_upsert(SkillReadinessState(
        skill_id="reading.inference_reason",
        practice_readiness=0.95,
        certified_readiness=0.95,
        total_attempts=6,
        certified_attempts=5,
        independent_passes=3,
        transfer_passes=1,
        review_passes=1,
        recent_hint_flags=(False, False, False, False, False),
        last_confidence=1.0,
    ))
    context = build_school_memory_context({
        "profiles": [{
            "domain": SCHOOL_DOMAIN,
            "skill_id": "reading.inference_reason",
            "readiness": 1.0,
            "mastery": 1.0,
            "confidence": 1.0,
            "attempts": 6,
            "gaps_json": [],
            "evidence_json": {
                "latest_quote": (
                    "Chapter assessment aggregate for reading.inference_reason"
                ),
                "attempt_type": "chapter_check",
                "chapter_id": "eng_c5_ch01",
                "school_readiness_state": mastered["school_readiness_state"],
                "skill_status": mastered["skill_status"],
            },
            "recommended_next_action": "Start the next chapter.",
        }],
        "events": [{
            "domain": SCHOOL_DOMAIN,
            "skill_id": "writing.reason_answer",
            "attempt_type": "chapter_check",
            "module_id": "eng_c5_ch01",
            "criteria_json": [{
                "id": "answer_match",
                "met": True,
                "evidence_quote": (
                    "He searched because he had forgotten the spectacles were on his head."
                ),
            }],
            "evidence_json": {
                "skill_ids": [
                    "reading.inference_reason",
                    "writing.reason_answer",
                ],
                "chapter_id": "eng_c5_ch01",
            },
        }],
    })

    assert context["mastered_skills"][0]["latest_evidence"] == (
        "He searched because he had forgotten the spectacles were on his head."
    )
    assert context["mastered_skills"][0]["last_attempt_type"] == "chapter_check"
    assert context["mastered_skills"][0]["last_chapter_id"] == "eng_c5_ch01"


def test_next_chapter_uses_school_memory_for_support_copy_not_progression(monkeypatch):
    chapter = curriculum.CLASS_3_CURRICULUM_CHAPTERS[0]
    first_level_skill_id = chapter["levels"][0]["skill_ids"][0]
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={"subject_ids": ["english"], "target_class_no": 3},
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
        learning_memory={
            "active_gaps": [{
                "skill_id": first_level_skill_id,
                "gap": "answer with a reason",
                "recommended_next_action": "Use because and one passage clue.",
            }],
            "improving_gaps": [],
            "strong_skills": [],
            "mastered_skills": [],
        },
    )

    activity = None
    for step_index in range(len(state["levels"][0]["teaching_steps"])):
        state["levels"][0]["v2_step_index"] = step_index
        candidate = curriculum._current_activity(state)
        if candidate and candidate.get("skill_ids"):
            activity = candidate
            break
    assert activity is not None
    assert "Zidd remembers" in activity["teaching_block"]
    assert "answer with a reason" not in activity["teaching_block"]
    assert "Use because and one passage clue" not in activity["teaching_block"]
    assert state["levels"][0]["focus"] in activity["teaching_block"]
    assert state["levels"][0]["status"] == "in_progress"
    assert state["current_level_index"] == 0


def test_curriculum_carries_hinglish_preference_into_teaching_not_progression(monkeypatch):
    chapter = curriculum.CLASS_3_CURRICULUM_CHAPTERS[0]
    monkeypatch.setattr(
        curriculum,
        "_available_chapters",
        lambda subject_id, class_no: (chapter,),
    )
    state = curriculum.new_curriculum_state(
        school_profile={
            "subject_ids": ["english"],
            "target_class_no": 3,
            "preferred_teaching_language": "hi_en",
        },
        placement_report={
            "report_id": "placement-report",
            "unlock_state": "target_unlocked",
            "watchlist_skills": [],
        },
        recap_session=None,
    )

    activity = curriculum._current_activity(state)

    assert state["preferred_teaching_language"] == "hi_en"
    assert "mushkil" in activity["teaching_block"].lower()
    assert "padho" in activity["teaching_block"].lower()
    assert state["levels"][0]["current_step"] == chapter["levels"][0][
        "teaching_steps"
    ][0]["phase"]


@pytest.mark.parametrize(
    ("attempt_type", "counter"),
    [
        ("v2_independent_application", "independent_passes"),
        ("v2_transfer", "transfer_passes"),
        ("v2_review", "review_passes"),
    ],
)
def test_activity_v2_certifying_phases_update_canonical_readiness_counters(
    attempt_type: str,
    counter: str,
):
    evidence = SchoolAttemptEvidence.from_dict(
        {
            "session_id": "curriculum-v2",
            "chapter_id": "eng_c5_ch01",
            "level_id": "chapter-one-skill",
            "module_id": "eng_c5_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "use the skill independently",
            "skill_ids": ["reading.inference_reason"],
            "attempt_type": attempt_type,
            "score": 0.9,
            "confidence": 0.9,
            "criteria": [{"id": "evidence", "met": True}],
            "blockers": [],
            "answer_excerpt": "The clue supports the answer.",
            "attempt_passed": True,
        }
    )

    [projected] = derive_school_projection_delta(evidence, [])
    readiness_state = projected["evidence_json"]["school_readiness_state"]

    assert readiness_state[counter] == 1
    assert readiness_state["certified_readiness"] is not None


def test_activity_v2_support_is_bridge_evidence_not_guided_certification():
    evidence = SchoolAttemptEvidence.from_dict(
        {
            "session_id": "curriculum-v2",
            "chapter_id": "eng_c5_ch01",
            "level_id": "chapter-one-skill",
            "module_id": "eng_c5_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "use one smaller clue",
            "skill_ids": ["reading.inference_reason"],
            "attempt_type": "v2_support",
            "score": 1.0,
            "confidence": 1.0,
            "criteria": [{"id": "supported_clue", "met": True}],
            "blockers": [],
            "answer_excerpt": "The supported clue points to the table.",
            "attempt_passed": True,
        }
    )

    [projected] = derive_school_projection_delta(evidence, [])
    readiness_state = projected["evidence_json"]["school_readiness_state"]

    assert readiness_state["certified_readiness"] is None
    assert readiness_state["independent_passes"] == 0
    assert readiness_state["practice_readiness"] is not None


def test_projection_uses_committed_language_instead_of_assuming_english():
    evidence = SchoolAttemptEvidence.from_dict(
        {
            "event_identity": "school_rebuild:curriculum:session-1:activity-1",
            "request_identity_hash": "request-hash-1",
            "session_id": "session-1",
            "chapter_id": "eng_c5_ch01",
            "level_id": "reason-level",
            "module_id": "eng_c5_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "explain the reason independently",
            "skill_ids": ["writing.reason_answer"],
            "attempt_type": "v2_independent_application",
            "score": 0.95,
            "confidence": 0.95,
            "criteria": [{"id": "uses_reason", "met": True, "quality": 0.9}],
            "misconception_tags": ["language_support_needed"],
            "blockers": [],
            "support_used": ["hinglish_glossary"],
            "language_detected": "hi",
            "answer_excerpt": "मुझे लगता है कि उसने मदद की।",
            "attempt_passed": True,
        }
    )

    [projected] = derive_school_projection_delta(evidence, [])
    readiness_state = projected["evidence_json"]["school_readiness_state"]

    assert readiness_state["certified_readiness"] is None
    assert readiness_state["independent_passes"] == 0
    assert "language_mismatch" in readiness_state["active_blockers"]
    assert projected["evidence_json"]["language_detected"] == "hi"
    assert projected["evidence_json"]["misconception_tags"] == [
        "language_support_needed"
    ]
    assert projected["evidence_json"]["support_used"] == ["hinglish_glossary"]
    assert projected["evidence_json"]["event_identity"].endswith("activity-1")
    assert projected["evidence_json"]["request_identity_hash"] == "request-hash-1"


def test_projection_envelope_is_derived_from_the_committed_event_identity():
    enriched = enrich_school_projection_evidence(
        {
            "session_id": "session-1",
            "chapter_id": "eng_c5_ch01",
            "level_id": "reason-level",
            "module_id": "eng_c5_ch01",
            "task_type": "school_rebuild_curriculum",
            "focus": "explain the reason",
            "skill_ids": ["writing.reason_answer"],
            "attempt_type": "v2_independent_application",
            "score": 0.9,
            "confidence": 0.9,
            "criteria": [],
            "blockers": [],
            "answer_excerpt": "I used a clue because it explained the action.",
            "attempt_passed": True,
        },
        learning_event={
            "source_event_key": "school:event:1",
            "task_type": "school_rebuild_curriculum",
            "evidence_json": {
                "misconception_tags": ["reason_without_clue"],
                "language_detected": "en",
                "support_mode": "bridge",
            },
        },
        user_id="learner-1",
        session_id="session-1",
        activity_id="activity-1",
        answer_hash="answer-hash-1",
    )

    assert enriched["event_identity"] == "school:event:1"
    assert enriched["misconception_tags"] == ["reason_without_clue"]
    assert enriched["language_detected"] == "en"
    assert enriched["support_used"] == ["bridge"]
    assert len(enriched["request_identity_hash"]) == 64

    replay = enrich_school_projection_evidence(
        enriched,
        learning_event={
            "source_event_key": "school:event:1",
            "task_type": "school_rebuild_curriculum",
            "evidence_json": {},
        },
        user_id="learner-1",
        session_id="session-1",
        activity_id="activity-1",
        answer_hash="answer-hash-1",
    )
    assert replay["request_identity_hash"] == enriched["request_identity_hash"]
