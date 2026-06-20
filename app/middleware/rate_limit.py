import asyncio
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

# Max 2 concurrent LLM calls globally
llm_semaphore = asyncio.Semaphore(2)

# 100 turns/user/day
# Simple in-memory tracker: {user_id: {"date": "YYYY-MM-DD", "count": 0}}
turn_counts = defaultdict(lambda: {"date": "", "count": 0})

# Hard ceiling on tracked user_ids. Without it the dict grows once per distinct
# user_id ever seen (including spoofable/anonymous ids) and never shrinks — an
# unbounded memory leak. We bound it at _MAX_TRACKED and prune lazily.
_MAX_TRACKED = 10000


def _prune(today: str) -> None:
    """Evict stale entries so turn_counts stays bounded.

    Called only when the tracker exceeds _MAX_TRACKED, so the O(n) sweep is
    amortised away from the per-request hot path. First drop every entry left
    over from a previous day (its counter is already stale and would reset on
    next touch anyway). If a single day still exceeds the cap (e.g. an id-spoof
    flood), evict oldest-inserted entries until back under it — dict preserves
    insertion order, so next(iter(...)) is the oldest key.
    """
    stale = [uid for uid, t in turn_counts.items() if t["date"] != today]
    for uid in stale:
        del turn_counts[uid]
    while len(turn_counts) > _MAX_TRACKED:
        turn_counts.pop(next(iter(turn_counts)))


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We only apply turn rate limiting to the turn endpoints
        if request.url.path.startswith("/session") and request.method == "POST":
            # Just extract user_id from state (populated by AuthMiddleware)
            user_id = getattr(request.state, "user_id", "anonymous")

            today = time.strftime("%Y-%m-%d")
            # Prune before touching the current user's entry so the active user is
            # added after the sweep and never evicted by it.
            if len(turn_counts) > _MAX_TRACKED:
                _prune(today)
            tracker = turn_counts[user_id]
            if tracker["date"] != today:
                tracker["date"] = today
                tracker["count"] = 0
            
            if tracker["count"] >= 100:
                return JSONResponse(status_code=429, content={"detail": "Daily limit of 100 turns exceeded"})
            
            tracker["count"] += 1

        # We wrap the downstream call in the semaphore if it's hitting an endpoint
        # However, asyncio.Semaphore across the whole request could cause deadlocks if SSE is open.
        # The prompt actually says: "max 2 concurrent LLM calls (asyncio.Semaphore)".
        # It's better to put the semaphore inside `app/ai/calls.py` so it only blocks the exact LLM call,
        # not the entire request including the SSE stream idle time.
        # But since the task explicitly says `app/middleware/`, I will add a request-level semaphore 
        # or maybe the task just listed `app/middleware/` for the rate limiter. I will just do the daily limit here
        # and inject the semaphore in `app/ai/calls.py` for "LLM calls". 
        
        return await call_next(request)
