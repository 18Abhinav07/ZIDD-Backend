"""Postgres storage backend — wraps the existing repo + pgvector memory store.

Same surface as LocalStore so the cloud swap is config-only (flip AI_BACKEND).
Each call acquires its own AsyncSession and degrades gracefully: if Postgres is
unreachable the method is a best-effort no-op (empty/zero), never an exception —
the engine must run with the DB offline.

NOTE: the weakness-aggregation tables (Phase 2.2) are not yet migrated on the
cloud schema. Until that migration lands, the weakness methods here are
degrade-gracefully no-ops; the LOCAL backend is the source of truth during the
qwen build (AI_BACKEND stays "local"). When the cloud schema gains the
`weaknesses`/`turns` tables these wrap repo calls the same way the others do.
"""
from contextlib import asynccontextmanager


@asynccontextmanager
async def _session():
    """Yield an AsyncSession, or None when Postgres is unreachable.

    Single yield per path: either we hand back a live session (closed in the
    finally), or — if the engine/sessionmaker can't be built — we yield None so
    the caller no-ops. A body exception propagates UNCHANGED: every PgStore
    method wraps its own body and degrades, so this context manager never needs
    to swallow. The old `except Exception: yield None` around the body yielded a
    SECOND time, which makes asynccontextmanager raise
    RuntimeError("generator didn't stop after athrow()") and masks the real
    error; it was harmless only because no method ever let its body raise here.
    """
    try:
        from app.db.engine import get_sessionmaker

        maker = get_sessionmaker()
        sess = maker()
    except Exception:
        yield None
        return
    try:
        yield sess
    finally:
        try:
            await sess.close()
        except Exception:
            pass


def _parse_context_rows(rows: list[dict]) -> list[dict]:
    """Turn pgvector (node_id, content) rows into LocalStore's list[dict] shape.

    Each row's `content` is a raw session summary (the 3-line Strengths/Watch/
    Next focus format write_memory persists). Parse the named lines the same way
    LocalStore and _memory_block do, and stamp the REAL competency node_id the row
    carries so a caller matching a summary to a node (the welcome-back recap) works
    identically on both backends. score/date are unknown on pg -> 0.0/"" (the
    fields LocalStore fills), so both backends return structurally identical dicts.
    """
    result: list[dict] = []
    for row in rows or []:
        node_id = row.get("node_id", "") if isinstance(row, dict) else ""
        chunk = ((row.get("content", "") if isinstance(row, dict) else "") or "").strip()
        if not chunk:
            continue
        parsed: dict[str, str] = {}
        for line in chunk.splitlines():
            if line.startswith("Strengths:"):
                parsed["strengths"] = line[len("Strengths:"):].strip()
            elif line.startswith("Watch:"):
                parsed["watch"] = line[len("Watch:"):].strip()
            elif line.startswith("Next focus:"):
                parsed["next_focus"] = line[len("Next focus:"):].strip()
        result.append({
            "node_id": node_id, "score": 0.0,
            "strengths": parsed.get("strengths", ""),
            "watch": parsed.get("watch", ""),
            "next_focus": parsed.get("next_focus", ""),
            "date": "", "raw": chunk,
        })
    return result


