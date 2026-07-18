from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.content.school import content_schema
from app.content.school.content_schema import (
    OpenAnswerRubric,
    OpenAnswerRubricCriterion,
    SchoolRubricEvaluation,
    SourceModuleRef,
)
from app.content.school.release_loader import load_release_manifest
from app.content.school.standards import (
    LOCKED_ENGLISH_SKILL_IDS,
    CompetencyFamilyRef,
    CompetencyFamilyRegistry,
    CompetencyStandardRef,
    CompetencyStandardRegistry,
    SkillTaxonomy,
    SkillTaxonomyEntry,
    locked_english_skill_ids,
    locked_english_taxonomy,
)
from app.services.school.evaluator_contract import (
    RUBRIC_SCHEMA_VERSION,
    SchoolCriterionPolicy,
    SchoolEvaluationContext,
    criterion_scores,
    parse_school_rubric_json,
    validate_school_rubric_evaluation,
)


VALID_RUBRIC_PAYLOAD = {
    "schema_version": "school-v3-rubric-1",
    "item_id": "chapter_reason_1",
    "skill_ids": ["writing.reason_answer"],
    "score": 0.86,
    "confidence": 0.92,
    "language_detected": "en",
    "criteria": [
        {
            "id": "answers_question",
            "met": True,
            "quality": 0.90,
            "evidence_quote": "because everyone helped",
        },
        {
            "id": "uses_reason_marker",
            "met": True,
            "quality": 0.82,
            "evidence_quote": "because",
        },
    ],
    "misconception_tags": [],
    "blockers": [],
    "needs_human_review": False,
    "feedback_to_learner": "Good reason. Keep naming the clue.",
}


def _family(
    skill_id: str,
    *,
    class_min: int = 2,
    prerequisites: tuple[str, ...] = (),
    subject_id: str = "english",
) -> CompetencyFamilyRef:
    return CompetencyFamilyRef(
        skill_id=skill_id,
        subject_id=subject_id,
        class_min=class_min,
        class_max=5,
        name=skill_id,
        description=f"Description for {skill_id}",
        prerequisite_skill_ids=prerequisites,
        certifying_language="en",
    )


def _standard(
    *,
    skill_id: str = "writing.reason_answer",
    proficiency_band: int = 3,
    taxonomy_version: str = "english-2026-27-v1",
    certification_epoch: str = "2026-27",
) -> CompetencyStandardRef:
    return CompetencyStandardRef(
        subject_id="english",
        skill_id=skill_id,
        proficiency_band=proficiency_band,
        taxonomy_version=taxonomy_version,
        certification_epoch=certification_epoch,
    )


def _evaluation_context(
    *,
    human_review_policy: str = "forbid",
    learner_answer: str = "I chose this because everyone helped with the work.",
) -> SchoolEvaluationContext:
    return SchoolEvaluationContext(
        expected_item_id="chapter_reason_1",
        scored_skill_ids=("writing.reason_answer",),
        criterion_policies=(
            SchoolCriterionPolicy(
                id="answers_question",
                required=True,
                min_quality=0.8,
            ),
            SchoolCriterionPolicy(
                id="uses_reason_marker",
                required=True,
                min_quality=0.8,
            ),
        ),
        pass_score=0.8,
        minimum_confidence=0.75,
        learner_answer=learner_answer,
        human_review_policy=human_review_policy,
    )


def test_canonical_contract_modules_do_not_import_legacy_school_versions():
    root = Path(__file__).resolve().parents[2]
    owned_modules = (
        root / "app/content/school/standards.py",
        root / "app/content/school/content_schema.py",
        root / "app/services/school/evaluator_contract.py",
    )

    for module in owned_modules:
        source = module.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        imported_modules.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        assert not any("school_v2" in name for name in imported_modules)
        assert not any("school_v3" in name for name in imported_modules)


