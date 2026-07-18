"""Compatibility view over the canonical School English skill taxonomy.

V3 callers still expect the legacy Pydantic container types, but the skill
identities and prerequisite graph are owned only by ``school.standards``.
"""

from __future__ import annotations

from app.content.school.standards import (
    LOCKED_ENGLISH_SKILL_IDS as CANONICAL_ENGLISH_SKILL_IDS,
    LOCKED_ENGLISH_TAXONOMY_ENTRIES as CANONICAL_ENGLISH_TAXONOMY_ENTRIES,
)
from app.content.school_v3_schema import SkillTaxonomy, SkillTaxonomyEntry


LOCKED_ENGLISH_SKILL_IDS: tuple[str, ...] = CANONICAL_ENGLISH_SKILL_IDS
LOCKED_ENGLISH_TAXONOMY_ENTRIES: tuple[SkillTaxonomyEntry, ...] = tuple(
    SkillTaxonomyEntry.model_validate(entry.model_dump(mode="json"))
    for entry in CANONICAL_ENGLISH_TAXONOMY_ENTRIES
)


def locked_english_taxonomy() -> SkillTaxonomy:
    return SkillTaxonomy(entries=list(LOCKED_ENGLISH_TAXONOMY_ENTRIES))


def locked_english_skill_ids() -> tuple[str, ...]:
    return LOCKED_ENGLISH_SKILL_IDS
