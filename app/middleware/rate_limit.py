import asyncio
from contextlib import asynccontextmanager, contextmanager
from contextvars import ContextVar
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from collections import defaultdict

from app.config import get_settings

logger = logging.getLogger(__name__)

# Max 2 concurrent LLM calls globally. Queued School evaluations may use this
# capacity, but retain one slot for Career's request-path evaluations.
LLM_CONCURRENCY = 2
CAREER_RESERVED_LLM_SLOTS = 1
llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY)
school_evaluation_semaphore = asyncio.Semaphore(
    LLM_CONCURRENCY - CAREER_RESERVED_LLM_SLOTS
)
_school_evaluation_job_active: ContextVar[bool] = ContextVar(
    "school_evaluation_job_active",
    default=False,
)


@contextmanager
def school_evaluation_job_context():
    """Mark work spawned by the durable School evaluation worker."""

    token = _school_evaluation_job_active.set(True)
    try:
        yield
    finally:
        _school_evaluation_job_active.reset(token)


@asynccontextmanager
async def school_evaluation_llm_slot():
    """Acquire model capacity without letting queued School work fill Career slots."""

    started_at = time.perf_counter()
    if _school_evaluation_job_active.get():
        async with school_evaluation_semaphore:
            async with llm_semaphore:
                logger.info(
                    "ai_queue_acquired %s",
                    {
                        "operation": "school_open_answer",
                        "lane": "school_worker",
                        "wait_ms": round((time.perf_counter() - started_at) * 1000),
                    },
                )
                yield
        return
    async with llm_semaphore:
        logger.info(
            "ai_queue_acquired %s",
            {
                "operation": "school_open_answer",
                "lane": "request",
                "wait_ms": round((time.perf_counter() - started_at) * 1000),
            },
        )
        yield

# 100 turns/user/day
# Simple in-memory tracker: {user_id: {"date": "YYYY-MM-DD", "count": 0}}
turn_counts = defaultdict(lambda: {"date": "", "count": 0})

# Hard ceiling on tracked user_ids. Without it the dict grows once per distinct
# user_id ever seen (including spoofable/anonymous ids) and never shrinks — an
# unbounded memory leak. We bound it at _MAX_TRACKED and prune lazily.
_MAX_TRACKED = 10000

# IP-keyed throttle for /auth/google. It is publicly reachable (no JWT yet), so
# it needs brute-force/backoff protection even though password auth is gone.
# {ip: {"window": "YYYY-MM-DDTHH:MM", "count": 0}}, one-minute buckets.
auth_ip_counts = defaultdict(lambda: {"window": "", "count": 0})
_MAX_TRACKED_IPS = 10000


def _prune_ips(window: str) -> None:
    stale = [ip for ip, t in auth_ip_counts.items() if t["window"] != window]
    for ip in stale:
        del auth_ip_counts[ip]
    while len(auth_ip_counts) > _MAX_TRACKED_IPS:
        auth_ip_counts.pop(next(iter(auth_ip_counts)))


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
        if request.url.path == "/auth/google":
            limit = get_settings().auth_google_limit_per_minute
            ip = request.client.host if request.client else "unknown"
            window = time.strftime("%Y-%m-%dT%H:%M")
            if len(auth_ip_counts) > _MAX_TRACKED_IPS:
                _prune_ips(window)
            tracker = auth_ip_counts[ip]
            if tracker["window"] != window:
                tracker["window"] = window
                tracker["count"] = 0
            if tracker["count"] >= limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "code": "auth_rate_limited",
                            "message": "Too many Google sign-in attempts, slow down",
                        }
                    },
                )
            tracker["count"] += 1

        # Count only real learner turns. Starting, opening, ending, progress, and
        # transcript reads are control-plane actions and must not burn the daily
        # learning-turn quota.
        if request.url.path == "/session/turn" and request.method == "POST":
            limit = get_settings().session_turn_limit_per_day
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
            
            if tracker["count"] >= limit:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "code": "turn_limit_exceeded",
                            "message": "Daily limit of 100 turns exceeded",
                        }
                    },
                )
            
            tracker["count"] += 1

        return await call_next(request)
