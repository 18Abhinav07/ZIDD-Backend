import json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from scripts.build_school_class5_deep_chapter import load_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
)
CHAPTER_IDS = ("eng_c5_ch02", "eng_c5_ch03")
REHEARSED_ASSESSMENT_IDS = {
    "eng_c5_ch02": {
        "eng_c5_ch02:assessment:11",
        "eng_c5_ch02:assessment:18",
    },
    "eng_c5_ch03": {
        "eng_c5_ch03:assessment:10",
        "eng_c5_ch03:assessment:13",
        "eng_c5_ch03:assessment:18",
        "eng_c5_ch03:assessment:21",
    },
}
COMPACT_PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
SUPPORT_CHECKS = {
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
}
GENERIC_PROMPT_FRAGMENTS = {
    "find the clear clue",
    "use the support steps",
    "answer this scene without choices",
    "carry the idea into this fresh situation",
    "write without copying",
}
COMPANION_TREATMENTS = {
    "guided_only",
    "optional_creative",
    "offline_group_activity",
    "textbook_companion",
}


def _payload(chapter_id: str) -> dict:
    return json.loads(
        (CHAPTER_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _all_teaching_activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]


def _all_learning_activities(payload: dict):
    yield from _all_teaching_activities(payload)
    for level in payload["levels"]:
        yield from level["checks"].values()


def _task_text(activity: dict) -> str:
    return " ".join(
        f"{activity['passage']} {activity['prompt']}".casefold().split()
    )


def _assert_four_fresh_certifying_variants_per_level(payload: dict) -> None:
    chapter_passages = set()

    for level in payload["levels"]:
        activities_by_phase = {}
        for step in level["teaching_steps"]:
            activities_by_phase[step["phase"]] = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )

        for phase in ("transfer", "review"):
            variants = activities_by_phase[phase]
            assert len(variants) >= 4, (level["level_id"], phase)

            passages = [
                " ".join(item["passage"].casefold().split()) for item in variants
            ]
            prompts = [
                " ".join(item["prompt"].casefold().split()) for item in variants
            ]
            assert len(passages) == len(set(passages))
            assert len(prompts) == len(set(prompts))
            assert chapter_passages.isdisjoint(passages)
            chapter_passages.update(passages)

            for index, left in enumerate(variants):
                for right in variants[index + 1 :]:
                    assert SequenceMatcher(
                        None,
                        _task_text(left),
                        _task_text(right),
                    ).ratio() < 0.68

            other_phase_activities = [
                activity
                for other_phase, activities in activities_by_phase.items()
                if other_phase != phase
                for activity in activities
            ]
            covered_skills = set()
            for activity in variants:
                assert max(
                    SequenceMatcher(
                        None,
                        _task_text(activity),
                        _task_text(other),
                    ).ratio()
                    for other in other_phase_activities
                ) < 0.65
                claimed_skills = set(activity["knowledge_components"])
                assert claimed_skills
                assert claimed_skills <= set(level["skill_ids"])
                covered_skills.update(claimed_skills)
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["evaluation_mode"] == "llm_rubric"
                assert activity["evidence_role"] == "certifying"
                assert activity["certifying_language"] == "en"
                assert activity["pass_score"] == 0.8
                assert activity["model_answer"].strip()
                assert activity["forbidden_phrases"]
                assert len(activity["relevance_terms"]) >= 2

                criteria = activity["rubric_criteria"]
                slots = activity["concept_slots"]
                assert [criterion["id"] for criterion in criteria] == [
                    slot["id"] for slot in slots
                ]
                assert all(criterion["required"] for criterion in criteria)
                assert all(criterion["description"].strip() for criterion in criteria)
                assert all(slot["description"].strip() for slot in slots)
                assert all(slot["any_of"] for slot in slots)
            assert covered_skills == set(level["skill_ids"])


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_has_deep_manifest_and_agent_reviewed_runtime(chapter_id):
    payload = _payload(chapter_id)
    manifest_path = MANIFEST_ROOT / f"{chapter_id}.py"

    assert manifest_path.is_file()
    manifest = load_manifest(manifest_path)
    assert manifest.chapter.chapter_id == chapter_id
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False

    chapter = load_live_chapter_file(CHAPTER_ROOT / f"{chapter_id}.json")
    assert chapter.approval_status == "agent_reviewed"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in evidence.lower() for evidence in chapter.review_evidence)
    assert any("official" in evidence.lower() for evidence in chapter.review_evidence)
    assert not chapter_quality_issues(chapter)
    assert 7 <= len(chapter.levels) <= 9
    assert len(manifest.levels) == len(chapter.levels)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_covers_official_sections_without_false_certification(chapter_id):
    payload = _payload(chapter_id)
    anchors = payload["source_anchors"]
    anchor_ids = {anchor["anchor_id"] for anchor in anchors}
    section_text = " ".join(anchor["section_label"].lower() for anchor in anchors)

    assert len(anchors) >= 8
    assert all(anchor["source_url"].startswith("https://ncert.nic.in/") for anchor in anchors)
    assert all(set(level["source_anchor_ids"]).issubset(anchor_ids) for level in payload["levels"])
    for section in ("think", "learn", "listen", "speak", "write", "do", "explore"):
        assert section in section_text

    companion_anchors = [
        anchor
        for anchor in anchors
        if anchor["coverage_treatment"] in COMPANION_TREATMENTS
    ]
    assert companion_anchors
    assert all(not anchor["required_for_chapter_certification"] for anchor in companion_anchors)
    assert any("listen" in anchor["section_label"].lower() for anchor in companion_anchors)
    assert any("speak" in anchor["section_label"].lower() for anchor in companion_anchors)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_every_level_runs_a_deep_distinct_teaching_and_support_loop(chapter_id):
    payload = _payload(chapter_id)
    signatures = []
    choice_positions = []

    for level in payload["levels"]:
        assert set(level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == COMPACT_PHASES
        by_phase = {step["phase"]: step for step in steps}
        assert len(by_phase["guided_practice"]["variant_pool"]) >= 2
        assert len(by_phase["independent_application"]["variant_pool"]) >= 2
        assert len(by_phase["transfer"]["variant_pool"]) >= 2
        assert len(by_phase["review"]["variant_pool"]) >= 2

        for phase in ("independent_application", "transfer", "review"):
            for activity in by_phase[phase]["variant_pool"]:
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["evaluation_mode"] == "llm_rubric"
                assert activity["evidence_role"] == "certifying"
                assert activity["certifying_language"] == "en"

        for check_name in SUPPORT_CHECKS:
            support = level["checks"][check_name]
            assert len(support["teaching_block"].split()) >= 5
            assert support.get("target_misconception_tags")

        for activity in _all_teaching_activities({"levels": [level]}):
            normalized = " ".join(activity["prompt"].lower().split())
            assert not any(fragment in normalized for fragment in GENERIC_PROMPT_FRAGMENTS)
            signatures.append(
                (
                    activity["teaching_block"],
                    activity["passage"],
                    activity["prompt"],
                )
            )
            if activity["options"]:
                choice_positions.append(
                    activity["options"].index(activity["accepted_answers"][0])
                )

    assert len(signatures) == len(set(signatures))
    assert len(set(choice_positions)) >= 3
    assert Counter(choice_positions)[0] / len(choice_positions) < 0.6


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_chapter_assessment_is_mixed_fresh_and_remediable(chapter_id):
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id
        for level in payload["levels"]
        for skill_id in level["skill_ids"]
    }
    assessed_skills = {
        skill_id for item in items for skill_id in item["skill_ids"]
    }
    teaching_passages = {
        " ".join(activity["passage"].lower().split())
        for activity in _all_teaching_activities(payload)
    }

    assert assessment["items_per_attempt"] == 16
    assert assessment["max_attempts"] == 2
    assert len(items) == 32
    assert len(taught_skills) <= assessment["items_per_attempt"]
    assert assessed_skills == taught_skills
    assert all(
        sum(skill_id in item["skill_ids"] for item in items) >= 2
        for skill_id in taught_skills
    )
    assert sum(bool(item["options"]) for item in items) >= 10
    assert sum(not item["options"] for item in items) >= 10
    assert len({item["item_id"] for item in items}) == 32
    assert all(
        " ".join(item["passage"].lower().split()) not in teaching_passages
        for item in items
    )
    assert all(
        item.get("grading_mode") == "selected_option"
        if item["options"]
        else item.get("grading_mode") == "strict_open_rubric"
        for item in items
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_reviewed_assessments_use_fresh_transfer_scenarios(chapter_id):
    payload = _payload(chapter_id)
    teaching_tasks = [
        _task_text(activity) for activity in _all_learning_activities(payload)
    ]
    reviewed = {
        item["item_id"]: item
        for item in payload["chapter_assessment"]["items"]
        if item["item_id"] in REHEARSED_ASSESSMENT_IDS[chapter_id]
    }

    assert set(reviewed) == REHEARSED_ASSESSMENT_IDS[chapter_id]
    for item in reviewed.values():
        assessment_task = _task_text(item)
        assert max(
            SequenceMatcher(None, assessment_task, teaching_task).ratio()
            for teaching_task in teaching_tasks
        ) < 0.65


def test_chapter_three_has_four_fresh_transfer_and_review_variants_per_level():
    _assert_four_fresh_certifying_variants_per_level(_payload("eng_c5_ch03"))


def test_chapter_two_has_four_genuinely_distinct_review_variants_per_level():
    payload = _payload("eng_c5_ch02")
    chapter_review_passages = set()

    for level in payload["levels"]:
        review_step = next(
            step for step in level["teaching_steps"] if step["phase"] == "review"
        )
        reviews = review_step["variant_pool"]

        assert len(reviews) == 4, level["level_id"]

        passages = [" ".join(item["passage"].casefold().split()) for item in reviews]
        prompts = [" ".join(item["prompt"].casefold().split()) for item in reviews]
        assert len(set(passages)) == 4
        assert len(set(prompts)) == 4
        assert chapter_review_passages.isdisjoint(passages)
        chapter_review_passages.update(passages)

        for index, left in enumerate(reviews):
            for right in reviews[index + 1 :]:
                assert SequenceMatcher(
                    None,
                    _task_text(left),
                    _task_text(right),
                ).ratio() < 0.68

        non_review_activities = []
        for step in level["teaching_steps"]:
            if step["phase"] == "review":
                continue
            if step.get("activity") is not None:
                non_review_activities.append(step["activity"])
            else:
                non_review_activities.extend(step["variant_pool"])
        non_review_activities.extend(level["checks"].values())

        for review in reviews:
            assert max(
                SequenceMatcher(
                    None,
                    _task_text(review),
                    _task_text(other),
                ).ratio()
                for other in non_review_activities
            ) < 0.65

        for activity in reviews:
            assert set(activity["knowledge_components"]) == set(level["skill_ids"])
            assert activity["options"] == []
            assert activity["grading_mode"] == "strict_open_rubric"
            assert activity["evaluation_mode"] == "llm_rubric"
            assert activity["evidence_role"] == "certifying"
            assert activity["model_answer"].strip()

            criteria = activity["rubric_criteria"]
            slots = activity["concept_slots"]
            assert criteria
            assert slots
            assert [criterion["id"] for criterion in criteria] == [
                slot["id"] for slot in slots
            ]
            assert all(criterion["required"] for criterion in criteria)
            assert all(slot["any_of"] for slot in slots)


def test_chapter_two_precise_grammar_teaches_only_tense_and_sentence_order():
    payload = _payload("eng_c5_ch02")
    level = next(
        level
        for level in payload["levels"]
        if level["level_id"] == "scooter_precise_grammar"
    )
    learner_copy = []
    for activity in _all_learning_activities({"levels": [level]}):
        assert set(activity["knowledge_components"]) <= {
            "grammar.tense_usage",
            "grammar.sentence_order",
        }
        learner_copy.extend(
            (activity["teaching_block"], activity["passage"], activity["prompt"])
        )

    normalized = " ".join(learner_copy).casefold()
    assert "adjective" not in normalized
    assert "word job" not in normalized
    assert "describes the" not in normalized


def test_chapter_two_composite_evidence_aliases_prove_the_complete_claim():
    payload = _payload("eng_c5_ch02")
    activities = {
        activity.get("variant_id"): activity
        for activity in _all_teaching_activities(payload)
    }

    scarf = activities["scooter_event_sequence:independent:2"]
    scarf_slots = {
        slot["id"].rsplit(":", 1)[-1]: slot
        for slot in scarf["concept_slots"]
    }
    assert set(scarf_slots) == {"main", "wind", "discovery"}
    assert all(
        any(term in alias.casefold() for term in ("wind", "blew"))
        for alias in scarf_slots["wind"]["any_of"]
    )
    assert all(
        any(term in alias.casefold() for term in ("cleaner", "spotted", "found"))
        for alias in scarf_slots["discovery"]["any_of"]
    )

    chalk = activities["scooter_event_sequence:independent:3"]
    route = next(
        slot
        for slot in chalk["concept_slots"]
        if slot["id"].endswith(":route")
    )
    assert all(
        "curtain gap" in alias.casefold() and "ramp" in alias.casefold()
        for alias in route["any_of"]
    )

    connectors = activities["scooter_connectors_and_adverbs:independent:1"]
    connector_slots = {
        slot["id"].rsplit(":", 1)[-1]: slot
        for slot in connectors["concept_slots"]
    }
    assert all(
        "but" in alias.casefold()
        for alias in connector_slots["contrast"]["any_of"]
    )
    assert all(
        "because" in alias.casefold()
        for alias in connector_slots["cause"]["any_of"]
    )

    clinic = activities["scooter_precise_grammar:transfer:1"]
    sentence = next(
        slot
        for slot in clinic["concept_slots"]
        if slot["id"].endswith(":sentence")
    )
    for alias in sentence["any_of"]:
        normalized = " ".join(alias.casefold().split())
        assert "nurse" in normalized
        assert "box" in normalized
        assert "storeroom" in normalized
        assert "morning" in normalized


def test_chapter_two_dialogue_prompt_does_not_miscount_required_speech_acts():
    payload = _payload("eng_c5_ch02")
    activity = next(
        item
        for item in _all_teaching_activities(payload)
        if item.get("passage", "").startswith("At a railway platform")
    )

    assert "three-turn" not in activity["prompt"].casefold()
    assert all(
        requirement in activity["prompt"].casefold()
        for requirement in ("problem", "question", "answer", "action")
    )


def test_chapter_two_assessment_choices_are_plausible_not_nonsense_eliminations():
    payload = _payload("eng_c5_ch02")
    options = {
        option
        for item in payload["chapter_assessment"]["items"]
        for option in item["options"]
    }
    assert "The coach owns many labels." not in options
    assert "The helmet asked, 'Is this your guard?'" not in options
    assert "The bell inspected at noon." not in options
    assert "The rain inspected the dry road." not in options


def test_chapter_three_final_journey_work_certifies_eighty_to_hundred_words():
    payload = _payload("eng_c5_ch03")
    level = next(
        level
        for level in payload["levels"]
        if level["level_id"] == "rainbow_journey_paragraph"
    )
    steps = {step["phase"]: step for step in level["teaching_steps"]}

    for phase in ("independent_application", "transfer", "review"):
        variants = steps[phase]["variant_pool"]
        assert variants
        assert all("writing.paragraph" in item["knowledge_components"] for item in variants)
        assert all("grammar.tense_usage" in item["knowledge_components"] for item in variants)
        assert all(item["min_response_words"] >= 80 for item in variants)
        assert all(
            item["preflight_rule"] == "journey_paragraph_80_100"
            for item in variants
        )
        assert all("80" in item["prompt"] and "100" in item["prompt"] for item in variants)

    journey_items = [
        item
        for item in payload["chapter_assessment"]["items"]
        if "writing.paragraph" in item["skill_ids"]
    ]
    assert {item["item_id"] for item in journey_items} == {
        "eng_c5_ch03:assessment:23",
        "eng_c5_ch03:assessment:24",
    }
    assert all(item["min_response_words"] >= 80 for item in journey_items)
    assert all(
        item["preflight_rule"] == "journey_paragraph_80_100"
        for item in journey_items
    )
    assert all("80" in item["prompt"] and "100" in item["prompt"] for item in journey_items)


def test_chapter_three_clay_pot_claim_stays_within_source():
    payload = _payload("eng_c5_ch03")
    item = next(
        item
        for item in payload["chapter_assessment"]["items"]
        if item["item_id"] == "eng_c5_ch03:assessment:32"
    )

    accepted = item["accepted_answers"][0]
    assert "locally made clay pot" in accepted
    assert "eight litres" in accepted
    assert "porous walls" in accepted
    assert not any(
        unsupported in accepted.casefold()
        for unsupported in ("international design prize", "oldest", "frozen")
    )


def test_chapter_three_reference_transfer_has_one_plural_antecedent_and_complete_key():
    payload = _payload("eng_c5_ch03")
    activity = next(
        item
        for item in _all_teaching_activities(payload)
        if item.get("variant_id") == "rainbow_reference_and_context:transfer:4"
    )

    assert activity["passage"] == (
        "Riya placed three seed packets beside a clay pot filled with damp soil. "
        "She labelled them before they were moved into a sheltered room, where "
        "the soil smelled earthy."
    )

    criteria = {item["id"]: item for item in activity["rubric_criteria"]}
    slots = {item["id"]: item for item in activity["concept_slots"]}
    reference_id = "rainbow_reference_and_context:transfer:4:references"
    expected_description = (
        "Identifies Riya as She and the seed packets as both plural antecedents."
    )

    assert criteria[reference_id]["description"] == expected_description
    assert slots[reference_id]["description"] == expected_description
    for alias in slots[reference_id]["any_of"]:
        normalized = alias.casefold()
        assert all(
            term in normalized for term in ("riya", "seed packets", "them", "they")
        )
    assert activity["model_answer"].startswith(
        "She refers to Riya, while them and they both refer to the seed packets."
    )