def test_banded_standard_identity_and_registry_use_the_full_certification_key():
    first = _standard()
    revised_taxonomy = _standard(taxonomy_version="english-2026-27-v2")
    next_epoch = _standard(certification_epoch="2027-28")
    registry = CompetencyStandardRegistry(
        entries=(first, revised_taxonomy, next_epoch)
    )

    assert first.identity_key == (
        "english",
        "writing.reason_answer",
        3,
        "english-2026-27-v1",
        "2026-27",
    )
    assert len(registry.entries) == 3
    assert not hasattr(first, "class_min")
    assert not hasattr(first, "prerequisite_skill_ids")

    with pytest.raises(ValidationError, match="duplicate_competency_standard"):
        CompetencyStandardRegistry(entries=(first, first))
    with pytest.raises(ValidationError):
        _standard(proficiency_band=6)


def test_locked_english_taxonomy_has_one_ordered_authority_and_legacy_identity_parity():
    from app.content.school_v3_taxonomy import locked_english_taxonomy as legacy_taxonomy

    canonical = locked_english_taxonomy()
    legacy = legacy_taxonomy()
    canonical_by_id = {
        entry.skill_id: entry.model_dump(mode="json") for entry in canonical.entries
    }
    legacy_by_id = {
        entry.skill_id: entry.model_dump(mode="json") for entry in legacy.entries
    }

    assert isinstance(canonical, SkillTaxonomy)
    assert all(isinstance(entry, SkillTaxonomyEntry) for entry in canonical.entries)
    assert len(canonical.entries) == 35
    assert locked_english_skill_ids() == LOCKED_ENGLISH_SKILL_IDS
    assert tuple(entry.skill_id for entry in canonical.entries) == LOCKED_ENGLISH_SKILL_IDS
    assert canonical_by_id == legacy_by_id
    assert {
        "reading.event_sequence",
        "reading.dialogue_attribution",
        "reading.poetic_language",
        "vocab.word_formation",
        "grammar.question_formation",
        "grammar.punctuation_capitalization",
        "writing.paragraph",
        "writing.dialogue",
        "writing.procedure",
        "research.information_selection",
    }.issubset(canonical_by_id)


def test_family_registry_rejects_invalid_prerequisites_cycles_and_identity():
    with pytest.raises(ValidationError, match="duplicate_skill_id"):
        CompetencyFamilyRegistry(
            entries=(_family("reading.same"), _family("reading.same"))
        )
    with pytest.raises(ValidationError, match="unknown_prerequisite_skill_id"):
        CompetencyFamilyRegistry(
            entries=(_family("reading.first", prerequisites=("reading.missing",)),)
        )
    with pytest.raises(ValidationError, match="cyclic_prerequisite_skill_id"):
        CompetencyFamilyRegistry(
            entries=(
                _family("reading.first", prerequisites=("reading.second",)),
                _family("reading.second", prerequisites=("reading.first",)),
            )
        )
    with pytest.raises(ValidationError, match="prerequisite_class_starts_later"):
        CompetencyFamilyRegistry(
            entries=(
                _family("reading.foundation", class_min=3),
                _family(
                    "reading.dependent",
                    class_min=2,
                    prerequisites=("reading.foundation",),
                ),
            )
        )
    with pytest.raises(ValidationError, match="standard_identity_invalid"):
        _family("Reading.Bad Identity")
    with pytest.raises(ValidationError, match="mixed_subject_standard_registry"):
        CompetencyFamilyRegistry(
            entries=(
                _family("reading.english"),
                _family("number.math", subject_id="math"),
            )
        )


def test_family_and_standard_contracts_are_immutable_and_forbid_extras():
    family = _family("reading.immutable")
    standard = _standard()
    family_registry = CompetencyFamilyRegistry(entries=(family,))

    with pytest.raises(ValidationError):
        family.name = "Changed"
    with pytest.raises(ValidationError):
        standard.proficiency_band = 4
    with pytest.raises(ValidationError):
        family_registry.entries = ()
    with pytest.raises(ValidationError):
        CompetencyStandardRef(**standard.model_dump(), invented=True)


