"""Deterministic non-LLM language pre-gate (Phase 0.2).

Local qwen's structured eval is over-lenient and unreliably sets the `english`
flag, so non-English answers slip through (and the bridge path stays
unreachable). This runs BEFORE the eval LLM as a cheap, deterministic check:
on a language-gated module, a long-enough answer judged non-English is
short-circuited (see evaluate_node) to an `english=False, score=0.0` diagnosis
that route_node sends to clarify — no LLM call needed.

Two complementary signals, both deterministic:
  1. A curated romanized-Hindi / Hinglish marker lexicon. langdetect reads
     Latin-script Hinglish as English (it keys on charset + n-gram profile, so a
     majority-English-by-token code-mix classifies as `en`), so the most common
     real failure — "I think company ko aur growth karna chahiye" — slips
     straight through. The lexicon catches it.
  2. langdetect itself, as the backstop for Devanagari and other confidently
     detected scripts.

Conservative by design: any uncertainty -> let the answer through to the LLM.
We never want to block a real English answer, so short inputs, names, "ok/yes",
the lenient school_english module, and predominantly-English answers (the marker
heuristic needs BOTH an absolute floor and a ratio floor) all bypass the gate.
"""
import string

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

# Curated romanized-Hindi / Hinglish markers. Deliberately UNAMBIGUOUS: every
# token here is one that essentially never appears as a valid English word.
# English-colliding romanizations are EXCLUDED on purpose so a real English
# answer is never gated — notably: main, the, to, par, is, us, do, ye, in, an,
# are, we, so, no, be, he (all valid English; all left out).
_HINGLISH_MARKERS = frozenset({
    # pronouns / postpositions
    "mujhe", "tujhe", "mujhse", "tujhse", "mera", "meri", "tera", "teri",
    "uska", "uski", "unka", "unki", "hum", "tum", "mein", "ko", "ka", "ki",
    "ke", "se", "pe", "ne", "inko", "unko",
    # copula / auxiliaries
    "hai", "hain", "tha", "thi", "hota", "hoti", "hote", "hona", "raha",
    "rahi", "rahe", "hua", "hui", "hue", "gaya", "gayi", "gaye",
    # question words / conjunctions
    "kya", "kyun", "kyon", "kyunki", "kyonki", "kaise", "kaisa", "kaisi",
    "jaise", "waise", "aur", "lekin", "magar", "toh", "ya", "isliye",
    "matlab", "agar", "jab", "tab", "phir",
    # negation / affirmation
    "nahi", "nahin", "haan",
    # common verbs
    "kar", "karna", "karta", "karti", "karte", "karo", "karunga", "karenge",
    "kiya", "jata", "jaata", "jana", "jaana", "diya", "liya", "dena", "lena",
    "chahiye", "chahta", "chahti", "lagta", "lagti", "lagte", "samajh",
    "pata", "bola", "bolta", "dekha", "soch", "socha",
    # adjectives / adverbs / misc
    "bahut", "bohot", "thoda", "sab", "kuch", "kuchh", "acha", "accha",
    "achha", "theek", "thik", "sahi", "galat", "bilkul", "abhi", "yaar",
    "bhi", "sirf", "bas", "ek", "wala", "wali", "wale",
    # determiners
    "yeh", "woh", "wo", "voh",
})

# A romanized / code-mixed answer must clear BOTH floors to gate: an absolute
# count (a lone stray marker never trips) AND a ratio (a predominantly-English
# answer with one or two Hindi words is left for the LLM, not slammed to 0.0).
_HINGLISH_MIN_MARKERS = 2
_HINGLISH_MARKER_RATIO = 0.30


def is_language_gated(module_id: str) -> bool:
    return module_id in LANGUAGE_GATED_MODULES


def _is_romanized_code_mixed(tokens: list[str]) -> bool:
    """True when enough tokens are unambiguous Hinglish markers that the answer
    is substantially non-English — the case langdetect misses because the script
    is Latin. Requires both an absolute and a ratio floor so a stray marker or a
    mostly-English answer never trips."""
    hits = 0
    for tok in tokens:
        if tok.strip(string.punctuation).lower() in _HINGLISH_MARKERS:
            hits += 1
    return hits >= _HINGLISH_MIN_MARKERS and hits / len(tokens) >= _HINGLISH_MARKER_RATIO


def fails_language_gate(user_input: str, module_id: str) -> bool:
    """True only when we are confident the answer is non-English on a gated
    module and long enough to judge. Any uncertainty returns False so the LLM
    evaluator still gets the final say and a real English answer is never blocked.
    """
    if not is_language_gated(module_id):
        return False
    tokens = user_input.split()
    if len(tokens) < MIN_LANGCHECK_TOKENS:
        return False
    # (1) Romanized-Hindi / code-mix lexicon: catches the Latin-script Hinglish
    #     that langdetect reads as English.
    if _is_romanized_code_mixed(tokens):
        return True
    # (2) langdetect backstop: Devanagari and other confidently detected scripts.
    try:
        return detect(user_input) != "en"
    except LangDetectException:
        return False
