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

# Fuzzy fallback: the evaluator's `next_focus` is FREE PROSE ("work on your past
# tense", "use the STAR method", "give specific examples"), never a bare enum
# value, so an exact-match-only coerce dumped essentially every weakness into
# OTHER and the per-skill hit_count aggregate never summed. These rules map the
# prose onto the taxonomy by distinctive phrase. Ordered SPECIFIC -> GENERIC:
# the first rule with any matching substring wins, so "past tense" resolves to
# GRAMMAR_PAST_TENSE before the generic "tense" rule can claim it. Phrases are
# matched against a normalized (lowercased, hyphen/slash -> space) form. Keep the
# phrases distinctive — a false map is worse than an honest OTHER.
_FUZZY_RULES: tuple[tuple[SkillID, tuple[str, ...]], ...] = (
    # ---- grammar / mechanics (specific tenses before the generic tense rule) ----
    (SkillID.GRAMMAR_PAST_TENSE, ("past tense",)),
    (SkillID.GRAMMAR_PRESENT_TENSE, ("present tense",)),
    (SkillID.GRAMMAR_TENSE_MIXED,
     ("mixed tense", "tense consistency", "consistent tense", "verb tense", "tenses", "tense")),
    (SkillID.GRAMMAR_SUBJECT_VERB_AGREEMENT,
     ("subject verb", "verb agreement", "subject-verb")),
    (SkillID.GRAMMAR_ARTICLES, ("article",)),
    (SkillID.GRAMMAR_PLURALS, ("plural",)),
    (SkillID.GRAMMAR_PREPOSITIONS, ("preposition",)),
    (SkillID.SENTENCE_STRUCTURE,
     ("sentence structure", "sentence construction", "run on sentence",
      "sentence fragment", "complete sentence", "full sentence")),
    (SkillID.PARAGRAPH_STRUCTURE, ("paragraph",)),
    (SkillID.VOCABULARY_RANGE,
     ("vocabulary", "vocab", "word choice", "range of words", "lexical", "richer words")),
    # ---- phonics / early literacy ----
    (SkillID.PHONICS_BLENDING, ("blending", "blend the sounds", "blend sounds", "sound out")),
    (SkillID.PHONICS_LETTER_SOUNDS, ("letter sound", "phonics", "letter recognition")),
    (SkillID.SPELLING, ("spelling", "misspell", "spell the")),
    # ---- communication / fluency ----
    (SkillID.PRONUNCIATION, ("pronunciation", "pronounce", "pronouncing")),
    (SkillID.FLUENCY_HESITATION,
     ("hesitation", "hesitant", "filler", "fillers", "pauses", "fluency", "halting", "stumbl")),
    (SkillID.CLARITY_CONCISENESS,
     ("concise", "conciseness", "clarity", "clearer", "more clear", "to the point",
      "rambl", "wordy", "verbose", "brevity", "succinct")),
    (SkillID.LANGUAGE_NOT_ENGLISH,
     ("in english", "not english", "another language", "speak english", "use english")),
    # ---- interview ----
    (SkillID.STRUCTURE_STAR_METHOD,
     ("star method", "star format", "star technique", "star framework",
      "situation task action", "use star")),
    (SkillID.SPECIFICITY_EXAMPLES,
     ("specific example", "specificity", "concrete example", "give example",
      "give an example", "use examples", "add examples", "more detail", "more specific",
      "be specific", "vague")),
    (SkillID.ANSWER_RELEVANCE,
     ("relevance", "relevant", "answer the question", "actual question",
      "address the question", "stay on topic", "off topic", "stay on track")),
    (SkillID.CONFIDENCE_TONE,
     ("confidence", "confident", "assertive", "conviction", "self assured", "tone")),
    # ---- group discussion ----
    (SkillID.GD_TURN_TAKING,
     ("turn taking", "take turns", "interrupt", "let others", "speaking time",
      "airtime", "dominat", "give space")),
    (SkillID.GD_REBUTTAL,
     ("rebut", "rebuttal", "counter argument", "counterargument",
      "respond to other", "respond to point")),
    (SkillID.GD_STANCE_CLARITY,
     ("stance", "take a side", "clear position", "your position", "pick a side")),
    (SkillID.GD_CONSENSUS_BUILDING,
     ("consensus", "common ground", "build agreement", "bring the group", "synthesi")),
)


def is_skill_id(value: str) -> bool:
    """True if `value` is exactly a known SkillID member value."""
    return value in _VALUES


def _fuzzy_skill_id(prose: str) -> str:
    """Best-effort map of free prose onto the taxonomy via the rule table, else OTHER."""
    norm = prose.lower().replace("-", " ").replace("/", " ")
    norm = " ".join(norm.split())  # collapse whitespace
    for skill, phrases in _FUZZY_RULES:
        if any(p in norm for p in phrases):
            return skill.value
    return SkillID.OTHER.value


def coerce_skill_id(raw: "str | SkillID | None") -> str:
    """Map a raw model output to a known SkillID value, or OTHER.

    Exact-match first (case/whitespace tolerant) so a clean enum value — and the
    storage layer's defensive re-coerce of an already-clean value — passes through
    untouched. Otherwise treat the input as the evaluator's free-prose `next_focus`
    and FUZZY-map it onto the taxonomy by distinctive phrase (see `_FUZZY_RULES`):
    prose that names a real skill ("use the STAR method") now lands on that skill's
    aggregate row instead of collapsing into OTHER. Prose with no recognizable
    signal still becomes OTHER, so novel weaknesses bucket cleanly rather than
    fragmenting the per-skill hit_count.
    """
    if raw is None:
        return SkillID.OTHER.value
    if isinstance(raw, SkillID):
        return raw.value
    if raw.strip().upper() in _VALUES:
        return raw.strip().upper()
    return _fuzzy_skill_id(raw)
