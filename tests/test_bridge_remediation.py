"""P0-3 — bridge / remediation actually works now.

Three compounding faults this pins:
  (a) a short "idk"/"not sure" is a STUCK learner -> bridge (scaffold down), not
      redirect (which pushed a harder task);
  (b) a served fill_blank / MCQ is graded DETERMINISTICALLY against its answer
      key, not by the key-blind LLM rubric;
  (c) the served exercise is chosen by SEVERITY (band steps down on repeats) and
      never repeats an already-served id.
"""
import os

import pytest

os.environ.setdefault("GROQ_API_KEY", "test")
os.environ.setdefault("GEMINI_API_KEY", "test")
os.environ.setdefault(
    "SUPABASE_POOLER_URL",
    "postgresql://postgres.ref:pwd@host.pooler.supabase.com:6543/postgres",
)

from app.content.schema import BridgeExercise  # noqa: E402
from app.graph.answer_check import (  # noqa: E402
    BRIDGE_CORRECT_SCORE,
    BRIDGE_WRONG_SCORE,
    grade_pending_answer,
    is_blank_nonanswer,
    is_giveup,
)
from app.graph.nodes.bridge import select_bridge_exercise  # noqa: E402


# ---------- (a) give-up detection ----------

@pytest.mark.parametrize("text", [
    "idk", "IDK", "i don't know", "I dont know", "not sure",
    "hmm i am not sure what to say here", "dunno", "no idea", "I give up",
    # broken-English / ESL stuck signals (Wave 1.2) — these are give-ups too.
    "is bad i not know", "me no good speak", "i not understand",
    "me no know", "i no understand the question",
])
def test_giveup_detected(text):
    assert is_giveup(text) is True


@pytest.mark.parametrize("text", [
    "I am a backend engineer who builds payment systems for millions of users",
    "My name is Abhinav and I work on reliability.",
    "The capital of France is Paris.",
    "",
    # broken English but a genuine ATTEMPT — must NOT be flagged a give-up.
    "i go office daily by bus and i like my work",
    "my name rahul i am from delhi city",
])
def test_giveup_not_falsely_triggered(text):
    assert is_giveup(text) is False


# ---------- (a2) blank non-answer detection (Wave 1.3) ----------

@pytest.mark.parametrize("text", ["", "   ", "\t\n", "...", "!!!", "??", "🙂", "—"])
def test_blank_nonanswer_detected(text):
    assert is_blank_nonanswer(text) is True


@pytest.mark.parametrize("text", [
    "B",            # a single LETTER is a valid alphabet-node answer, not blank
    "7",            # a single digit likewise
    "ball",
    "Hello, I am Abhinav.",
    "a.",           # punctuation plus a letter still has gradable content
])
def test_blank_nonanswer_not_falsely_triggered(text):
    assert is_blank_nonanswer(text) is False


# ---------- (b) deterministic answer-key grading ----------

def _fill(key):
    return {"type": "fill_blank", "answer_key": key, "options": None}


def test_fill_blank_exact_correct():
    d = grade_pending_answer(_fill("is"), "is")
    assert d.score == BRIDGE_CORRECT_SCORE
    assert d.on_task is True and d.english is True


def test_fill_blank_word_in_sentence_correct():
    # learner writes the whole sentence; the key word is present as a token
    d = grade_pending_answer(_fill("is"), "My name is Ravi")
    assert d.score == BRIDGE_CORRECT_SCORE


def test_fill_blank_substring_does_not_false_match():
    # "is" must NOT match inside "this" — token boundary, not raw substring
    d = grade_pending_answer(_fill("is"), "this car")
    assert d.score == BRIDGE_WRONG_SCORE


def test_fill_blank_wrong():
    d = grade_pending_answer(_fill("drinks"), "drink")
    assert d.score == BRIDGE_WRONG_SCORE


