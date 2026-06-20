"""Phase 2.2a — fixed SkillID taxonomy for weakness aggregation.

Free-text weakness tags never aggregate: "struggles with past tense" and
"failed past tense" become two rows that never sum. So the evaluator emits a
`skill_id` from a CLOSED enum; weaknesses UPSERT on exact (user, task_type,
skill_id). Anything the model emits that isn't a known member coerces to OTHER
so a novel weakness is bucketed, never lost and never silently dropped.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.skills import OTHER, SkillID, coerce_skill_id, is_skill_id  # noqa: E402


def test_other_is_a_member():
    assert OTHER == SkillID.OTHER
    assert is_skill_id("OTHER") is True


def test_known_skill_ids_exist_per_family():
    # A few anchors from each task family the plan names explicitly.
    for name in (
        "GRAMMAR_PAST_TENSE",
        "STRUCTURE_STAR_METHOD",
        "GD_TURN_TAKING",
        "PHONICS_BLENDING",
    ):
        assert is_skill_id(name) is True


def test_coerce_passes_through_valid_member():
    assert coerce_skill_id("GRAMMAR_PAST_TENSE") == "GRAMMAR_PAST_TENSE"
    assert coerce_skill_id(SkillID.GD_TURN_TAKING) == "GD_TURN_TAKING"


def test_coerce_unmatched_falls_to_other():
    # Genuinely signal-free prose still buckets to OTHER (no fuzzy rule fires).
    assert coerce_skill_id("they did fine overall") == "OTHER"
    assert coerce_skill_id("") == "OTHER"
    assert coerce_skill_id(None) == "OTHER"
    # Case / whitespace tolerance onto an exact member.
    assert coerce_skill_id("  grammar_past_tense  ") == "GRAMMAR_PAST_TENSE"


def test_coerce_fuzzy_maps_prose_onto_taxonomy():
    # Free-prose next_focus now lands on the named skill instead of OTHER (see
    # the dedicated fuzzy test for the full matrix). The two phrasings the module
    # docstring calls out must converge on ONE row.
    assert coerce_skill_id("struggles with past tense") == "GRAMMAR_PAST_TENSE"
    assert coerce_skill_id("failed past tense again") == "GRAMMAR_PAST_TENSE"
