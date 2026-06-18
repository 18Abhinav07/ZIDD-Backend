"""bridge node — learner struggling: scaffold DOWN to a smaller sub-step.

Increments bridge_attempts. route_node enforces the 3-attempt cap (council fix
for the infinite-bridge loop): after BRIDGE_ATTEMPT_CAP failed bridges it routes
to teach instead, so this node never runs a 4th consecutive time.

Pre-authored exercises are selected by SEVERITY, not at random (P0-3c): the first
bridge serves a `standard` step, each repeat steps DOWN toward `foundational`, a
very weak answer starts at foundational immediately, and already-served ids are
skipped so the learner never gets the same exercise twice. For closed items
(fill_blank / MCQ) the answer key is stashed so the next turn grades the fill
deterministically (P0-3b) instead of through the key-blind LLM rubric.
"""
from app.ai.calls import GEMINI_FLASH, GenSpec
from app.ai.behaviors import behavior_for_value
from app.ai.prompts import build_bridge_prompt, coach_view
from app.content.registry import get_node
from app.content.schema import BridgeExercise

_BAND_ORDER = ["foundational", "standard", "stretch"]  # easiest -> hardest


def _band_index(band: str | None) -> int:
    """Map a band label to its difficulty rank; None/unknown reads as standard."""
    try:
        return _BAND_ORDER.index(band)
    except (ValueError, TypeError):
        return 1


def select_bridge_exercise(
    exercises: list[BridgeExercise],
    bridge_attempts: int,
    served_ids: list[str],
    score: float,
) -> BridgeExercise:
    """Pick the next bridge exercise by severity (pure, testable).

    Targets a difficulty band that starts at `standard` and steps DOWN one band
    per prior bridge attempt (so a repeatedly-stuck learner is scaffolded harder),
    and clamps to `foundational` immediately for a very weak (<0.2) answer.
    Already-served ids are skipped; once every exercise has been served, repeats
    are allowed (still preferring the target band)."""
    served = set(served_ids or [])
    target = 1 - bridge_attempts          # 0 attempts -> standard, then step down
    if score < 0.2:
        target = min(target, 0)           # very weak -> foundational now
    target = max(0, min(len(_BAND_ORDER) - 1, target))

    unserved = [e for e in exercises if e.id not in served]
    pool = unserved or list(exercises)    # all served -> allow repeats

    def sort_key(e: BridgeExercise):
        bi = _band_index(e.band)
        # exact target band first, then bands at/under target (easier), then by
        # absolute distance — never overshoot to a harder band when an easier fits.
        return (abs(bi - target), bi > target, bi)

    return sorted(pool, key=sort_key)[0]


async def bridge_node(state: dict) -> dict:
    node = get_node(state["competency_node"])

    # Pre-authored scaffolding: if the curriculum defines bridge exercises, serve
    # one (severity-selected, de-duplicated) and skip the LLM generation.
    if node.bridge_exercises:
        served = state.get("served_bridge_ids", [])
        exercise = select_bridge_exercise(
            node.bridge_exercises,
            state.get("bridge_attempts", 0),
            served,
            state.get("last_eval_score", 0.0),
        )
        out = {
            "pending_game": exercise.model_dump(),
            "served_bridge_ids": list(served) + [exercise.id],
            "last_route": "bridge",
            "bridge_attempts": state.get("bridge_attempts", 0) + 1,
        }
        # Stash the key so the NEXT turn grades the fill against it — but ONLY for
        # closed items. A `spoken` bridge is an open production task with no single
        # correct string, so it must fall through to the LLM evaluator as before.
        if exercise.type in ("fill_blank", "multiple_choice"):
            out["pending_answer_key"] = {
                "type": exercise.type,
                "answer_key": exercise.answer_key,
                "accept": exercise.accept,
                "options": exercise.options,
            }
        return out

    # Fallback: prompt the LLM to generate a bridge step on the fly.
    prompt = build_bridge_prompt(
        node,
        state.get("messages", []),
        state.get("last_diagnosis", {}),
        state.get("memory_context", ""),
        coach_view(state),
        behavior=behavior_for_value(state.get("task_type", "")),
        weaknesses=state.get("weakness_context", []),
    )
    spec = GenSpec(
        provider="gemini", model=GEMINI_FLASH, prompt=prompt, kind="bridge"
    )
    return {
        "pending": spec,
        "last_route": "bridge",
        "bridge_attempts": state.get("bridge_attempts", 0) + 1,
    }