_MCQ = {
    "type": "multiple_choice",
    "answer_key": "Last week we visited my grandparents and stayed two nights.",
    "options": [
        "Last week we visited my grandparents and stayed two nights.",
        "Last week we visit my grandparents and stay two nights.",
        "Last week we will visit my grandparents and stay two nights.",
    ],
}


def test_mcq_correct_by_full_text():
    d = grade_pending_answer(_MCQ, "Last week we visited my grandparents and stayed two nights.")
    assert d.score == BRIDGE_CORRECT_SCORE


def test_mcq_correct_by_letter():
    d = grade_pending_answer(_MCQ, "a")          # option a == index 0 == the key
    assert d.score == BRIDGE_CORRECT_SCORE


def test_mcq_correct_by_number():
    d = grade_pending_answer(_MCQ, "1")          # 1-based -> index 0
    assert d.score == BRIDGE_CORRECT_SCORE


def test_mcq_wrong_by_letter():
    d = grade_pending_answer(_MCQ, "b")          # option b == index 1 (wrong)
    assert d.score == BRIDGE_WRONG_SCORE


# Regression: a WRONG MCQ distractor whose text CONTAINS the answer key as a
# substring must NOT grade correct when typed, and must grade the same as picking
# it by letter. The old `nkey in nui` text-fallback graded "i will go" / "going"
# as correct for key "go" (input-form-dependent inconsistency).
_MCQ_SUBSTRING = {
    "type": "multiple_choice",
    "answer_key": "go",
    "options": ["go", "i will go", "going"],
}


def test_mcq_correct_option_text_still_passes():
    assert grade_pending_answer(_MCQ_SUBSTRING, "go").score == BRIDGE_CORRECT_SCORE


def test_mcq_wrong_distractor_containing_key_is_not_correct():
    # typing the full text of a wrong option that contains the key
    assert grade_pending_answer(_MCQ_SUBSTRING, "i will go").score == BRIDGE_WRONG_SCORE
    assert grade_pending_answer(_MCQ_SUBSTRING, "going").score == BRIDGE_WRONG_SCORE


def test_mcq_text_and_letter_grade_consistently():
    # picking the same wrong options by letter agrees with typing their text
    assert grade_pending_answer(_MCQ_SUBSTRING, "b").score == BRIDGE_WRONG_SCORE  # "i will go"
    assert grade_pending_answer(_MCQ_SUBSTRING, "c").score == BRIDGE_WRONG_SCORE  # "going"
    assert grade_pending_answer(_MCQ_SUBSTRING, "a").score == BRIDGE_CORRECT_SCORE  # "go"


# ---------- (c) severity-aware, de-duplicated selection ----------

def _ex(eid, band, typ="fill_blank"):
    return BridgeExercise(
        id=eid, type=typ, sentence="fill the ___ gap", hint="h", context="c",
        answer_key="k", band=band,
    )


_EXS = [_ex("f", "foundational"), _ex("s", "standard"), _ex("t", "stretch")]


def test_first_bridge_serves_standard():
    chosen = select_bridge_exercise(_EXS, bridge_attempts=0, served_ids=[], score=0.35)
    assert chosen.id == "s"


def test_repeat_bridge_steps_down_to_foundational():
    chosen = select_bridge_exercise(_EXS, bridge_attempts=1, served_ids=["s"], score=0.35)
    assert chosen.id == "f"


def test_very_weak_answer_starts_foundational():
    chosen = select_bridge_exercise(_EXS, bridge_attempts=0, served_ids=[], score=0.1)
    assert chosen.id == "f"


def test_never_repeats_served_id():
    chosen = select_bridge_exercise(_EXS, bridge_attempts=0, served_ids=["s", "f"], score=0.35)
    assert chosen.id == "t"   # only unserved one left


def test_all_served_allows_repeat():
    chosen = select_bridge_exercise(_EXS, bridge_attempts=0, served_ids=["f", "s", "t"], score=0.35)
    assert chosen.id in {"f", "s", "t"}   # falls back to a repeat, never crashes


