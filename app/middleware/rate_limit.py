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

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # We only apply turn rate limiting to the turn endpoints
        if request.url.path.startswith("/session") and request.method == "POST":
            # Just extract user_id from state (populated by AuthMiddleware)
            user_id = getattr(request.state, "user_id", "anonymous")
            
            today = time.strftime("%Y-%m-%d")
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
