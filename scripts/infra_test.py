"""Complete tutor-agent INFRA test on the live qwen model.

The persona harness exercises emergent BEHAVIOR. This exercises every ENGINE
PATH — including the ones personas can't reach in a short session (challenge
route, node advance, module_done, remediation flag, bridge-attempt cap) — by
seeding canonical state, then firing the REAL model through run_turn.

Routing recap (app/graph/route.py): evaluate writes score+EMA-mastery, then
route_node reads them:
  score<0.4 & bridge_attempts<3 -> bridge
  score<0.6                     -> strengthen
  mastery>0.8                   -> challenge
  else                          -> teach
So seeding current_mastery=0.9 forces challenge for any score>=0.6, and
bridge_attempts==CAP re-anchors to teach (cap escalation). Deterministic
regardless of the model's exact score.

Progression is NOT model-dependent and NOT EMA-gated: a node advances on a
CONSECUTIVE clean-pass streak (clean_streak >= ADVANCE_STREAK), down-ladders
scaffold after DOWN_LADDER_FAILS hard fails, and flags remediation when the
module clean-rate drops below the floor. Batteries C/D exercise that logic
DETERMINISTICALLY by calling svc._update_progress / svc._maybe_advance directly
with seeded scores — no model, instant, exact.

Run:  PYTHONPATH=. .venv/bin/python -u scripts/infra_test.py
"""
import asyncio
import time

from app.content.registry import get_module, module_of, next_node
from app.services import session_service as svc

STRONG = (
    "I'm Arjun, a product manager with five years in fintech. In my last role I "
    "cut onboarding drop-off by a third by redesigning the first-run flow, and "
    "I'm now looking to drive that kind of measurable impact at larger scale."
)
MEDIUM = "I am working as analyst. I like my job and I want to improve my speaking skill."
WEAK = "idk lol whatever"
OPENING_STUB = "Let's begin. Please introduce yourself in a few sentences."

PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []


def _check(name: str, cond: bool, detail: str = "") -> None:
    status = PASS if cond else FAIL
    _results.append((name, status, detail))
    print(f"  [{status}] {name}  {detail}", flush=True)


async def _drain(agen) -> str:
    out = []
    async for t in agen:
        out.append(t)
    return "".join(out)


def _fresh(node_id: str, **seed) -> dict:
    """A canonical fresh state for deterministic progression-logic tests."""
    st = svc._new_state("infra", "logic_" + node_id, node_id, "")
    st.update(seed)
    return st


async def _advance_step(st: dict, score: float) -> None:
    """Simulate one scored turn's progression bookkeeping (no model)."""
    st["last_eval_score"] = score
    st["attempts"] = st.get("attempts", 0) + 1
    svc._update_progress(st)
    await svc._maybe_advance(st)


async def _seeded_turn(node_id: str, user_input: str, seed: dict) -> dict:
    """start session, skip the streamed opening, seed state, fire one real turn."""
    sid, _ = await svc.start_session("infra", node_id)
    st = svc.get_state(sid)
    st["turn_count"] = 1  # past turn 0 -> entry_router sends to evaluate
    st["messages"] = [{"role": "assistant", "content": OPENING_STUB}]
    st.update(seed)
    tutor = await _drain(svc.run_turn(sid, user_input))
    st = svc.get_state(sid)
    out = {
        "sid": sid,
        "route": st["last_route"],
        "score": round(st["last_eval_score"], 3),
        "mastery": round(st["current_mastery"], 3),
        "node": st["competency_node"],
        "attempts": st["attempts"],
        "bridge_attempts": st["bridge_attempts"],
        "module_done": st["module_done"],
        "remediation": st["remediation"],
        "tutor_len": len(tutor),
    }
    return out