# ---------- end-to-end: stuck -> bridge served -> fill graded ----------

from app.ai.schemas import DiagnosisEval  # noqa: E402
from app.services import session_service as svc  # noqa: E402

pytestmark_e2e = pytest.mark.asyncio


class _CountingEval:
    """Records how often the LLM evaluator is hit — the deterministic branches
    must NOT call it."""

    def __init__(self):
        self.calls = 0

    async def __call__(self, node, messages, user_input, behavior=None):
        self.calls += 1
        return DiagnosisEval(
            score=0.5, understanding="x", errors=[], strengths=[],
            next_focus="n", on_task=True, english=True,
        )


async def _fake_stream(spec):
    for tok in ("ok", " ", "done"):
        yield tok


@pytest.fixture
def _patched(monkeypatch):
    ce = _CountingEval()
    monkeypatch.setattr("app.graph.nodes.evaluate.evaluate_answer", ce)
    monkeypatch.setattr("app.services.session_service.stream_generation", _fake_stream)

    async def _fake_summary(node, messages):
        return "summary"

    monkeypatch.setattr("app.services.session_service.summarize_session", _fake_summary)
    yield ce
    svc.SessionStore.clear()


async def _collect(agen):
    return [t async for t in agen]


@pytest.mark.asyncio
async def test_idk_routes_to_bridge_and_serves_exercise(_patched):
    sid, state = await svc.start_session("br1", "comm_01_self_intro")
    state["turn_count"] = 1

    frames = await _collect(svc.run_turn(sid, "idk"))

    assert state["last_route"] == "bridge"
    assert state["bridge_attempts"] == 1
    # a pre-authored exercise was served as a game prompt, with its key stashed
    assert any(isinstance(f, svc.GamePrompt) for f in frames)
    assert state["pending_answer_key"] is not None
    assert state["served_bridge_ids"]            # an id was recorded
    # the LLM evaluator was NOT consulted for the give-up turn
    assert _patched.calls == 0


@pytest.mark.asyncio
async def test_bridge_fill_graded_deterministically(_patched):
    sid, state = await svc.start_session("br2", "comm_01_self_intro")
    state["turn_count"] = 1

    # turn 1: give up -> bridge serves comm_01's foundational fill_blank ("is")
    await _collect(svc.run_turn(sid, "idk"))
    key = state["pending_answer_key"]["answer_key"]

    # turn 2: answer the fill correctly -> deterministic pass, key cleared
    await _collect(svc.run_turn(sid, key))

    assert state["last_eval_score"] == BRIDGE_CORRECT_SCORE
    assert state["pending_answer_key"] is None
    assert _patched.calls == 0   # both turns were deterministic, no LLM eval


# ---------- M2: give-up DURING a pending bridge fill ----------

@pytest.mark.asyncio
async def test_giveup_during_pending_bridge_is_stuck_not_wrong_fill():
    # M2: an "idk" while a bridge fill is pending is a NON-ATTEMPT, not a wrong
    # fill. evaluate_node must score it stuck (0.0), clear the served key so the
    # learner is re-scaffolded, and NOT grade it BRIDGE_WRONG_SCORE (0.3). Checked
    # at the node level because the full turn re-serves a fresh bridge item, which
    # would mask the clear.
    from app.graph.nodes.evaluate import evaluate_node

    state = {
        "competency_node": "comm_01_self_intro",
        "user_input": "idk",
        "pending_answer_key": {"type": "fill_blank", "answer_key": "is", "options": None},
        "current_mastery": 0.3,
        "attempts": 1,
        "session_attempts": 1,
    }
    out = await evaluate_node(state)

    assert out["last_eval_score"] == 0.0                  # stuck ...
    assert out["last_eval_score"] != BRIDGE_WRONG_SCORE   # ... NOT a wrong fill
    assert out["last_diagnosis"]["on_task"] is True       # routes stuck->bridge
    assert out["last_diagnosis"]["english"] is True
    assert out["pending_answer_key"] is None              # cleared -> re-scaffold


