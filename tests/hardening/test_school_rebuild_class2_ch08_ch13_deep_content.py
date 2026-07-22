from __future__ import annotations

import json
import re
from collections import Counter
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import pytest

from app.content.school.standards import locked_english_taxonomy
from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_quality import chapter_quality_issues
from app.services.school_rebuild_curriculum import _select_chapter_assessment_items
from app.services.school.evaluator_contract import (
    OPEN_RUBRIC_SCHEMA_VERSION,
    school_open_context_from_activity,
    validate_school_open_evaluation,
)
from scripts.build_school_deep_chapter import (
    build_deep_chapter,
    load_manifest,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CHAPTER_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_2"
)
MANIFEST_ROOT = (
    REPO_ROOT
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_2"
)
EXTRACT_ROOT = Path("/tmp/zidd-ncert-class2-3")
CHAPTER_IDS = tuple(f"eng_c2_ch{chapter_no:02d}" for chapter_no in range(8, 14))
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
SUPPORT_SEQUENCE = (
    "bridge",
    "masterclass",
    "revision_level_1",
    "revision_level_2",
    "revision_level_3",
)
MIN_VARIANTS = {
    "guided_practice": 4,
    "independent_application": 4,
    "transfer": 4,
    "review": 4,
}
COMPANION_TREATMENTS = {
    "guided_only",
    "optional_creative",
    "offline_group_activity",
    "textbook_companion",
}
NON_TEXT_CERTIFICATION_PREFIXES = ("listening.", "speaking.", "oral.")
NON_TEXT_INTERACTIONS = {
    "audio",
    "drawing",
    "image_only",
    "performance",
    "recording",
}
SOURCE_CONTRACT = {
    "eng_c2_ch08": (7, ("poem", "speak", "write", "draw", "listen")),
    "eng_c2_ch09": (7, ("read", "speak", "listen", "write", "do", "project")),
    "eng_c2_ch10": (8, ("poem", "speak", "write", "draw", "listen")),
    "eng_c2_ch11": (8, ("read", "speak", "draw", "listen", "write", "project")),
    "eng_c2_ch12": (7, ("song", "speak", "listen", "draw", "write", "project")),
    "eng_c2_ch13": (
        18,
        ("read", "speak", "draw", "listen", "write", "something new", "project"),
    ),
}
CHAPTER_CONCEPTS = {
    "eng_c2_ch08": ("cloud", "shape", "drift", "comparison"),
    "eng_c2_ch09": ("name", "search", "memory", "polite"),
    "eng_c2_ch10": ("crow", "feather", "quality", "accept"),
    "eng_c2_ch11": ("litter", "dustbin", "clean", "responsible"),
    "eng_c2_ch12": ("drop", "grain", "kindness", "sentence"),
    "eng_c2_ch13": ("profile", "language", "festival", "belong"),
}
REQUIRED_CLASS2_SKILLS = {
    "reading.word_meaning_context",
    "reading.sentence_comprehension",
    "reading.event_sequence",
    "vocab.chapter_word_usage",
    "vocab.spelling",
    "grammar.noun_verb_adjective",
    "grammar.sentence_order",
    "grammar.punctuation_capitalization",
    "writing.complete_sentence",
}
REQUIRED_ASSET_PHRASES = {
    "look at the image",
    "look at the picture",
    "listen to the audio",
    "listen to the recording",
    "watch the video",
    "read the textbook",
    "on the page",
}
BANNED_LEARNER_PHRASES = {
    "retrieve the skill",
    "repair the misconception",
    "exact reference wording",
    "certifying response",
    "misconception check",
}
BANNED_LANGUAGE_FRAGMENTS = {
    "who did sort",
    "who did bin",
    "each small grain adds an amount",
    "what action does kindness show",
}
REPEATED_CARD_BOILERPLATE = (
    "Use only this new card and write the answer in your own words. "
    "Use the card clues to answer."
)
CONTENT_STOPWORDS = {
    "a",
    "an",
    "and",
    "answer",
    "card",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "use",
    "which",
    "with",
    "write",
}


