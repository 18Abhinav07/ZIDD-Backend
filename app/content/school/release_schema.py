"""Strict metadata contract for immutable School curriculum releases.

This module describes source structure only. Textbook prose and authored lesson
content belong to separate, approval-gated content packages.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


Month = Literal[
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
ModuleKind = Literal[
    "lesson",
    "picture_reading",
    "self_assessment",
    "reference",
]
LanguageStructure = Literal["listening", "speaking", "reading", "writing"]
SourceGenre = Literal[
    "poem",
    "story",
    "prose",
    "play",
    "informational",
    "mixed",
    "none",
    "reference",
]
PedagogicalMode = Literal[
    "singing",
    "oral_expression",
    "reading",
    "drawing",
    "pronunciation",
    "writing",
    "recitation",
    "reasoning",
    "language_focus",
    "listening",
    "activity",
    "exploration",
]

_MONTH_ORDER = {
    month: index
    for index, month in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}


def _validate_official_ncert_url(
    url: HttpUrl,
    *,
    expected_path: str,
    field_name: Literal["selector", "pdf"],
) -> None:
    prefix = f"official_{field_name}"
    if url.scheme != "https":
        raise ValueError(f"{prefix}_scheme_invalid")
    if url.host != "ncert.nic.in":
        raise ValueError(f"{prefix}_host_invalid")
    if url.port != 443:
        raise ValueError(f"{prefix}_port_invalid")
    if url.username is not None or url.password is not None:
        raise ValueError(f"{prefix}_userinfo_invalid")
    if url.path != expected_path:
        raise ValueError(f"{prefix}_path_invalid")
    if url.query is not None:
        raise ValueError(f"{prefix}_query_invalid")
    if url.fragment is not None:
        raise ValueError(f"{prefix}_fragment_invalid")


class StrictReleaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class EditionRecord(StrictReleaseModel):
    kind: Literal["first_edition", "reprint"]
    month: Month
    year: int = Field(ge=2000, le=2100)


class ReleaseVerificationEvidence(StrictReleaseModel):
    verified_on: date
    method: Literal["official_pdf_metadata_and_local_sha256"]
    official_url: HttpUrl
    hash_algorithm: Literal["sha256"]
    provenance: Literal["official_ncert_pdf"]
    evidence_note: str = Field(min_length=12, max_length=500)

    @field_validator("evidence_note")
    @classmethod
    def _clean_evidence_note(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("release_verification_evidence_empty")
        return cleaned


class CurriculumModule(StrictReleaseModel):
    module_id: str = Field(pattern=r"^eng_c[2-5]_(?:u\d{2}_m\d{2}|ref\d{2})$")
    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    kind: ModuleKind
    source_genre: SourceGenre

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("curriculum_module_title_empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_source_genre(self) -> "CurriculumModule":
        lesson_genres = {"poem", "story", "prose", "play", "informational", "mixed"}
        if self.kind == "lesson" and self.source_genre not in lesson_genres:
            raise ValueError("lesson_requires_source_genre")
        if self.kind in {"picture_reading", "self_assessment"} and self.source_genre != "none":
            raise ValueError("special_module_source_genre_must_be_none")
        if self.kind == "reference" and self.source_genre != "reference":
            raise ValueError("reference_module_source_genre_must_be_reference")
        return self


class PedagogicalSection(StrictReleaseModel):
    order: int = Field(ge=1)
    label: str = Field(min_length=2, max_length=40)
    mode: PedagogicalMode
    source_pdf_page: int = Field(ge=1)
    source_evidence: Literal["official_front_matter"]

    @field_validator("label")
    @classmethod
    def _clean_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("pedagogical_section_label_empty")
        return cleaned


class CurriculumUnit(StrictReleaseModel):
    unit_id: str = Field(pattern=r"^eng_c[2-5]_u\d{2}$")
    order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=160)
    modules: tuple[CurriculumModule, ...] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("curriculum_unit_title_empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_module_order(self) -> "CurriculumUnit":
        orders = [module.order for module in self.modules]
        if len(orders) != len(set(orders)):
            raise ValueError("duplicate_module_order")
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError("non_contiguous_module_order")
        module_ids = [module.module_id for module in self.modules]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("duplicate_module_id")
        if any(module.kind == "reference" for module in self.modules):
            raise ValueError("reference_module_must_be_back_matter")
        if any(
            not module.module_id.startswith(f"{self.unit_id}_m")
            for module in self.modules
        ):
            raise ValueError("module_unit_mismatch")
        return self


class CurriculumRelease(StrictReleaseModel):
    curriculum_release_id: str = Field(
        pattern=r"^english_cbse_2026_27_c[2-5]_[a-z0-9]+$"
    )
    board_id: Literal["cbse"]
    subject_id: Literal["english"]
    class_no: int
    academic_year: Literal["2026-27"]
    release_label: Literal["Reprint 2026-27"]
    release_status: Literal["current", "retired"]
    verification_status: Literal["verified"]
    book_title: str = Field(min_length=1, max_length=100)
    book_code: str = Field(pattern=r"^[a-z]{4}\d$")
    isbn: str = Field(pattern=r"^978-\d{2}-\d{4}-\d{3}-\d$")
    official_selector_url: HttpUrl
    official_pdf_url: HttpUrl
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_size_bytes: int = Field(gt=0)
    edition_history: tuple[EditionRecord, ...] = Field(min_length=2)
    effective_from: date
    effective_through: date
    retired_on: date | None
    language_structures: tuple[LanguageStructure, ...] = Field(min_length=4)
    pedagogical_sections: tuple[PedagogicalSection, ...] = Field(min_length=1)
    verification_evidence: ReleaseVerificationEvidence
    units: tuple[CurriculumUnit, ...] = Field(min_length=1)
    reference_modules: tuple[CurriculumModule, ...]

    @field_validator("class_no")
    @classmethod
    def _supported_class(cls, value: int) -> int:
        if value not in {2, 3, 4, 5}:
            raise ValueError("invalid_school_class")
        return value

    @field_validator("book_title")
    @classmethod
    def _clean_book_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("curriculum_release_book_title_empty")
        return cleaned

    @field_validator("language_structures")
    @classmethod
    def _unique_language_structures(
        cls, values: tuple[LanguageStructure, ...]
    ) -> tuple[LanguageStructure, ...]:
        if len(values) != len(set(values)):
            raise ValueError("duplicate_language_structure")
        required = {"listening", "speaking", "reading", "writing"}
        if set(values) != required:
            raise ValueError("incomplete_language_structures")
        return values

    @model_validator(mode="after")
    def _validate_release(self) -> "CurriculumRelease":
        if self.release_status == "current" and self.retired_on is not None:
            raise ValueError("current_release_cannot_be_retired")
        if self.release_status == "retired" and self.retired_on is None:
            raise ValueError("retired_release_requires_date")
        if self.effective_through < self.effective_from:
            raise ValueError("invalid_release_effective_window")
        if self.retired_on is not None and not (
            self.effective_from <= self.retired_on <= self.effective_through
        ):
            raise ValueError("retired_date_outside_effective_window")

        expected_release_id = (
            f"english_cbse_2026_27_c{self.class_no}_{self.book_code}"
        )
        if self.curriculum_release_id != expected_release_id:
            raise ValueError("curriculum_release_id_mismatch")
        _validate_official_ncert_url(
            self.official_selector_url,
            expected_path="/textbook.php",
            field_name="selector",
        )
        _validate_official_ncert_url(
            self.official_pdf_url,
            expected_path=f"/textbook/pdf/{self.book_code}ps.pdf",
            field_name="pdf",
        )

        unit_orders = [unit.order for unit in self.units]
        if len(unit_orders) != len(set(unit_orders)):
            raise ValueError("duplicate_unit_order")
        if unit_orders != list(range(1, len(unit_orders) + 1)):
            raise ValueError("non_contiguous_unit_order")
        unit_ids = [unit.unit_id for unit in self.units]
        if len(unit_ids) != len(set(unit_ids)):
            raise ValueError("duplicate_unit_id")

        all_modules = [module for unit in self.units for module in unit.modules]
        all_modules.extend(self.reference_modules)
        module_ids = [module.module_id for module in all_modules]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("duplicate_module_id")
        if not any(module.kind == "lesson" for module in all_modules):
            raise ValueError("release_requires_lesson_module")

        reference_orders = [module.order for module in self.reference_modules]
        if len(reference_orders) != len(set(reference_orders)):
            raise ValueError("duplicate_reference_order")
        if reference_orders != list(range(1, len(reference_orders) + 1)):
            raise ValueError("non_contiguous_reference_order")
        if any(module.kind != "reference" for module in self.reference_modules):
            raise ValueError("back_matter_module_must_be_reference")

        section_orders = [section.order for section in self.pedagogical_sections]
        if section_orders != list(range(1, len(section_orders) + 1)):
            raise ValueError("invalid_pedagogical_section_order")
        section_labels = [section.label for section in self.pedagogical_sections]
        if len(section_labels) != len(set(section_labels)):
            raise ValueError("duplicate_pedagogical_section")

        first_editions = [
            record for record in self.edition_history if record.kind == "first_edition"
        ]
        if len(first_editions) != 1 or self.edition_history[0].kind != "first_edition":
            raise ValueError("invalid_first_edition_history")
        edition_keys = [
            (record.year, _MONTH_ORDER[record.month])
            for record in self.edition_history
        ]
        if len(edition_keys) != len(set(edition_keys)):
            raise ValueError("duplicate_edition_history")
        if edition_keys != sorted(edition_keys):
            raise ValueError("edition_history_not_chronological")
        if self.edition_history[-1].kind != "reprint" or self.edition_history[-1].year != 2026:
            raise ValueError("release_requires_2026_reprint")

        expected_prefix = f"eng_c{self.class_no}_"
        if any(not unit.unit_id.startswith(expected_prefix) for unit in self.units):
            raise ValueError("unit_class_mismatch")
        if any(not module.module_id.startswith(expected_prefix) for module in all_modules):
            raise ValueError("module_class_mismatch")
        if self.verification_evidence.official_url != self.official_pdf_url:
            raise ValueError("verification_url_mismatch")
        return self


class CurriculumReleaseManifest(StrictReleaseModel):
    schema_version: Literal["1.0"]
    manifest_id: Literal["english_cbse_2026_27"]
    academic_year: Literal["2026-27"]
    created_on: date
    source_policy: Literal["official_metadata_only_no_textbook_body"]
    releases: tuple[CurriculumRelease, ...] = Field(min_length=4)
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_release_set(self) -> "CurriculumReleaseManifest":
        release_ids = [release.curriculum_release_id for release in self.releases]
        if len(release_ids) != len(set(release_ids)):
            raise ValueError("duplicate_curriculum_release_id")
        classes = [release.class_no for release in self.releases]
        if len(classes) != len(set(classes)):
            raise ValueError("duplicate_curriculum_release_class")
        if classes != [2, 3, 4, 5]:
            raise ValueError("release_classes_must_be_ordered_2_to_5")
        if any(release.academic_year != self.academic_year for release in self.releases):
            raise ValueError("release_academic_year_mismatch")
        return self
