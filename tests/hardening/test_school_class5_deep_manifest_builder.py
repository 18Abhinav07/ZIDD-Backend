from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from app.content.school_rebuild_schema import LiveSchoolChapter
from scripts.build_school_deep_chapter import build_deep_chapter
from scripts.mark_school_chapter_agent_reviewed import mark_agent_reviewed


SKILL_ID = "grammar.tense_usage"
LEVEL_ID = "fixture_tense_level"


def _legacy_activity(name: str, *, choice: bool) -> dict:
    if choice:
        return {
            "teaching_block": f"Legacy teaching block for {name} with enough distinct detail.",
            "passage": f"Legacy passage for {name} describes a complete classroom event.",
            "prompt": f"Which answer is correct for {name}?",
            "options": [f"{name} correct", f"{name} distractor"],
            "accepted_answers": [f"{name} correct"],
            "response_mode": "short",
        }
    return {
        "teaching_block": f"Legacy teaching block for {name} with enough distinct detail.",
        "passage": f"Legacy passage for {name} describes a complete classroom event.",
        "prompt": f"Write the exact response for {name}.",
        "options": [],
        "accepted_answers": [f"{name} answer"],
        "response_mode": "short",
    }


def _assessment_item(index: int) -> dict:
    common = {
        "item_id": f"assessment-{index}",
        "passage": f"Assessment passage {index} contains an original classroom event.",
        "prompt": f"Complete assessment task number {index}.",
        "skill_ids": [SKILL_ID],
    }
    if index < 10:
        return {
            **common,
            "options": [f"correct-{index}", f"wrong-{index}"],
            "accepted_answers": [f"correct-{index}"],
            "grading_mode": "selected_option",
            "response_mode": "short",
        }
    return {
        **common,
        "options": [],
        "accepted_answers": [f"answer-{index}"],
        "grading_mode": "exact_text",
        "response_mode": "short",
    }


def _chapter_payload() -> dict:
    checks = {
        "guided_check": _legacy_activity("guided", choice=True),
        "bridge": _legacy_activity("bridge", choice=True),
        "masterclass": _legacy_activity("masterclass", choice=True),
        "revision_level_1": _legacy_activity("revision-one", choice=True),
        "revision_level_2": _legacy_activity("revision-two", choice=True),
        "revision_level_3": _legacy_activity("revision-three", choice=True),
        "independent_check": _legacy_activity("independent", choice=False),
        "transfer_check": _legacy_activity("transfer", choice=False),
    }
    return {
        "approval_status": "draft",
        "review_evidence": [],
        "runtime_sha256": "0" * 64,
        "chapter_id": "eng_c5_ch99",
        "chapter_no": 99,
        "title": "Fixture chapter",
        "book_title": "Santoor",
        "unit_title": "Fixture unit",
        "source_url": "https://ncert.nic.in/textbook/pdf/eesa199.pdf",
        "source_note": "Structural alignment only; all fixture content is original.",
        "levels": [
            {
                "level_id": LEVEL_ID,
                "title": "Use tense in context",
                "focus": "choose and produce accurate tense forms",
                "skill_ids": [SKILL_ID],
                "teaching_goal": "Use the target tense accurately in a complete context.",
                "checks": checks,
            }
        ],
        "chapter_assessment": {
            "items_per_attempt": 10,
            "pass_score": 0.8,
            "max_attempts": 2,
            "items": [_assessment_item(index) for index in range(20)],
        },
    }


def _choice(activity_id: str) -> dict:
    return {
        "kind": "selected_option",
        "activity_id": activity_id,
        "teaching_block": f"Use the time clue in the {activity_id} example before choosing.",
        "passage": f"For {activity_id}, Reema finished the task before the bell rang.",
        "prompt": f"Which tense form completes the {activity_id} sentence correctly?",
        "skill_ids": [SKILL_ID],
        "options": [f"{activity_id} correct", f"{activity_id} incorrect"],
        "accepted_answers": [f"{activity_id} correct"],
    }