def _payload(chapter_id: str) -> dict:
    return json.loads(
        (CHAPTER_ROOT / f"{chapter_id}.json").read_text(encoding="utf-8")
    )


def _activities(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            if step.get("activity") is not None:
                yield step["activity"]
            else:
                yield from step["variant_pool"]


def _certifying_activities(payload: dict):
    for item in payload["chapter_assessment"]["items"]:
        yield item, item["skill_ids"]
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            for activity in activities:
                if activity.get("evidence_role") == "certifying":
                    yield activity, level["skill_ids"]


def _all_runtime_activities(payload: dict):
    yield from _activities(payload)
    for level in payload["levels"]:
        yield from level["checks"].values()
    yield from payload["chapter_assessment"]["items"]


def _normalise(value: str) -> str:
    return " ".join(value.casefold().split())


def _word_tokens(value: str) -> list[str]:
    return re.findall(r"[a-z]+(?:'[a-z]+)?", value.casefold())


def _ngrams(value: str, size: int) -> set[tuple[str, ...]]:
    tokens = _word_tokens(value)
    return {
        tuple(tokens[index : index + size])
        for index in range(len(tokens) - size + 1)
    }


def _content_tokens(value: str) -> set[str]:
    return {
        token
        for token in _word_tokens(value)
        if token not in CONTENT_STOPWORDS and len(token) >= 3
    }


def _semantic_jaccard(left: str, right: str) -> float:
    left_tokens = _content_tokens(left)
    right_tokens = _content_tokens(right)
    union = left_tokens | right_tokens
    return len(left_tokens & right_tokens) / len(union) if union else 1.0


def _scenario_text(activity: dict) -> str:
    return _normalise(
        " ".join(
            (
                activity["passage"],
                activity["prompt"],
                activity.get("model_answer", ""),
            )
        )
    )


def _positive_open_payload(activity: dict, answer: str) -> dict:
    item_id = activity.get("item_id") or activity.get("activity_id")
    skills = activity.get("skill_ids") or activity.get("knowledge_components")
    aliases_by_id = {
        slot["id"]: [
            alias
            for alias in slot["any_of"]
            if alias in answer
        ]
        for slot in activity["concept_slots"]
    }
    return {
        "schema_version": OPEN_RUBRIC_SCHEMA_VERSION,
        "item_id": item_id,
        "skill_ids": list(skills),
        "score": 0.95,
        "confidence": 0.95,
        "language_detected": "en",
        "criteria": [
            {
                "id": criterion["id"],
                "met": bool(aliases_by_id[criterion["id"]]),
                "quality": 0.9 if aliases_by_id[criterion["id"]] else 0.0,
                "evidence_quote": (
                    aliases_by_id[criterion["id"]][0]
                    if aliases_by_id[criterion["id"]]
                    else answer
                ),
            }
            for criterion in activity["rubric_criteria"]
        ],
        "misconception_tags": [],
        "blockers": [],
        "needs_human_review": False,
        "feedback_to_learner": "The response uses the needed ideas.",
    }


def _validate_open_probe(activity: dict, answer: str):
    return validate_school_open_evaluation(
        _positive_open_payload(activity, answer),
        context=school_open_context_from_activity(activity, answer),
    )


def _activity_strings(activity: dict):
    for field in (
        "teaching_block",
        "passage",
        "prompt",
        "model_answer",
    ):
        value = activity.get(field)
        if isinstance(value, str):
            yield f"{field}", value
    for field in (
        "options",
        "accepted_answers",
        "forbidden_phrases",
        "relevance_terms",
    ):
        for index, value in enumerate(activity.get(field) or ()):
            if isinstance(value, str):
                yield f"{field}[{index}]", value
    for field in ("rubric_criteria", "concept_slots"):
        for index, item in enumerate(activity.get(field) or ()):
            description = item.get("description")
            if isinstance(description, str):
                yield f"{field}[{index}].description", description
            for phrase_index, phrase in enumerate(item.get("any_of") or ()):
                if isinstance(phrase, str):
                    yield f"{field}[{index}].any_of[{phrase_index}]", phrase


def _learner_strings(payload: dict):
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            candidates = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            for activity in candidates:
                for field, value in _activity_strings(activity):
                    yield f"{level['level_id']}:{step['phase']}:{field}", value
        for check_name in SUPPORT_CHECKS:
            for field, value in _activity_strings(level["checks"][check_name]):
                yield f"{level['level_id']}:{check_name}:{field}", value
    for item in payload["chapter_assessment"]["items"]:
        for field, value in _activity_strings(item):
            yield f"{item['item_id']}:{field}", value


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_manifest_compiles_to_deep_hash_stable_class2_runtime(chapter_id):
    manifest_path = MANIFEST_ROOT / f"{chapter_id}.py"
    assert manifest_path.is_file()
    manifest = load_manifest(manifest_path)
    payload = _payload(chapter_id)
    chapter = load_live_chapter_file(CHAPTER_ROOT / f"{chapter_id}.json")
    rebuilt = load_live_chapter_file(
        CHAPTER_ROOT / f"{chapter_id}.json"
    ).model_copy(update={"approval_status": "draft"})
    compiled = build_deep_chapter(None, manifest)

    assert manifest.schema_version == "school-class2-deep-manifest-v1"
    assert manifest.chapter.chapter_id == chapter_id
    assert "class2" in manifest.chapter.content_version
    assert "class2" in manifest.chapter.certification_version
    assert manifest.chapter.authorship.zidd_authored_original is True
    assert manifest.chapter.authorship.textbook_body_or_questions_copied is False
    assert 5 <= len(manifest.levels) <= 7
    assert len(payload["levels"]) == len(manifest.levels)
    assert chapter.calculated_runtime_sha256() == payload["runtime_sha256"]
    assert compiled["runtime_sha256"] == payload["runtime_sha256"]
    assert rebuilt.runtime_dict() == chapter.runtime_dict()
    assert chapter.approval_status == "agent_reviewed"
    assert chapter.approval_status != "release_approved"
    assert chapter.reviewed_by
    assert chapter.reviewed_at
    assert any("manifest" in item.casefold() for item in chapter.review_evidence)
    assert any("official" in item.casefold() for item in chapter.review_evidence)
    assert any("originality" in item.casefold() for item in chapter.review_evidence)
    assert any("pedagogy" in item.casefold() for item in chapter.review_evidence)
    assert any("language" in item.casefold() for item in chapter.review_evidence)
    assert any("runtime" in item.casefold() for item in chapter.review_evidence)
    assert not chapter_quality_issues(chapter)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_levels_use_class2_taxonomy_and_exact_deep_phase_roles(chapter_id):
    payload = _payload(chapter_id)
    taxonomy = locked_english_taxonomy()
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }

    assert 5 <= len(payload["levels"]) <= 7
    assert REQUIRED_CLASS2_SKILLS <= taught_skills
    assert len(taught_skills) <= 12
    for skill_id in taught_skills:
        standard = taxonomy.get(skill_id)
        assert standard.class_min <= 2 <= standard.class_max
        assert not skill_id.startswith(NON_TEXT_CERTIFICATION_PREFIXES)

    for level in payload["levels"]:
        assert set(level["checks"]) == SUPPORT_CHECKS | {
            "guided_check",
            "independent_check",
            "transfer_check",
        }
        steps = level["teaching_steps"]
        assert tuple(step["phase"] for step in steps) == COMPACT_PHASES
        by_phase = {step["phase"]: step for step in steps}

        connect = by_phase["connect"]["activity"]
        assert connect["interaction_type"] == "continue"
        assert connect["evidence_role"] == "experience"
        assert by_phase["co_construct"]["activity"]["evidence_role"] == "formative"
        for phase, minimum in MIN_VARIANTS.items():
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) >= minimum
            expected_role = "supported" if phase == "guided_practice" else "certifying"
            assert all(activity["evidence_role"] == expected_role for activity in variants)
            assert len({activity["variant_id"] for activity in variants}) == len(variants)
            assert len({_normalise(activity["passage"]) for activity in variants}) == len(variants)
            assert len({_normalise(activity["prompt"]) for activity in variants}) == len(variants)
            for left, right in combinations(variants, 2):
                left_authority = f"{left['passage']} {left['prompt']}"
                right_authority = f"{right['passage']} {right['prompt']}"
                assert _semantic_jaccard(left_authority, right_authority) < 0.72

            if phase != "guided_practice":
                assert all(activity["options"] == [] for activity in variants)
                assert all(
                    activity["grading_mode"] == "strict_open_rubric"
                    for activity in variants
                )
                assert all(activity["certifying_language"] == "en" for activity in variants)

        for phase in ("transfer", "review"):
            variants = by_phase[phase]["variant_pool"]
            assert all(
                set(activity["knowledge_components"]) == set(level["skill_ids"])
                for activity in variants
            )
            for left, right in combinations(variants, 2):
                left_scenario = _scenario_text(left)
                right_scenario = _scenario_text(right)
                assert SequenceMatcher(
                    None,
                    left_scenario,
                    right_scenario,
                ).ratio() < 0.68
                assert _semantic_jaccard(left_scenario, right_scenario) < 0.55
                assert not _ngrams(left_scenario, 10).intersection(
                    _ngrams(right_scenario, 10)
                )

        support_signatures = set()
        for check_name in SUPPORT_CHECKS:
            check = level["checks"][check_name]
            assert check["evidence_role"] == "supported"
            assert check.get("target_misconception_tags")
            support_signatures.add(
                (
                    _normalise(check["teaching_block"]),
                    _normalise(check["passage"]),
                    _normalise(check["prompt"]),
                )
            )
        assert len(support_signatures) == 5


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_support_is_class2_staged_targeted_and_child_facing(chapter_id):
    payload = _payload(chapter_id)

    for level in payload["levels"]:
        support = [level["checks"][name] for name in SUPPORT_SEQUENCE]
        bridge, short_response, worked_example, alternate_case, open_response = support

        assert bridge["grading_mode"] == "selected_option"
        assert bridge["options"]
        assert short_response["grading_mode"] == "strict_open_rubric"
        assert short_response["interaction_type"] == "short_text"
        assert short_response["min_response_words"] == 6
        assert worked_example["grading_mode"] == "selected_option"
        assert "worked example" in worked_example["teaching_block"].casefold()
        assert "another case" in (
            f"{alternate_case['teaching_block']} {alternate_case['prompt']}".casefold()
        )
        assert alternate_case["grading_mode"] == "strict_open_rubric"
        assert alternate_case["interaction_type"] == "short_text"
        assert alternate_case["min_response_words"] == 6
        assert open_response["grading_mode"] == "strict_open_rubric"
        assert open_response["interaction_type"] == "evidence_text"
        assert open_response["min_response_words"] >= 8
        assert open_response["min_response_words"] > short_response["min_response_words"]
        assert sum(
            "worked example" in item["teaching_block"].casefold()
            for item in support
        ) == 1
        assert len({_normalise(item["passage"]) for item in support}) == 5
        assert all(item.get("target_misconception_tags") for item in support)

        for item in support:
            learner_text = _normalise(
                f"{item['teaching_block']} {item['passage']} {item['prompt']}"
            )
            assert not any(phrase in learner_text for phrase in BANNED_LEARNER_PHRASES)


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_source_anchors_cover_extract_progression_without_false_modality(chapter_id):
    payload = _payload(chapter_id)
    anchors = payload["source_anchors"]
    expected_last_page, expected_sections = SOURCE_CONTRACT[chapter_id]
    section_text = " ".join(anchor["section_label"].casefold() for anchor in anchors)
    anchor_ids = {anchor["anchor_id"] for anchor in anchors}

    assert anchors
    assert min(anchor["page_start"] for anchor in anchors) == 1
    assert max(anchor["page_end"] for anchor in anchors) == expected_last_page
    assert all(1 <= anchor["page_start"] <= anchor["page_end"] <= expected_last_page for anchor in anchors)
    assert all(anchor["source_url"].startswith("https://ncert.nic.in/") for anchor in anchors)
    assert all(section in section_text for section in expected_sections)
    assert all(
        set(level["source_anchor_ids"]).issubset(anchor_ids)
        for level in payload["levels"]
    )

    companion_anchors = [
        anchor
        for anchor in anchors
        if anchor["coverage_treatment"] in COMPANION_TREATMENTS
    ]
    assert companion_anchors
    assert all(not anchor["required_for_chapter_certification"] for anchor in companion_anchors)
    for anchor in anchors:
        label = anchor["section_label"].casefold()
        if any(
            modality in label
            for modality in (
                "listen",
                "speak",
                "recite",
                "sing",
                "draw",
                "picture",
                "project",
                "performance",
            )
        ):
            assert anchor["coverage_treatment"] in COMPANION_TREATMENTS
            assert anchor["required_for_chapter_certification"] is False

    for activity, skill_ids in _certifying_activities(payload):
        assert activity.get("interaction_type") not in NON_TEXT_INTERACTIONS
        assert not any(
            skill_id.startswith(NON_TEXT_CERTIFICATION_PREFIXES)
            for skill_id in skill_ids
        )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_has_two_disjoint_skill_complete_remediable_forms(chapter_id):
    payload = _payload(chapter_id)
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }
    assessed_skills = {
        skill_id for item in items for skill_id in item["skill_ids"]
    }
    teaching_and_support = list(_activities(payload)) + [
        level["checks"][name]
        for level in payload["levels"]
        for name in SUPPORT_SEQUENCE
    ]
    teaching_passages = {
        _normalise(activity["passage"]) for activity in teaching_and_support
    }

    assert assessment["items_per_attempt"] == 12
    assert assessment["max_attempts"] == 2
    assert len(items) == 24
    assert len({item["item_id"] for item in items}) == 24
    assert taught_skills == assessed_skills
    assert sum(bool(item["options"]) for item in items) >= 8
    assert sum(not item["options"] for item in items) >= 8
    assert len({item["passage"] for item in items}) == 24
    assert all(_normalise(item["passage"]) not in teaching_passages for item in items)
    for item in items:
        item_authority = f"{item['passage']} {item['prompt']}"
        for activity in teaching_and_support:
            authored_authority = f"{activity['passage']} {activity['prompt']}"
            assert _semantic_jaccard(item_authority, authored_authority) < 0.72
            assert not _ngrams(item_authority, 6).intersection(
                _ngrams(authored_authority, 6)
            )

    first = _select_chapter_assessment_items(
        items,
        item_count=12,
        attempt_no=1,
        used_item_ids=set(),
    )
    first_ids = {item["item_id"] for item in first}
    second = _select_chapter_assessment_items(
        items,
        item_count=12,
        attempt_no=2,
        used_item_ids=first_ids,
    )
    assert len(first) == len(second) == 12
    assert first_ids.isdisjoint(item["item_id"] for item in second)
    for left, right in ((left, right) for left in first for right in second):
        left_authority = f"{left['passage']} {left['prompt']}"
        right_authority = f"{right['passage']} {right['prompt']}"
        assert _semantic_jaccard(left_authority, right_authority) < 0.72
        assert not _ngrams(left_authority, 6).intersection(
            _ngrams(right_authority, 6)
        )
    for form in (first, second):
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills
        assert sum(bool(item["options"]) for item in form) >= 4
        assert sum(not item["options"] for item in form) >= 4

    remediated_skills = {
        skill_id
        for level in payload["levels"]
        for check_name in SUPPORT_CHECKS
        for skill_id in level["checks"][check_name]["knowledge_components"]
    }
    assert assessed_skills <= remediated_skills


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_visible_authority_rubrics_and_prompts_are_honest(chapter_id):
    payload = _payload(chapter_id)

    for activity in _all_runtime_activities(payload):
        visible_text = _normalise(
            " ".join(
                (
                    activity.get("teaching_block", ""),
                    activity["passage"],
                    activity["prompt"],
                )
            )
        )
        assert len(_word_tokens(activity["passage"])) >= 4
        assert not any(phrase in visible_text for phrase in REQUIRED_ASSET_PHRASES)
        assert not any(phrase in visible_text for phrase in BANNED_LEARNER_PHRASES)
        assert not any(phrase in visible_text for phrase in BANNED_LANGUAGE_FRAGMENTS)
        prompt = _normalise(activity["prompt"])
        for answer in activity.get("accepted_answers") or ():
            assert _normalise(answer) not in prompt

        if activity.get("grading_mode") == "strict_open_rubric":
            criteria = activity["rubric_criteria"]
            slots = activity["concept_slots"]
            assert criteria
            assert slots
            assert activity["model_answer"]
            assert activity["relevance_terms"]
            assert len(_word_tokens(activity["model_answer"])) >= activity["min_response_words"]
            assert [criterion["id"] for criterion in criteria] == [
                slot["id"] for slot in slots
            ]
            assert all(
                criterion["required"] and criterion["min_quality"] >= 0.7
                for criterion in criteria
            )
            model_answer = _normalise(activity["model_answer"])
            alias_sets = []
            for slot in slots:
                aliases = {_normalise(alias) for alias in slot["any_of"]}
                assert len(aliases) >= 2
                assert all(len(_word_tokens(alias)) >= 2 for alias in aliases)
                assert model_answer not in aliases
                alias_sets.append(aliases)
            for left, right in combinations(alias_sets, 2):
                assert left.isdisjoint(right)
            if re.search(r"\b(?:and|both|two|three|all|before|after)\b", prompt):
                assert len(slots) >= 2


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_assessment_open_claims_accept_paraphrases_and_require_every_slot(chapter_id):
    open_items = [
        item
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
        if item.get("grading_mode") == "strict_open_rubric"
    ]
    assert open_items

    for item in open_items:
        answer = ". ".join(slot["any_of"][-1] for slot in item["concept_slots"])
        if len(_word_tokens(answer)) < item["min_response_words"]:
            answer += " The new card supports this complete answer."
        assert _normalise(answer) != _normalise(item["model_answer"])
        validated = _validate_open_probe(item, answer)
        assert validated.effective_blockers == ()
        assert validated.certification_eligible is True

        if len(item["concept_slots"]) >= 2:
            partial = ". ".join(
                slot["any_of"][-1] for slot in item["concept_slots"][:-1]
            )
            if len(_word_tokens(partial)) < item["min_response_words"]:
                partial += " The new card gives useful details for my answer."
            blocked = _validate_open_probe(item, partial)
            assert "semantic_required_claim_missing" in blocked.effective_blockers
            assert blocked.certification_eligible is False


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_both_assessment_forms_use_natural_punctuation_authority(chapter_id):
    punctuation_items = [
        item
        for item in _payload(chapter_id)["chapter_assessment"]["items"]
        if "grammar.punctuation_capitalization" in item["skill_ids"]
    ]
    assert sum("assessment_form_1" in item["item_id"] for item in punctuation_items) >= 2
    assert sum("assessment_form_2" in item["item_id"] for item in punctuation_items) >= 2

    for item in punctuation_items:
        assert item["grading_mode"] == "strict_open_rubric"
        closure = item["model_answer"].rstrip()[-1]
        assert closure in ".?!"
        aliases = [
            alias
            for slot in item["concept_slots"]
            for alias in slot["any_of"]
        ]
        assert all(alias.strip() not in {"?", ".", "!"} for alias in aliases)
        assert any(
            alias.rstrip().endswith(closure) and len(_word_tokens(alias)) >= 2
            for alias in aliases
        )
        validated = _validate_open_probe(item, item["model_answer"])
        assert validated.effective_blockers == ()
        assert validated.certification_eligible is True


