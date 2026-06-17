"""Routing + mastery update. Pure functions — no I/O, fully unit-testable.

Council fix (ITEM: infinite bridge loop): route_node now respects
bridge_attempts. After 3 failed bridges, escalate to teach instead of
looping on bridge forever.
"""

from app.content.task_types import TaskType

# TEST-mode task types: scored as a whole simulation, not coached per skill, so
# their level_kind is always "test" regardless of any per-node flags.
_TEST_TASK_TYPES = frozenset(
    {TaskType.INTERVIEW_TEST.value, TaskType.GD_TEST.value}
)

BRIDGE_ATTEMPT_CAP = 3
STRENGTHEN_ATTEMPT_CAP = 2  # consecutive strengthens before escaping the 0.4-0.6 plateau
GIVE_UP_FAILS = 5  # consecutive hard fails before easing off instead of drilling
CEILING_SCORE = 0.85  # a first answer this strong skips re-teach -> challenge
MASTERY_ALPHA = 0.3  # EMA smoothing — one good answer can't spike mastery
MASTERY_RAISE_FLOOR = 0.6  # below this, an answer never raises EMA mastery


def route_node(state: dict) -> str:
    score = state["last_eval_score"]
    mastery = state["current_mastery"]
    diag = state.get("last_diagnosis", {})
    on_task = diag.get("on_task", True)
    english = diag.get("english", True)

    # Non-English / gibberish / empty (B11/B12, Test-fix-01): english False means
    # the learner did NOT produce competent English at all — bridge would scaffold
    # a competency SKILL they never attempted in English (category error). Send a
    # warm "say that in English" nudge (clarify) before any skill routing.
    if not english:
        return "clarify"

    # Fluent-but-off-task (council fix #1/#6): competent English aimed at the
    # wrong question scores 0.0, but the learner is capable — point them back at
    # the task (redirect), don't scaffold them down.
    if english and not on_task:
        return "redirect"

    if score < 0.4:
        # Very weak answer: scaffold down via bridge until the cap, then
        # re-anchor on a full teach (NOT strengthen — strengthen assumes the
        # skill is present-but-shaky, which a sub-0.4 answer contradicts).
        if state.get("bridge_attempts", 0) < BRIDGE_ATTEMPT_CAP:
            return "bridge"
        # Bridge exhausted AND still hard-failing for a long run: stop drilling
        # and offer a graceful off-ramp instead of teaching forever (fix #3).
        if state.get("level_fails", 0) >= GIVE_UP_FAILS:
            return "ease"
        return "teach"
    if score < 0.6:
        # Skill shaky-but-present: reinforce. But a learner can stall here
        # forever (0.4-0.6 every turn), so cap consecutive strengthens — after
        # the cap, scaffold DOWN to bridge (or re-anchor on teach if bridge is
        # also exhausted) instead of looping strengthen indefinitely.
        if state.get("strengthen_attempts", 0) >= STRENGTHEN_ATTEMPT_CAP:
            if state.get("bridge_attempts", 0) < BRIDGE_ATTEMPT_CAP:
                return "bridge"
            return "teach"
        return "strengthen"
    if mastery > 0.8:
        return "challenge"
    # Ceiling escape (fix #2): a near-perfect FIRST answer needs no re-teach —
    # stretch immediately instead of EMA-gating them behind a slow mastery climb.
    if score >= CEILING_SCORE and state.get("attempts", 0) <= 1:
        return "challenge"
    return "teach"


def level_kind(state: dict) -> str:
    """Name the finer-grained section the learner is currently in (Phase 5).

    Precedence: test > bridge > review > tester > prep. A TEST session is one
    graded simulation, so it always reads "test". Otherwise a module that fell
    below the clean-rate floor is in a "bridge" (remediation) section; a passed
    module surfaces a "review"; a fast clean advance flags a "tester" stretch;
    everything else is ordinary "prep" coaching.
    """
    if state.get("task_type", "") in _TEST_TASK_TYPES:
        return "test"
    if state.get("remediation"):
        return "bridge"
    if state.get("review_level"):
        return "review"
    if state.get("tester_level"):
        return "tester"
    return "prep"


def session_phase(state: dict) -> str:
    """Macro lifecycle of the session, orthogonal to level_kind.

    intro before the first turn, complete once the module is done, active in
    between.
    """
    if state.get("module_done"):
        return "complete"
    if state.get("turn_count", 0) == 0:
        return "intro"
    return "active"


_SCORE_SWING_GATE = 0.4   # single-turn swing larger than this is dampened


def update_mastery(old: float, score: float) -> float:
    """EMA toward the score, but only when the answer is good enough to count.

    Sub-floor answers (score < MASTERY_RAISE_FLOOR) leave mastery flat: a run of
    mediocre 0.5s must not inch the EMA upward and fake progress. At/above the
    floor, standard EMA (new = old + alpha * (score - old)).

    Swing gate: if the raw score jumps >0.4 in one turn (qwen calibration spike),
    dampen to the midpoint before applying EMA. Prevents a lucky 0.9 from vaulting
    mastery past all guard rails in a single turn."""
    if old > 0 and abs(score - old) > _SCORE_SWING_GATE:
        score = (score + old) / 2
    if score < MASTERY_RAISE_FLOOR:
        return old
    return old + (score - old) * MASTERY_ALPHA