def _open(activity_id: str) -> dict:
    criterion_id = f"{activity_id}-tense"
    return {
        "kind": "open_response",
        "activity_id": activity_id,
        "teaching_block": f"Build the {activity_id} answer independently from the time relationship.",
        "passage": f"In {activity_id}, Kavya completed her notes before the teacher collected them.",
        "prompt": f"Write one complete sentence for {activity_id} using the required tense.",
        "skill_ids": [SKILL_ID],
        "interaction_type": "paragraph_text",
        "rubric_criteria": [
            {
                "id": criterion_id,
                "description": "Uses the required tense in a complete sentence.",
                "required": True,
                "min_quality": 0.7,
            }
        ],
        "concept_slots": [
            {
                "id": criterion_id,
                "description": "Uses the required tense in a complete sentence.",
                "any_of": ["had completed", "had finished"],
            }
        ],
        "forbidden_phrases": ["I do not know"],
        "min_response_words": 6,
        "relevance_terms": ["completed", "teacher"],
        "model_answer": "Kavya had completed her notes before the teacher collected them.",
        "pass_score": 0.8,
    }


def _ordered(activity_id: str) -> dict:
    return {
        "kind": "ordered_slots",
        "activity_id": activity_id,
        "teaching_block": (
            f"Use the stated rule to order every item in the {activity_id} task."
        ),
        "passage": (
            f"For {activity_id}, arrange seed, lemon, and melon from the smallest "
            "width to the greatest width."
        ),
        "prompt": f"Order the three objects correctly in the {activity_id} task.",
        "skill_ids": [SKILL_ID],
        "interaction_type": "ordering",
        "concept_slots": [
            {
                "id": f"{activity_id}-first",
                "description": "The smallest object is first.",
                "any_of": ["seed"],
            },
            {
                "id": f"{activity_id}-second",
                "description": "The middle-sized object is second.",
                "any_of": ["lemon"],
            },
            {
                "id": f"{activity_id}-third",
                "description": "The largest object is third.",
                "any_of": ["melon"],
            },
        ],
        "ordered_concept_slot_ids": [
            f"{activity_id}-first",
            f"{activity_id}-second",
            f"{activity_id}-third",
        ],
    }


def _manifest_payload() -> dict:
    support_ids = [
        "support-bridge",
        "support-masterclass",
        "support-revision-one",
        "support-revision-two",
        "support-revision-three",
    ]
    return {
        "schema_version": "school-class5-deep-manifest-v1",
        "chapter": {
            "chapter_id": "eng_c5_ch99",
            "chapter_no": 99,
            "title": "Fixture chapter deep loop",
            "book_title": "Santoor",
            "unit_title": "Fixture unit",
            "source_url": "https://ncert.nic.in/textbook/pdf/eesa199.pdf",
            "source_note": "NCERT structural alignment only; all learner content is original.",
            "content_version": "2026-07-15.1",
            "certification_version": "2026-07-15.1",
            "authorship": {
                "zidd_authored_original": True,
                "textbook_body_or_questions_copied": False,
                "source_analysis_reference": "fixture structural exercise matrix",
            },
        },
        "source_anchors": [
            {
                "anchor_id": "eng_c5_ch99:learn:1",
                "section_label": "Language practice",
                "page_start": 1,
                "page_end": 2,
                "source_url": "https://ncert.nic.in/textbook/pdf/eesa199.pdf#page=1",
                "coverage_treatment": "zidd_equivalent",
                "required_for_chapter_certification": True,
            }
        ],
        "levels": [
            {
                "level_id": LEVEL_ID,
                "title": "Use tense in context",
                "focus": "choose and produce accurate tense forms",
                "outcome": "Use the target tense accurately in an original complete sentence.",
                "skill_ids": [SKILL_ID],
                "episode_kind": "language_lab",
                "source_anchor_ids": ["eng_c5_ch99:learn:1"],
                "connect": {
                    "teaching_block": "Time relationships help a reader choose a precise verb form.",
                    "passage": "Mina had packed her notebook before the school bus arrived.",
                    "prompt": "Continue when the before-and-after relationship is clear.",
                },
                "co_construct": _choice("co-construct"),
                "guided_variants": [
                    _choice(f"guided-{index}") for index in range(4)
                ],
                "independent_variants": [
                    _open(f"independent-{index}") for index in range(4)
                ],
                "transfer_variants": [
                    _open(f"transfer-{index}") for index in range(4)
                ],
                "review_variants": [
                    _open(f"review-{index}") for index in range(2)
                ],
                "misconception_clusters": [
                    {
                        "cluster_id": "tense-sequence-confusion",
                        "skill_ids": [SKILL_ID],
                        "misconception": "The learner selects a tense without first ordering the two events.",
                        "remediation": "Place both events on a timeline, then rebuild the sentence from that order.",
                        "support_check_ids": support_ids,
                    }
                ],
                "support_checks": {
                    "bridge": _choice(support_ids[0]),
                    "masterclass": _choice(support_ids[1]),
                    "revision_level_1": _choice(support_ids[2]),
                    "revision_level_2": _choice(support_ids[3]),
                    "revision_level_3": _choice(support_ids[4]),
                },
            }
        ],
        "chapter_assessment": {
            "items_per_attempt": 10,
            "pass_score": 0.8,
            "max_attempts": 2,
            "bank_item_count": 20,
            "items": [
                *[_choice(f"assessment-choice-{index}") for index in range(10)],
                *[_open(f"assessment-open-{index}") for index in range(10)],
            ],
            "strands": [
                {
                    "strand_id": "tense-use",
                    "skill_ids": [SKILL_ID],
                    "minimum_items": 20,
                    "evidence_forms": [
                        "selected_option",
                        "constructed_response",
                    ],
                    "remediation_level_ids": [LEVEL_ID],
                }
            ],
        },
    }


