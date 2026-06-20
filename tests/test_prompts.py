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

from app.ai.prompts import build_eval_prompt, coach_view, _coach_block, _history_block  # noqa: E402
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


# ---------- P1: de-formulaic openers (name + progress no longer forced every turn) ----------

def test_coach_block_always_carries_vary_openings_directive():
    # The anti-template rule must be present whenever there is any coaching dict.
    assert "vary how you open" in _coach_block({"clean_streak": 0}).lower()


def test_name_directive_is_soft_not_forced():
    block = _coach_block({"name": "Rahul"})
    low = block.lower()
    assert "rahul" in low
    assert "naturally" in low
    # the old forced phrasing is gone
    assert "must address" not in low
    assert "at least once" not in low


def test_progress_line_suppressed_at_zero_streak():
    # A fresh/struggling learner must NOT be told "0 of 2" every turn.
    block = _coach_block({"clean_streak": 0, "advance_streak": 2})
    assert "clean passes" not in block.lower()


def test_progress_line_present_once_streak_started():
    block = _coach_block({"clean_streak": 1, "advance_streak": 3})
    low = block.lower()
    assert "1 of 3 clean passes" in low


def test_progress_emphasises_the_win_one_pass_from_advance():
    block = _coach_block({"clean_streak": 1, "advance_streak": 2})
    low = block.lower()
    assert "one clean pass from the next level" in low


# ---- _history_block char budget (large-context builders) --------------------

def test_history_block_no_budget_keeps_every_turn():
    # the default coaching path (limit=8, no max_chars) must be byte-for-byte the
    # old behaviour: no trimming, every turn in the window rendered.
    msgs = [{"role": "user", "content": "x" * 500} for _ in range(8)]
    block = _history_block(msgs)
    assert block.count("user:") == 8


def test_history_block_budget_drops_oldest_until_it_fits():
    # 40 long turns exceed the budget; the oldest lines are dropped, the most
    # recent are kept, and the block fits inside max_chars.
    msgs = [{"role": "user", "content": f"turn-{i} " + "x" * 400} for i in range(40)]
    block = _history_block(msgs, limit=40, max_chars=2000)
    assert len(block) <= 2000
    assert "turn-39" in block          # newest kept
    assert "turn-0 " not in block      # oldest dropped


def test_history_block_budget_never_drops_below_one_line():
    # even a single oversized turn must still render (we never return empty).
    msgs = [{"role": "user", "content": "y" * 5000}]
    block = _history_block(msgs, limit=40, max_chars=100)
    assert block.startswith("user:")
    assert "y" in block