def test_source_module_ref_uses_one_cached_immutable_release_index(monkeypatch):
    manifest = load_release_manifest()
    class_two = manifest.releases[0]
    class_three = manifest.releases[1]
    module_id = class_two.units[0].modules[0].module_id
    original_loader = content_schema.load_release_manifest
    calls = 0

    def counting_loader():
        nonlocal calls
        calls += 1
        return original_loader()

    content_schema._release_module_index.cache_clear()
    monkeypatch.setattr(content_schema, "load_release_manifest", counting_loader)
    try:
        SourceModuleRef(
            curriculum_release_id=class_two.curriculum_release_id,
            module_id=module_id,
        )
        SourceModuleRef(
            curriculum_release_id=class_two.curriculum_release_id,
            module_id=module_id,
        )
        index = content_schema._release_module_index()

        assert calls == 1
        assert module_id in index.modules_by_release[class_two.curriculum_release_id]
        with pytest.raises(TypeError):
            index.modules_by_release[class_two.curriculum_release_id] = frozenset()
        with pytest.raises(TypeError):
            index.release_by_module[module_id] = class_three.curriculum_release_id
        with pytest.raises(ValidationError, match="source_module_release_mismatch"):
            SourceModuleRef(
                curriculum_release_id=class_three.curriculum_release_id,
                module_id=module_id,
            )
        with pytest.raises(ValidationError, match="source_module_not_found"):
            SourceModuleRef(
                curriculum_release_id=class_two.curriculum_release_id,
                module_id="eng_c2_u99_m99",
            )
    finally:
        content_schema._release_module_index.cache_clear()


def test_open_answer_rubric_authoring_contract_is_strict_and_immutable():
    rubric = OpenAnswerRubric(
        preflight_rule="answer_is_relevant_and_long_enough",
        pass_score=0.8,
        criteria=(
            OpenAnswerRubricCriterion(
                id="answers_question",
                description="Answers the question that was asked.",
                required=True,
                min_quality=0.6,
            ),
        ),
    )

    assert rubric.criteria[0].id == "answers_question"
    with pytest.raises(ValidationError):
        OpenAnswerRubricCriterion(
            id="answers_question",
            description="Answers the question that was asked.",
            model_score=1.0,
        )
    with pytest.raises(ValidationError):
        rubric.criteria = ()


def test_contextual_evaluator_round_trips_wire_shape_and_uses_backend_targets():
    context = _evaluation_context()
    validated = parse_school_rubric_json(
        json.dumps(VALID_RUBRIC_PAYLOAD), context=context
    )

    assert RUBRIC_SCHEMA_VERSION == "school-v3-rubric-1"
    assert validated.evaluation.model_dump(mode="json") == VALID_RUBRIC_PAYLOAD
    assert validated.scored_skill_ids == context.scored_skill_ids
    assert validated.aggregate_score == pytest.approx(0.86)
    assert validated.meets_required_criteria is True
    assert validated.meets_confidence_requirement is True
    assert validated.requires_human_review is False
    assert validated.certification_eligible is True
    assert criterion_scores(validated) == {
        "answers_question": 0.90,
        "uses_reason_marker": 0.82,
    }


def test_backend_derives_failure_and_review_despite_inflated_model_score():
    weak_payload = {
        **VALID_RUBRIC_PAYLOAD,
        "score": 1.0,
        "confidence": 0.0,
        "criteria": [
            {**criterion, "quality": 0.0}
            for criterion in VALID_RUBRIC_PAYLOAD["criteria"]
        ],
        "needs_human_review": False,
    }

    validated = validate_school_rubric_evaluation(
        weak_payload,
        context=_evaluation_context(),
    )

    assert validated.evaluation.score == 1.0
    assert validated.aggregate_score == 0.0
    assert validated.meets_required_criteria is False
    assert validated.meets_confidence_requirement is False
    assert validated.requires_human_review is True
    assert validated.certification_eligible is False


def test_model_score_cannot_veto_backend_eligible_evidence():
    payload = {**VALID_RUBRIC_PAYLOAD, "score": 0.0}

    validated = validate_school_rubric_evaluation(
        payload,
        context=_evaluation_context(),
    )

    assert validated.evaluation.score == 0.0
    assert validated.aggregate_score == pytest.approx(0.86)
    assert validated.certification_eligible is True


