import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import pytest

from app.content.school.content_schema import SchoolRubricEvaluation
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services import school_rebuild_curriculum as curriculum
from app.services.school.evaluator_contract import OPEN_RUBRIC_SCHEMA_VERSION


CLASS_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
ALL_CHAPTER_PATHS = sorted(CLASS_ROOT.parent.glob("class_*/*.json"))
SOURCE_MAP_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "ncert_source_map"
    / "english"
    / "class_5.json"
)
CHAPTERS = {
    "eng_c5_ch01": (1, "Papa's Spectacles", 9, 16),
    "eng_c5_ch02": (2, "Gone with the Scooter", 7, 14),
    "eng_c5_ch03": (3, "The Rainbow", 7, 13),
}
CHECK_STAGES = {
    "guided_check",
    "bridge",
    "masterclass",
    "independent_check",
    "transfer_check",
}
DEEP_CHECK_STAGES = CHECK_STAGES | {
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
}
HIDDEN_GRADING_KEYS = {
    "accepted_answers",
    "answer_rule",
    "concept_slots",
    "forbidden_phrases",
    "ordered_concept_slot_ids",
    "preflight_rule",
    "pass_score",
    "rubric_criteria",
}
OPEN_EXPRESSION_PROMPT = re.compile(
    r"\b(own words|new sentence|different sentence|fresh sentence|new phrase|"
    r"write a new|use\s+[^.?!]{0,45}\s+in\s+(?:a|one)\s+(?:new\s+)?sentence)\b",
    re.IGNORECASE,
)


@pytest.fixture(autouse=True)
def hardening_test_env():
    """Keep this content-only slice isolated from concurrent catalog rebuilds."""
    yield


def _source_entries() -> dict[str, dict]:
    payload = json.loads(SOURCE_MAP_PATH.read_text(encoding="utf-8"))
    return {entry["chapter_id"]: entry for entry in payload["chapters"]}


