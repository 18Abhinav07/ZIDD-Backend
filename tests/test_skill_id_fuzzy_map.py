"""P1 — coerce_skill_id fuzzy-maps free-prose next_focus onto the taxonomy.

The evaluator's `next_focus` is prose ("work on your past tense", "use the STAR
method"), never a bare enum value, so the old exact-match coerce dumped virtually
every weakness into OTHER and the per-skill hit_count aggregate never summed.
coerce_skill_id now exact-matches first (clean enums + the storage layer's
defensive re-coerce pass straight through) and otherwise fuzzy-maps the prose by
distinctive phrase, falling back to OTHER only when no signal is present.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.content.skills import SkillID, coerce_skill_id  # noqa: E402


# One representative prose phrasing per taxonomy family the evaluator actually
# emits, asserted to land on the right skill row.
@pytest.mark.parametrize("prose, expected", [
    # grammar / mechanics — specific tenses beat the generic tense rule
    ("you keep slipping into the past tense incorrectly", SkillID.GRAMMAR_PAST_TENSE),
    ("watch your present tense endings", SkillID.GRAMMAR_PRESENT_TENSE),
    ("keep your verb tenses consistent", SkillID.GRAMMAR_TENSE_MIXED),
    ("work on subject-verb agreement", SkillID.GRAMMAR_SUBJECT_VERB_AGREEMENT),
    ("remember to use the right article", SkillID.GRAMMAR_ARTICLES),
    ("your plural forms need work", SkillID.GRAMMAR_PLURALS),
    ("the wrong preposition there", SkillID.GRAMMAR_PREPOSITIONS),
    ("tighten your sentence structure", SkillID.SENTENCE_STRUCTURE),
    ("organise your paragraph better", SkillID.PARAGRAPH_STRUCTURE),
    ("widen your vocabulary", SkillID.VOCABULARY_RANGE),
    # phonics / early literacy
    ("practise blending the sounds", SkillID.PHONICS_BLENDING),
    ("revise your letter sounds", SkillID.PHONICS_LETTER_SOUNDS),
    ("careful with spelling", SkillID.SPELLING),
    # communication / fluency
    ("improve your pronunciation", SkillID.PRONUNCIATION),
    ("reduce hesitation and filler words", SkillID.FLUENCY_HESITATION),
    ("be more concise and to the point", SkillID.CLARITY_CONCISENESS),
    ("please answer in english", SkillID.LANGUAGE_NOT_ENGLISH),
    # interview
    ("structure the answer with the STAR method", SkillID.STRUCTURE_STAR_METHOD),
    ("give a concrete example next time", SkillID.SPECIFICITY_EXAMPLES),
    ("answer the question that was actually asked", SkillID.ANSWER_RELEVANCE),
    ("speak with more confidence", SkillID.CONFIDENCE_TONE),
    # group discussion
    ("let others take turns to speak", SkillID.GD_TURN_TAKING),
    ("offer a rebuttal to the other points", SkillID.GD_REBUTTAL),
    ("make your stance clear and pick a side", SkillID.GD_STANCE_CLARITY),
    ("work toward consensus with the group", SkillID.GD_CONSENSUS_BUILDING),
])
def test_fuzzy_prose_maps_to_expected_skill(prose, expected):
    assert coerce_skill_id(prose) == expected.value


def test_exact_match_still_short_circuits():
    # A clean enum value (and the storage layer's re-coerce of one) passes through
    # without engaging the fuzzy table — including OTHER itself.
    assert coerce_skill_id("GD_TURN_TAKING") == "GD_TURN_TAKING"
    assert coerce_skill_id("  structure_star_method  ") == "STRUCTURE_STAR_METHOD"
    assert coerce_skill_id("OTHER") == "OTHER"
    assert coerce_skill_id(SkillID.SPELLING) == "SPELLING"


def test_signal_free_prose_falls_to_other():
    # No recognizable skill phrase -> honest OTHER (a wrong map is worse).
    for prose in ("they did fine overall", "good effort today", "keep it up", ""):
        assert coerce_skill_id(prose) == "OTHER"
    assert coerce_skill_id(None) == "OTHER"


def test_specific_tense_beats_generic_tense_rule():
    # Ordering guard: "past tense" must resolve to PAST, not the generic mixed rule.
    assert coerce_skill_id("fix the past tense verbs") == "GRAMMAR_PAST_TENSE"
    assert coerce_skill_id("your tenses wander mid-answer") == "GRAMMAR_TENSE_MIXED"


def test_two_phrasings_of_one_weakness_converge():
    # The aggregation guarantee: different prose for the same skill -> one row key.
    a = coerce_skill_id("you forgot to use the STAR method")
    b = coerce_skill_id("structure it using STAR format")
    assert a == b == "STRUCTURE_STAR_METHOD"