class PgStore:
    async def ping_writable(self) -> bool:
        """Cloud equivalent of the writability probe: confirm the pooled
        Postgres connection answers. SELECT 1 is sufficient — repo writes already
        degrade to no-ops when the pooler is down, so connectivity is the health
        signal that matters. Returns False on any connection/query failure."""
        from sqlalchemy import text

        async with _session() as s:
            if s is None:
                return False
            try:
                result = await s.execute(text("SELECT 1"))
                return result.scalar() == 1
            except Exception:
                return False

    async def ensure_profile(self, user_id: str, name: str = "", password_hash: str | None = None) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return
            try:
                await repo.ensure_profile(s, user_id, name, password_hash)
            except Exception:
                pass

    async def get_profile(self, user_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.get_profile(s, user_id)
            except Exception:
                return None

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        task_type: str,
        module_id: str,
        node_id: str,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return
            try:
                await repo.create_session(s, session_id, user_id, node_id)
            except Exception:
                pass

    async def end_session(
        self, session_id: str, final_summary: str = "", avg_score: float = 0.0
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return
            try:
                await repo.end_session(s, session_id, 0, avg_score, final_summary)
            except Exception:
                pass

    async def record_turn(
        self,
        session_id: str,
        user_id: str,
        node_id: str,
        score: float,
        on_task: bool = True,
        english: bool = True,
        affect: str = "neutral",
    ) -> None:
        # turns table not yet on cloud schema (Phase 2.2 migration) — no-op.
        return

    async def get_turns(self, session_id: str) -> list[dict]:
        return []

    async def upsert_mastery(
        self,
        user_id: str,
        node_id: str,
        ema: float,
        attempts: int,
        clean_pass: bool = False,
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return
            try:
                await repo.upsert_mastery(
                    s, user_id, node_id, ema, attempts, clean_pass
                )
            except Exception:
                pass

    async def get_progression(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return []
            try:
                return await repo.get_progression(s, user_id)
            except Exception:
                return []

    async def get_module_passrate(
        self, user_id: str, node_ids: list[str]
    ) -> tuple[int, int]:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return (0, 0)
            try:
                return await repo.get_module_passrate(s, user_id, node_ids)
            except Exception:
                return (0, 0)

    async def bump_weakness(
        self,
        user_id: str,
        task_type: str,
        skill_id: str,
        score: float,
        raw: str = "",
    ) -> None:
        # weaknesses table not yet on cloud schema (Phase 2.2 migration) — no-op.
        return

    async def get_weaknesses(
        self, user_id: str, task_type: str | None = None
    ) -> list[dict]:
        return []

    async def write_memory(
        self,
        user_id: str,
        session_id: str,
        node_id: str,
        content: str,
        task_type: str = "",
        score: float = 0.0,
    ) -> bool:
        # `score` mirrors LocalStore.write_memory's signature so session_service's
        # end_session call `write_memory(..., score=avg_score)` does not raise a
        # TypeError under the cloud backend (which a bare `except Exception: pass`
        # at the call site would have silently swallowed, dropping the memory).
        # The pgvector store keys on content, so score is not forwarded.
        from app.memory import store as memory_store

        async with _session() as s:
            if s is None:
                return False
            try:
                return await memory_store.write_memory(
                    s, user_id, session_id, node_id, content
                )
            except Exception:
                return False

    async def load_context(self, user_id: str, task_type: str, k: int = 3) -> list[dict]:
        """Most recent k session summaries as structured dicts, newest-first.

        Identical return shape to LocalStore.load_context (list[dict] with keys
        node_id, score, strengths, watch, next_focus, date, raw) so callers see
        ONE contract regardless of backend. The pgvector store hands back
        (node_id, content) rows; each carries the REAL competency node that
        produced the summary, so the node-level match in start_session (the
        welcome-back recap) holds the same as on LocalStore. Empty/offline -> []."""
        from app.memory import store as memory_store

        async with _session() as s:
            if s is None:
                return []
            try:
                # task_type biases the semantic query; each row carries its true
                # competency node_id (see memory_store.load_context).
                rows = await memory_store.load_context(s, user_id, task_type, k)
            except Exception:
                return []
        return _parse_context_rows(rows)

    # ---------- test-item cache (Phase 4 Layer B) ----------
    # Not migrated to the cloud schema yet; degrade gracefully. Local backend is
    # the source of truth during the qwen build, so a cloud miss just regenerates.

    async def cache_test_items(
        self,
        user_id: str,
        task_type: str,
        items: list[dict],
        ts: float | None = None,
    ) -> None:
        return

    async def get_cached_test_items(
        self, user_id: str, task_type: str, max_age: float | None = None
    ) -> list[dict] | None:
        return None

    # ---------- billing: credits ----------

    async def get_credits(self, user_id: str) -> int:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return 0
            try:
                return await repo.get_credits(s, user_id)
            except Exception:
                return 0

    async def is_demo(self, user_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            try:
                profile = await repo.get_profile(s, user_id)
                if profile is None:
                    return False
                return bool(profile["demo_unlimited"])
            except Exception:
                return False

    async def set_demo_unlimited(self, user_id: str, enabled: bool = True) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.set_demo_unlimited(s, user_id, enabled)
            except Exception:
                return None

    async def grant_credits(self, user_id: str, amount: int, reason: str) -> int:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return 0
            try:
                return await repo.grant_credits(s, user_id, amount, reason)
            except Exception:
                return 0

    async def deduct_credits(self, user_id: str, amount: int, reason: str) -> bool:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            try:
                return await repo.deduct_credit(s, user_id, amount, reason)
            except Exception:
                return False

    async def charge_and_unlock(
        self,
        user_id: str,
        amount: int,
        reason: str,
        scope: str,
        ref_id: str,
    ) -> bool:
        """Deduct credits AND record an ACCESS unlock atomically (one txn)."""
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            try:
                return await repo.charge_and_unlock(
                    s, user_id, amount, reason, scope, ref_id
                )
            except Exception:
                return False

    # ---------- billing: content unlocks ----------

    async def has_unlock(self, user_id: str, scope: str, ref_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            try:
                return await repo.has_unlock(s, user_id, scope, ref_id)
            except Exception:
                return False

    async def add_unlock(
        self, user_id: str, scope: str, ref_id: str, credits_spent: int
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.add_unlock(
                    s, user_id, scope, ref_id, credits_spent
                )
            except Exception:
                return None

    async def remove_unlock(self, user_id: str, scope: str, ref_id: str) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.remove_unlock(s, user_id, scope, ref_id)
            except Exception:
                return None

    async def list_unlocks(self, user_id: str) -> list[dict]:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return []
            try:
                return await repo.list_unlocks(s, user_id)
            except Exception:
                return []

    async def count_attempts(self, user_id: str, module_id: str) -> int:
        from app.content import registry
        from app.db import repo

        async with _session() as s:
            if s is None:
                return 0
            try:
                nodes = await repo.list_session_nodes(s, user_id)
                count = 0
                for node_id in nodes:
                    try:
                        if registry.module_of(node_id) == module_id:
                            count += 1
                    except KeyError:
                        continue
                return count
            except Exception:
                return 0

    # ---------- billing: purchases ----------

    async def record_purchase(
        self,
        order_id: str,
        user_id: str,
        pack_id: str,
        credits: int,
        amount_paise: int,
        status: str = "created",
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.record_purchase(
                    s, order_id, user_id, pack_id, credits, amount_paise, status=status
                )
            except Exception:
                return None

    async def get_purchase(self, order_id: str) -> dict | None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.get_purchase(s, order_id)
            except Exception:
                return None

    async def mark_purchase_paid(self, order_id: str) -> bool:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            try:
                return await repo.mark_purchase_paid(s, order_id)
            except Exception:
                return False

    async def mark_paid_and_grant(
        self, order_id: str, user_id: str, credits: int, reason: str
    ) -> bool:
        """Latch a purchase to 'paid' AND grant its credits in ONE transaction.

        Delegates to repo.mark_paid_and_grant, which folds the latch + grant +
        ledger row under a SINGLE commit() with rollback-on-failure, mirroring
        LocalStore. The old body committed the latch and the grant in TWO
        separate transactions (mark_purchase_paid then grant_credits): an error
        between them left the order permanently 'paid' with credits never
        granted, and Razorpay's retry then skipped the grant forever.

        Exceptions are intentionally NOT swallowed here. The repo helper rolls
        the whole unit back before raising, so the order stays UNPAID on failure
        and the grant is never lost: a missing-profile KeyError is handled by the
        webhook route (deferred for reconciliation), and a transient DB error
        propagates to a 5xx so Razorpay retries. Returns True on the first
        captured webhook (granted once); False on a retry (already paid) or when
        the DB is offline.
        """
        from app.db import repo

        async with _session() as s:
            if s is None:
                return False
            return await repo.mark_paid_and_grant(
                s, order_id, user_id, credits, reason
            )
