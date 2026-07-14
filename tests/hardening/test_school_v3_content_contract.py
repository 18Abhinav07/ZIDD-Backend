import pytest

from app.content.school_v3_content import (
    approved_chapters_for_class,
    load_ncert_source_map,
    public_school_v3_chapter,
    seed_content_enabled,
    supported_classes,
    validate_school_v3_launch_gate,
)
from app.content.school_v3_schema import (
    ContentGateError,
    SchoolV3AssessmentItem,
    SchoolV3ChapterBlueprint,
    SchoolV3LessonOutcome,
    SchoolV3RubricEvaluation,
)
from app.content.school_v3_taxonomy import (
    LOCKED_ENGLISH_SKILL_IDS,
    locked_english_taxonomy,
)
from app.services.school_v3_evaluator import grade_deterministic_item


FORBIDDEN_PUBLIC_KEYS = {"answer_key", "model_answer", "rubric"}


def _items(prefix: str, skill_id: str, *, chapter_checks: int) -> list[SchoolV3AssessmentItem]:
    items: list[SchoolV3AssessmentItem] = []
    for index in range(6):
        items.append(
            SchoolV3AssessmentItem(
                item_id=f"{prefix}_guided_{index}",
                stage="guided",
                item_type="short_answer",
                prompt="What clue helps you answer?",
                skill_ids=[skill_id],
                model_answer="Use the nearby sentence clue.",
                rubric={"criteria": ["names a useful clue"]},
            )
        )
        items.append(
            SchoolV3AssessmentItem(
                item_id=f"{prefix}_independent_{index}",
                stage="independent_check",
                item_type="short_answer",
                prompt="Answer independently in one sentence.",
                skill_ids=[skill_id],
                model_answer="A clear answer with a reason.",
                rubric={"criteria": ["answers without a hint"]},
            )
        )
    for index in range(3):
        items.append(
            SchoolV3AssessmentItem(
                item_id=f"{prefix}_transfer_{index}",
                stage="transfer_check",
                item_type="short_answer",
                prompt="Use the same skill in a new sentence.",
                skill_ids=[skill_id],
                model_answer="Transfers the same idea to a new example.",
                rubric={"criteria": ["uses the skill in a new context"]},
            )
        )
    for index in range(4):
        items.append(
            SchoolV3AssessmentItem(
                item_id=f"{prefix}_bridge_{index}",
                stage="bridge",
                item_type="multiple_choice",
                prompt="Choose the strongest clue.",
                skill_ids=[skill_id],
                answer_key="nearby words",
                options=["nearby words", "random guess", "longest word"],
            )
        )
    items.append(
        SchoolV3AssessmentItem(
            item_id=f"{prefix}_review_0",
            stage="review_check",
            item_type="short_answer",
            prompt="Review the skill after a short delay.",
            skill_ids=[skill_id],
            model_answer="A retained answer with evidence.",
            rubric={"criteria": ["retains the skill"]},
        )
    )
    for index in range(chapter_checks):
        items.append(
            SchoolV3AssessmentItem(
                item_id=f"{prefix}_chapter_{index}",
                stage="chapter_check",
                item_type="fill_blank",
                prompt="The answer is __.",
                skill_ids=[skill_id],
                answer_key="because",
            )
        )
    return items


def _launch_blueprint() -> SchoolV3ChapterBlueprint:
    skill_ids = list(LOCKED_ENGLISH_SKILL_IDS)
    return SchoolV3ChapterBlueprint(
        subject_id="english",
        class_no=5,
        book_title="Santoor",
        curriculum_version="school-v3-contract-2026-07",
        chapter_id="eng_c5_contract_chapter",
        chapter_title="Contract Chapter",
        source_url="https://ncert.nic.in/textbook.php",
        outcomes=[
            SchoolV3LessonOutcome(
                outcome_id=f"outcome_{index}",
                title=f"Outcome {index}",
                skill_ids=[skill_ids[index % len(skill_ids)]],
                items=_items(
                    f"outcome_{index}",
                    skill_ids[index % len(skill_ids)],
                    chapter_checks=4,
                ),
            )
            for index in range(5)
        ],
    )


