from __future__ import annotations

import ast
import json
import re
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path

import pytest

from app.content.school_rebuild_content import load_live_chapter_file
from app.content.school_rebuild_schema import LiveSchoolChapter
from app.services.school_rebuild_curriculum import (
    _plan_two_fresh_assessment_forms,
)
from scripts.build_school_deep_chapter import build_deep_chapter, load_manifest


CHAPTER_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_chapters"
    / "english"
    / "class_5"
)
MANIFEST_ROOT = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "content"
    / "school_rebuild_manifests"
    / "english"
    / "class_5"
)
PHASES = (
    "connect",
    "co_construct",
    "guided_practice",
    "independent_application",
    "transfer",
    "review",
)
REQUIRED_SKILLS = {
    "eng_c5_ch06": {
        "reading.event_sequence",
        "reading.inference_reason",
        "grammar.punctuation_capitalization",
        "writing.paragraph",
        "writing.procedure",
        "research.information_selection",
    },
    "eng_c5_ch07": {
        "reading.poetic_language",
        "vocab.word_formation",
        "grammar.pronouns",
        "grammar.question_formation",
        "writing.procedure",
        "vocab.antonyms",
    },
    "eng_c5_ch08": {
        "reading.event_sequence",
        "reading.dialogue_attribution",
        "reading.inference_reason",
        "grammar.prepositions",
        "writing.friendly_message",
        "vocab.word_formation",
    },
}
EXPECTED_UNIT_TITLES = {
    "eng_c5_ch06": "Water",
    "eng_c5_ch07": "Ups and Downs",
    "eng_c5_ch08": "Ups and Downs",
}
INTERNAL_LEARNER_TERMS = (
    "browser lesson",
    "chapter-check stimulus",
    "lesson exemplar",
    "scored response",
    "typed response",
    "typed work",
    "certifies",
    "certification",
)
ATOMIC_PROMPT_PARTS = {
    "eng_c5_ch06": {
        "tank-purpose-sequence-transfer-2": ("main_idea", "supporting_detail"),
        "tank-design-inference:guided:3": (
            "practical_feature",
            "identity_feature",
        ),
        "tank-design-inference:bridge:1": (
            "practical_feature",
            "identity_feature",
        ),
        "tank-purpose-sequence:guided:3": ("first", "next", "last"),
        "tank-purpose-sequence:bridge:1": ("first", "next", "last"),
        "tank-design-inference-guided-1": ("function", "identity"),
        "tank-design-inference:guided:4": ("function", "identity"),
        "tank-design-inference-independent-1": ("identity", "function"),
        "tank-design-inference-review-1": ("decision", "reason"),
        "tank-design-inference:revision_level_1:1": ("function", "identity"),
        "tank-contractions-independent-2": ("first_contraction", "second_contraction"),
        "tank-contractions-review-1": ("first_contraction", "second_contraction"),
        "tank-exclamation-emotion-independent-1": ("punctuation", "context"),
        "tank-exclamation-emotion-independent-2": ("emotion", "cause"),
        "tank-animal-word-meaning:guided:3": ("adult", "young", "group"),
        "tank-animal-word-meaning:guided:4": ("adult", "young", "group"),
        "tank-animal-word-meaning-review-1": ("thanked", "caretaker"),
        "tank-animal-word-meaning:bridge:1": ("adult", "young", "group"),
        "tank-animal-word-meaning:revision_level_1:1": (
            "shelter",
            "young",
            "group",
        ),
        "tank-animal-word-meaning:revision_level_2:1": ("young", "group"),
        "eng_c5_ch06-assessment-tank-design-inference-3": (
            "information",
            "weather",
        ),
        "eng_c5_ch06-assessment-tank-contractions-4": (
            "first_contraction",
            "second_contraction",
        ),
        "eng_c5_ch06-assessment-tank-contractions-5": ("rule", "example"),
        "eng_c5_ch06-assessment-tank-exclamation-emotion-3": (
            "emotion",
            "cause",
        ),
        "eng_c5_ch06-assessment-tank-animal-word-meaning-4": (
            "adult",
            "young",
            "group",
        ),
    },
    "eng_c5_ch07": {
        "gilli-poetic-meaning-transfer-2": ("event", "mood_change"),
        "gilli-prefix-formation:guided:3": ("formed_word", "sentence_use"),
        "gilli-prefix-formation-independent-1": ("prefix_meaning", "context_use"),
        "gilli-prefix-formation-independent-2": ("prefix_meaning", "context_use"),
        "gilli-concrete-abstract:guided:3": ("concrete", "abstract"),
        "gilli-concrete-abstract:guided:4": ("quality", "evidence"),
        "gilli-concrete-abstract-independent-1": ("classification", "reason"),
        "gilli-concrete-abstract-independent-2": ("classification", "reason"),
        "gilli-concrete-abstract-transfer-1": ("concrete", "abstract"),
        "gilli-concrete-abstract-transfer-2": ("correction", "reason"),
        "gilli-concrete-abstract:bridge:1": ("classification", "reason"),
        "gilli-concrete-abstract:masterclass:1": ("classification", "evidence"),
        "gilli-concrete-abstract:revision_level_2:1": ("quality", "evidence"),
        "gilli-possessive-pronouns-independent-1": ("pronoun", "reason"),
        "gilli-possessive-pronouns-independent-2": ("pronoun", "reason"),
        "gilli-possessive-pronouns-transfer-1": ("pronoun", "reason"),
        "gilli-source-questions-transfer-1": ("question", "answer"),
        "gilli-spelling-opposites-transfer-2": ("winner", "loser"),
        "eng_c5_ch07-assessment-gilli-possessive-pronouns-3": (
            "pronoun",
            "reason",
        ),
        "eng_c5_ch07-assessment-gilli-possessive-pronouns-5": (
            "pronoun",
            "reason",
        ),
        "eng_c5_ch07-assessment-gilli-spelling-opposites-4": (
            "spelling_check",
            "antonym_check",
        ),
    },
    "eng_c5_ch08": {
        "panchayat-sequence-summary:bridge:1": ("first", "next", "last"),
        "panchayat-dialogue-attribution:guided:3": (
            "speaker",
            "listener",
            "request",
        ),
        "panchayat-dialogue-attribution:review:3": (
            "questioner",
            "answerer",
            "reference",
        ),
        "panchayat-dialogue-attribution:guided:4": ("reference", "purpose"),
        "panchayat-dialogue-attribution-independent-2": ("speaker", "condition"),
        "panchayat-dialogue-attribution-transfer-2": ("speaker", "reason"),
        "panchayat-dialogue-attribution:transfer:4": (
            "problem_speaker",
            "problem",
            "response_speaker",
            "response",
        ),
        "panchayat-dialogue-attribution:revision_level_2:1": (
            "reference",
            "evidence",
        ),
        "panchayat-language-relations-independent-1": (
            "direction",
            "position",
            "surface",
        ),
        "panchayat-language-relations-independent-2": ("claim", "evidence"),
        "panchayat-language-relations-transfer-1": ("group", "position"),
        "panchayat-language-relations-review-1": ("time", "movement"),
        "panchayat-past-chronology:guided:3": ("earlier_event", "verb_form"),
        "panchayat-past-chronology-review-2": ("first", "second"),
        "panchayat-clue-prediction-independent-2": (
            "supported_action",
            "prediction",
        ),
        "panchayat-less-words:guided:3": ("formed_word", "sentence_use"),
        "panchayat-less-words-transfer-2": ("meaning", "alternative"),
        "panchayat-less-words:revision_level_1:1": ("base", "meaning"),
        "panchayat-bounded-research-transfer-1": ("storage", "record_fields"),
        "eng_c5_ch08-assessment-panchayat-sequence-summary-3": (
            "claim",
            "evidence",
            "response",
        ),
        "eng_c5_ch08-assessment-panchayat-language-relations-4": (
            "relationship_strategy",
            "context_strategy",
        ),
        "eng_c5_ch08-assessment-panchayat-past-chronology-3": (
            "earlier",
            "later",
        ),
        "eng_c5_ch08-assessment-panchayat-past-chronology-4": (
            "form",
            "purpose",
        ),
        "eng_c5_ch08-assessment-panchayat-bounded-research-3": (
            "material",
            "preparation",
            "product",
            "boundary",
        ),
    },
}