# ============================ A. PLACEMENT MATRIX ============================
async def battery_placement():
    print("\n" + "=" * 78 + "\nA. PLACEMENT MATRIX (real CEFR eval, all 3 modules)\n" + "=" * 78)
    for mod in ("communication", "interview", "group_discussion", "school_english"):
        title = get_module(mod).title
        # strong sample
        r = await svc.place_user(mod, writing_sample=STRONG)
        _check(f"{mod}: strong-sample node in module",
               module_of(r["starting_node"]) == mod,
               f"est={r['estimated_cefr']} -> {r['starting_node']}")
        # weak sample
        r = await svc.place_user(mod, writing_sample="me no speak good. job want.")
        _check(f"{mod}: weak-sample node in module",
               module_of(r["starting_node"]) == mod,
               f"est={r['estimated_cefr']} -> {r['starting_node']}")
        # self-report only (no model call)
        r = await svc.place_user(mod, self_report="advanced")
        _check(f"{mod}: self-report-only maps band",
               module_of(r["starting_node"]) == mod and r["estimated_cefr"] == "B2",
               f"est={r['estimated_cefr']} -> {r['starting_node']}")
        # nothing -> default B1
        r = await svc.place_user(mod)
        _check(f"{mod}: default placement B1",
               r["estimated_cefr"] == "B1" and module_of(r["starting_node"]) == mod,
               f"est={r['estimated_cefr']} -> {r['starting_node']}")


# ============================ B. ROUTE COVERAGE ============================
async def battery_routes():
    print("\n" + "=" * 78 + "\nB. ROUTE COVERAGE (force each of bridge/strengthen/teach/challenge)\n" + "=" * 78)
    node = "comm_01_self_intro"

    r = await _seeded_turn(node, WEAK, {"current_mastery": 0.0, "bridge_attempts": 0})
    _check("route=bridge on weak answer", r["route"] == "bridge",
           f"score={r['score']} mastery={r['mastery']} tutor_len={r['tutor_len']}")

    r = await _seeded_turn(node, WEAK, {"current_mastery": 0.0, "bridge_attempts": 3})
    _check("bridge cap re-anchors to teach (bridge_attempts==3)", r["route"] == "teach",
           f"route={r['route']} score={r['score']}")

    r = await _seeded_turn(node, STRONG, {"current_mastery": 0.0, "bridge_attempts": 0})
    _check("route=teach on strong answer, low mastery", r["route"] == "teach",
           f"score={r['score']} mastery={r['mastery']} tutor_len={r['tutor_len']}")

    r = await _seeded_turn(node, STRONG, {"current_mastery": 0.9, "bridge_attempts": 0})
    _check("route=challenge when mastery>0.8 + good answer", r["route"] == "challenge",
           f"score={r['score']} mastery={r['mastery']} tutor_len={r['tutor_len']}")

    # strengthen needs score in [0.4,0.6); model-dependent. Record, assert valid route.
    r = await _seeded_turn(node, MEDIUM, {"current_mastery": 0.0, "bridge_attempts": 0})
    _check("medium answer -> valid route + non-empty gen",
           r["route"] in ("bridge", "strengthen", "teach", "challenge") and r["tutor_len"] > 0,
           f"route={r['route']} score={r['score']} (strengthen if 0.4<=score<0.6)")


# ============================ C. PROGRESSION (deterministic) ============================
async def battery_progression():
    print("\n" + "=" * 78 + "\nC. PROGRESSION (clean-streak advance / down-ladder / module_done)\n" + "=" * 78)
    mid = "comm_01_self_intro"
    nxt = next_node(mid)

    # one clean pass: streak ticks to 1, no advance yet
    st = _fresh(mid)
    await _advance_step(st, 0.8)
    _check("1 clean pass: streak=1, no advance",
           st["clean_streak"] == 1 and st["competency_node"] == mid,
           f"streak={st['clean_streak']} node={st['competency_node']}")

    # second consecutive clean pass: advance + every per-node counter resets
    await _advance_step(st, 0.9)
    advanced = (st["competency_node"] == nxt and st["current_mastery"] == 0.0
                and st["attempts"] == 0 and st["clean_streak"] == 0)
    _check("2nd clean pass: advance + counters reset",
           advanced, f"{mid} -> {st['competency_node']} (expected {nxt}) streak={st['clean_streak']}")

    # a non-pass between clean passes resets the streak (no premature advance)
    st = _fresh(mid)
    await _advance_step(st, 0.8)
    await _advance_step(st, 0.3)
    _check("non-pass resets streak (no advance)",
           st["clean_streak"] == 0 and st["competency_node"] == mid,
           f"streak={st['clean_streak']} node={st['competency_node']}")

    # two hard fails turn on the down-ladder scaffold
    st = _fresh(mid)
    await _advance_step(st, 0.2)
    await _advance_step(st, 0.2)
    _check("2 hard fails -> scaffold on",
           st["scaffold"] == 1 and st["level_fails"] == 2,
           f"scaffold={st['scaffold']} level_fails={st['level_fails']}")

    # clean streak on the LAST node of a module -> module_done, no overrun
    last = mid
    while next_node(last) is not None:
        last = next_node(last)
    st = _fresh(last)
    await _advance_step(st, 0.8)
    await _advance_step(st, 0.9)
    _check("module_done True on clean streak at last node",
           st["module_done"] is True and st["competency_node"] == last,
           f"last={last} module_done={st['module_done']}")


