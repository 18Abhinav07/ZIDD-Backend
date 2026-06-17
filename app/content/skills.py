"""Fixed SkillID taxonomy — the closed vocabulary weaknesses aggregate on.

The evaluator emits ONE `skill_id` per low-scoring answer, drawn from this
closed enum. Weaknesses UPSERT on the exact (user_id, task_type, skill_id)
tuple, so the same skill always lands on the same row and `hit_count` actually
sums. Free text ("struggles with past tense" vs "failed past tense") never
would. Anything outside the enum coerces to OTHER — bucketed, never lost.

Keep this small and stable: it is a join key, not prose. Raw model phrasing is
kept separately (weaknesses.last_raw) for prompt color. Add members
deliberately; renaming one orphans its history.
"""
from enum import Enum


class SkillID(str, Enum):
    # ---------- grammar / mechanics (school + communication) ----------
    GRAMMAR_PAST_TENSE = "GRAMMAR_PAST_TENSE"
    GRAMMAR_PRESENT_TENSE = "GRAMMAR_PRESENT_TENSE"
    GRAMMAR_TENSE_MIXED = "GRAMMAR_TENSE_MIXED"
    GRAMMAR_SUBJECT_VERB_AGREEMENT = "GRAMMAR_SUBJECT_VERB_AGREEMENT"
    GRAMMAR_ARTICLES = "GRAMMAR_ARTICLES"
    GRAMMAR_PLURALS = "GRAMMAR_PLURALS"
    GRAMMAR_PREPOSITIONS = "GRAMMAR_PREPOSITIONS"
    VOCABULARY_RANGE = "VOCABULARY_RANGE"
    SENTENCE_STRUCTURE = "SENTENCE_STRUCTURE"

    # ---------- phonics / early literacy (school_english) ----------
    PHONICS_BLENDING = "PHONICS_BLENDING"
    PHONICS_LETTER_SOUNDS = "PHONICS_LETTER_SOUNDS"
    SPELLING = "SPELLING"
    PARAGRAPH_STRUCTURE = "PARAGRAPH_STRUCTURE"

    # ---------- communication / fluency ----------
    FLUENCY_HESITATION = "FLUENCY_HESITATION"
    CLARITY_CONCISENESS = "CLARITY_CONCISENESS"
    PRONUNCIATION = "PRONUNCIATION"
    LANGUAGE_NOT_ENGLISH = "LANGUAGE_NOT_ENGLISH"

    # ---------- interview ----------
    STRUCTURE_STAR_METHOD = "STRUCTURE_STAR_METHOD"
    ANSWER_RELEVANCE = "ANSWER_RELEVANCE"
    SPECIFICITY_EXAMPLES = "SPECIFICITY_EXAMPLES"
    CONFIDENCE_TONE = "CONFIDENCE_TONE"

    # ---------- group discussion ----------
    GD_TURN_TAKING = "GD_TURN_TAKING"
    GD_REBUTTAL = "GD_REBUTTAL"
    GD_STANCE_CLARITY = "GD_STANCE_CLARITY"
    GD_CONSENSUS_BUILDING = "GD_CONSENSUS_BUILDING"

    # ---------- fallback bucket ----------
    OTHER = "OTHER"


OTHER = SkillID.OTHER
_VALUES: frozenset[str] = frozenset(s.value for s in SkillID)


def is_skill_id(value: str) -> bool:
    """True if `value` is exactly a known SkillID member value."""
    return value in _VALUES


def coerce_skill_id(raw: "str | SkillID | None") -> str:
    """Map a raw model output to a known SkillID value, or OTHER.

    Tolerant of case and surrounding whitespace, but ONLY onto real members —
    arbitrary free text becomes OTHER so novel weaknesses bucket cleanly instead
    of fragmenting the aggregate.
    """
    if raw is None:
        return SkillID.OTHER.value
    if isinstance(raw, SkillID):
        return raw.value
    candidate = raw.strip().upper()
    return candidate if candidate in _VALUES else SkillID.OTHER.value
