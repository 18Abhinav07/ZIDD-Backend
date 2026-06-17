"""Deterministic non-LLM language pre-gate (Phase 0.2).

Local qwen's structured eval is over-lenient and unreliably sets the `english`
flag, so non-English answers slip through (and the bridge path stays
unreachable). This runs BEFORE the eval LLM as a cheap, deterministic check:
on a language-gated module, a long-enough answer detected as non-English is
short-circuited (see evaluate_node) to an `english=False, score=0.0` diagnosis
that route_node sends to bridge — no LLM call needed.

Conservative by design: any uncertainty -> let the answer through to the LLM.
We never want to block a real English answer, so short inputs, names, "ok/yes",
and the lenient school_english module all bypass the gate.
"""
from langdetect import DetectorFactory, detect
from langdetect.lang_detect_exception import LangDetectException

# langdetect is randomised per-process; pin the seed so the gate is
# deterministic (same input -> same verdict) for tests and reproducibility.
DetectorFactory.seed = 0

# Modules whose answers must be in English. school_english is intentionally
# excluded: children code-mix and transliterate constantly, so gating it would
# false-positive and punish exactly the learners it should encourage.
LANGUAGE_GATED_MODULES = frozenset({"communication", "interview", "group_discussion"})

# Below this token count, skip detection. Names, "ok", "yes please", and short
# fragments fool langdetect into a wrong language and would false-positive.
MIN_LANGCHECK_TOKENS = 4


def is_language_gated(module_id: str) -> bool:
    return module_id in LANGUAGE_GATED_MODULES


def fails_language_gate(user_input: str, module_id: str) -> bool:
    """True only when we are confident the answer is non-English on a gated
    module and long enough to judge. Any uncertainty returns False so the LLM
    evaluator still gets the final say and a real English answer is never blocked.
    """
    if not is_language_gated(module_id):
        return False
    if len(user_input.split()) < MIN_LANGCHECK_TOKENS:
        return False
    try:
        return detect(user_input) != "en"
    except LangDetectException:
        return False