def _chapter_path(chapter_id: str) -> Path:
    return CHAPTER_ROOT / f"{chapter_id}.json"


def _manifest_path(chapter_id: str) -> Path:
    candidates = (
        MANIFEST_ROOT / f"{chapter_id}.py",
        MANIFEST_ROOT / f"{chapter_id}.json",
    )
    return next(path for path in candidates if path.is_file())


def _normalized_task(activity: dict) -> str:
    return " ".join(
        f"{activity['passage']} {activity['prompt']}".casefold().split()
    )


def _normalized_words(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", value.casefold())


def _activity_by_variant(chapter_id: str, variant_id: str) -> dict:
    payload = json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))
    matches = []
    for level in payload["levels"]:
        for step in level["teaching_steps"]:
            activities = (
                [step["activity"]]
                if step.get("activity") is not None
                else step["variant_pool"]
            )
            matches.extend(
                activity
                for activity in activities
                if activity.get("variant_id") == variant_id
            )

    assert len(matches) == 1
    return matches[0]


def _embedded_json_manifest(path: Path) -> dict:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for statement in module.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "MANIFEST"
            for target in statement.targets
        ):
            continue
        value = statement.value
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id == "json"
            and value.func.attr == "loads"
            and value.args
            and isinstance(value.args[0], ast.Constant)
            and isinstance(value.args[0].value, str)
        ):
            continue
        return json.loads(value.args[0].value)
    raise AssertionError(f"embedded MANIFEST json not found: {path}")