@pytest.mark.parametrize("chapter_id", CHAPTERS)
def test_owned_class5_chapter_meets_launch_structure_and_source_contract(chapter_id):
    chapter_no, title, expected_levels, _ = CHAPTERS[chapter_id]
    chapter = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json")
    runtime = chapter.runtime_dict()
    source = _source_entries()[chapter_id]

    if chapter_id == "eng_c5_ch01":
        assert chapter.approval_status == "agent_reviewed"
        assert chapter.reviewed_by == "Codex School content and browser review"
        reviewed_at = datetime.fromisoformat(chapter.reviewed_at)
        assert reviewed_at.tzinfo is not None
        evidence = "\n".join(chapter.review_evidence).lower()
        assert "official" in evidence
        assert "browser qa" in evidence
        assert "test_school_rebuild_class5_ch1_gold_slice.py" in evidence
        assert "semantic claim slots" in evidence
    else:
        assert chapter.approval_status == "agent_reviewed"
        assert chapter.reviewed_by
        assert chapter.reviewed_at
        assert chapter.review_evidence
        assert any(
            "manifest" in evidence.lower() for evidence in chapter.review_evidence
        )
        assert any(
            "official" in evidence.lower() for evidence in chapter.review_evidence
        )
    assert runtime["chapter_id"] == chapter_id
    assert runtime["chapter_no"] == chapter_no == source["chapter_no"]
    assert runtime["title"] == title == source["chapter_title"]
    assert runtime["source_url"] == source["pdf_url"]
    assert runtime["book_title"] == "Santoor"
    assert len(runtime["levels"]) == expected_levels

    for level in runtime["levels"]:
        check_stages = set(level["checks"])
        assert DEEP_CHECK_STAGES <= check_stages
        assert check_stages - DEEP_CHECK_STAGES <= {"revision_level_4"}
        independent = level["checks"]["independent_check"]
        transfer = level["checks"]["transfer_check"]
        assert independent["options"] == transfer["options"] == []
        assert (independent["passage"], independent["prompt"]) != (
            transfer["passage"],
            transfer["prompt"],
        )

    reparsed = LiveSchoolChapter.model_validate(
        json.loads((CLASS_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8"))
    )
    assert reparsed.runtime_dict() == runtime
    assert reparsed.calculated_runtime_sha256() == chapter.runtime_sha256


def test_ch01_story_revision_accepts_the_concise_sentence_the_prompt_asks_for():
    chapter = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json")
    level = next(
        item
        for item in chapter.levels
        if item.level_id == "papas_spectacles_poem_to_story"
    )
    activity = level.checks.revision_level_1

    assert activity.min_response_words <= 9
    assert activity.model_answer == "Mira opened the gate and walked into the garden."
    assert "looked along" not in activity.model_answer.casefold()


@pytest.mark.parametrize(
    "chapter_id",
    ("eng_c5_ch02", "eng_c5_ch03", "eng_c5_ch04", "eng_c5_ch05"),
)
def test_certifying_activity_provenance_uses_only_certifying_source_anchors(
    chapter_id,
):
    runtime = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json").runtime_dict()
    certifying_anchor_ids = {
        anchor["anchor_id"]
        for anchor in runtime["source_anchors"]
        if anchor["required_for_chapter_certification"]
    }
    non_certifying_anchor_ids = {
        anchor["anchor_id"]
        for anchor in runtime["source_anchors"]
        if not anchor["required_for_chapter_certification"]
    }

    assert non_certifying_anchor_ids
    for level in runtime["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if "activity" in step
                else step["variant_pool"]
            )
            for activity in activities:
                if activity.get("evidence_role") != "certifying":
                    continue
                assert set(activity["source_anchor_ids"]) <= certifying_anchor_ids
        for check in level["checks"].values():
            if check.get("evidence_role") == "certifying":
                assert set(check["source_anchor_ids"]) <= certifying_anchor_ids


@pytest.mark.parametrize("chapter_id", CHAPTERS)
def test_owned_class5_chapter_assessment_is_diverse_and_covers_taught_skills(chapter_id):
    _, _, _, expected_skill_count = CHAPTERS[chapter_id]
    runtime = load_live_chapter_file(CLASS_ROOT / f"{chapter_id}.json").runtime_dict()
    taught_skills = {
        skill_id
        for level in runtime["levels"]
        for skill_id in level["skill_ids"]
    }
    assessment = runtime["chapter_assessment"]
    coverage = Counter(
        skill_id
        for item in assessment["items"]
        for skill_id in item["skill_ids"]
    )

    assert len(taught_skills) == expected_skill_count
    assert assessment["items_per_attempt"] == 16
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(assessment["items"]) == 32
    assert set(coverage) == taught_skills
    assert all(count >= 2 for count in coverage.values())
    assert sum(bool(item["options"]) for item in assessment["items"]) >= 8
    assert sum(not item["options"] for item in assessment["items"]) >= 8
    if chapter_id == "eng_c5_ch01":
        assert sum(
            item.get("grading_mode") == "strict_open_rubric"
            for item in assessment["items"]
        ) >= 4
        assert all(item.get("grading_mode") for item in assessment["items"])
    else:
        open_items = [item for item in assessment["items"] if not item["options"]]
        selected_items = [item for item in assessment["items"] if item["options"]]
        assert all(
            item.get("grading_mode") == "strict_open_rubric"
            and item.get("evaluation_mode") == "llm_rubric"
            for item in open_items
        )
        assert all(
            item.get("grading_mode") == "selected_option"
            and item.get("evaluation_mode") != "llm_rubric"
            for item in selected_items
        )


def test_chapter_two_summary_level_uses_child_facing_focus_copy():
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch02.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "scooter_summary_and_profile"
    )

    assert level["focus"] == (
        "write clear summaries and fact-based profiles in your own words"
    )
    assert "bounded" not in level["focus"].casefold()


def test_chapter_one_word_floors_allow_concise_complete_answers():
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    authored_floors: list[tuple[str, int]] = []
    for level in runtime["levels"]:
        authored_floors.extend(
            (level["level_id"], int(check["min_response_words"]))
            for check in level["checks"].values()
            if check.get("min_response_words") is not None
        )
        authored_floors.extend(
            (level["level_id"], int(activity["min_response_words"]))
            for step in level.get("teaching_steps") or []
            for activity in step.get("variant_pool") or []
            if activity.get("min_response_words") is not None
        )

    assert authored_floors
    assert max(floor for _, floor in authored_floors) <= 12
    assert all(
        floor <= 10
        for level_id, floor in authored_floors
        if level_id != "papas_spectacles_sound_lab"
    )
    assert max(
        int(item["min_response_words"])
        for item in runtime["chapter_assessment"]["items"]
        if item.get("min_response_words") is not None
    ) <= 8
    assert max(
        int(activity["min_response_words"])
        for step in runtime["levels"][3]["teaching_steps"]
        for activity in step.get("variant_pool") or []
        if activity.get("min_response_words") is not None
    ) <= 6


def test_chapter_one_sound_lab_accepts_a_complete_own_words_paraphrase():
    """A correct meaning explanation must not require model-answer wording."""

    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_sound_lab"
    )
    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    activity = next(
        item
        for item in independent_step["variant_pool"]
        if "light and night share the ending" in item["passage"]
    )
    activity = {
        **activity,
        "activity_id": activity["variant_id"],
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "Light and night share the ending -ight. Light means illumination, "
        "while night is the time after sunset. The light helped me read."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer explains each part clearly.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert "semantic_required_claim_missing" not in decision["blockers"]


def test_chapter_one_sound_lab_recovers_authorized_own_words_from_a_literal_provider():
    """Provider literalism must not reject an authored equivalent meaning."""

    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_sound_lab"
    )
    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    activity = next(
        item
        for item in independent_step["variant_pool"]
        if "light and night share the ending" in item["passage"]
    )
    activity = {
        **activity,
        "activity_id": activity["variant_id"],
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "Light and night share the ending -ight. Light means illumination, "
        "while night means the dark time. The light shone on my book."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.8,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"]
                    not in {
                        "sound_lab_independent_application_v1_first_meaning",
                        "sound_lab_independent_application_v1_second_meaning",
                    },
                    "quality": (
                        0.0
                        if criterion["id"]
                        in {
                            "sound_lab_independent_application_v1_first_meaning",
                            "sound_lab_independent_application_v1_second_meaning",
                        }
                        else 1.0
                    ),
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": ["ignored_context_clues"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer needs more context detail.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []
    assert not set(decision["blockers"]).intersection(
        {"semantic_required_claim_missing", "low_evaluator_confidence"}
    )


@pytest.mark.parametrize(
    ("passage_fragment", "answer"),
    [
        (
            "rain and train share the letter sequence",
            "Rain and train share rain, but train starts with t. Rain is water "
            "from the sky, while a train is a vehicle on rails. The train stopped "
            "at the station.",
        ),
        (
            "coat and goat share -oat",
            "Coat and goat share -oat but have different first letters. A coat is "
            "clothing for cold weather, while a goat is an animal. The goat climbed "
            "the hill.",
        ),
        (
            "pin and pen keep p and n",
            "Pin and pen keep p and n but change the middle letter. A pin is a sharp "
            "fastener, while a pen is a writing instrument. My pen wrote a note.",
        ),
    ],
)
def test_chapter_one_sound_lab_authorizes_natural_context_equivalents(
    passage_fragment,
    answer,
):
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_sound_lab"
    )
    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    activity = next(
        item
        for item in independent_step["variant_pool"]
        if passage_fragment in item["passage"]
    )
    activity = {
        **activity,
        "activity_id": activity["variant_id"],
        "skill_ids": list(activity["knowledge_components"]),
    }
    false_negative_ids = {
        criterion["id"]
        for criterion in activity["rubric_criteria"]
        if criterion["id"].endswith(("first_meaning", "second_meaning"))
    }
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 0.6,
            "confidence": 1.0,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": criterion["id"] not in false_negative_ids,
                    "quality": (
                        0.0 if criterion["id"] in false_negative_ids else 1.0
                    ),
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": ["ignored_context_clues"],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer needs more context detail.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert decision["missing_criteria"] == []


