"""Canonical School competency families and certification identities."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_STANDARD_ID = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")


class _StrictFrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class CompetencyStandardRef(_StrictFrozenModel):
    """Full identity of one certifiable skill at one proficiency band."""

    subject_id: str
    skill_id: str
    proficiency_band: int = Field(ge=1, le=5)
    taxonomy_version: str
    certification_epoch: str

    @field_validator(
        "subject_id", "skill_id", "taxonomy_version", "certification_epoch"
    )
    @classmethod
    def _clean_identity_field(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("competency_standard_identity_empty")
        return cleaned

    @model_validator(mode="after")
    def _validate_skill_identity(self) -> "CompetencyStandardRef":
        if not _STANDARD_ID.fullmatch(self.skill_id):
            raise ValueError(f"standard_identity_invalid:{self.skill_id}")
        return self

    @property
    def identity_key(self) -> tuple[str, str, int, str, str]:
        return (
            self.subject_id,
            self.skill_id,
            self.proficiency_band,
            self.taxonomy_version,
            self.certification_epoch,
        )


class CompetencyStandardRegistry(_StrictFrozenModel):
    entries: tuple[CompetencyStandardRef, ...] = Field(min_length=1)

    @field_validator("entries", mode="before")
    @classmethod
    def _tuple_entries(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _validate_full_key_uniqueness(self) -> "CompetencyStandardRegistry":
        keys = [entry.identity_key for entry in self.entries]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate_competency_standard")
        return self

    def get(
        self,
        *,
        subject_id: str,
        skill_id: str,
        proficiency_band: int,
        taxonomy_version: str,
        certification_epoch: str,
    ) -> CompetencyStandardRef:
        identity = (
            subject_id,
            skill_id,
            proficiency_band,
            taxonomy_version,
            certification_epoch,
        )
        for entry in self.entries:
            if entry.identity_key == identity:
                return entry
        raise KeyError(identity)


class CompetencyFamilyRef(_StrictFrozenModel):
    """Subject-wide compatibility metadata shared by banded standards."""

    skill_id: str
    subject_id: str
    class_min: int = Field(ge=1, le=12)
    class_max: int = Field(ge=1, le=12)
    name: str
    description: str
    prerequisite_skill_ids: tuple[str, ...] = ()
    certifying_language: str = "en"

    @field_validator("prerequisite_skill_ids", mode="before")
    @classmethod
    def _tuple_prerequisites(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator(
        "skill_id",
        "subject_id",
        "name",
        "description",
        "certifying_language",
    )
    @classmethod
    def _clean_required_string(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("competency_family_field_empty")
        return cleaned

    @field_validator("prerequisite_skill_ids")
    @classmethod
    def _validate_prerequisite_values(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        cleaned = tuple(value.strip() for value in values)
        if any(not value for value in cleaned):
            raise ValueError("prerequisite_skill_id_empty")
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("duplicate_prerequisite_skill_id")
        return cleaned

    @model_validator(mode="after")
    def _validate_family(self) -> "CompetencyFamilyRef":
        if not _STANDARD_ID.fullmatch(self.skill_id):
            raise ValueError(f"standard_identity_invalid:{self.skill_id}")
        if self.class_min > self.class_max:
            raise ValueError("class_min_cannot_exceed_class_max")
        if self.skill_id in self.prerequisite_skill_ids:
            raise ValueError(f"cyclic_prerequisite_skill_id:{self.skill_id}")
        return self


class CompetencyFamilyRegistry(_StrictFrozenModel):
    entries: tuple[CompetencyFamilyRef, ...] = Field(min_length=1)

    @field_validator("entries", mode="before")
    @classmethod
    def _tuple_entries(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def _validate_closed_acyclic_registry(self) -> "CompetencyFamilyRegistry":
        by_id: dict[str, CompetencyFamilyRef] = {}
        for entry in self.entries:
            if entry.skill_id in by_id:
                raise ValueError(f"duplicate_skill_id:{entry.skill_id}")
            by_id[entry.skill_id] = entry

        if len({entry.subject_id for entry in self.entries}) != 1:
            raise ValueError("mixed_subject_standard_registry")

        for entry in self.entries:
            for prerequisite in entry.prerequisite_skill_ids:
                prerequisite_entry = by_id.get(prerequisite)
                if prerequisite_entry is None:
                    raise ValueError(f"unknown_prerequisite_skill_id:{prerequisite}")
                if prerequisite_entry.subject_id != entry.subject_id:
                    raise ValueError(
                        f"cross_subject_prerequisite_skill_id:"
                        f"{entry.skill_id}:{prerequisite}"
                    )
                if prerequisite_entry.class_min > entry.class_min:
                    raise ValueError(
                        f"prerequisite_class_starts_later:"
                        f"{entry.skill_id}:{prerequisite}"
                    )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(skill_id: str) -> None:
            if skill_id in visiting:
                raise ValueError(f"cyclic_prerequisite_skill_id:{skill_id}")
            if skill_id in visited:
                return
            visiting.add(skill_id)
            for prerequisite in by_id[skill_id].prerequisite_skill_ids:
                visit(prerequisite)
            visiting.remove(skill_id)
            visited.add(skill_id)

        for skill_id in by_id:
            visit(skill_id)
        return self

    def skill_ids(self) -> set[str]:
        return {entry.skill_id for entry in self.entries}

    def get(self, skill_id: str) -> CompetencyFamilyRef:
        for entry in self.entries:
            if entry.skill_id == skill_id:
                return entry
        raise KeyError(skill_id)


# Existing subject-wide API retained as a compatibility view.
SkillTaxonomyEntry = CompetencyFamilyRef
SkillTaxonomy = CompetencyFamilyRegistry


# This tuple is the single ordered authority for the compatibility taxonomy.
LOCKED_ENGLISH_TAXONOMY_ENTRIES: tuple[CompetencyFamilyRef, ...] = (
    CompetencyFamilyRef(
        skill_id="reading.word_meaning_context",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use context to understand words",
        description="Infer the meaning of a word from sentence or passage clues.",
    ),
    CompetencyFamilyRef(
        skill_id="reading.sentence_comprehension",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Understand sentence meaning",
        description="Read a sentence and identify who or what it is about.",
    ),
    CompetencyFamilyRef(
        skill_id="reading.paragraph_main_idea",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Find the main idea",
        description=(
            "Identify the central idea of a short passage or chapter section."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="reading.inference_reason",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Infer a reason",
        description=(
            "Use textual clues to explain why an event happened or why a "
            "character acted."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="reading.event_sequence",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Sequence events and processes",
        description=(
            "Place connected events or process steps in a supported order using "
            "time, cause, and transition clues."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="reading.dialogue_attribution",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Track speakers and dialogue",
        description=(
            "Identify who is speaking, who is being addressed, and what the "
            "utterance contributes to the event."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="reading.poetic_language",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Interpret poetic language",
        description=(
            "Use context to interpret imagery, comparison, repetition, rhyme, "
            "and a poem's speaker or mood without treating poetic exaggeration "
            "as literal fact."
        ),
        prerequisite_skill_ids=(
            "reading.word_meaning_context",
            "reading.sentence_comprehension",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="vocab.chapter_word_usage",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use chapter vocabulary",
        description=(
            "Use new words from a chapter correctly in a sentence or answer."
        ),
        prerequisite_skill_ids=("reading.word_meaning_context",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.noun_verb_adjective",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Identify nouns, verbs, and adjectives",
        description="Recognize basic word roles and use them in simple sentences.",
    ),
    CompetencyFamilyRef(
        skill_id="grammar.tense_usage",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Use tense correctly",
        description=(
            "Choose present, past, or future forms that match the sentence context."
        ),
        prerequisite_skill_ids=("grammar.noun_verb_adjective",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.connectors_because_and_but",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Use because, and, and but",
        description="Connect ideas with reason, addition, and contrast markers.",
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.sentence_order",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Arrange words into a sentence",
        description=(
            "Order jumbled words into a grammatical sentence with a clear subject "
            "and action or description."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="writing.complete_sentence",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Write a complete sentence",
        description=(
            "Write an answer with a subject and meaningful action or description."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="writing.short_answer",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write a short answer",
        description=(
            "Answer a reading question clearly in one or two relevant sentences."
        ),
        prerequisite_skill_ids=("writing.complete_sentence",),
    ),
    CompetencyFamilyRef(
        skill_id="writing.reason_answer",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write an answer with a reason",
        description=(
            "Support an answer with a because/evidence clue rather than only "
            "restating the event."
        ),
        prerequisite_skill_ids=(
            "reading.inference_reason",
            "grammar.connectors_because_and_but",
            "writing.short_answer",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="writing.summary_own_words",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Summarize in own words",
        description=(
            "Retell the main idea or chapter event without copying a model answer."
        ),
        prerequisite_skill_ids=(
            "reading.paragraph_main_idea",
            "writing.short_answer",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="writing.compare_contrast",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Compare two subjects",
        description=(
            "State an accurate similarity and difference using clear comparison "
            "language."
        ),
        prerequisite_skill_ids=(
            "reading.sentence_comprehension",
            "writing.short_answer",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="writing.friendly_message",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write a friendly message",
        description=(
            "Reply to a known reader with a greeting, relevant details, a useful "
            "question or response, and a closing."
        ),
        prerequisite_skill_ids=("writing.complete_sentence",),
    ),
    CompetencyFamilyRef(
        skill_id="vocab.attribute_ordering",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Order objects by an attribute",
        description=(
            "Arrange familiar words by a stated quality such as size, weight, "
            "length, or intensity and explain the ordering rule."
        ),
        prerequisite_skill_ids=("reading.word_meaning_context",),
    ),
    CompetencyFamilyRef(
        skill_id="vocab.spelling",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Recognize and produce standard spellings",
        description=(
            "Choose or write the standard spelling of familiar curriculum words "
            "using letter-pattern and word-family knowledge."
        ),
        prerequisite_skill_ids=("reading.word_meaning_context",),
    ),
    CompetencyFamilyRef(
        skill_id="vocab.antonyms",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use words with opposite meanings",
        description=(
            "Recognize and use an antonym that fits the meaning and grammar of a "
            "sentence."
        ),
        prerequisite_skill_ids=("reading.word_meaning_context",),
    ),
    CompetencyFamilyRef(
        skill_id="vocab.word_formation",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Build and explain related words",
        description=(
            "Form compounds or add a taught prefix or suffix, then verify that "
            "the resulting word has the intended meaning in context."
        ),
        prerequisite_skill_ids=("reading.word_meaning_context",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.prepositions",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use prepositions in context",
        description=(
            "Select and use position, direction, and time prepositions to express "
            "clear relationships in a sentence."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.adverbs",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Use adverbs in context",
        description=(
            "Recognize and use words or phrases that answer when, how often, "
            "where, or how an action happens."
        ),
        prerequisite_skill_ids=("grammar.noun_verb_adjective",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.pronouns",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Track and use pronouns",
        description=(
            "Connect pronouns to clear referents and choose subject, object, or "
            "possessive forms that fit the sentence."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.question_formation",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Form answerable questions",
        description=(
            "Choose an appropriate question word and arrange a complete, "
            "relevant question with correct punctuation."
        ),
        prerequisite_skill_ids=("grammar.sentence_order",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.punctuation_capitalization",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use capitals and punctuation",
        description=(
            "Mark names, sentence boundaries, questions, lists, and dialogue so "
            "the reader can follow the intended meaning."
        ),
        prerequisite_skill_ids=("writing.complete_sentence",),
    ),
    CompetencyFamilyRef(
        skill_id="grammar.subject_verb_agreement",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Match subjects and verbs",
        description=(
            "Choose a verb form that agrees with the sentence subject in number "
            "and person."
        ),
        prerequisite_skill_ids=("grammar.noun_verb_adjective",),
    ),
    CompetencyFamilyRef(
        skill_id="writing.paragraph",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Develop an organised paragraph",
        description=(
            "Write a focused paragraph with an opening idea, connected supporting "
            "details, and a closing or concluding idea."
        ),
        prerequisite_skill_ids=(
            "writing.complete_sentence",
            "writing.short_answer",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="writing.dialogue",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Write a coherent dialogue",
        description=(
            "Write a brief exchange in which each turn has a clear speaker, "
            "responds to the previous turn, and uses readable punctuation."
        ),
        prerequisite_skill_ids=(
            "writing.complete_sentence",
            "grammar.punctuation_capitalization",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="writing.procedure",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Explain a procedure",
        description=(
            "Present materials, ordered actions, and an intended result using "
            "clear sequence language and necessary safety details."
        ),
        prerequisite_skill_ids=(
            "reading.event_sequence",
            "writing.complete_sentence",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="research.information_selection",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Select and report supplied facts",
        description=(
            "Choose relevant facts from a bounded, attributed source packet and "
            "report them accurately without inventing unsupported details."
        ),
        prerequisite_skill_ids=(
            "reading.paragraph_main_idea",
            "writing.short_answer",
        ),
    ),
    CompetencyFamilyRef(
        skill_id="speaking.recitation",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Recite with phrasing and expression",
        description=(
            "Recite a short age-appropriate text with audible phrasing, pace, and "
            "expression when a teacher or facilitator can observe performance."
        ),
        prerequisite_skill_ids=("reading.sentence_comprehension",),
    ),
    CompetencyFamilyRef(
        skill_id="speaking.multilingual_expression",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Share language knowledge across languages",
        description=(
            "Explain a familiar word or expression from another known language "
            "during an observed conversation without treating translation alone "
            "as English mastery."
        ),
        prerequisite_skill_ids=("speaking.recitation",),
    ),
    CompetencyFamilyRef(
        skill_id="listening.sound_discrimination",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Distinguish contrasting speech sounds",
        description=(
            "Distinguish spoken word pairs that differ by one sound when verified "
            "audio or a live facilitator supplies the listening evidence."
        ),
    ),
)

LOCKED_ENGLISH_SKILL_IDS: tuple[str, ...] = tuple(
    entry.skill_id for entry in LOCKED_ENGLISH_TAXONOMY_ENTRIES
)


def locked_english_taxonomy() -> SkillTaxonomy:
    return SkillTaxonomy(entries=LOCKED_ENGLISH_TAXONOMY_ENTRIES)


def locked_english_skill_ids() -> tuple[str, ...]:
    return LOCKED_ENGLISH_SKILL_IDS


__all__ = [
    "CompetencyFamilyRef",
    "CompetencyFamilyRegistry",
    "CompetencyStandardRef",
    "CompetencyStandardRegistry",
    "LOCKED_ENGLISH_SKILL_IDS",
    "LOCKED_ENGLISH_TAXONOMY_ENTRIES",
    "SkillTaxonomy",
    "SkillTaxonomyEntry",
    "locked_english_skill_ids",
    "locked_english_taxonomy",
]
