"""_detect_frustration — high-precision discouragement pre-gate.

The naive substring scan fired the support pivot on upbeat / negated messages
("I can't wait to start, this is fun!", "I'm not frustrated at all"), patronising
a confident learner. The detector now vetoes known positive/negated idioms and
matches phrases on word boundaries. It must STILL fire on genuine frustration
(recall is backstopped by the LLM affect read, but clear cases must not regress).
"""
import os

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

import pytest  # noqa: E402

from app.services.session_service import _detect_frustration  # noqa: E402


# ---------- genuine frustration MUST still fire (no recall regression) ----------

@pytest.mark.parametrize("msg", [
    "I can't do this",
    "this is too hard",
    "I give up",
    "I'm so frustrated with this exercise",
    "I'm confused",
    "I'm lost",
    "I don't get it",
    "this is hard and I keep failing",
])
def test_genuine_frustration_fires(msg):
    assert _detect_frustration(msg) is True


# ---------- upbeat / negated messages MUST NOT fire (precision) ----------

@pytest.mark.parametrize("msg", [
    "I can't wait to start, this is fun!",      # positive idiom
    "I'm not frustrated at all, loving it",     # negation
    "too hard work pays off, I nailed it",      # "hard work" idiom
    "I don't give up easily",                   # negation
    "I will never give up on this",             # negation
    "this isn't too hard for me",               # contracted negation
    "communication is the exchange of ideas",   # unrelated answer
    "",                                          # empty
])
def test_positive_or_neutral_does_not_fire(msg):
    assert _detect_frustration(msg) is False


def test_none_input_is_safe():
    assert _detect_frustration(None) is False  # type: ignore[arg-type]