def test_evaluation_context_owns_strict_criterion_and_confidence_policy():
    context = _evaluation_context()

    assert context.expected_criterion_ids == (
        "answers_question",
        "uses_reason_marker",
    )
    with pytest.raises(ValidationError):
        SchoolCriterionPolicy(
            id="answers_question",
            required=True,
            min_quality=0.8,
            model_override=True,
        )
    with pytest.raises(ValidationError):
        SchoolEvaluationContext(
            **context.model_dump(),
            expected_criterion_ids=("model_owned",),
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    (
        ({"item_id": "invented_item"}, "rubric_item_id_mismatch"),
        ({"skill_ids": ["writing.invented"]}, "rubric_scored_skill_ids_mismatch"),
        (
            {
                "criteria": [
                    {
                        "id": "invented_criterion",
                        "met": True,
                        "quality": 0.9,
                        "evidence_quote": "because",
                    }
                ]
            },
            "rubric_criterion_ids_mismatch",
        ),
    ),
)
def test_contextual_evaluator_rejects_invented_authority(mutation, error):
    with pytest.raises(ValueError, match=error):
        validate_school_rubric_evaluation(
            {**VALID_RUBRIC_PAYLOAD, **mutation},
            context=_evaluation_context(),
        )


def test_contextual_evaluator_rejects_untraceable_or_incoherent_evidence():
    untraceable = {
        **VALID_RUBRIC_PAYLOAD,
        "criteria": [
            {**VALID_RUBRIC_PAYLOAD["criteria"][0], "evidence_quote": "never said"},
            VALID_RUBRIC_PAYLOAD["criteria"][1],
        ],
    }
    with pytest.raises(ValueError, match="rubric_evidence_quote_untraceable"):
        validate_school_rubric_evaluation(
            untraceable,
            context=_evaluation_context(),
        )

    incoherent = {
        **VALID_RUBRIC_PAYLOAD,
        "criteria": [
            {
                **VALID_RUBRIC_PAYLOAD["criteria"][0],
                "met": False,
                "quality": 0.2,
            },
            VALID_RUBRIC_PAYLOAD["criteria"][1],
        ],
    }
    with pytest.raises(ValueError, match="rubric_unmet_criterion_has_quality"):
        validate_school_rubric_evaluation(
            incoherent,
            context=_evaluation_context(),
        )


def test_contextual_evaluator_enforces_human_review_policy():
    payload = {**VALID_RUBRIC_PAYLOAD, "needs_human_review": True}

    with pytest.raises(ValueError, match="rubric_human_review_disallowed"):
        validate_school_rubric_evaluation(
            payload,
            context=_evaluation_context(human_review_policy="forbid"),
        )

    validated = validate_school_rubric_evaluation(
        payload,
        context=_evaluation_context(human_review_policy="allow"),
    )
    assert validated.evaluation.needs_human_review is True
    assert validated.requires_human_review is True
    assert validated.certification_eligible is False


@pytest.mark.parametrize(
    "forbidden_field",
    ("mastered", "mastery", "ready_to_advance", "advance", "unlocked"),
)
def test_evaluator_result_rejects_model_owned_progression_fields(forbidden_field: str):
    with pytest.raises(ValidationError):
        validate_school_rubric_evaluation(
            {**VALID_RUBRIC_PAYLOAD, forbidden_field: True},
            context=_evaluation_context(),
        )


def test_evaluator_parser_requires_context_and_rejects_invalid_payloads():
    with pytest.raises(TypeError):
        parse_school_rubric_json(json.dumps(VALID_RUBRIC_PAYLOAD))
    with pytest.raises(ValueError, match="invalid_school_rubric_json"):
        parse_school_rubric_json("not json", context=_evaluation_context())
    with pytest.raises(ValueError, match="unsupported_school_rubric_schema"):
        validate_school_rubric_evaluation(
            {**VALID_RUBRIC_PAYLOAD, "schema_version": "future-rubric-2"},
            context=_evaluation_context(),
        )
    with pytest.raises(ValidationError):
        SchoolRubricEvaluation.model_validate(
            {**VALID_RUBRIC_PAYLOAD, "unexpected": "field"}
        )