def test_deep_builder_emits_six_phase_draft_validated_by_live_chapter() -> None:
    source = _chapter_payload()
    built = build_deep_chapter(source, _manifest_payload())

    checked = LiveSchoolChapter.model_validate(built)
    assert built["approval_status"] == "draft"
    assert "reviewed_by" not in built
    assert source["levels"][0].get("teaching_steps") is None
    level = checked.levels[0]
    assert [step.phase for step in level.teaching_steps or []] == [
        "connect",
        "co_construct",
        "guided_practice",
        "independent_application",
        "transfer",
        "review",
    ]
    pools = {step.phase: step for step in level.teaching_steps or []}
    assert len(pools["guided_practice"].variant_pool or []) == 4
    assert len(pools["independent_application"].variant_pool or []) == 4
    assert len(pools["transfer"].variant_pool or []) == 4
    assert checked.calculated_runtime_sha256() == built["runtime_sha256"]


def test_deep_builder_can_create_complete_chapter_without_shallow_input() -> None:
    built = build_deep_chapter(None, _manifest_payload())

    checked = LiveSchoolChapter.model_validate(built)
    assert checked.chapter_id == "eng_c5_ch99"
    assert len(checked.levels) == 1
    assert checked.chapter_assessment is not None
    assert len(checked.chapter_assessment.items) == 20


def test_deep_builder_marks_certifying_deterministic_variant_as_english() -> None:
    manifest = _manifest_payload()
    manifest["levels"][0]["independent_variants"][0] = _ordered(
        "independent-order"
    )

    built = build_deep_chapter(None, manifest)

    activity = built["levels"][0]["teaching_steps"][3]["variant_pool"][0]
    assert activity["grading_mode"] == "ordered_slots"
    assert activity["evidence_role"] == "certifying"
    assert activity["certifying_language"] == "en"


def test_deep_builder_preserves_explicit_non_evidentiary_guided_role() -> None:
    manifest = _manifest_payload()
    guided = manifest["levels"][0]["guided_variants"][0]
    guided["skill_ids"] = []
    guided["evidence_role_override"] = "experience"

    built = build_deep_chapter(None, manifest)

    activity = built["levels"][0]["teaching_steps"][2]["variant_pool"][0]
    assert activity["knowledge_components"] == []
    assert activity["evidence_role"] == "experience"
    assert "certifying_language" not in activity


