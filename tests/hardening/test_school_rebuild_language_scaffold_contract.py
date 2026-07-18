from app.content.school.standards import locked_english_taxonomy
from app.services.school_rebuild_language import localized_teaching_support


def test_hinglish_guided_support_teaches_strategy_without_translating_answer():
    support = localized_teaching_support(
        preferred_language="hi_en",
        skill_ids=["reading.inference_reason"],
        stage="guided_check",
    )

    assert "clue" in support.lower()
    assert "kyun" in support.lower()
    assert "answer" not in support.lower() or "English" not in support


def test_chapter_check_adds_no_localized_scaffold():
    for language in ("hi", "hi_en"):
        assert localized_teaching_support(
            preferred_language=language,
            skill_ids=["writing.reason_answer"],
            stage="chapter_check",
        ) == ""


def test_chapter_check_support_never_teaches_the_answer_strategy():
    support = localized_teaching_support(
        preferred_language="hi_en",
        skill_ids=["reading.inference_reason"],
        stage="chapter_check",
    )

    assert support == ""


def test_english_preference_adds_no_duplicate_scaffold():
    assert localized_teaching_support(
        preferred_language="en",
        skill_ids=["writing.reason_answer"],
        stage="bridge",
    ) == ""


def test_language_scaffold_is_meta_support_not_a_readiness_signal():
    support = localized_teaching_support(
        preferred_language="hi_en",
        skill_ids=["grammar.tense_usage"],
        stage="independent_check",
    )

    assert "score" not in support.lower()
    assert "master" not in support.lower()
    assert "English" in support


def test_v2_certifying_phases_keep_the_english_response_requirement():
    for stage in ("independent_application", "transfer", "review"):
        support = localized_teaching_support(
            preferred_language="hi_en",
            skill_ids=["reading.event_sequence"],
            stage=stage,
            en_production_confidence=0.95,
        )

        assert "answer English mein likho" in support


def test_strong_english_evidence_reduces_support_without_changing_certification_copy():
    guided = localized_teaching_support(
        preferred_language="hi_en",
        skill_ids=["grammar.tense_usage"],
        stage="guided_check",
        en_production_confidence=0.9,
    )
    certifying = localized_teaching_support(
        preferred_language="hi_en",
        skill_ids=["grammar.tense_usage"],
        stage="transfer_check",
        en_production_confidence=0.9,
    )

    assert guided == ""
    assert "English" in certifying


def test_every_live_english_skill_has_hindi_and_hinglish_strategy_support():
    skill_ids = locked_english_taxonomy().skill_ids()

    unsupported = [
        (language, skill_id)
        for language in ("hi", "hi_en")
        for skill_id in skill_ids
        if not localized_teaching_support(
            preferred_language=language,
            skill_ids=[skill_id],
            stage="guided_practice",
            en_production_confidence=0.0,
        )
    ]

    assert unsupported == []