def test_chapter_one_word_phrase_review_accepts_a_natural_new_example():
    """A phrase task assesses meaning and new use, not copied passage nouns."""

    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_chapter_words"
    )
    review_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "review"
    )
    activity = next(
        item
        for item in review_step["variant_pool"]
        if item["variant_id"] == "papas_spectacles_chapter_words:review:v2"
    )
    activity = {
        **activity,
        "activity_id": activity["variant_id"],
        "skill_ids": list(activity["knowledge_components"]),
    }
    answer = (
        "A wave of means a large amount of something happening together. "
        "A wave of laughter came from the classroom."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer explains and uses the phrase clearly.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert activity["semantic_evidence_policy"] == "traceable_rubric"
    assert decision["correct"] is True
    assert "semantic_required_claim_missing" not in decision["blockers"]

def test_chapter_one_personal_response_accepts_a_backend_owned_paraphrase():
    """A learner can express the evidence and caution without matching aliases."""

    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_personal_response"
    )
    independent_step = next(
        step
        for step in level["teaching_steps"]
        if step["phase"] == "independent_application"
    )
    activity = next(
        item
        for item in independent_step["variant_pool"]
        if item["variant_id"] == "papas_spectacles_personal_response:independent_application:v4"
    )
    activity = {
        **activity,
        "activity_id": activity["variant_id"],
        "skill_ids": list(activity["knowledge_components"]),
    }
    assert activity.get("semantic_evidence_policy") is None
    answer = (
        "I would check the reading room first because the pencil was last used there, "
        "but I would not trust the art-room guess because nobody has verified it."
    )
    evaluation = SchoolRubricEvaluation.model_validate(
        {
            "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
            "item_id": activity["activity_id"],
            "skill_ids": activity["skill_ids"],
            "score": 1.0,
            "confidence": 0.95,
            "language_detected": "en",
            "criteria": [
                {
                    "id": criterion["id"],
                    "met": True,
                    "quality": 1.0,
                    "evidence_quote": answer,
                }
                for criterion in activity["rubric_criteria"]
            ],
            "misconception_tags": [],
            "blockers": [],
            "needs_human_review": False,
            "feedback_to_learner": "The answer clearly gives evidence and a responsible limit.",
        }
    )

    decision = curriculum.decide_open_answer_evaluation(
        activity,
        evaluation,
        answer=answer,
    )

    assert decision["correct"] is True
    assert "semantic_required_claim_missing" not in decision["blockers"]

    contradictory_answer = (
        "I would check the art room first because it is probably correct, "
        "but I have no proof yet."
    )
    contradictory_evaluation = evaluation.model_copy(
        update={
            "criteria": [
                criterion.model_copy(update={"evidence_quote": contradictory_answer})
                for criterion in evaluation.criteria
            ]
        }
    )
    contradictory = curriculum.decide_open_answer_evaluation(
        activity,
        contradictory_evaluation,
        answer=contradictory_answer,
    )

    assert contradictory["correct"] is False
    assert "authored_contradiction" in contradictory["blockers"]


