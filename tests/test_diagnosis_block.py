"""P1 — the diagnosis is rendered as clean labelled lines, not a Python dict repr.

The coaching builders (teach / bridge / strengthen / challenge / redirect /
clarify / ease) used to f-string the raw diagnosis dict into the prompt, which
emits a Python repr: braces, quotes, booleans, and fields the coaching move does
not need (score, goodbye, on_task, english). A local model parses labelled plain
lines far better than dict syntax. `_diagnosis_block` now renders only the fields
that shape the next move.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import _diagnosis_block, build_teach_prompt  # noqa: E402
from app.content.registry import get_node  # noqa: E402

_DIAG = {
    "score": 0.42,
    "understanding": "grasped the greeting but not the role",
    "errors": ["missing the job title", "tense slipped to present"],
    "strengths": ["clear self-introduction"],
    "next_focus": "state your current role in one clause",
    "on_task": True,
    "english": True,
    "affect": "confused",
    "goodbye": False,
}


# ---------- the helper renders labelled lines, drops the noise ----------

def test_block_has_no_dict_repr_syntax():
    out = _diagnosis_block(_DIAG)
    # none of the Python-repr scaffolding leaks into the prompt
    for needle in ("{", "}", "'understanding'", "'score'", "True", "False"):
        assert needle not in out, f"dict-repr artifact leaked: {needle!r}"


def test_block_surfaces_the_useful_fields():
    out = _diagnosis_block(_DIAG)
    assert "grasped the greeting but not the role" in out
    assert "missing the job title" in out
    assert "clear self-introduction" in out
    assert "state your current role in one clause" in out


def test_block_drops_irrelevant_fields():
    out = _diagnosis_block(_DIAG)
    # score / goodbye / the on_task & english booleans never belong in a teaching move
    assert "0.42" not in out
    assert "goodbye" not in out.lower()
    assert "on_task" not in out.lower()


def test_block_shows_non_neutral_affect_only():
    assert "emotional tone: confused" in _diagnosis_block(_DIAG)
    neutral = {**_DIAG, "affect": "neutral"}
    assert "emotional tone" not in _diagnosis_block(neutral)


def test_block_caps_errors_and_strengths_at_three():
    many = {
        "understanding": "u",
        "errors": ["e1", "e2", "e3", "e4", "e5"],
        "strengths": ["s1", "s2", "s3", "s4"],
        "next_focus": "n",
    }
    out = _diagnosis_block(many)
    assert "e3" in out and "e4" not in out
    assert "s3" in out and "s4" not in out


def test_empty_diagnosis_is_graceful():
    out = _diagnosis_block({})
    assert "{" not in out and "}" not in out
    assert "no prior read" in out.lower()


def test_diagnosis_with_only_empty_lists_notes_no_detail():
    out = _diagnosis_block({"errors": [], "strengths": [], "understanding": "", "next_focus": ""})
    assert "no detail captured" in out.lower()


# ---------- wired into a real coaching builder ----------

def test_teach_prompt_uses_the_clean_block_not_dict_repr():
    node = get_node("comm_01_self_intro")
    prompt = build_teach_prompt(node, [], _DIAG, [])
    assert "Your read of their last answer:" in prompt
    assert "- main error(s): missing the job title" in prompt
    # the raw dict repr must not appear
    assert "'understanding':" not in prompt
    assert "{'score'" not in prompt
