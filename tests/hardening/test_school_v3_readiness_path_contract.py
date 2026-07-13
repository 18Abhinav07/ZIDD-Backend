from app.services.school_v3_readiness_path import build_readiness_path


def test_school_v3_readiness_path_uses_missing_prerequisites_not_full_lower_class_replay():
    path = build_readiness_path(
        subject_id="english",
        target_class_no=5,
        weak_skill_ids=("writing.reason_answer",),
    )

    module_skill_ids = [module["skill_id"] for module in path["modules"]]
    assert module_skill_ids == [
        "reading.sentence_comprehension",
        "writing.complete_sentence",
        "reading.inference_reason",
        "grammar.connectors_because_and_but",
        "writing.short_answer",
        "writing.reason_answer",
    ]
    assert "grammar.noun_verb_adjective" not in module_skill_ids
    assert path["target_unlocked"] is False
    assert path["path_type"] == "readiness_path"


def test_school_v3_readiness_path_marks_residual_weak_skills_as_watchlist_when_target_unlocks():
    path = build_readiness_path(
        subject_id="english",
        target_class_no=5,
        weak_skill_ids=("vocab.chapter_word_usage",),
        non_blocking_weak_skill_ids=("vocab.chapter_word_usage",),
    )

    assert path["target_unlocked"] is True
    assert path["modules"] == []
    assert path["watchlist_skill_ids"] == ["vocab.chapter_word_usage"]
    assert "watchlist" in path["deviation_note"].lower()
