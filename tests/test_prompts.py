"""Prompt-builder content guards — no network, no model call.

Cheap assertions that the evaluator prompt actually carries the ruthless-0.0
rubric and English-only mandate (council fix #2). The model can still ignore
them, but a regression that silently drops the rules from the prompt is caught
here.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_eval_prompt, coach_view  # noqa: E402
from app.content.registry import get_node  # noqa: E402


def _prompt() -> str:
    node = get_node("comm_01_self_intro")
    return build_eval_prompt(node, [], "some answer").lower()


def test_eval_prompt_has_zero_rubric():
    p = _prompt()
    assert "0.0" in p
    for needle in ("empty", "gibberish", "emoji", "refusal", "off-task"):
        assert needle in p, f"rubric missing '{needle}'"


def test_eval_prompt_mandates_english():
    p = _prompt()
    assert "english" in p
    assert "not in english" in p or "non-english" in p


def test_eval_prompt_asks_on_task_and_english_fields():
    # The model must report the on_task / english split so routing can tell a
    # fluent-but-off-task answer (redirect) from a genuine non-answer (bridge).
    p = _prompt()
    assert "on_task" in p
    assert "english:" in p or '"english"' in p


def test_eval_prompt_asks_affect():
    p = _prompt()
    assert "affect" in p


# ---------- fix #5: affect-driven support ----------

def test_coach_view_support_from_frustrated_affect():
    # Even without the regex frustration flag, a 'frustrated' affect read from
    # the diagnosis must flip the support directive on.
    state = {"last_diagnosis": {"affect": "frustrated"}}
    assert coach_view(state)["support"] is True


def test_coach_view_neutral_affect_no_support():
    state = {"last_diagnosis": {"affect": "neutral"}}
    assert coach_view(state)["support"] is False