# ============================ D. REMEDIATION FLAG (deterministic) ============================
async def battery_remediation():
    print("\n" + "=" * 78 + "\nD. REMEDIATION (clean pass-rate < 0.5 sets flag on advance)\n" + "=" * 78)
    node = "comm_01_self_intro"
    # streak already at the gate; this node is dirty (attempts>cap) and two prior
    # nodes were dirty -> 0/3 clean after this advance -> remediation.
    st = _fresh(
        node,
        clean_streak=2,
        attempts=5,  # > CLEAN_PASS_MAX_ATTEMPTS -> this node not clean
        node_history={
            "x_prev": {"attempts": 6, "clean": False},
            "y_prev": {"attempts": 7, "clean": False},
        },
    )
    await svc._maybe_advance(st)
    _check("remediation flag set when clean-rate < 0.5",
           st["remediation"] is True, f"remediation={st['remediation']}")

    # control: a clean history must NOT trip remediation
    st = _fresh(
        node,
        clean_streak=2,
        attempts=1,  # clean
        node_history={"x_prev": {"attempts": 1, "clean": True}},
    )
    await svc._maybe_advance(st)
    _check("remediation stays off when clean-rate >= 0.5",
           st["remediation"] is False, f"remediation={st['remediation']}")


# ============================ E. INTERVIEW MODULE ============================
async def battery_interview():
    print("\n" + "=" * 78 + "\nE. INTERVIEW MODULE (challenge path on a second module)\n" + "=" * 78)
    node = "int_01_elevator_pitch"
    r = await _seeded_turn(node, STRONG, {"current_mastery": 0.9})
    _check("interview node routes challenge + streams",
           r["route"] == "challenge" and r["tutor_len"] > 0,
           f"route={r['route']} score={r['score']} tutor_len={r['tutor_len']}")


# ============================ F. LIFECYCLE / ERRORS ============================
async def battery_lifecycle():
    print("\n" + "=" * 78 + "\nF. LIFECYCLE + ERROR PATHS\n" + "=" * 78)
    try:
        await svc.start_session("infra", "no_such_node")
        _check("start_session unknown node raises ValueError", False, "no raise")
    except ValueError:
        _check("start_session unknown node raises ValueError", True)

    try:
        await _drain(svc.run_turn("no_such_session", "hi"))
        _check("run_turn unknown session raises KeyError", False, "no raise")
    except KeyError:
        _check("run_turn unknown session raises KeyError", True)

    # full lifecycle: start -> end -> state popped + summary produced (real model)
    sid, _ = await svc.start_session("infra", "comm_01_self_intro")
    st = svc.get_state(sid)
    st["turn_count"] = 1
    st["messages"] = [
        {"role": "assistant", "content": OPENING_STUB},
        {"role": "user", "content": STRONG},
    ]
    summary = await svc.end_session(sid)
    _check("end_session returns non-empty summary", bool(summary.strip()),
           f"summary_len={len(summary)}")
    _check("state popped after end_session", svc.get_state(sid) is None)


async def main():
    print("ZIDD TUTOR-AGENT INFRA TEST  (backend=local qwen2.5:14b)", flush=True)
    t0 = time.time()
    await battery_placement()
    await battery_routes()
    await battery_progression()
    await battery_remediation()
    await battery_interview()
    await battery_lifecycle()

    print("\n" + "=" * 78)
    npass = sum(1 for _, s, _ in _results if s == PASS)
    nfail = len(_results) - npass
    print(f"INFRA RESULT: {npass}/{len(_results)} PASS, {nfail} FAIL  ({round(time.time()-t0,1)}s)")
    if nfail:
        for name, s, detail in _results:
            if s == FAIL:
                print(f"  FAIL: {name}  {detail}")


if __name__ == "__main__":
    asyncio.run(main())
