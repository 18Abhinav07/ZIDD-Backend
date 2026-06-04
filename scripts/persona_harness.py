"""Persona simulation harness — drive full engine sessions with synthetic learners.

qwen plays BOTH sides: the tutor (via the real engine) and the learner (via a
persona prompt here). We exercise placement -> opening -> multi-turn routing
(bridge/strengthen/teach/challenge) -> mastery EMA -> module-complete -> summary,
across the communication AND interview modules, for a spread of learner profiles.

Run:  .venv/bin/python scripts/persona_harness.py 2>&1 | tee /tmp/persona_run.log
"""
import asyncio
import json
import time

import httpx

from app.services import session_service as svc

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"

# ---- personas: writing sample drives placement, sim_prompt drives every reply ----
PERSONAS = [
    {
        "name": "Ravi (A2 struggler)",
        "sample": "I am Ravi. I working in shop. I like cricket and my friends. Yesterday I go market.",
        "self_report": "beginner",
        "sim_prompt": (
            "You are Ravi, an Indian beginner English learner (CEFR A2). You make "
            "tense errors (use present for past), drop articles, write 1-2 short "
            "broken sentences, sometimes miss the point. You are willing but weak. "
            "Never write more than 2 short sentences. Do not correct yourself."
        ),
    },
    {
        "name": "Meena (B1 average)",
        "sample": (
            "I am Meena and I work as a junior analyst. I enjoy reading and I am "
            "trying to improve my speaking for interviews. Last month I finished a "
            "project that my manager liked."
        ),
        "self_report": "intermediate",
        "sim_prompt": (
            "You are Meena, a B1 English learner. You write 2-3 mostly-correct "
            "sentences with occasional small errors (article/preposition). You "
            "follow instructions reasonably and answer on-topic, but your answers "
            "lack specificity and polish. Keep replies short."
        ),
    },
    {
        "name": "Arjun (C1 strong)",
        "sample": (
            "I'm a product manager with five years of experience shipping fintech "
            "tools. What drives me is turning ambiguous user pain into measurable "
            "outcomes; in my last role I cut onboarding drop-off by roughly a third "
            "by rethinking the first-run flow. I'm now looking to do that at scale."
        ),
        "self_report": "fluent",
        "sim_prompt": (
            "You are Arjun, a near-fluent C1 English speaker and sharp professional. "
            "You give crisp, specific, well-structured answers with concrete detail "
            "and evidence. You nail whatever task the coach sets on the first try. "
            "Keep it tight — 2-4 strong sentences, no rambling."
        ),
    },
    {
        "name": "Sam (erratic/off-topic)",
        "sample": "haha idk lol I guess I talk fine? whatever. pizza is good. ask me something easy.",
        "self_report": "intermediate",
        "sim_prompt": (
            "You are Sam, a distracted, jokey learner who ignores instructions. You "
            "go off-topic, crack jokes, ask unrelated questions, rarely do the actual "
            "task. Sometimes you half-comply then derail. Keep replies short and chaotic."
        ),
    },
    {
        "name": "Kiran (terse one-liner)",
        "sample": "I am fine. I want job. I can do work.",
        "self_report": "beginner",
        "sim_prompt": (
            "You are Kiran, who answers with the absolute minimum. Replies like 'ok', "
            "'yes', 'I am good', 'I work hard', 'done'. You almost never elaborate even "
            "when asked. One short fragment per reply, nothing more."
        ),
    },
]


async def learner_reply(sim_prompt: str, tutor_msg: str) -> str:
    """qwen role-plays the learner answering the coach's latest message."""
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sim_prompt + (
                " Output ONLY the learner's reply text — no quotes, no narration, "
                "no labels. Stay fully in character.")},
            {"role": "user", "content": (
                f"The coach just said:\n\"{tutor_msg}\"\n\nWrite your reply as the learner.")},
        ],
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 4096},
    }
    async with httpx.AsyncClient(timeout=60.0) as c:
        r = await c.post(OLLAMA, json=body)
        r.raise_for_status()
        return (r.json()["message"]["content"] or "").strip()