def _assert_no_forbidden_public_keys(value):
    if isinstance(value, dict):
        assert not (set(value) & FORBIDDEN_PUBLIC_KEYS)
        for child in value.values():
            _assert_no_forbidden_public_keys(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_forbidden_public_keys(child)


def test_locked_english_taxonomy_exposes_known_school_v3_skill_ids():
    taxonomy = locked_english_taxonomy()

    assert "reading.word_meaning_context" in LOCKED_ENGLISH_SKILL_IDS
    assert "writing.reason_answer" in taxonomy.skill_ids()
    assert "writing.summary_own_words" in taxonomy.skill_ids()
    assert "grammar.sentence_order" in taxonomy.skill_ids()
    assert "writing.compare_contrast" in taxonomy.skill_ids()
    assert "writing.friendly_message" in taxonomy.skill_ids()
    assert "eng.c5.answer.reason" not in taxonomy.skill_ids()


def test_launch_gate_accepts_bounded_school_v3_chapter_contract():
    result = validate_school_v3_launch_gate(_launch_blueprint())

    assert result.outcome_count == 5
    assert result.chapter_check_count == 20
    assert result.stage_counts_by_outcome["outcome_0"]["guided"] == 6
    assert result.stage_counts_by_outcome["outcome_0"]["independent_check"] == 6
    assert result.stage_counts_by_outcome["outcome_0"]["transfer_check"] == 3


def test_launch_gate_requires_five_to_seven_outcomes():
    blueprint = _launch_blueprint()
    blueprint.outcomes = blueprint.outcomes[:4]

    with pytest.raises(ContentGateError, match="launch_gate_outcome_count:5:7"):
        validate_school_v3_launch_gate(blueprint)


def test_launch_gate_requires_minimum_stage_depth_per_outcome():
    blueprint = _launch_blueprint()
    blueprint.outcomes[0].items = [
        item for item in blueprint.outcomes[0].items if item.stage != "independent_check"
    ]

    with pytest.raises(ContentGateError, match="launch_gate_min_stage_items:outcome_0:independent_check:6"):
        validate_school_v3_launch_gate(blueprint)


def test_launch_gate_requires_bridge_support_depth_per_outcome():
    blueprint = _launch_blueprint()
    blueprint.outcomes[0].items = [
        item for item in blueprint.outcomes[0].items if item.stage != "bridge"
    ]

    with pytest.raises(ContentGateError, match="launch_gate_min_stage_items:outcome_0:bridge:4"):
        validate_school_v3_launch_gate(blueprint)


def test_launch_gate_requires_twenty_chapter_check_items_per_chapter():
    blueprint = _launch_blueprint()
    blueprint.outcomes[-1].items = [
        item for item in blueprint.outcomes[-1].items if item.stage != "chapter_check"
    ]

    with pytest.raises(ContentGateError, match="launch_gate_min_chapter_check_items:20"):
        validate_school_v3_launch_gate(blueprint)


def test_launch_gate_rejects_unknown_skill_and_duplicate_item_ids():
    blueprint = _launch_blueprint()
    blueprint.outcomes[0].skill_ids = ["eng.c5.invented.skill"]

    with pytest.raises(ContentGateError, match="unknown_skill_id:eng.c5.invented.skill"):
        validate_school_v3_launch_gate(blueprint)

    duplicate = _launch_blueprint()
    duplicate.outcomes[1].items[0].item_id = duplicate.outcomes[0].items[0].item_id

    with pytest.raises(ContentGateError, match="duplicate_item_id"):
        validate_school_v3_launch_gate(duplicate)


def test_public_serializers_never_leak_answers_models_or_rubrics():
    payload = public_school_v3_chapter(_launch_blueprint())

    _assert_no_forbidden_public_keys(payload)
    first_item = payload["outcomes"][0]["items"][0]
    assert first_item["item_id"] == "outcome_0_guided_0"
    assert first_item["stage"] == "guided"


def test_current_ncert_source_map_covers_school_v3_english_classes_2_to_5():
    expected = {
        2: ("Mridang", "bemr1"),
        3: ("Santoor", "cesa1"),
        4: ("Santoor", "desa1"),
        5: ("Santoor", "eesa1"),
    }

    assert supported_classes("english") == (2, 3, 4, 5)
    for class_no, (book_title, book_code) in expected.items():
        source_map = load_ncert_source_map("english", class_no)
        assert source_map["book_title"] == book_title
        assert source_map["book_code"] == book_code
        assert source_map["source_url"] == "https://ncert.nic.in/textbook.php"
        assert len(source_map["chapters"]) >= 5


def test_every_approved_school_v3_blueprint_passes_launch_gate_and_public_contract():
    chapters = []
    for class_no in supported_classes("english"):
        chapters.extend(approved_chapters_for_class("english", class_no))

    assert len(chapters) >= 20
    for chapter in chapters:
        result = validate_school_v3_launch_gate(chapter)
        assert result.outcome_count >= 5
        assert result.chapter_check_count >= 20
        assert chapter.approval_status in {"seed", "approved"}
        _assert_no_forbidden_public_keys(public_school_v3_chapter(chapter))


def test_school_v3_seed_content_is_not_marked_human_approved():
    chapters = [
        chapter
        for class_no in supported_classes("english")
        for chapter in approved_chapters_for_class("english", class_no)
    ]

    assert chapters
    assert {chapter.approval_status for chapter in chapters} == {"seed"}
    assert all(chapter.reviewed_by == "zidd-seed-content-contract" for chapter in chapters)


def test_school_v3_seed_content_is_disabled_by_default_in_prod(monkeypatch):
    approved_chapters_for_class.cache_clear()
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.delenv("SCHOOL_V3_ALLOW_SEED_CONTENT", raising=False)

    assert seed_content_enabled() is False
    with pytest.raises(ContentGateError, match="approved_blueprint_missing"):
        approved_chapters_for_class("english", 2)

    approved_chapters_for_class.cache_clear()


def test_school_v3_seed_prompts_do_not_embed_answer_keys():
    chapters = [
        chapter
        for class_no in supported_classes("english")
        for chapter in approved_chapters_for_class("english", class_no)
    ]

    leaks: list[str] = []
    for chapter in chapters:
        for outcome in chapter.outcomes:
            for item in outcome.items:
                if item.answer_key and item.answer_key.lower() in item.prompt.lower():
                    leaks.append(item.item_id)

    assert leaks == []