def _manifest_activity(chapter_id: str, activity_id: str) -> dict:
    manifest = load_manifest(_manifest_path(chapter_id)).model_dump(mode="json")
    matches = [
        node
        for node in _dict_nodes(manifest)
        if node.get("activity_id") == activity_id
    ]
    assert len(matches) == 1
    return matches[0]


def _dict_nodes(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _dict_nodes(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _dict_nodes(nested)


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_each_chapter_has_one_canonical_manifest_authority(chapter_id: str) -> None:
    candidates = (
        MANIFEST_ROOT / f"{chapter_id}.py",
        MANIFEST_ROOT / f"{chapter_id}.json",
    )
    existing = [path for path in candidates if path.is_file()]

    assert existing == [MANIFEST_ROOT / f"{chapter_id}.py"]


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_canonical_manifest_compiles_to_reviewed_runtime_without_drift(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))
    built = LiveSchoolChapter.model_validate(build_deep_chapter(None, manifest))
    reviewed = load_live_chapter_file(_chapter_path(chapter_id))

    assert built.runtime_dict() == reviewed.runtime_dict()
    assert built.runtime_sha256 == reviewed.runtime_sha256


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_deep_chapter_manifest_and_runtime_are_complete(chapter_id: str) -> None:
    manifest_path = _manifest_path(chapter_id)
    chapter_path = _chapter_path(chapter_id)

    assert manifest_path.is_file()
    assert chapter_path.is_file()

    manifest = load_manifest(manifest_path).model_dump(mode="json")
    chapter = load_live_chapter_file(chapter_path)

    assert manifest["schema_version"] == "school-class5-deep-manifest-v1"
    assert manifest["chapter"]["authorship"] == {
        "zidd_authored_original": True,
        "textbook_body_or_questions_copied": False,
        "source_analysis_reference": "official NCERT structural exercise matrix reviewed 2026-07-15",
    }
    assert chapter.approval_status == "agent_reviewed"
    assert chapter.reviewed_by == "codex-school-content-review"
    assert chapter.reviewed_at
    assert chapter.review_evidence
    assert manifest["chapter"]["unit_title"] == EXPECTED_UNIT_TITLES[chapter_id]
    assert chapter.unit_title == EXPECTED_UNIT_TITLES[chapter_id]
    assert 7 <= len(chapter.levels) <= 9
    assert len(chapter.source_anchors or []) >= 4

    taught_skills = {
        skill_id for level in chapter.levels for skill_id in level.skill_ids
    }
    assert len(taught_skills) <= 16
    assert REQUIRED_SKILLS[chapter_id] <= taught_skills

    for level in chapter.levels:
        assert tuple(step.phase for step in level.teaching_steps or ()) == PHASES
        by_phase = {step.phase: step for step in level.teaching_steps or ()}
        assert len(by_phase["guided_practice"].variant_pool or ()) >= 4
        assert len(by_phase["independent_application"].variant_pool or ()) >= 4
        assert len(by_phase["transfer"].variant_pool or ()) >= 4
        assert len(by_phase["review"].variant_pool or ()) >= 4

        variant_ids: list[str] = []
        signatures: list[tuple[str, str, str]] = []
        for step in level.teaching_steps or ():
            activities = list(step.variant_pool or ())
            if step.activity is not None:
                activities.append(step.activity)
            for activity in activities:
                if activity.variant_id:
                    variant_ids.append(activity.variant_id)
                signatures.append(
                    (activity.teaching_block, activity.passage, activity.prompt)
                )
                if activity.evidence_role == "certifying":
                    assert not any(
                        skill_id.startswith(("speaking.", "listening."))
                        for skill_id in activity.knowledge_components or ()
                    )

        assert len(variant_ids) == len(set(variant_ids))
        assert len(signatures) == len(set(signatures))
        assert level.checks.bridge is not None
        assert level.checks.masterclass is not None
        assert level.checks.revision_level_1 is not None
        assert level.checks.revision_level_2 is not None
        assert level.checks.revision_level_3 is not None

    assessment = chapter.chapter_assessment
    assert assessment is not None
    assert assessment.items_per_attempt == 16
    assert assessment.max_attempts == 2
    assert len(assessment.items) == 32

    assessed_skills = {
        skill_id for item in assessment.items for skill_id in item.skill_ids
    }
    assert assessed_skills == taught_skills
    assert not any(
        skill_id.startswith(("speaking.", "listening."))
        for skill_id in assessed_skills
    )
    for skill_id in assessed_skills:
        assert sum(skill_id in item.skill_ids for item in assessment.items) >= 2

    manifests_levels = {level["level_id"]: level for level in manifest["levels"]}
    for strand in manifest["chapter_assessment"]["strands"]:
        remediated = {
            skill_id
            for level_id in strand["remediation_level_ids"]
            for cluster in manifests_levels[level_id]["misconception_clusters"]
            for skill_id in cluster["skill_ids"]
        }
        assert set(strand["skill_ids"]) <= remediated


def test_chapter_six_assessment_mix_limits_open_grading_and_keeps_complete_forms(
) -> None:
    payload = json.loads(_chapter_path("eng_c5_ch06").read_text(encoding="utf-8"))
    assessment = payload["chapter_assessment"]
    items = assessment["items"]
    items_by_id = {item["item_id"]: item for item in items}
    taught_skills = {
        skill_id for level in payload["levels"] for skill_id in level["skill_ids"]
    }

    strict_open = [
        item for item in items if item["grading_mode"] == "strict_open_rubric"
    ]
    selected = [
        item for item in items if item["grading_mode"] == "selected_option"
    ]

    assert len(strict_open) <= 16
    assert len(selected) >= 16

    planned_forms = _plan_two_fresh_assessment_forms(
        items,
        item_count=assessment["items_per_attempt"],
    )
    assert len(planned_forms) == 2
    assert set(planned_forms[0]).isdisjoint(planned_forms[1])
    assert set(planned_forms[0]) | set(planned_forms[1]) == set(items_by_id)

    for form_ids in planned_forms:
        form = [items_by_id[item_id] for item_id in form_ids]
        assert len(form) == assessment["items_per_attempt"]
        assert {
            skill_id for item in form for skill_id in item["skill_ids"]
        } == taught_skills


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_transfer_and_review_are_fresh_strict_and_cover_exact_level_skills(
    chapter_id: str,
) -> None:
    payload = json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))

    for level in payload["levels"]:
        level_skills = set(level["skill_ids"])
        by_phase = {step["phase"]: step for step in level["teaching_steps"]}
        certifying_activities = [
            activity
            for phase in ("independent_application", "transfer", "review")
            for activity in by_phase[phase]["variant_pool"]
        ]
        certifying_tasks = [
            _normalized_task(activity) for activity in certifying_activities
        ]

        assert len(certifying_tasks) == len(set(certifying_tasks))
        for left, right in combinations(certifying_tasks, 2):
            assert SequenceMatcher(None, left, right).ratio() < 0.88

        for phase in ("transfer", "review"):
            variants = by_phase[phase]["variant_pool"]
            assert len(variants) >= 4
            assert {
                skill_id
                for activity in variants
                for skill_id in activity["knowledge_components"]
            } == level_skills

            for activity in variants:
                assert activity["options"] == []
                assert activity["grading_mode"] == "strict_open_rubric"
                assert activity["evaluation_mode"] == "llm_rubric"
                assert activity["evidence_role"] == "certifying"
                assert activity["certifying_language"] == "en"
                assert set(activity["knowledge_components"]) <= level_skills
                assert activity["source_anchor_ids"]
                assert len(_normalized_words(activity["model_answer"])) >= activity[
                    "min_response_words"
                ]

                criteria = {item["id"]: item for item in activity["rubric_criteria"]}
                slots = {item["id"]: item for item in activity["concept_slots"]}
                assert criteria.keys() == slots.keys()
                assert all(item["required"] for item in criteria.values())
                normalized_answer = " ".join(
                    activity["model_answer"].casefold().split()
                )
                for slot in slots.values():
                    assert any(
                        " ".join(alias.casefold().split()) in normalized_answer
                        for alias in slot["any_of"]
                    )


