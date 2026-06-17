import asyncio
import json
import time
import httpx
import sys
import traceback

sys.path.insert(0, "/Users/18abhinav07/Documents/Brain/10-Projects/zidd/BUILD/Zidd-Backend")

from dotenv import load_dotenv
load_dotenv("/Users/18abhinav07/Documents/Brain/10-Projects/zidd/BUILD/Zidd-Backend/.env")

from app.services import session_service as svc
from app.content.registry import get_node

OLLAMA = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"

async def learner_reply(sim_prompt: str, tutor_msg: str) -> str:
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": sim_prompt + " Output ONLY the learner reply — no quotes, no narration, no labels."},
            {"role": "user", "content": f"The tutor just said:\n\"{tutor_msg}\"\n\nWrite your reply as the learner."},
        ],
        "stream": False,
        "options": {"temperature": 0.8, "num_ctx": 4096},
    }
    print("      [qwen start]", flush=True)
    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=90.0) as c:
            r = await c.post(OLLAMA, json=body)
            r.raise_for_status()
            res = (r.json()["message"]["content"] or "").strip()
            print(f"      [qwen end] {time.time()-t0:.2f}s", flush=True)
            return res
    except Exception as e:
        print(f"      [qwen error] {e} {time.time()-t0:.2f}s", flush=True)
        return f"ERROR: {e}"

async def drain(agen):
    out, advances = [], []
    async for t in agen:
        if isinstance(t, svc.NodeAdvance):
            advances.append((t.from_node, t.to_node))
        else:
            out.append(t)
    return "".join(out), advances

def snapshot(sid):
    st = svc.get_state(sid)
    diag = st.get("last_diagnosis") or {}
    return {
        "node": st.get("competency_node"),
        "route": st.get("last_route"),
        "score": st.get("last_eval_score", 0.0),
        "mastery": st.get("current_mastery", 0.0),
        "level_fails": st.get("level_fails", 0),
        "module_done": st.get("module_done", False),
    }

async def run_scenario(scenario_id, turns_def):
    print(f"[{time.strftime('%H:%M:%S')}] --- RUNNING SCENARIO {scenario_id} ---", flush=True)
    try:
        placement = await svc.place_user("communication", self_report="beginner")
        sid, state = await svc.start_session("usr_"+scenario_id, placement["starting_node"])
        tutor_msg, _ = await drain(svc.stream_opening(sid))
        print("  Opened.", flush=True)

        for i, turn_input in enumerate(turns_def):
            if isinstance(turn_input, dict):
                user_msg = await learner_reply(turn_input["sim_prompt"], tutor_msg)
            else:
                user_msg = turn_input
                
            t0 = time.time()
            tutor_msg, advances = await drain(svc.run_turn(sid, user_msg))
            print(f"  Turn {i+1} ran in {time.time()-t0:.2f}s", flush=True)
            if snapshot(sid)["module_done"] or svc.get_state(sid).get("session_over"):
                print("  Done/Session over.", flush=True)
                break
        await svc.end_session(sid)
    except Exception as e:
        print(f"ERROR: {e}")

async def run_all():
    await run_scenario("B14", ["I am done with my assignment so I am ready to practice now."])
    await run_scenario("A1", ["idk"] * 2)
    sim_a2 = "You are a learner who gives partially correct but vague 2-sentence answers."
    await run_scenario("A2", [{"sim_prompt": sim_a2}] * 2)

if __name__ == "__main__":
    asyncio.run(run_all())
