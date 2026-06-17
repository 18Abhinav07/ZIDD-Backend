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

from app.ai.prompts import build_eval_prompt, coach_view, _coach_block  # noqa: E402
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


# ---------- C20: confident affect must reach the coach ----------

def test_coach_view_exposes_confident_affect():
    # 'confident' was read by the evaluator but silently discarded by coach_view.
    state = {"last_diagnosis": {"affect": "confident"}}
    assert coach_view(state)["confident"] is True


def test_coach_view_confident_not_set_when_neutral():
    state = {"last_diagnosis": {"affect": "neutral"}}
    assert coach_view(state)["confident"] is False


def test_confident_does_not_also_trip_support():
    # Confident is the opposite of struggling — it must NOT turn on support.
    state = {"last_diagnosis": {"affect": "confident"}}
    assert coach_view(state)["support"] is False


def test_coach_block_confident_directive_stretches():
    block = _coach_block({"confident": True})
    low = block.lower()
    assert "confiden" in low or "stretch" in low or "raise the bar" in low


# ---------- A7: remediation / level_kind must reach the coach ----------

def test_coach_view_exposes_level_kind_and_remediation():
    # A module that fell below the clean-rate floor is in a remediation 'bridge'
    # section; coach_view must surface both so the coach can adapt its framing.
    state = {"remediation": True}
    view = coach_view(state)
    assert view["remediation"] is True
    assert view["level_kind"] == "bridge"


def test_coach_view_level_kind_defaults_prep():
    assert coach_view({})["level_kind"] == "prep"
    assert coach_view({})["remediation"] is False


def test_coach_block_remediation_directive_present():
    block = _coach_block({"level_kind": "bridge", "remediation": True})
    low = block.lower()
    assert "again" in low or "before" in low or "revisit" in low or "remediat" in low