def test_deep_builder_can_author_a_distinct_choice_guided_check() -> None:
    manifest = _manifest_payload()
    manifest["source_anchors"].append(
        {
            "anchor_id": "eng_c5_ch99:learn:2",
            "section_label": "Expression practice",
            "page_start": 3,
            "page_end": 3,
            "source_url": "https://ncert.nic.in/textbook/pdf/eesa199.pdf#page=3",
            "coverage_treatment": "zidd_equivalent",
            "required_for_chapter_certification": False,
        }
    )
    manifest["levels"][0]["source_anchor_ids"].append("eng_c5_ch99:learn:2")
    manifest["levels"][0]["connect"]["source_anchor_ids_override"] = [
        "eng_c5_ch99:learn:1"
    ]
    manifest["levels"][0]["connect"]["knowledge_components_override"] = []
    manifest["levels"][0]["co_construct"] = _open("co-construct-open")
    manifest["levels"][0]["guided_pool_id"] = "fixture_tense_level:guided"
    manifest["levels"][0]["support_checks"]["guided_check"] = {
        **_choice("guided-check"),
        "teaching_phase_override": "guided_practice",
        "source_anchor_ids_override": ["eng_c5_ch99:learn:1"],
    }
    manifest["levels"][0]["support_checks"]["independent_check"] = _open(
        "independent-check"
    )
    manifest["levels"][0]["support_checks"]["transfer_check"] = _open(
        "transfer-check"
    )

    built = build_deep_chapter(None, manifest)

    guided_check = built["levels"][0]["checks"]["guided_check"]
    connect = built["levels"][0]["teaching_steps"][0]["activity"]
    assert connect["source_anchor_ids"] == ["eng_c5_ch99:learn:1"]
    assert connect["knowledge_components"] == []
    assert guided_check["grading_mode"] == "selected_option"
    assert guided_check["options"]
    assert guided_check["teaching_phase"] == "guided_practice"
    assert guided_check["source_anchor_ids"] == ["eng_c5_ch99:learn:1"]
    assert guided_check["prompt"] == _choice("guided-check")["prompt"]
    assert (
        built["levels"][0]["teaching_steps"][2]["pool_id"]
        == "fixture_tense_level:guided"
    )
    assert (
        built["levels"][0]["checks"]["independent_check"]["prompt"]
        == _open("independent-check")["prompt"]
    )
    assert (
        built["levels"][0]["checks"]["transfer_check"]["prompt"]
        == _open("transfer-check")["prompt"]
    )


@pytest.mark.parametrize("items_per_attempt", [10, 16, 20])
def test_deep_builder_preserves_configurable_items_per_attempt(
    items_per_attempt: int,
) -> None:
    manifest = _manifest_payload()
    manifest["chapter_assessment"]["items_per_attempt"] = items_per_attempt

    built = build_deep_chapter(None, manifest)

    checked = LiveSchoolChapter.model_validate(built)
    assert checked.chapter_assessment is not None
    assert checked.chapter_assessment.items_per_attempt == items_per_attempt
    assert checked.calculated_runtime_sha256() == built["runtime_sha256"]


def test_deep_builder_replaces_shallow_level_set_with_manifest_authority() -> None:
    source = _chapter_payload()
    legacy_extra = copy.deepcopy(source["levels"][0])
    legacy_extra["level_id"] = "legacy_extra_level"
    legacy_extra["title"] = "Legacy extra level"
    source["levels"].append(legacy_extra)

    built = build_deep_chapter(source, _manifest_payload())

    assert [level["level_id"] for level in built["levels"]] == [LEVEL_ID]


def test_deep_manifest_rejects_missing_variant_depth() -> None:
    manifest = _manifest_payload()
    manifest["levels"][0]["guided_variants"] = manifest["levels"][0][
        "guided_variants"
    ][:1]

    with pytest.raises(ValidationError, match="guided_variants"):
        build_deep_chapter(_chapter_payload(), manifest)


def test_deep_manifest_rejects_open_model_below_its_response_floor() -> None:
    manifest = copy.deepcopy(_manifest_payload())
    manifest["levels"][0]["independent_variants"][0]["model_answer"] = (
        "Kavya had completed."
    )

    with pytest.raises(ValidationError, match="deep_manifest_model_below_word_floor"):
        build_deep_chapter(_chapter_payload(), manifest)


