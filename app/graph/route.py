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
CLARIFY_ATTEMPT_CAP = 3  # consecutive "say it in English" nudges before escaping to teach
REDIRECT_ATTEMPT_CAP = 3  # consecutive fluent-off-task steer-backs before delivering content
STRENGTHEN_ATTEMPT_CAP = 2  # consecutive strengthens before escaping the 0.4-0.6 plateau
GIVE_UP_FAILS = 5  # consecutive hard fails before easing off instead of drilling
CEILING_SCORE = 0.85  # a first answer this strong skips re-teach -> challenge
CHALLENGE_PASS_SCORE = 0.7  # a clean-streak answer at/above this stretches instead of re-teaching
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
    # warm "say that in English" nudge (clarify) before any skill routing. But a
    # learner who keeps answering non-English would loop clarify forever, so after
    # CLARIFY_ATTEMPT_CAP nudges escape to teach — deliver content directly rather
    # than softlock (mirrors _neutral_diagnosis's keep-alive teach fallback; the
    # cap is non-penalizing, like clarify itself).
    if not english:
        if state.get("clarify_attempts", 0) < CLARIFY_ATTEMPT_CAP:
            return "clarify"
        return "teach"

    # Fluent-but-off-task (council fix #1/#6): competent English aimed at the
    # wrong question scores 0.0, but the learner is capable — point them back at
    # the task (redirect), don't scaffold them down. A learner who keeps answering
    # off-task would loop redirect forever (redirect_node touches no progression
    # counters and _update_progress early-returns on on_task=False), so after
    # REDIRECT_ATTEMPT_CAP steer-backs, stop steering and just DELIVER the content
    # (teach) — the same non-penalizing escape the clarify cap uses.
    if english and not on_task:
        if state.get("redirect_attempts", 0) < REDIRECT_ATTEMPT_CAP:
            return "redirect"
        return "teach"

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
    # Strong answer on an established clean streak: stop re-teaching, stretch them.
    # The old `mastery > 0.8` gate was mathematically UNREACHABLE — the EMA
    # (update_mastery, alpha 0.3) asymptotes TO the score, so a learner answering a
    # steady 0.8 converges to ~0.79 and never crosses a strict >0.8 gate, and
    # challenge fired once on turn 1 then never again. Gate on the clean-pass streak
    # instead: a consistently-strong learner actually reaches it (and earns one
    # stretch turn right before advancing).
    if score >= CHALLENGE_PASS_SCORE and state.get("clean_streak", 0) >= 1:
        return "challenge"
    # Ceiling escape (fix #2): a near-perfect answer EARLY in this session's work on
    # the node needs no re-teach — stretch immediately. Use session_attempts (reset
    # per node, never loaded from storage) not lifetime `attempts`, so it fires for
    # a RETURNING learner too instead of being dead the moment attempts>1 on disk.
    if score >= CEILING_SCORE and state.get(
        "session_attempts", state.get("attempts", 0)
    ) <= 1:
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


def update_mastery(old: float, score: float) -> float:
    """EMA toward the score, but only when the answer is good enough to count.

    Sub-floor answers (score < MASTERY_RAISE_FLOOR) leave mastery flat: a run of
    mediocre 0.5s must not inch the EMA upward and fake progress. At/above the
    floor, standard EMA (new = old + alpha * (score - old)).

    The upstream swing damper in evaluate_node smooths only DOWNWARD score swings
    (noise that would wrongly crash a learner); an upward 0.9 reaches this function
    at face value. What stops that single 0.9 from masquerading as sustained mastery
    is THIS EMA: alpha 0.3 moves mastery only 30% of the gap per turn, so one high
    score nudges but never spikes mastery — sustained highs are required to climb.
    Doing a SECOND swing gate here — blending the score against the slow-moving
    MASTERY itself — froze a recovering learner forever (mastery 0.27, genuine 0.9s
    → (0.9+0.27)/2=0.585 < 0.6 floor → stuck at 0.27 every turn). The raise-floor
    and the EMA alpha are therefore the ONLY guards at this layer."""
    if score < MASTERY_RAISE_FLOOR:
        return old
    return old + (score - old) * MASTERY_ALPHA