def test_deep_chapter_choice_keys_do_not_follow_a_first_option_pattern() -> None:
    answer_positions: list[int] = []
    for chapter_id in sorted(REQUIRED_SKILLS):
        payload = json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8"))
        for level in payload["levels"]:
            for step in level["teaching_steps"]:
                activities = step.get("variant_pool") or [step.get("activity")]
                for activity in activities:
                    if not activity or activity.get("grading_mode") != "selected_option":
                        continue
                    answer_positions.append(
                        activity["options"].index(activity["accepted_answers"][0])
                    )
        for item in payload["chapter_assessment"]["items"]:
            if item.get("grading_mode") != "selected_option":
                continue
            answer_positions.append(
                item["options"].index(item["accepted_answers"][0])
            )

    assert len(answer_positions) >= 80
    assert set(answer_positions) >= {0, 1, 2}
    assert answer_positions.count(0) / len(answer_positions) < 0.5


def test_chapters_six_to_eight_hide_platform_language_from_learners() -> None:
    learner_keys = {
        "teaching_block",
        "passage",
        "prompt",
        "teaching_goal",
        "title",
        "focus",
    }

    def visit(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in learner_keys and isinstance(value, str):
                    lowered = value.casefold()
                    assert not any(term in lowered for term in INTERNAL_LEARNER_TERMS)
                else:
                    visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    for chapter_id in sorted(REQUIRED_SKILLS):
        visit(json.loads(_chapter_path(chapter_id).read_text(encoding="utf-8")))


def test_gilli_source_questions_assess_both_question_and_source_answer() -> None:
    runtime = json.loads(_chapter_path("eng_c5_ch07").read_text(encoding="utf-8"))
    items = {
        item["item_id"]: item for item in runtime["chapter_assessment"]["items"]
    }
    for item_id in (
        "eng_c5_ch07-assessment-gilli-source-questions-1",
        "eng_c5_ch07-assessment-gilli-source-questions-2",
    ):
        item = items[item_id]
        assert item["grading_mode"] == "strict_open_rubric"
        assert not item["options"]
        assert item["model_answer"]
        assert len(item["concept_slots"]) >= 2
        assert {criterion["id"] for criterion in item["rubric_criteria"]} == {
            slot["id"] for slot in item["concept_slots"]
        }


def test_past_perfect_is_explicitly_zidd_strengthening_not_ncert_required() -> None:
    runtime = json.loads(_chapter_path("eng_c5_ch08").read_text(encoding="utf-8"))
    level = next(
        level
        for level in runtime["levels"]
        if level["level_id"] == "panchayat-past-chronology"
    )
    anchors = {anchor["anchor_id"]: anchor for anchor in runtime["source_anchors"]}

    assert "strengthening" in level["title"].casefold()
    assert level["source_anchor_ids"] == ["eng_c5_ch08:zidd-strengthening:chronology"]
    strengthening = anchors[level["source_anchor_ids"][0]]
    assert "strengthening" in strengthening["section_label"].casefold()
    assert strengthening["required_for_chapter_certification"] is False
    assert "chronology" not in anchors["eng_c5_ch08:language:6-8"][
        "section_label"
    ].casefold()


def test_cited_implausible_distractors_are_removed() -> None:
    all_options = {
        option.casefold()
        for chapter_id in sorted(REQUIRED_SKILLS)
        for item in json.loads(
            _chapter_path(chapter_id).read_text(encoding="utf-8")
        )["chapter_assessment"]["items"]
        for option in item["options"]
    }
    assert "the lane asks why" not in all_options
    assert "the trolley owns the card" not in all_options


def test_chapter_eight_semicolon_choice_segments_match_passage_blanks() -> None:
    manifest_path = _manifest_path("eng_c5_ch08")
    sources = (
        ("manifest", _embedded_json_manifest(manifest_path)),
        ("runtime", json.loads(_chapter_path("eng_c5_ch08").read_text())),
    )
    checked = set()
    violations = []

    for origin, payload in sources:
        for activity in _dict_nodes(payload):
            selected_option = (
                activity.get("kind") == "selected_option"
                or activity.get("grading_mode") == "selected_option"
            )
            options = activity.get("options")
            if not selected_option or not options:
                continue
            if not all(isinstance(option, str) and ";" in option for option in options):
                continue

            activity_id = (
                activity.get("activity_id")
                or activity.get("variant_id")
                or activity.get("item_id")
                or activity.get("prompt")
            )
            blank_count = activity.get("passage", "").count("___")
            invalid_answers = []
            for answer in options + activity.get("accepted_answers", []):
                segments = [segment.strip() for segment in answer.split(";")]
                if len(segments) != blank_count or not all(segments):
                    invalid_answers.append((answer, len(segments)))

            checked.add((origin, activity_id))
            if invalid_answers:
                violations.append(
                    {
                        "origin": origin,
                        "activity_id": activity_id,
                        "blank_count": blank_count,
                        "invalid_answers": invalid_answers,
                    }
                )

    assert checked
    assert violations == []


def test_panchayat_fairness_remedy_is_grounded_in_an_explicit_policy_card() -> None:
    activity = _activity_by_variant(
        "eng_c5_ch08",
        "panchayat-fairness-reasoning-guided-1",
    )
    passage = activity["passage"].casefold()
    model_answer = activity["model_answer"].casefold()

    assert "policy card:" in passage
    assert "record every late arrival" in passage
    assert "verified transport breakdown" in passage
    assert "give a late slip when a student left home late" in passage
    assert "record all three late arrivals" in model_answer
    assert "do not issue a late slip" in model_answer
    assert "issue late slips to the two students who left home late" in model_answer
    assert "policy" in model_answer


@pytest.mark.parametrize(
    ("chapter_id", "activity_id", "expected_suffixes"),
    [
        (chapter_id, activity_id, suffixes)
        for chapter_id, activities in ATOMIC_PROMPT_PARTS.items()
        for activity_id, suffixes in activities.items()
    ],
)
def test_explicit_prompt_parts_have_atomic_evidence_and_matching_guidance(
    chapter_id: str,
    activity_id: str,
    expected_suffixes: tuple[str, ...],
) -> None:
    activity = _manifest_activity(chapter_id, activity_id)
    expected_ids = [f"{activity_id}:{suffix}" for suffix in expected_suffixes]

    assert [item["id"] for item in activity["rubric_criteria"]] == expected_ids
    assert [item["id"] for item in activity["concept_slots"]] == expected_ids
    assert len({item["description"] for item in activity["concept_slots"]}) == len(
        expected_ids
    )
    guidance = (
        "include both details"
        if len(expected_ids) == 2
        else f"include all {len(expected_ids)} details"
    )
    assert guidance in activity["teaching_block"].casefold()

    normalized_answer = " ".join(activity["model_answer"].casefold().split())
    for slot in activity["concept_slots"]:
        assert any(
            " ".join(alias.casefold().split()) in normalized_answer
            for alias in slot["any_of"]
        )


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_selected_options_do_not_issue_constructed_response_commands(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id)).model_dump(mode="json")
    production_command = re.compile(
        r"^(?:build|complete|fill|make|report|rewrite|write)\b",
        re.IGNORECASE,
    )
    offenders = {
        node["activity_id"]: node["prompt"]
        for node in _dict_nodes(manifest)
        if node.get("kind") == "selected_option"
        and production_command.match(node.get("prompt", "").strip())
    }

    assert offenders == {}