@pytest.mark.asyncio
async def test_real_attempt_on_pending_bridge_still_graded():
    # Regression: the M2 reorder must not swallow genuine (non-giveup) attempts —
    # a real fill is still graded against the key, right or wrong.
    from app.graph.nodes.evaluate import evaluate_node

    base = {
        "competency_node": "comm_01_self_intro",
        "pending_answer_key": {"type": "fill_blank", "answer_key": "is", "options": None},
        "current_mastery": 0.3, "attempts": 1, "session_attempts": 1,
    }
    correct = await evaluate_node({**base, "user_input": "is"})
    assert correct["last_eval_score"] == BRIDGE_CORRECT_SCORE
    assert correct["pending_answer_key"] is None

    wrong = await evaluate_node({**base, "user_input": "xqz"})
    assert wrong["last_eval_score"] == BRIDGE_WRONG_SCORE


# ---------- H1: a correct bridge fill must NOT advance the node ----------

@pytest.mark.asyncio
async def test_correct_bridge_fill_does_not_accrue_clean_streak(_patched):
    # H1: a correct scaffolded bridge fill breaks the fail streak and refunds the
    # bridge cap, but must NOT count toward the advance streak — a scaffolded-down
    # sub-step is not a clean pass at this node.
    sid, state = await svc.start_session("brh1", "comm_01_self_intro")
    state["turn_count"] = 1

    await _collect(svc.run_turn(sid, "idk"))     # bridge serves a fill
    assert state["last_route"] == "bridge"
    assert state["bridge_attempts"] == 1
    key = state["pending_answer_key"]["answer_key"]

    await _collect(svc.run_turn(sid, key))       # correct fill -> 0.7
    assert state["last_eval_score"] == BRIDGE_CORRECT_SCORE
    assert state["last_graded_bridge"] is True
    # the scaffolded fill did NOT accrue toward advancement ...
    assert state["clean_streak"] == 0
    # ... but DID refund the bridge cap (genuine progress, not force-escalation)
    assert state["bridge_attempts"] == 0
    # and the node did NOT advance off comm_01
    assert state["competency_node"] == "comm_01_self_intro"


def test_update_progress_bridge_pass_does_not_accrue_but_real_pass_does():
    # H1 (focused): the advance-streak gate. A PASS-scoring turn refunds the
    # bridge cap and breaks the fail streak either way; only a NON-bridge pass
    # increments the clean streak.
    from app.services.session_service import _update_progress

    base = {
        "last_diagnosis": {"english": True, "on_task": True},
        "last_eval_score": BRIDGE_CORRECT_SCORE,  # == PASS_SCORE
        "clean_streak": 0, "bridge_attempts": 3, "level_fails": 2,
    }
    bridge = {**base, "last_graded_bridge": True}
    _update_progress(bridge)
    assert bridge["clean_streak"] == 0       # bridge fill: no streak accrual
    assert bridge["bridge_attempts"] == 0    # cap still refunded
    assert bridge["level_fails"] == 0        # fail streak still broken

    real = {**base, "last_graded_bridge": False}
    _update_progress(real)
    assert real["clean_streak"] == 1         # a genuine pass DOES accrue


# ---------- M3: synonym accept-list ----------

def test_accept_list_admits_equally_correct_synonyms():
    # M3: an `accept` list of interchangeable forms grades any valid form correct,
    # without marking equally-correct English wrong.
    comm06 = {"type": "fill_blank", "answer_key": "For example",
              "accept": ["For instance"], "options": None}
    assert grade_pending_answer(comm06, "For instance").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(comm06, "For example").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(comm06, "banana").score == BRIDGE_WRONG_SCORE

    comm07 = {"type": "fill_blank", "answer_key": "but",
              "accept": ["however", "yet", "though"], "options": None}
    assert grade_pending_answer(comm07, "however").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(comm07, "but").score == BRIDGE_CORRECT_SCORE

    comm02 = {"type": "fill_blank", "answer_key": "First",
              "accept": ["Firstly"], "options": None}
    assert grade_pending_answer(comm02, "Firstly").score == BRIDGE_CORRECT_SCORE


