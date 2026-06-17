"""Phase 0.2 (secondary) — eval-prompt tightening, defense-in-depth.

The langdetect pre-gate stops cleanly non-English answers, but code-mixed /
heavily broken English passes the gate (langdetect calls it "en") and reaches
the LLM. Local qwen tends to praise it. So the eval prompt carries an explicit
worked example: a broken / code-mixed answer must score low (<=0.3). This is a
prompt-content assertion (offline, no LLM call) — it guards the instruction,
not the model's obedience.
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.ai.prompts import build_eval_prompt  # noqa: E402
from app.content.registry import get_node  # noqa: E402


def test_eval_prompt_has_broken_english_fewshot():
    node = get_node("comm_01_self_intro")
    prompt = build_eval_prompt(node, [], "me name rahul, i is go office daily morning")

    low = prompt.lower()
    # An explicit worked example anchoring broken / code-mixed English to a low score.
    assert "example" in low
    assert "broken" in low or "code-mix" in low or "code mix" in low
    # The example must name a low ceiling for broken English so qwen can't praise it.
    assert "0.3" in prompt
