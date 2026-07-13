import json
import re
from pathlib import Path

from app.content.school_rebuild_content import load_live_chapter_file
from app.services.school_rebuild_curriculum import (
    _evaluate_deterministic_answer,
    _select_chapter_assessment_items,
)


LIVE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
    / "eng_c5_ch05.json"
)


def _normalized(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def test_frog_live_chapter_meets_structural_and_authored_quality_gate():
    chapter = load_live_chapter_file(LIVE_PATH)
    runtime = chapter.runtime_dict()

    assert chapter.approval_status == "qa_approved"
    assert runtime["chapter_id"] == "eng_c5_ch05"
    assert runtime["chapter_no"] == 5
    assert runtime["title"] == "The Frog"
    assert runtime["unit_title"] == "Water"
    assert runtime["content_version"] == "2026-07-11.3"
    assert runtime["source_url"] == "https://ncert.nic.in/textbook/pdf/eesa105.pdf"
    assert len(runtime["levels"]) == 7

    required_skills = {
        "reading.sentence_comprehension",
        "reading.paragraph_main_idea",
        "reading.inference_reason",
        "reading.word_meaning_context",
        "vocab.chapter_word_usage",
        "grammar.connectors_because_and_but",
        "grammar.sentence_order",
        "writing.complete_sentence",
        "writing.short_answer",
        "writing.reason_answer",
        "writing.summary_own_words",
        "writing.compare_contrast",
        "writing.friendly_message",
    }
    taught_skills = {
        skill_id
        for level in runtime["levels"]
        for skill_id in level["skill_ids"]
    }
    assert taught_skills == required_skills

    llm_level_checks = 0
    constructed_support_checks = 0
    for level in runtime["levels"]:
        checks = level["checks"]
        supported = [checks["guided_check"], checks["bridge"], checks["masterclass"]]
        independent = checks["independent_check"]
        assert all(
            not check["options"] or len(check["options"]) >= 2
            for check in supported
        )
        constructed_support_checks += sum(not check["options"] for check in supported)
        assert independent["options"] == []
        assert len(
            {
                (check["teaching_block"], check["passage"], check["prompt"])
                for check in [*supported, independent]
            }
        ) == 4
        assert independent["passage"] not in {check["passage"] for check in supported}
        assert independent["prompt"] not in {check["prompt"] for check in supported}
        if independent.get("evaluation_mode") == "llm_rubric":
            llm_level_checks += 1
        else:
            passage = _normalized(independent["passage"])
            for accepted in independent.get("accepted_answers") or []:
                normalized_answer = _normalized(accepted)
                if len(normalized_answer.split()) >= 2:
                    assert normalized_answer not in passage
    assert llm_level_checks >= 2
    assert constructed_support_checks >= 6

    sentence_level = next(
        level for level in runtime["levels"] if "grammar.sentence_order" in level["skill_ids"]
    )
    sentence_text = json.dumps(sentence_level).lower()
    assert "jumbled" in sentence_text
    assert "first" not in sentence_level["checks"]["independent_check"]["prompt"].lower()

    assessment = runtime["chapter_assessment"]
    assert assessment["items_per_attempt"] == 13
    assert assessment["pass_score"] == 0.8
    assert assessment["max_attempts"] == 2
    assert len(assessment["items"]) == 26
    assert sum(bool(item["options"]) for item in assessment["items"]) >= 8
    assert sum(not item["options"] for item in assessment["items"]) >= 8
    assert sum(
        item.get("evaluation_mode") == "llm_rubric"
        for item in assessment["items"]
    ) >= 4

    serialized = json.dumps(runtime).lower()
    for forbidden in (
        "santoor chapter 5",
        "sample sentence",
        "which choice best supports",
        "random guess",
        "page number",
        "bird wings",
        "lives in the sky",
        "turns the moth into a leaf",
    ):
        assert forbidden not in serialized


def test_frog_habitat_checks_accept_natural_paraphrases_without_accepting_noise():
    chapter = load_live_chapter_file(LIVE_PATH).runtime_dict()
    checks = chapter["levels"][0]["checks"]
    natural_answers = {
        "independent_check": (
            "It hopped across the moss on land, then stayed in the rain-filled "
            "ditch with its eyes above the water, so it can manage both places."
        ),
        "bridge": (
            "The frog uses the wet leaves on land as shelter in the afternoon, "
            "and it uses the shallow pool as its water habitat at night."
        ),
        "masterclass": (
            "The main idea is that a frog uses different parts of a pond habitat "
            "for different needs. The reeds provide shelter, and diving below the "
            "water provides an escape from danger."
        ),
    }

    for kind, answer in natural_answers.items():
        evaluation = _evaluate_deterministic_answer(checks[kind], answer)
        assert evaluation["correct"] is True, (kind, evaluation)

    irrelevant = _evaluate_deterministic_answer(
        checks["independent_check"],
        "A fish lives in the ocean and the sky is blue above it.",
    )
    contradictory = _evaluate_deterministic_answer(
        checks["independent_check"],
        "It hopped across moss, but it does not use water.",
    )
    alternate_contradiction = _evaluate_deterministic_answer(
        checks["independent_check"],
        "It hopped across moss and used the water-filled ditch, but it did not enter it.",
    )
    assert irrelevant["correct"] is False
    assert contradictory["correct"] is False
    assert alternate_contradiction["correct"] is False


def test_frog_life_cycle_summary_accepts_natural_stage_word_order():
    chapter = load_live_chapter_file(LIVE_PATH).runtime_dict()
    check = chapter["levels"][1]["checks"]["independent_check"]

    evaluation = _evaluate_deterministic_answer(
        check,
        "The eggs hatch into long-tailed tadpoles, and later the tadpoles grow "
        "four legs while their tails become tiny.",
    )

    assert evaluation["correct"] is True, evaluation
    assert evaluation["missing_criteria"] == []


def test_frog_defence_check_accepts_not_seen_as_a_correct_camouflage_result():
    chapter = load_live_chapter_file(LIVE_PATH).runtime_dict()
    check = chapter["levels"][2]["checks"]["independent_check"]

    evaluation = _evaluate_deterministic_answer(
        check,
        "Pressing flat lets its speckled body blend with the stones so the hunter "
        "may not see it, while slipping under the root gives it extra cover.",
    )

    assert evaluation["correct"] is True, evaluation
    assert evaluation["missing_criteria"] == []


def test_frog_assessment_forms_are_fresh_cover_all_skills_and_bound_llm_cost():
    chapter = load_live_chapter_file(LIVE_PATH).runtime_dict()
    assessment = chapter["chapter_assessment"]
    first = _select_chapter_assessment_items(
        assessment["items"],
        item_count=assessment["items_per_attempt"],
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        assessment["items"],
        item_count=assessment["items_per_attempt"],
        attempt_no=2,
        used_item_ids=first_ids,
    )
    second_ids = {item["item_id"] for item in second}
    taught_skills = {
        skill_id
        for level in chapter["levels"]
        for skill_id in level["skill_ids"]
    }

    assert len(first) == len(second) == 13
    assert first_ids.isdisjoint(second_ids)
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(item.get("evaluation_mode") == "llm_rubric" for item in form) == 2
        assert sum(
            "writing.compare_contrast" in item["skill_ids"] for item in form
        ) == 1
        assert sum(
            "writing.friendly_message" in item["skill_ids"] for item in form
        ) == 1


def test_frog_concept_items_accept_paraphrases_and_reject_contradictions():
    chapter = load_live_chapter_file(LIVE_PATH).runtime_dict()
    activities = [
        level["checks"]["independent_check"] for level in chapter["levels"]
    ] + list(chapter["chapter_assessment"]["items"])
    concept_items = {
        item.get("item_id") or item.get("prompt"): item
        for item in activities
        if item.get("answer_rule") == "concept_slots"
    }
    probes = [
        (
            "What evidence suggests that the animal can manage both land and water?",
            "It hopped on moss and later hid in the ditch.",
        ),
        (
            "Summarize the development recorded in the three notes in one sentence.",
            "Eggs hatch into tadpoles, which grow legs as their tails shrink.",
        ),
        (
            "How do the frog's two actions reduce the danger in different ways?",
            "Its speckles match the stones, and it slips under the root to hide.",
        ),
        (
            "Why might calling help frogs that are spread across the area? Answer in one sentence.",
            "So they can hear each other.",
        ),
        (
            "How may the frog's pattern protect it?",
            "It makes the frog hard for the bird to spot.",
        ),
        (
            "Write two complete connected ideas: one about the possible calling places and one about the distant call reaching the pond.",
            "A frog may call next to the drain or among the grass. Even though the grass is a long way from the pond, its voice carries to the water.",
        ),
    ]
    for prompt, answer in probes:
        item = next(
            item for item in concept_items.values() if item["prompt"] == prompt
        )
        assert _evaluate(item, answer)["correct"] is True

    webbed_sentence = _evaluate(
        concept_items["eng_c5_ch05_assess_06"],
        "A frog's webbed feet help it push through the water while swimming.",
    )
    assert webbed_sentence["correct"] is True, webbed_sentence

    habitat = next(
        item
        for item in concept_items.values()
        if item["prompt"]
        == "What evidence suggests that the animal can manage both land and water?"
    )
    contradiction = _evaluate(
        habitat,
        "The frog uses land and water, but it does not use water.",
    )
    assert contradiction["correct"] is False
    assert "contradictory_response" in contradiction["blockers"]

    predator = concept_items["eng_c5_ch05_assess_13"]
    reversed_roles = _evaluate(
        predator,
        "Other animals hunt an animal, while prey catches it to eat near the pond.",
    )
    assert reversed_roles["correct"] is False

    life_cycle = next(
        item
        for item in concept_items.values()
        if item["prompt"]
        == "Summarize the development recorded in the three notes in one sentence."
    )
    reversed_cycle = _evaluate(
        life_cycle,
        "Tails shrink and legs grow before tadpoles hatch from eggs.",
    )
    assert reversed_cycle["correct"] is False
    assert "concept_sequence" in reversed_cycle["missing_criteria"]

    fragment_probes = {
        "eng_c5_ch05_assess_04": "because hot under rock",
        "eng_c5_ch05_assess_06": "webbed feet swimming",
        "eng_c5_ch05_assess_10": "locate",
        "eng_c5_ch05_assess_17": "powerful hind legs escape",
    }
    for item_id, fragment in fragment_probes.items():
        result = _evaluate(concept_items[item_id], fragment)
        assert result["correct"] is False
        assert "response_min_words" in result["missing_criteria"]

    keyword_bags = {
        "What evidence suggests that the animal can manage both land and water?": (
            "Moss hopped. Ditch eyes above."
        ),
        "Summarize the development recorded in the three notes in one sentence.": (
            "Eggs tadpoles grow legs tiny tails."
        ),
        "eng_c5_ch05_assess_01": "Bank rests stream dives.",
        "eng_c5_ch05_assess_13": "Hunter prey.",
        "eng_c5_ch05_assess_15": "Tadpole grows legs tiny tail.",
        "eng_c5_ch05_assess_19": "Camouflage predator.",
        "eng_c5_ch05_assess_21": "Damp needs moisture.",
    }
    for item_key, keyword_bag in keyword_bags.items():
        item = concept_items.get(item_key) or next(
            candidate
            for candidate in concept_items.values()
            if candidate["prompt"] == item_key
        )
        assert _evaluate(item, keyword_bag)["correct"] is False


def _evaluate(item: dict, answer: str) -> dict:
    from app.services.school_rebuild_curriculum import _evaluate_deterministic_answer

    return _evaluate_deterministic_answer(item, answer)
