"""Phase 1.3 — BehaviorPack injection into prompt builders.

The engine graph is identical across task types; the only per-type difference
is *voice* and *stance*, carried by a BehaviorPack. These guards prove the pack
is actually threaded into the rendered prompt (persona, pedagogy, output style)
and that the evaluator's language gate tightens/loosens with the pack's
`language_strictness`. No network, no model call.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.behaviors import behavior_for  # noqa: E402
from app.ai.prompts import (  # noqa: E402
    build_eval_prompt,
    build_opening_prompt,
    build_teach_prompt,
)
from app.content.registry import get_node  # noqa: E402
from app.content.task_types import TaskType  # noqa: E402


def test_behavior_pack_in_prompt():
    # An injected pack's persona, pedagogy, and output style all reach the prompt.
    node = get_node("int_01_elevator_pitch")
    pack = behavior_for(TaskType.INTERVIEW_PREP)
    prompt = build_opening_prompt(node, "", coach=None, behavior=pack)
    assert pack.persona in prompt
    assert pack.pedagogy in prompt
    assert pack.output_style in prompt


def test_default_behavior_falls_back_to_base_persona():
    # No pack -> the legacy single-voice persona, so existing callers don't break.
    from app.ai.prompts import TUTOR_PERSONA

    node = get_node("comm_01_self_intro")
    prompt = build_opening_prompt(node, "")
    assert TUTOR_PERSONA in prompt


def test_school_prompt_is_gentle():
    node = get_node("c2_alphabet_sounds")
    pack = behavior_for(TaskType.SCHOOL_ENGLISH)
    prompt = build_opening_prompt(node, "", coach=None, behavior=pack).lower()
    assert "child" in prompt or "gentle" in prompt or "playful" in prompt


def test_teach_prompt_carries_behavior():
    node = get_node("int_01_elevator_pitch")
    pack = behavior_for(TaskType.INTERVIEW_PREP)
    prompt = build_teach_prompt(node, [], {}, "", coach=None, behavior=pack)
    assert pack.persona in prompt


def test_gd_test_prompt_gates_language_strict():
    # A strict pack tightens the evaluator's bar; a lenient pack loosens it.
    node = get_node("gd_01_stake_position")
    strict = build_eval_prompt(
        node, [], "answer", behavior=behavior_for(TaskType.GD_TEST)
    ).lower()
    lenient = build_eval_prompt(
        node, [], "answer", behavior=behavior_for(TaskType.SCHOOL_ENGLISH)
    ).lower()
    assert "high bar" in strict or "strict" in strict
    assert "generous" in lenient or "lenient" in lenient or "young" in lenient
