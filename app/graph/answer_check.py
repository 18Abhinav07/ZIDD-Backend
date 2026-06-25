"""Deterministic pre-evaluation checks (no LLM).

Two faults this fixes (P0-3):

  * Served bridge answer keys were never checked. A pre-authored fill_blank/MCQ
    has exactly ONE correct answer, but the learner's fill was routed back through
    the general LLM rubric (which has no access to the key) and fuzzily mis-scored.
    `grade_pending_answer` grades it exactly against the key.

  * A short "idk" / "not sure" was over-flagged by the evaluator as off-task and
    misrouted to redirect (which pushes a HARDER task) instead of bridge (scaffold
    down). `is_giveup` catches the stuck-learner signal deterministically.

All functions are pure and depend on nothing in the graph, so they unit-test in
isolation.
"""
import re

from app.ai.schemas import DiagnosisEval

# A correct scaffolded answer is a genuine win that breaks the fail streak and
# counts as a pass; a wrong one keeps the learner in the sub-0.4 bridge band so
# the next turn scaffolds further. Neither is a full-mastery (0.85+) signal.
BRIDGE_CORRECT_SCORE = 0.7
BRIDGE_WRONG_SCORE = 0.3


def _norm(s: str) -> str:
    """Lowercase, keep word chars + apostrophes, collapse the rest to spaces."""
    return re.sub(r"[^a-z0-9' ]+", " ", (s or "").lower()).strip()


# ---------- give-up / stuck detection ----------

# Substrings that, in a SHORT message, signal a learner who is stuck rather than
# answering a different question. Kept tight; the word-count guard below stops a
# long sentence that merely contains "not sure" from being treated as a give-up.
_GIVEUP_PATTERNS = (
    "idk", "i dont know", "i don't know", "dont know", "don't know",
    "do not know", "no idea", "not sure", "im not sure", "i'm not sure",
    "i am not sure", "dunno", "no clue", "i give up", "i cant", "i can't",
    "i cannot", "i dont get", "i don't get", "not sure what to say",
    "dont know what to say", "don't know what to say", "no clue what to say",
)
# Broken-English / ESL stuck signals — the SAME give-up intent in non-native
# grammar. The struggling learner who most needs scaffolding phrases it worst
# ("is bad i not know", "me no good speak"), and the standard patterns above all
# assume native grammar, so these fell through to the LLM, scored english=false,
# and were misrouted to clarify ("say it in English") instead of bridge. Kept
# multi-word so they cannot fire as substrings of a real attempt.
_GIVEUP_BROKEN = (
    "i not know", "me no know", "me not know", "i no know", "me no good",
    "no good speak", "i not understand", "me no understand", "i no understand",
    "me no speak", "i not speak english", "i no speak", "i not good english",
)
# Whole-message one-word give-ups (exact match only, so they don't fire as
# substrings of a real answer).
_GIVEUP_EXACT = {"idk", "dunno", "nothing", "blank", "pass", "huh", "hmm"}
# Short enough that a real answer is not mistaken for a give-up, but long enough
# to catch the canonical stuck phrasing seen live ("hmm i am not sure what to say
# here" — 9 words). The patterns above are specific, so this is the main guard.
_GIVEUP_MAX_WORDS = 12


def is_giveup(text: str) -> bool:
    """True when a short learner message is a stuck/give-up non-answer.

    Deterministic and conservative: only fires on a short message (a long answer
    is a real attempt even if it contains "not sure"). These route to bridge,
    not redirect — a stuck learner needs scaffolding, not a steer-back."""
    t = _norm(text)
    if not t:
        return False
    words = t.split()
    if len(words) > _GIVEUP_MAX_WORDS:
        return False
    if t in _GIVEUP_EXACT:
        return True
    return any(p in t for p in _GIVEUP_PATTERNS) or any(
        p in t for p in _GIVEUP_BROKEN
    )


_ALNUM = re.compile(r"[a-z0-9]", re.I)


def is_blank_nonanswer(text: str) -> bool:
    """True for a non-answer with NO gradable content: empty, whitespace-only,
    or only punctuation / symbols / emoji.

    A deterministic short-circuit (Wave 1.3) so the coach never ships such a turn
    to the eval LLM — which, live, fabricated a fake summary of a prior turn
    ("It's nice to hear about your daily activities" on an empty input) — and
    never counts it as a scored attempt. Conservative on purpose: a single LETTER
    or DIGIT is NOT blank, because "B" is a valid answer on an alphabet node."""
    if not text or not text.strip():
        return True
    return not _ALNUM.search(text)


def stuck_diagnosis() -> DiagnosisEval:
    """Synthesized verdict for a give-up answer: a weak but ON-TASK attempt.

    score 0.0 + on_task=True + english=True routes to bridge (route_node) so the
    learner is scaffolded DOWN, never to redirect (which would push a harder
    task). affect=confused so the coach leads with reassurance."""
    return DiagnosisEval(
        score=0.0,
        understanding="The learner is stuck and unsure how to start.",
        errors=["did not attempt the answer — signalled being stuck"],
        strengths=[],
        next_focus="break the task into a smaller first step",
        on_task=True,
        english=True,
        affect="confused",
    )