def test_gilli_certifying_pools_replace_word_swap_prompt_templates() -> None:
    manifest = load_manifest(_manifest_path("eng_c5_ch07")).model_dump(mode="json")
    level_ids = {
        "gilli-prefix-formation",
        "gilli-concrete-abstract",
        "gilli-possessive-pronouns",
    }

    for level in manifest["levels"]:
        if level["level_id"] not in level_ids:
            continue
        activities = [
            *level["independent_variants"][:2],
            *level["transfer_variants"][:2],
            *level["review_variants"][:2],
        ]
        templates = [
            re.sub(
                r"'[^']+'|\b\d+\b",
                "<target>",
                " ".join(activity["prompt"].casefold().split()),
            )
            for activity in activities
        ]
        assert len(templates) == len(set(templates))
        for left, right in combinations(templates, 2):
            assert SequenceMatcher(None, left, right).ratio() < 0.88


@pytest.mark.parametrize("chapter_id", sorted(REQUIRED_SKILLS))
def test_assessment_directions_are_child_facing_and_count_required_details(
    chapter_id: str,
) -> None:
    manifest = load_manifest(_manifest_path(chapter_id))

    for activity in manifest.chapter_assessment.items:
        direction = activity.teaching_block.casefold()
        assert "chapter-check stimulus" not in direction
        assert "lesson exemplar" not in direction
        if activity.kind == "selected_option":
            continue
        criterion_count = len(activity.rubric_criteria)
        guidance = (
            "include the detail the question asks for"
            if criterion_count == 1
            else "include both details"
            if criterion_count == 2
            else f"include all {criterion_count} details"
        )
        assert guidance in direction


def test_picture_prediction_instruction_names_the_visible_zidd_stimulus() -> None:
    manifest = load_manifest(_manifest_path("eng_c5_ch08"))
    level = next(
        level
        for level in manifest.levels
        if level.level_id == "panchayat-clue-prediction"
    )
    direction = level.connect.teaching_block.casefold()

    assert "the chapter includes" not in direction
    assert "written scene card" in direction
    assert "visible clues" in direction