def test_deep_manifest_rejects_open_model_missing_a_required_concept_slot() -> None:
    manifest = copy.deepcopy(_manifest_payload())
    manifest["levels"][0]["independent_variants"][0]["concept_slots"][0][
        "any_of"
    ] = ["will have completed", "future perfect"]

    with pytest.raises(ValidationError, match="deep_manifest_model_missing_slot"):
        build_deep_chapter(_chapter_payload(), manifest)


def test_deep_manifest_rejects_alias_shared_across_required_slots() -> None:
    manifest = copy.deepcopy(_manifest_payload())
    activity = manifest["levels"][0]["independent_variants"][0]
    shared_alias = activity["concept_slots"][0]["any_of"][0]
    activity["rubric_criteria"].append(
        {
            "id": "independent-0-result",
            "description": "States the result as a separate claim.",
            "required": True,
            "min_quality": 0.7,
        }
    )
    activity["concept_slots"].append(
        {
            "id": "independent-0-result",
            "description": "States the result as a separate claim.",
            "any_of": [shared_alias, "teacher collected the notes"],
        }
    )

    with pytest.raises(ValidationError, match="deep_manifest_alias_shared_across_slots"):
        build_deep_chapter(_chapter_payload(), manifest)


def test_deep_manifest_rejects_missing_remediation_mapping() -> None:
    manifest = _manifest_payload()
    manifest["levels"][0]["misconception_clusters"][0][
        "support_check_ids"
    ].pop()

    with pytest.raises(ValidationError, match="support_check_not_mapped"):
        build_deep_chapter(_chapter_payload(), manifest)


def test_selected_option_cannot_claim_writing_production() -> None:
    manifest = copy.deepcopy(_manifest_payload())
    manifest["levels"][0]["guided_variants"][0]["skill_ids"] = [
        "writing.complete_sentence"
    ]

    with pytest.raises(ValidationError, match="productive_skill"):
        build_deep_chapter(_chapter_payload(), manifest)


@pytest.mark.parametrize("class_no", [2, 3, 4, 5])
def test_deep_manifest_accepts_supported_english_classes(class_no: int) -> None:
    manifest = _manifest_payload()
    chapter_id = f"eng_c{class_no}_ch99"
    manifest["chapter"]["chapter_id"] = chapter_id

    built = build_deep_chapter(None, manifest)

    checked = LiveSchoolChapter.model_validate(built)
    assert checked.chapter_id == chapter_id
    assert checked.calculated_runtime_sha256() == built["runtime_sha256"]


@pytest.mark.parametrize(
    "chapter_id",
    [
        "eng_c1_ch01",
        "eng_c6_ch01",
        "math_c2_ch01",
        "hin_c3_ch01",
        "eng_c2_ch1",
        "eng_c2_ch001",
        "eng_c02_ch01",
        "eng_c2_unit01",
        "eng_c2_chab",
    ],
)
def test_deep_manifest_rejects_unsupported_or_malformed_chapter_ids(
    chapter_id: str,
) -> None:
    manifest = _manifest_payload()
    manifest["chapter"]["chapter_id"] = chapter_id

    with pytest.raises(ValidationError, match="chapter_id"):
        build_deep_chapter(None, manifest)


def test_agent_review_promotion_is_explicit_and_hash_stable() -> None:
    built = build_deep_chapter(_chapter_payload(), _manifest_payload())

    reviewed = mark_agent_reviewed(
        built,
        reviewed_by="Codex bounded content review",
        reviewed_at="2026-07-15T12:00:00+05:30",
        review_evidence=["manifest review", "runtime pedagogy checks"],
    )

    checked = LiveSchoolChapter.model_validate(reviewed)
    assert reviewed["approval_status"] == "agent_reviewed"
    assert reviewed["reviewed_by"] == "Codex bounded content review"
    assert checked.calculated_runtime_sha256() == reviewed["runtime_sha256"]
