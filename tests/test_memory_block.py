"""Phase 2.4 — personalization block renders named weaknesses.

Felt continuity: the prompt's memory block must surface the learner's logged
weaknesses (from the Phase-2 store, aggregated on SkillID) so the coach can say
"last time you struggled with X" instead of starting cold every session.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import _memory_block  # noqa: E402


def test_memory_block_empty_when_nothing_known():
    assert _memory_block([]) == ""


def test_memory_block_empty_string_legacy_still_ok():
    assert _memory_block("") == ""


def test_memory_block_renders_memory_context_legacy_str():
    out = _memory_block("She loves cricket analogies.")
    assert "cricket" in out


def test_memory_block_renders_list_dict():
    rows = [
        {
            "node_id": "comm_04",
            "score": 0.62,
            "strengths": "good vocabulary",
            "watch": "missing articles",
            "next_focus": "article usage",
            "date": "2026-06-08",
            "raw": "Strengths: good vocabulary\nWatch: missing articles\nNext focus: article usage",
        }
    ]
    out = _memory_block(rows)
    assert "comm_04" in out
    assert "0.62" in out
    assert "good vocabulary" in out
    assert "missing articles" in out


def test_memory_block_list_dict_most_recent_label():
    rows = [{"node_id": "comm_01", "score": 0.8, "strengths": "clear", "watch": "", "next_focus": "", "date": "2026-06-07", "raw": ""}]
    out = _memory_block(rows)
    assert "Most recent session" in out


def test_memory_block_list_dict_multiple_sessions():
    rows = [
        {"node_id": "comm_02", "score": 0.75, "strengths": "fluent", "watch": "tense", "next_focus": "past tense", "date": "2026-06-08", "raw": ""},
        {"node_id": "comm_01", "score": 0.55, "strengths": "", "watch": "articles", "next_focus": "article usage", "date": "2026-06-07", "raw": ""},
    ]
    out = _memory_block(rows)
    assert "Most recent session" in out
    assert "2 sessions ago" in out
    assert "comm_02" in out
    assert "comm_01" in out


def test_memory_block_renders_weakness():
    weaknesses = [
        {"skill_id": "STRUCTURE_STAR_METHOD", "hit_count": 3, "last_raw": "no STAR structure"},
        {"skill_id": "GRAMMAR_PAST_TENSE", "hit_count": 1, "last_raw": "mixed tenses"},
    ]
    out = _memory_block([], weaknesses=weaknesses)
    assert out != ""
    assert "STRUCTURE_STAR_METHOD" in out
    assert "no STAR structure" in out


def test_memory_block_combines_list_dict_and_weakness():
    rows = [{"node_id": "gd_01", "score": 0.5, "strengths": "confident", "watch": "", "next_focus": "turn-taking", "date": "2026-06-08", "raw": ""}]
    out = _memory_block(
        rows,
        weaknesses=[{"skill_id": "GD_TURN_TAKING", "hit_count": 2, "last_raw": "interrupts"}],
    )
    assert "gd_01" in out
    assert "GD_TURN_TAKING" in out


def test_memory_block_combines_memory_and_weakness():
    out = _memory_block(
        "She loves cricket.",
        weaknesses=[{"skill_id": "GD_TURN_TAKING", "hit_count": 2, "last_raw": "interrupts"}],
    )
    assert "cricket" in out
    assert "GD_TURN_TAKING" in out