def test_no_accept_list_is_unchanged():
    # Regression: a blank with no `accept` grades exactly as before.
    ex = {"type": "fill_blank", "answer_key": "drinks", "accept": None, "options": None}
    assert grade_pending_answer(ex, "drinks").score == BRIDGE_CORRECT_SCORE
    assert grade_pending_answer(ex, "drink").score == BRIDGE_WRONG_SCORE


# ---------- H4: open-numeric blank ----------

def test_numeric_blank_accepts_any_number():
    # H4: the "<number>" sentinel accepts any number the learner supplies, not
    # just the authored "40" — there is no single right figure for the blank.
    pending = {"type": "fill_blank", "answer_key": "<number>",
               "accept": None, "options": None}
    for ans in ("40", "30", "55", "40%", "12", "100"):
        assert grade_pending_answer(pending, ans).score == BRIDGE_CORRECT_SCORE, ans
    for ans in ("a lot", "lots", "forty per cent", ""):
        assert grade_pending_answer(pending, ans).score == BRIDGE_WRONG_SCORE, ans


def test_content_synonym_and_numeric_blanks_configured():
    # Guards the curriculum edits: the live JSON items carry the accept lists /
    # numeric sentinel, so the grader actually receives them through bridge_node.
    from app.content.registry import get_node

    def _ex(node_id):
        return {e.id: e for e in get_node(node_id).bridge_exercises}

    intv = _ex("int_08_quantify_impact")
    assert intv["int_08_quantify_impact_bx1"].answer_key == "<number>"

    comm = {**_ex("comm_06_persuade"), **_ex("comm_07_handle_question"),
            **_ex("comm_02_describe_routine")}
    assert "For instance" in (comm["comm_06_persuade_bx1"].accept or [])
    assert "however" in (comm["comm_07_handle_question_bx2"].accept or [])
    assert "Firstly" in (comm["comm_02_describe_routine_bx2"].accept or [])

    gd = _ex("gd_02_support_with_evidence")
    assert "For example" in (gd["gd_02_support_with_evidence_bx1"].accept or [])


# ---------- Wave 1.3: blank non-answer short-circuits the turn ----------

@pytest.mark.asyncio
async def test_blank_input_reprompts_without_eval_or_attempt(_patched):
    # A whitespace-only turn must NOT reach the eval LLM (which fabricated content
    # live) and must NOT count as a scored attempt. It yields a fixed re-prompt.
    sid, state = await svc.start_session("blank1", "comm_01_self_intro")
    state["turn_count"] = 1

    frames = await _collect(svc.run_turn(sid, "   "))

    assert any("didn't catch that" in f for f in frames if isinstance(f, str))
    assert _patched.calls == 0          # eval LLM never consulted
    assert state.get("attempts", 0) == 0  # not scored as an attempt
    assert state.get("last_route") is None  # the graph never ran


@pytest.mark.asyncio
async def test_real_answer_after_blank_is_still_evaluated(_patched):
    # The short-circuit must not poison the session: a real answer next turn is
    # evaluated normally (the LLM IS consulted).
    sid, state = await svc.start_session("blank2", "comm_01_self_intro")
    state["turn_count"] = 1

    await _collect(svc.run_turn(sid, ""))            # blank -> short-circuit
    assert _patched.calls == 0
    await _collect(svc.run_turn(sid, "My name is Abhinav and I am from Jaipur."))
    assert _patched.calls == 1                       # real answer was evaluated