def test_chapter_one_sound_lab_uses_traceable_rubrics_for_open_own_words_work():
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_sound_lab"
    )
    activities = [*level["checks"].values()]
    activities.extend(
        activity
        for step in level["teaching_steps"]
        for activity in step.get("variant_pool") or []
    )
    alias_bound_open_activities = [
        activity
        for activity in activities
        if activity.get("grading_mode") == "strict_open_rubric"
        and activity.get("concept_slots")
    ]

    assert len(alias_bound_open_activities) == 14
    assert {
        activity.get("semantic_evidence_policy")
        for activity in alias_bound_open_activities
    } == {"traceable_rubric"}


def test_open_expression_work_uses_traceable_evidence_across_the_live_corpus():
    """Own-words work cannot secretly require a copied source alias."""

    missing_policy: list[str] = []
    for chapter_path in ALL_CHAPTER_PATHS:
        runtime = load_live_chapter_file(chapter_path).runtime_dict()
        activities_with_owner: list[tuple[str, dict]] = []
        for level in runtime["levels"]:
            activities = list((level.get("checks") or {}).values())
            for step in level.get("teaching_steps") or []:
                if isinstance(step.get("activity"), dict):
                    activities.append(step["activity"])
                activities.extend(step.get("variant_pool") or [])
            activities_with_owner.extend(
                (str(level["level_id"]), activity) for activity in activities
            )
        activities_with_owner.extend(
            ("chapter_assessment", activity)
            for activity in (runtime.get("chapter_assessment") or {}).get("items")
            or []
        )
        for owner, activity in activities_with_owner:
            if activity.get("grading_mode") != "strict_open_rubric":
                continue
            if activity.get("semantic_validator_id"):
                continue
            if activity.get("ordered_concept_slot_ids"):
                continue
            if not OPEN_EXPRESSION_PROMPT.search(str(activity.get("prompt") or "")):
                continue
            if activity.get("semantic_evidence_policy") != "traceable_rubric":
                missing_policy.append(
                    ":".join(
                        (
                            str(runtime["chapter_id"]),
                            owner,
                            str(
                                activity.get("variant_id")
                                or activity.get("item_id")
                                or "check"
                            ),
                        )
                    )
                )

    assert not missing_policy, "\\n".join(missing_policy)


