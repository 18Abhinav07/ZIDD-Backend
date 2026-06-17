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
    try:
        from app.db.engine import get_sessionmaker

        maker = get_sessionmaker()
    except Exception:
        yield None
        return
    sess = maker()
    try:
        yield sess
    except Exception:
        yield None
    finally:
        try:
            await sess.close()
        except Exception:
            pass


class PgStore:
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
    ) -> bool:
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

    async def load_context(self, user_id: str, task_type: str, k: int = 3) -> str:
        from app.memory import store as memory_store

        async with _session() as s:
            if s is None:
                return ""
            try:
                # pg memory keys on node_id; task_type is the local analogue.
                return await memory_store.load_context(s, user_id, task_type, k)
            except Exception:
                return ""

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
    ) -> None:
        from app.db import repo

        async with _session() as s:
            if s is None:
                return None
            try:
                return await repo.record_purchase(
                    s, order_id, user_id, pack_id, credits, amount_paise
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
