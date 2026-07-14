"""Locked School V3 English skill taxonomy.

The IDs are subject-wide skills that can recur across class 2-5 chapters. Class
range and prerequisites model progression without inventing per-chapter aliases.
"""

from __future__ import annotations

from app.content.school_v3_schema import SkillTaxonomy, SkillTaxonomyEntry


LOCKED_ENGLISH_SKILL_IDS: tuple[str, ...] = (
    "reading.word_meaning_context",
    "reading.sentence_comprehension",
    "reading.paragraph_main_idea",
    "reading.inference_reason",
    "vocab.chapter_word_usage",
    "grammar.noun_verb_adjective",
    "grammar.tense_usage",
    "grammar.connectors_because_and_but",
    "grammar.sentence_order",
    "writing.complete_sentence",
    "writing.short_answer",
    "writing.reason_answer",
    "writing.summary_own_words",
    "writing.compare_contrast",
    "writing.friendly_message",
)


LOCKED_ENGLISH_TAXONOMY_ENTRIES: tuple[SkillTaxonomyEntry, ...] = (
    SkillTaxonomyEntry(
        skill_id="reading.word_meaning_context",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use context to understand words",
        description="Infer the meaning of a word from sentence or passage clues.",
    ),
    SkillTaxonomyEntry(
        skill_id="reading.sentence_comprehension",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Understand sentence meaning",
        description="Read a sentence and identify who or what it is about.",
    ),
    SkillTaxonomyEntry(
        skill_id="reading.paragraph_main_idea",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Find the main idea",
        description="Identify the central idea of a short passage or chapter section.",
        prerequisite_skill_ids=["reading.sentence_comprehension"],
    ),
    SkillTaxonomyEntry(
        skill_id="reading.inference_reason",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Infer a reason",
        description="Use textual clues to explain why an event happened or why a character acted.",
        prerequisite_skill_ids=["reading.sentence_comprehension"],
    ),
    SkillTaxonomyEntry(
        skill_id="vocab.chapter_word_usage",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Use chapter vocabulary",
        description="Use new words from a chapter correctly in a sentence or answer.",
        prerequisite_skill_ids=["reading.word_meaning_context"],
    ),
    SkillTaxonomyEntry(
        skill_id="grammar.noun_verb_adjective",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Identify nouns, verbs, and adjectives",
        description="Recognize basic word roles and use them in simple sentences.",
    ),
    SkillTaxonomyEntry(
        skill_id="grammar.tense_usage",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Use tense correctly",
        description="Choose present, past, or future forms that match the sentence context.",
        prerequisite_skill_ids=["grammar.noun_verb_adjective"],
    ),
    SkillTaxonomyEntry(
        skill_id="grammar.connectors_because_and_but",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Use because, and, and but",
        description="Connect ideas with reason, addition, and contrast markers.",
        prerequisite_skill_ids=["reading.sentence_comprehension"],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.complete_sentence",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Write a complete sentence",
        description="Write an answer with a subject and meaningful action or description.",
        prerequisite_skill_ids=["reading.sentence_comprehension"],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.short_answer",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write a short answer",
        description="Answer a reading question clearly in one or two relevant sentences.",
        prerequisite_skill_ids=["writing.complete_sentence"],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.reason_answer",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write an answer with a reason",
        description="Support an answer with a because/evidence clue rather than only restating the event.",
        prerequisite_skill_ids=[
            "reading.inference_reason",
            "grammar.connectors_because_and_but",
            "writing.short_answer",
        ],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.summary_own_words",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Summarize in own words",
        description="Retell the main idea or chapter event without copying a model answer.",
        prerequisite_skill_ids=[
            "reading.paragraph_main_idea",
            "writing.short_answer",
        ],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.compare_contrast",
        subject_id="english",
        class_min=4,
        class_max=5,
        name="Compare two subjects",
        description=(
            "State an accurate similarity and difference using clear comparison "
            "language."
        ),
        prerequisite_skill_ids=[
            "reading.sentence_comprehension",
            "writing.short_answer",
        ],
    ),
    SkillTaxonomyEntry(
        skill_id="writing.friendly_message",
        subject_id="english",
        class_min=3,
        class_max=5,
        name="Write a friendly message",
        description=(
            "Reply to a known reader with a greeting, relevant details, a useful "
            "question or response, and a closing."
        ),
        prerequisite_skill_ids=["writing.complete_sentence"],
    ),
    SkillTaxonomyEntry(
        skill_id="grammar.sentence_order",
        subject_id="english",
        class_min=2,
        class_max=5,
        name="Arrange words into a sentence",
        description=(
            "Order jumbled words into a grammatical sentence with a clear subject "
            "and action or description."
        ),
        prerequisite_skill_ids=["reading.sentence_comprehension"],
    ),
)


def locked_english_taxonomy() -> SkillTaxonomy:
    return SkillTaxonomy(entries=list(LOCKED_ENGLISH_TAXONOMY_ENTRIES))


def locked_english_skill_ids() -> tuple[str, ...]:
    return LOCKED_ENGLISH_SKILL_IDS