def test_chapter_one_sound_lab_prompts_name_each_required_reasoning_move():
    runtime = load_live_chapter_file(CLASS_ROOT / "eng_c5_ch01.json").runtime_dict()
    level = next(
        item
        for item in runtime["levels"]
        if item["level_id"] == "papas_spectacles_sound_lab"
    )
    activities = [
        activity
        for step in level["teaching_steps"]
        for activity in step.get("variant_pool") or []
    ]
    activities.extend(level["checks"].values())
    prompts = [
        activity["prompt"]
        for activity in activities
        if activity.get("grading_mode") == "strict_open_rubric"
        and any(
            str(criterion.get("id") or "").endswith("first_meaning")
            for criterion in activity.get("rubric_criteria") or []
        )
        and any(
            str(criterion.get("id") or "").endswith("second_meaning")
            for criterion in activity.get("rubric_criteria") or []
        )
    ]

    assert prompts
    assert all("First say what each word means" in prompt for prompt in prompts)
    assert all("written" in prompt and "new complete sentence" in prompt for prompt in prompts)


def test_school_public_activity_allowlist_hides_authored_grading_contract():
    public = curriculum._public_activity(
        {
            "activity_id": "chapter-1:independent:1",
            "level_id": "chapter-1",
            "kind": "independent_check",
            "title": "Explain the clue",
            "focus": "inference",
            "skill_ids": ["reading.inference_reason"],
            "teaching_block": "Answer independently.",
            "passage": "Mira carried an umbrella under a bright sky.",
            "prompt": "What did Mira expect?",
            "options": [],
            "response_mode": "paragraph",
            "pass_score": 0.8,
            "rubric_criteria": [{"id": "uses_clue"}],
            "forbidden_phrases": ["Mira expected no rain"],
            "relevance_terms": ["Mira", "umbrella", "rain"],
            "model_answer": "Mira expected rain because she carried an umbrella.",
            "accepted_answers": [],
            "can_answer": True,
        }
    )
    assert public is not None
    public_keys = set(public)

    assert {"passage", "prompt", "options", "can_answer"} <= public_keys
    assert HIDDEN_GRADING_KEYS.isdisjoint(public_keys)
