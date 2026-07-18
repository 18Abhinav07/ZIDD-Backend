"""Canonical School content compatibility contracts."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.content.school.release_loader import load_release_manifest


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


@dataclass(frozen=True)
class _ReleaseModuleIndex:
    modules_by_release: Mapping[str, frozenset[str]]
    release_by_module: Mapping[str, str]


@lru_cache(maxsize=1)
def _release_module_index() -> _ReleaseModuleIndex:
    manifest = load_release_manifest()
    modules_by_release: dict[str, frozenset[str]] = {}
    release_by_module: dict[str, str] = {}
    for release in manifest.releases:
        module_ids = {
            module.module_id
            for unit in release.units
            for module in unit.modules
        }
        module_ids.update(module.module_id for module in release.reference_modules)
        for module_id in module_ids:
            existing_release = release_by_module.get(module_id)
            if existing_release is not None:
                raise ValueError(
                    f"source_module_identity_duplicate:{module_id}:"
                    f"{existing_release}:{release.curriculum_release_id}"
                )
            release_by_module[module_id] = release.curriculum_release_id
        modules_by_release[release.curriculum_release_id] = frozenset(module_ids)
    return _ReleaseModuleIndex(
        modules_by_release=MappingProxyType(modules_by_release),
        release_by_module=MappingProxyType(release_by_module),
    )


class SourceModuleRef(_StrictFrozenModel):
    curriculum_release_id: str
    module_id: str

    @field_validator("curriculum_release_id", "module_id")
    @classmethod
    def _clean_identity(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source_module_identity_empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_release_module_link(self) -> "SourceModuleRef":
        index = _release_module_index()
        release_modules = index.modules_by_release.get(self.curriculum_release_id)
        if release_modules is None:
            raise ValueError(
                f"source_curriculum_release_not_found:{self.curriculum_release_id}"
            )
        if self.module_id in release_modules:
            return self
        if self.module_id in index.release_by_module:
            raise ValueError(
                f"source_module_release_mismatch:{self.module_id}:"
                f"{self.curriculum_release_id}"
            )
        raise ValueError(f"source_module_not_found:{self.module_id}")


class OpenAnswerRubricCriterion(_StrictFrozenModel):
    id: str
    description: str
    required: bool = True
    min_quality: float = Field(default=0.6, ge=0.0, le=1.0)

    @field_validator("id", "description")
    @classmethod
    def _clean_required_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("rubric_criterion_field_empty")
        return cleaned


class OpenAnswerRubric(_StrictFrozenModel):
    preflight_rule: str
    pass_score: float = Field(ge=0.0, le=1.0)
    criteria: tuple[OpenAnswerRubricCriterion, ...] = Field(min_length=1)

    @field_validator("preflight_rule")
    @classmethod
    def _clean_preflight_rule(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("open_answer_preflight_rule_empty")
        return cleaned

    @field_validator("criteria", mode="before")
    @classmethod
    def _tuple_criteria(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _unique_criteria(self) -> "OpenAnswerRubric":
        criterion_ids = [criterion.id for criterion in self.criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("duplicate_open_answer_rubric_criterion")
        return self


class SchoolRubricCriterion(_StrictFrozenModel):
    id: str
    met: bool
    quality: float = Field(ge=0.0, le=1.0)
    evidence_quote: str = Field(min_length=1)

    @field_validator("id", "evidence_quote")
    @classmethod
    def _clean_required_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("rubric_result_field_empty")
        return cleaned

class SchoolRubricEvaluation(_StrictFrozenModel):
    schema_version: Literal["school-v3-rubric-1", "school.open.v1"]
    item_id: str
    skill_ids: tuple[str, ...] = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    language_detected: Literal["en", "hi", "hi_en", "other", "unknown"]
    criteria: tuple[SchoolRubricCriterion, ...] = Field(min_length=1)
    misconception_tags: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    needs_human_review: bool
    feedback_to_learner: str

    @field_validator(
        "skill_ids", "criteria", "misconception_tags", "blockers", mode="before"
    )
    @classmethod
    def _tuple_collections(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator(
        "schema_version", "item_id", "language_detected", "feedback_to_learner"
    )
    @classmethod
    def _clean_required_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("rubric_evaluation_field_empty")
        return cleaned

    @field_validator("skill_ids", "misconception_tags", "blockers")
    @classmethod
    def _validate_string_collections(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("rubric_evaluation_list_value_empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("rubric_evaluation_list_value_duplicate")
        return cleaned

    @model_validator(mode="after")
    def _unique_criterion_ids(self) -> "SchoolRubricEvaluation":
        criterion_ids = [criterion.id for criterion in self.criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise ValueError("duplicate_rubric_result_criterion")
        if self.schema_version == "school.open.v1":
            invalid = next(
                (
                    criterion
                    for criterion in self.criteria
                    if not criterion.met and criterion.quality > 0.0
                ),
                None,
            )
            if invalid is not None:
                raise ValueError(
                    f"rubric_unmet_criterion_has_quality:{invalid.id}"
                )
        return self


# Compatibility names for callers migrated in Task 0.4.
SchoolV3RubricCriterion = SchoolRubricCriterion
SchoolV3RubricEvaluation = SchoolRubricEvaluation


__all__ = [
    "OpenAnswerRubric",
    "OpenAnswerRubricCriterion",
    "SchoolRubricCriterion",
    "SchoolRubricEvaluation",
    "SchoolV3RubricCriterion",
    "SchoolV3RubricEvaluation",
    "SourceModuleRef",
]