def test_ch11_ch12_learner_english_has_no_reviewed_regressions():
    corpus = " ".join(
        value.casefold()
        for chapter_id in ("eng_c2_ch11", "eng_c2_ch12")
        for _, value in _learner_strings(_payload(chapter_id))
    )
    assert not any(fragment in corpus for fragment in BANNED_LANGUAGE_FRAGMENTS)
    assert not re.search(
        r"\b(?:children|pupils|learners|workers|volunteers|monkeys|families|"
        r"neighbours|birds)\s+(?:sorts|puts|uses|cleans|carries|helps|keeps|"
        r"throws|collects|moves)\b",
        corpus,
    )


def test_chapters_are_chapter_specific_not_interchangeable_templates():
    all_prompts: list[str] = []
    all_signatures: list[tuple[str, str, str]] = []

    for chapter_id in CHAPTER_IDS:
        payload = _payload(chapter_id)
        chapter_text = json.dumps(
            {
                "levels": payload["levels"],
                "assessment": payload["chapter_assessment"],
            },
            ensure_ascii=True,
        ).casefold()
        assert all(concept in chapter_text for concept in CHAPTER_CONCEPTS[chapter_id])
        for activity in _activities(payload):
            prompt = _normalise(activity["prompt"])
            all_prompts.append(prompt)
            all_signatures.append(
                (
                    _normalise(activity["teaching_block"]),
                    _normalise(activity["passage"]),
                    prompt,
                )
            )

    assert len(all_signatures) == len(set(all_signatures))
    prompt_counts = Counter(all_prompts)
    assert len(prompt_counts) / len(all_prompts) >= 0.9
    assert prompt_counts.most_common(1)[0][1] <= len(CHAPTER_IDS)
    assert Counter(prompt.split()[0] for prompt in all_prompts).most_common(1)[0][1] < (
        len(all_prompts) * 0.7
    )


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_directions_drop_card_boilerplate_without_a_global_replacement(
    chapter_id,
):
    payload = _payload(chapter_id)
    learner_copy = [
        (location, _normalise(value))
        for location, value in _learner_strings(payload)
    ]
    repeated_phrase = _normalise(REPEATED_CARD_BOILERPLATE)

    assert not [
        location
        for location, value in learner_copy
        if repeated_phrase in value
    ]

    authored_directions = [
        _normalise(activity["teaching_block"])
        for activity in _activities(payload)
        if activity.get("teaching_block")
    ]
    duplicate_directions = {
        direction: count
        for direction, count in Counter(authored_directions).items()
        if count > 1
    }
    assert duplicate_directions == {}


@pytest.mark.parametrize("chapter_id", CHAPTER_IDS)
def test_learner_content_has_no_ten_word_overlap_with_official_extract(chapter_id):
    extract_path = EXTRACT_ROOT / f"{chapter_id}.txt"
    if not extract_path.is_file():
        pytest.skip("official Class 2 structural extract is not available")
    source_ngrams = _ngrams(extract_path.read_text(encoding="utf-8"), 10)
    assert source_ngrams

    for location, value in _learner_strings(_payload(chapter_id)):
        overlaps = _ngrams(value, 10).intersection(source_ngrams)
        assert not overlaps, f"{chapter_id}:{location}:{sorted(overlaps)[0]}"