# ---------- deterministic bridge answer-key grading ----------

def _selected_option_index(user_input: str, options: list[str]) -> int | None:
    """If the learner picked an option by letter (a/b/c) or number (1/2/3),
    return its 0-based index; else None. Tolerates 'b', 'B)', 'option 2'."""
    t = _norm(user_input)
    if not t:
        return None
    # bare single letter -> a=0, b=1, ...
    if len(t) == 1 and t.isalpha():
        idx = ord(t) - ord("a")
        return idx if 0 <= idx < len(options) else None
    # bare number -> 1-based selection
    if t.isdigit():
        idx = int(t) - 1
        return idx if 0 <= idx < len(options) else None
    # "option b" / "option 2"
    m = re.fullmatch(r"option\s+([a-z0-9])", t)
    if m:
        tok = m.group(1)
        idx = (ord(tok) - ord("a")) if tok.isalpha() else (int(tok) - 1)
        return idx if 0 <= idx < len(options) else None
    return None


# Sentinel answer_key for an OPEN numeric blank ("by ___%"): there is no single
# right figure — the sentence is a template for the learner's own metric — so any
# number they supply is correct (H4).
NUMERIC_KEY = "<number>"


def _matches_one(typ: str, key: str, options: list, user_input: str) -> bool:
    """True if user_input satisfies a SINGLE acceptable key (exact / single-token
    word-boundary / substring, or an option-index pick for multiple_choice)."""
    nkey = _norm(key)
    nui = _norm(user_input)
    if not nui or not nkey:
        return False
    if typ == "multiple_choice" and options:
        # Resolve option indices by EXACT option text FIRST. _norm strips terminal
        # punctuation, so two options differing only by '?' vs '.' (e.g.
        # "Where is the lion?" vs "Where is the lion.") collapse to the same
        # normalized string — which made norm_opts.index() return the WRONG
        # option's index and graded a distractor AS the key (even on a click). The
        # FE sends the chosen option's exact text on a click, so match raw text
        # first; fall back to normalized only when the key isn't stored verbatim.
        raw_opts = [o.strip() for o in options]
        raw_key = (key or "").strip()
        raw_ui = (user_input or "").strip()
        if raw_key in raw_opts:
            key_idx = raw_opts.index(raw_key)
        else:
            norm_opts = [_norm(o) for o in options]
            key_idx = norm_opts.index(nkey) if nkey in norm_opts else -1
        if raw_ui in raw_opts:
            chosen = raw_opts.index(raw_ui)
        else:
            chosen = _selected_option_index(user_input, options)
        if chosen is not None and key_idx != -1:
            return chosen == key_idx
        # Typed-text fallback for a closed-option MCQ: require an EXACT match to
        # the correct option. A substring test (`nkey in nui`) would grade a WRONG
        # distractor whose text merely CONTAINS the key (key "go", distractor
        # "i will go") as correct, and grade it inconsistently vs the same option
        # picked by letter. Substring matching is safe only for fill_blank below.
        return nui == nkey
    # fill_blank / spoken-as-key: exact, single-token, or substring match
    if nui == nkey:
        return True
    key_words = nkey.split()
    if len(key_words) == 1:
        return key_words[0] in nui.split()   # word-boundary, not raw substring
    return nkey in nui


def _is_correct(pending: dict, user_input: str) -> bool:
    typ = pending.get("type")
    key = (pending.get("answer_key") or "").strip()
    options = pending.get("options") or []
    accept = pending.get("accept") or []

    # H4: an open-numeric blank accepts any number (with or without a trailing %).
    if key == NUMERIC_KEY:
        candidate = re.sub(r"[%\s]", "", user_input or "")
        return bool(re.fullmatch(r"-?\d+(\.\d+)?", candidate))

    # M3: a blank with interchangeable correct forms carries an `accept` list of
    # equally-valid alternatives; the item is correct if the answer matches the
    # keyed form OR any accepted synonym, so equally-correct English never fails.
    return any(
        _matches_one(typ, k, options, user_input) for k in (key, *accept)
    )


def grade_pending_answer(pending: dict, user_input: str) -> DiagnosisEval:
    """Grade a served fill_blank / MCQ deterministically against its answer key.

    Returns an ON-TASK English diagnosis (so it never trips the redirect/clarify
    paths): a correct fill is a clean-pass-level score, a wrong one stays in the
    bridge band. The general LLM evaluator never sees the key, so this is the only
    place a one-correct-answer item is graded correctly."""
    correct = _is_correct(pending, user_input)
    if correct:
        return DiagnosisEval(
            score=BRIDGE_CORRECT_SCORE,
            understanding="Got the scaffolded step right.",
            errors=[],
            strengths=["produced the target form correctly"],
            next_focus="build back up to the full skill",
            on_task=True,
            english=True,
            affect="confident",
        )
    return DiagnosisEval(
        score=BRIDGE_WRONG_SCORE,
        understanding="The scaffolded step is still shaky.",
        errors=["the answer did not match the target form"],
        strengths=[],
        next_focus="re-model the smaller step, then retry",
        on_task=True,
        english=True,
        affect="confused",
    )
