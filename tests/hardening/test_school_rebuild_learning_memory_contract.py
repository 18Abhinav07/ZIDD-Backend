import asyncio

from app.services import school_rebuild_curriculum as curriculum
from app.services.school_rebuild_learning import (
    SCHOOL_DOMAIN,
    SchoolLearningProfileService,
    build_school_memory_context,
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


def test_chapter_certification_can_mark_mastery_but_support_attempts_cannot():
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
    assert store.profiles["reading.inference_reason"]["mastery"] == 1.0


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
    assert store.profiles["reading.inference_reason"]["mastery"] == 1.0
    assert store.profiles["writing.reason_answer"]["mastery"] == 1.0
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
    assert profile["mastery"] == 1.0


def test_public_curriculum_memory_includes_mastered_skills_as_confirmed_strengths():
    summary = curriculum._public_memory_summary({
        "active_gaps": [],
        "improving_gaps": [],
        "strong_skills": [],
        "mastered_skills": [{
            "skill_id": "reading.inference_reason",
            "latest_evidence": "I used the clue and explained the reason.",
            "last_attempt_type": "transfer_check",
            "last_chapter_id": "eng_c5_ch01",
            "attempts": 4,
        }],
    })

    assert summary["strong_skill_ids"] == ["reading.inference_reason"]
    assert summary["strong_skills"] == [{
        "skill_id": "reading.inference_reason",
        "latest_evidence": "I used the clue and explained the reason.",
        "last_attempt_type": "transfer_check",
        "last_chapter_id": "eng_c5_ch01",
        "attempts": 4,
    }]


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


def test_school_memory_context_prefers_latest_ledger_answer_over_cached_summary():
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
                "skill_id": "reading.inference_reason",
                "gap": "answer with a reason",
                "recommended_next_action": "Use because and one passage clue.",
            }],
            "improving_gaps": [],
            "strong_skills": [],
            "mastered_skills": [],
        },
    )

    activity = curriculum._current_activity(state)
    assert "Zidd remembers" in activity["teaching_block"]
    assert "Use because and one passage clue" in activity["teaching_block"]
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
    assert "kyun" in activity["teaching_block"].lower()
    assert state["levels"][0]["current_step"] == "guided_check"
