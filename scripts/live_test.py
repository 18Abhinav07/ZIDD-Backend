"""Live engine smoke test — real Gemini/Groq, DB best-effort.

Drives one comm_01 session: opening, then scripted learner answers that go
weak -> strong so we can watch the router move bridge/strengthen/teach/challenge
and mastery climb. Prints streamed tokens + a state snapshot after every turn.

Run:  .venv/bin/python -m scripts.live_test
"""
import asyncio
import sys

from app.services import session_service as svc

USER = "live_test_user"
NODE = "comm_01_self_intro"

# Scripted learner turns: deliberately weak first, then improving.
TURNS = [
    "uhh i dont know how to introduce myself really",
    "my name is rahul and i am student",
    "Hi, I'm Rahul, a final-year computer science student at Pune University. "
    "I'm passionate about backend systems and recently built a real-time chat app.",
    "Hello, my name is Rahul Sharma. I'm a final-year Computer Science student "
    "at Pune University, focused on distributed backend systems. I led a team "
    "of three to ship a real-time chat platform handling 5,000 concurrent users, "
    "and I'm now looking to grow as a backend engineer at a product company.",
]


def _snap(state: dict) -> str:
    return (
        f"  node={state['competency_node']} "
        f"route={state.get('last_route')} "
        f"score={state.get('last_eval_score')} "
        f"mastery={round(state['current_mastery'], 3)} "
        f"attempts={state.get('attempts')} "
        f"bridge={state.get('bridge_attempts')} "
        f"remediation={state.get('remediation')} "
        f"done={state.get('module_done')}"
    )


async def _drain(label: str, agen) -> None:
    sys.stdout.write(f"{label}: ")
    sys.stdout.flush()
    async for tok in agen:
        sys.stdout.write(tok)
        sys.stdout.flush()
    sys.stdout.write("\n")


async def main() -> None:
    print("=== START SESSION ===")
    sid, state = await svc.start_session(USER, NODE)
    print(f"session_id={sid}  node={state['competency_node']}")
    print(f"memory_context={'<loaded>' if state['memory_context'] else '<none>'}")

    print("\n=== OPENING (Gemini Flash) ===")
    await _drain("tutor", svc.stream_opening(sid))
    print(_snap(state))

    for i, ans in enumerate(TURNS, 1):
        print(f"\n=== TURN {i} ===")
        print(f"learner: {ans}")
        await _drain("tutor", svc.run_turn(sid, ans))
        print(_snap(state))

    print("\n=== END SESSION ===")
    summary = await svc.end_session(sid)
    print(f"summary: {summary}")


if __name__ == "__main__":
    asyncio.run(main())