async def _drain(agen) -> str:
    out = []
    async for t in agen:
        out.append(t)
    return "".join(out)


async def run_session(persona: dict, module_id: str, max_turns: int = 6) -> dict:
    log = {"persona": persona["name"], "module": module_id, "turns": [], "events": []}
    t0 = time.time()

    placement = await svc.place_user(
        module_id, writing_sample=persona["sample"], self_report=persona["self_report"]
    )
    log["placement"] = placement

    sid, state = await svc.start_session("sim_" + persona["name"][:4], placement["starting_node"])
    opening = await _drain(svc.stream_opening(sid))
    log["opening"] = opening
    last_tutor = opening

    for i in range(max_turns):
        reply = await learner_reply(persona["sim_prompt"], last_tutor)
        tutor = await _drain(svc.run_turn(sid, reply))
        st = svc.get_state(sid)
        turn = {
            "n": i + 1,
            "node": st["competency_node"],
            "user": reply,
            "route": st["last_route"],
            "score": round(st["last_eval_score"], 3),
            "mastery": round(st["current_mastery"], 3),
            "attempts": st["attempts"],
            "bridge_attempts": st["bridge_attempts"],
            "module_done": st["module_done"],
            "remediation": st["remediation"],
            "tutor": tutor,
        }
        log["turns"].append(turn)
        last_tutor = tutor
        if st["module_done"]:
            log["events"].append(f"module_done at turn {i+1}")
            break

    summary = await svc.end_session(sid)
    log["summary"] = summary
    log["elapsed_s"] = round(time.time() - t0, 1)
    return log


def _print(log: dict) -> None:
    p = log
    print("\n" + "=" * 78)
    print(f"PERSONA: {p['persona']}   MODULE: {p['module']}   ({p['elapsed_s']}s)")
    pl = p["placement"]
    print(f"PLACEMENT: est {pl['estimated_cefr']} -> {pl['node_title']} ({pl['node_cefr']})")
    print(f"  rationale: {pl['rationale']}")
    print(f"OPENING: {p['opening'][:240]}")
    for t in p["turns"]:
        print(f"\n  --- turn {t['n']} | node={t['node']} | route={t['route']} "
              f"| score={t['score']} mastery={t['mastery']} att={t['attempts']} "
              f"bridge={t['bridge_attempts']} done={t['module_done']}")
        print(f"  LEARNER: {t['user'][:200]}")
        print(f"  TUTOR  : {t['tutor'][:300]}")
    if p["events"]:
        print(f"  EVENTS: {p['events']}")
    print(f"  SUMMARY: {p['summary'][:300]}")


async def _safe(persona, module_id, max_turns, runs):
    try:
        log = await run_session(persona, module_id, max_turns=max_turns)
    except Exception as e:  # one bad session must not kill the whole run
        log = {"persona": persona["name"], "module": module_id, "error": repr(e),
               "turns": [], "events": [f"CRASH: {e!r}"], "placement": {},
               "opening": "", "summary": "", "elapsed_s": 0}
        print(f"\n!!! {persona['name']} / {module_id} CRASHED: {e!r}", flush=True)
    else:
        _print(log)
    print(flush=True)
    runs.append(log)


async def main():
    runs = []
    # all 5 personas through communication
    for persona in PERSONAS:
        await _safe(persona, "communication", 6, runs)
    # interview: the higher-level / on-topic personas (placement keeps weak ones low anyway)
    for persona in PERSONAS:
        if persona["name"].startswith(("Meena", "Arjun", "Sam")):
            await _safe(persona, "interview", 6, runs)

    with open("/tmp/persona_runs.json", "w") as f:
        json.dump(runs, f, indent=2)
    print("\n\nALL RUNS -> /tmp/persona_runs.json")


if __name__ == "__main__":
    asyncio.run(main())
