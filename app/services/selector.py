"""Spec B two-stage hybrid content selector.

This is the advancement primitive. It answers ONE question at the advance
boundary: given the learner's state, which content node do they move to next?

Two stages:
  Stage 1 — deterministic rules (`compute_valid_candidates`): the only place
            that knows the content graph. In the linear MVP module there is
            exactly ONE valid candidate (the linear next node), so the caller's
            fast path reproduces today's `next_node` advance verbatim.
  Stage 2 — a single LLM call (only when >1 candidate; lives in
            `app.ai.calls.select_next_content`). This module never calls the
            model; it only builds the snapshot the call consumes and validates /
            backstops the decision the call returns.

Pure module: no DB, no network, no disk I/O. In-memory registry reads only.
"""
from app.ai.schemas import SelectionDecision
from app.content.registry import next_node

# Actions that move the learner forward (consume a candidate's next_ref).
_FORWARD_ACTIONS = ("ADVANCE", "SKIP", "REMEDIATE")


def compute_valid_candidates(state: dict) -> list[dict]:
    """Stage 1: deterministic valid next-content candidates for `state`.

    MVP linear module: zero or one candidate.
      - terminal node (no linear next) -> [] (caller marks the module done).
      - otherwise -> exactly one ADVANCE candidate, the linear next node.

    The multi-candidate path (len > 1) is a real code path in the caller and is
    exercised in tests by monkeypatching this function; the linear content graph
    just never produces it today.
    """
    node_id = state["competency_node"]
    try:
        nxt = next_node(node_id)
    except (KeyError, ValueError):
        # Unknown node_id (not in the registry): treat like a terminal node so
        # the caller marks the module done rather than crashing. Degrades the
        # same way a real terminal node does -> no valid forward candidate.
        return []
    if nxt is None:
        return []
    return [{"action": "ADVANCE", "next_ref": nxt, "band": "standard"}]


def build_selection_snapshot(state: dict) -> dict:
    """Compact learner snapshot for the selector prompt (Stage 2 input).

    Small on purpose: only what the model needs to pick a band / candidate, not
    the whole session state. Recent weaknesses come from `weakness_context`.
    """
    return {
        "current_node": state.get("competency_node"),
        "mastery": state.get("current_mastery", 0.0),
        "clean_streak": state.get("clean_streak", 0),
        "attempts": state.get("attempts", 0),
        "weaknesses": state.get("weakness_context", []),
    }


def fallback_decision(state: dict, candidates: list[dict]) -> SelectionDecision:
    """Deterministic decision when the LLM call is unavailable or errors.

    Prefer the first forward candidate (advance to its next_ref); if none is
    forward, repeat the current node. Never raises, never invents a ref.
    """
    for cand in candidates:
        if cand.get("action") in _FORWARD_ACTIONS:
            return SelectionDecision(
                action="ADVANCE",
                next_ref=cand["next_ref"],
                band="standard",
                rationale="fallback: advance to first forward candidate",
            )
    return SelectionDecision(
        action="REPEAT",
        next_ref=state["competency_node"],
        band="standard",
        rationale="fallback: no forward candidate, repeat current node",
    )


def validate_decision(
    decision: SelectionDecision, candidates: list[dict], state: dict
) -> SelectionDecision:
    """Clamp an LLM decision back onto the valid candidate set.

    Guarantees the returned decision is safe to act on:
      - REPEAT keeps its action but its next_ref is pinned to the current node.
      - any other action must name a next_ref from the candidate list and an
        action from the candidate list; out-of-set values snap to candidates[0].
      - a missing/blank band defaults to "standard".
    """
    if decision.action == "REPEAT":
        return SelectionDecision(
            action="REPEAT",
            next_ref=state["competency_node"],
            band=decision.band or "standard",
            rationale=decision.rationale,
        )

    # No candidate to snap a forward action onto: degrade to REPEAT on the
    # current node rather than IndexError on candidates[0] below. Mirrors
    # fallback_decision's "no forward candidate -> repeat current node".
    if not candidates:
        return SelectionDecision(
            action="REPEAT",
            next_ref=state["competency_node"],
            band=decision.band or "standard",
            rationale="no valid candidates; repeat current node",
        )

    valid_refs = {c["next_ref"] for c in candidates}
    valid_actions = {c["action"] for c in candidates}

    next_ref = decision.next_ref
    action = decision.action
    if next_ref not in valid_refs:
        next_ref = candidates[0]["next_ref"]
    if action not in valid_actions:
        action = candidates[0]["action"]

    return SelectionDecision(
        action=action,
        next_ref=next_ref,
        band=decision.band or "standard",
        rationale=decision.rationale,
    )
