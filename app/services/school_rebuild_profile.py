import hashlib
import json
import secrets
from copy import deepcopy
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


SCHOOL_PROFILE_FIELDS = (
    "display_name",
    "school_name",
    "board_id",
    "target_class_no",
    "subject_ids",
    "preferred_teaching_language",
    "english_comfort",
    "learner_goal",
    "parent_goal",
    "prior_difficulty_signals",
)

CANONICAL_SCHOOL_COACH_IDS = (
    "stuttering_sam",
    "fluent_finn",
    "brave_bella",
    "quiet_quint",
    "tech_black",
    "casual_purple",
    "casual_male",
    "casual_female",
    "casual_blue",
)

SCHOOL_BOARD_CATALOG = (
    {
        "board_id": "cbse",
        "title": "CBSE",
        "description": "CBSE curriculum aligned with approved learning material.",
        "support_status": "available",
        "subjects": [
            {
                "subject_id": "english",
                "title": "English",
                "support_status": "available",
                "classes": [
                    {
                        "class_no": class_no,
                        "title": f"Class {class_no}",
                        "support_status": "available",
                    }
                    for class_no in (2, 3, 4, 5)
                ],
            }
        ],
    },
    {
        "board_id": "ncert",
        "title": "NCERT",
        "description": "NCERT is used as a content source for the CBSE release.",
        "support_status": "unavailable",
        "unavailable_reason": "NCERT is a content source, not a school board.",
        "subjects": [
            {
                "subject_id": "english",
                "title": "English",
                "support_status": "unavailable",
                "unavailable_reason": (
                    "Choose CBSE to use the available English release."
                ),
                "classes": [
                    {
                        "class_no": class_no,
                        "title": f"Class {class_no}",
                        "support_status": "unavailable",
                        "unavailable_reason": (
                            "NCERT is not a selectable school board."
                        ),
                    }
                    for class_no in (2, 3, 4, 5)
                ],
            }
        ],
    },
)


def choose_school_coach_identity() -> dict[str, str]:
    avatar_id = secrets.choice(CANONICAL_SCHOOL_COACH_IDS)
    return {
        "coach_avatar_id": avatar_id,
        "coach_palette_id": avatar_id,
    }


def school_coach_identity(source: dict[str, Any] | None) -> dict[str, str | None]:
    source = source or {}
    return {
        "coach_avatar_id": source.get("coach_avatar_id"),
        "coach_palette_id": source.get("coach_palette_id"),
    }


def public_school_catalog() -> dict[str, list[dict]]:
    return {"boards": deepcopy(list(SCHOOL_BOARD_CATALOG))}


def school_catalog_selection_available(
    profile: dict[str, Any],
) -> bool:
    subject_ids = profile.get("subject_ids")
    if not isinstance(subject_ids, (list, tuple)) or len(subject_ids) != 1:
        return False
    target_class_no = profile.get("target_class_no")
    if target_class_no is None:
        return False
    board_id = str(profile.get("board_id") or "")
    subject_id = str(subject_ids[0])
    board = next(
        (
            candidate
            for candidate in public_school_catalog()["boards"]
            if candidate.get("board_id") == board_id
        ),
        None,
    )
    if not board or board.get("support_status") != "available":
        return False
    subject = next(
        (
            candidate
            for candidate in board.get("subjects") or []
            if candidate.get("subject_id") == subject_id
        ),
        None,
    )
    if not subject or subject.get("support_status") != "available":
        return False
    return any(
        int(candidate.get("class_no") or 0) == int(target_class_no)
        and candidate.get("support_status") == "available"
        for candidate in subject.get("classes") or []
    )


class SchoolRebuildProfileIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: str = Field(min_length=2, max_length=120)
    school_name: str = Field(min_length=2, max_length=160)
    board_id: Literal["cbse", "ncert"] = "cbse"
    target_class_no: int = Field(ge=2, le=5)
    subject_ids: list[Literal["english"]] = Field(
        default_factory=lambda: ["english"],
        min_length=1,
        max_length=1,
    )
    preferred_teaching_language: Literal["en", "hi", "hi_en"]
    english_comfort: Literal["low", "medium", "high"]
    learner_goal: str = Field(default="", max_length=360)
    parent_goal: str = Field(default="", max_length=360)
    prior_difficulty_signals: list[
        Literal["reading", "vocabulary", "grammar", "writing", "chapter_answers"]
    ] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def require_at_least_one_goal(self) -> "SchoolRebuildProfileIn":
        if not self.learner_goal.strip() and not self.parent_goal.strip():
            raise ValueError("school_profile_goal_required")
        return self


class SchoolOnboardingDraftPatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    display_name: str | None = Field(default=None, max_length=120)
    school_name: str | None = Field(default=None, max_length=160)
    board_id: Literal["cbse", "ncert"] | None = None
    target_class_no: int | None = Field(default=None, ge=2, le=5)
    subject_ids: list[Literal["english"]] | None = Field(default=None, max_length=1)
    preferred_teaching_language: Literal["en", "hi", "hi_en"] | None = None
    english_comfort: Literal["low", "medium", "high"] | None = None
    learner_goal: str | None = Field(default=None, max_length=360)
    parent_goal: str | None = Field(default=None, max_length=360)
    prior_difficulty_signals: list[
        Literal["reading", "vocabulary", "grammar", "writing", "chapter_answers"]
    ] | None = Field(default=None, max_length=5)
    coach_avatar_id: str | None = Field(default=None, min_length=1, max_length=80)
    coach_palette_id: str | None = Field(default=None, min_length=1, max_length=80)
    current_step: int = Field(ge=0, le=4)
    request_id: UUID
    profile_version_id: UUID | None = None
    expected_revision: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_coach_identity(self) -> "SchoolOnboardingDraftPatchIn":
        avatar_id = self.coach_avatar_id
        palette_id = self.coach_palette_id
        if avatar_id is None and palette_id is None:
            return self
        if (
            avatar_id is None
            or palette_id is None
            or avatar_id != palette_id
            or avatar_id not in CANONICAL_SCHOOL_COACH_IDS
        ):
            raise ValueError("school_coach_identity_invalid")
        return self

    def profile_patch(self) -> dict[str, Any]:
        provided = self.model_fields_set
        values = self.model_dump(mode="json")
        patch = {
            field: values[field]
            for field in SCHOOL_PROFILE_FIELDS
            if field in provided
        }
        if "coach_avatar_id" in provided:
            patch.update(
                {
                    "coach_avatar_id": values["coach_avatar_id"],
                    "coach_palette_id": values["coach_palette_id"],
                }
            )
        return patch

    def payload_hash(self) -> str:
        return canonical_payload_hash(
            self.model_dump(mode="json", exclude={"request_id"}, exclude_unset=True)
        )


class SchoolOnboardingCompleteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile_version_id: UUID
    expected_revision: int = Field(ge=1)
    request_id: UUID

    def payload_hash(self) -> str:
        return canonical_payload_hash(
            self.model_dump(mode="json", exclude={"request_id"})
        )


def canonical_payload_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, str):
        try:
            return _json_list(json.loads(value))
        except json.JSONDecodeError:
            return []
    if isinstance(value, list):
        return list(value)
    return []


def public_school_profile(row: dict[str, Any]) -> dict[str, Any]:
    target_class_no = row.get("target_class_no")
    return {
        "profile_version_id": str(row["profile_version_id"]),
        "display_name": row.get("display_name"),
        "school_name": row.get("school_name"),
        "board_id": row.get("board_id"),
        "target_class_no": (
            int(target_class_no) if target_class_no is not None else None
        ),
        "subject_ids": _json_list(row.get("subject_ids")),
        "preferred_teaching_language": row.get("preferred_teaching_language"),
        "english_comfort": row.get("english_comfort"),
        "learner_goal": row.get("learner_goal"),
        "parent_goal": row.get("parent_goal"),
        "prior_difficulty_signals": _json_list(row.get("prior_difficulty_signals")),
        **school_coach_identity(row),
    }


def public_school_profile_draft(row: dict[str, Any]) -> dict[str, Any]:
    def draft_list(value: Any) -> list[Any] | None:
        return None if value is None else _json_list(value)

    target_class_no = row.get("target_class_no")
    return {
        "profile_version_id": str(row["profile_version_id"]),
        "status": "draft",
        "current_step": int(row.get("current_step") or 0),
        "draft_revision": int(row.get("draft_revision") or 1),
        "display_name": row.get("display_name"),
        "school_name": row.get("school_name"),
        "board_id": row.get("board_id"),
        "target_class_no": (
            int(target_class_no) if target_class_no is not None else None
        ),
        "subject_ids": draft_list(row.get("subject_ids")),
        "preferred_teaching_language": row.get("preferred_teaching_language"),
        "english_comfort": row.get("english_comfort"),
        "learner_goal": row.get("learner_goal"),
        "parent_goal": row.get("parent_goal"),
        "prior_difficulty_signals": draft_list(
            row.get("prior_difficulty_signals")
        ),
        **school_coach_identity(row),
    }
