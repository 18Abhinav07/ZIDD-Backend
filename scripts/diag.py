import asyncio
import sys
import traceback
from dotenv import load_dotenv

sys.path.insert(0, "/Users/18abhinav07/Documents/Brain/10-Projects/zidd/BUILD/Zidd-Backend")
load_dotenv("/Users/18abhinav07/Documents/Brain/10-Projects/zidd/BUILD/Zidd-Backend/.env")

from app.services import session_service as svc

async def drain(agen):
    out = []
    async for t in agen:
        if not isinstance(t, svc.NodeAdvance):
            out.append(t)
    return "".join(out)

async def test():
    try:
        print("Placing user...", flush=True)
        placement = await svc.place_user("communication", self_report="beginner")
        print("Starting session...", flush=True)
        sid, state = await svc.start_session("test_usr_a1", placement["starting_node"])
        
        print("Opening stream...", flush=True)
        await drain(svc.stream_opening(sid))
        
        for i in range(6):
            print(f"Turn {i+1}...", flush=True)
            await drain(svc.run_turn(sid, "idk"))
        
        print("Done.", flush=True)
    except Exception as e:
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
