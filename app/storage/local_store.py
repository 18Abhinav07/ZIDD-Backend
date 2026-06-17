"""SQLite local-first storage backend.

Mirrors the cloud surface (pg_store) on a plain SQLite file so every turn and
weakness is logged and retrievable with Postgres OFFLINE — the felt-memory fix
for qwen-dev. No pgvector: retrieval is by user_id + task_type + recency +
weakness tags, which is plenty offline (cosine adds nothing at dev scale).

sqlite3 is synchronous; methods are `async def` to match the interface but call
straight into the driver. At single-user dev scale the blocking is negligible
and keeps the backend dependency-free (no aiosqlite).

Weaknesses aggregate on the fixed SkillID taxonomy: bump_weakness coerces the
raw tag to a known SkillID and UPSERTs on (user_id, task_type, skill_id), so the
same skill always lands on one row and hit_count actually sums.
"""
import json
import sqlite3
import time

from app.content.skills import coerce_skill_id

_SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    user_id TEXT PRIMARY KEY,
    name    TEXT DEFAULT '',
    password_hash TEXT,
    credits INTEGER NOT NULL DEFAULT 0,
    demo_unlimited INTEGER NOT NULL DEFAULT 0,
    created REAL
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id    TEXT PRIMARY KEY,
    user_id       TEXT,
    task_type     TEXT,
    module_id     TEXT,
    node_id       TEXT,
    started       REAL,
    ended         REAL,
    final_summary TEXT DEFAULT '',
    avg_score     REAL
);
CREATE TABLE IF NOT EXISTS turns (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    user_id    TEXT,
    node_id    TEXT,
    score      REAL,
    on_task    INTEGER,
    english    INTEGER,
    affect     TEXT,
    ts         REAL
);
CREATE TABLE IF NOT EXISTS weaknesses (
    user_id   TEXT,
    task_type TEXT,
    skill_id  TEXT,
    hit_count INTEGER DEFAULT 0,
    last_score REAL,
    last_seen  REAL,
    last_raw   TEXT DEFAULT '',
    PRIMARY KEY (user_id, task_type, skill_id)
);
CREATE TABLE IF NOT EXISTS mastery (
    user_id    TEXT,
    node_id    TEXT,
    ema        REAL,
    attempts   INTEGER,
    clean_pass INTEGER DEFAULT 0,
    updated_at REAL,
    PRIMARY KEY (user_id, node_id)
);
CREATE TABLE IF NOT EXISTS memory (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    TEXT,
    session_id TEXT,
    task_type  TEXT,
    node_id    TEXT,
    content    TEXT,
    ts         REAL
);
CREATE TABLE IF NOT EXISTS test_items (
    user_id   TEXT,
    task_type TEXT,
    items     TEXT,
    cached_at REAL,
    PRIMARY KEY (user_id, task_type)
);
CREATE TABLE IF NOT EXISTS content_unlocks (
    user_id       TEXT,
    scope         TEXT,
    ref_id        TEXT,
    credits_spent INTEGER DEFAULT 0,
    created       REAL,
    PRIMARY KEY (user_id, scope, ref_id)
);
CREATE TABLE IF NOT EXISTS credit_transactions (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    delta   INTEGER,
    reason  TEXT,
    created REAL
);
CREATE TABLE IF NOT EXISTS purchases (
    order_id     TEXT PRIMARY KEY,
    user_id      TEXT,
    pack_id      TEXT,
    credits      INTEGER,
    amount_paise INTEGER,
    status       TEXT DEFAULT 'created',
    created      REAL
);
"""


class LocalStore:
    def __init__(self, db_path: str = ".zidd_local.db") -> None:
        self.db_path = db_path
        # check_same_thread=False: FastAPI may touch this from worker threads.
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        # Pre-monetization databases have a profiles table without the credit
        # columns. SQLite lacks "ADD COLUMN IF NOT EXISTS", so guard each ALTER
        # and swallow the "duplicate column name" OperationalError.
        for ddl in (
            "ALTER TABLE profiles ADD COLUMN credits INTEGER NOT NULL DEFAULT 0",
            "ALTER TABLE profiles ADD COLUMN demo_unlimited INTEGER NOT NULL DEFAULT 0",
        ):
            try:
                self._conn.execute(ddl)
            except sqlite3.OperationalError as e:
                # Only swallow the "column already exists" case (fresh DBs get
                # these columns from _SCHEMA; this loop only matters for
                # pre-existing dev DBs missing them). Re-raise anything real.
                if "duplicate column name" not in str(e):
                    raise
        self._conn.commit()

    # ---------- profiles ----------

    async def ensure_profile(self, user_id: str, name: str = "", password_hash: str | None = None) -> None:
        self._conn.execute(
            "INSERT INTO profiles (user_id, name, password_hash, created) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "name = CASE WHEN excluded.name != '' THEN excluded.name ELSE profiles.name END, "
            "password_hash = CASE WHEN excluded.password_hash IS NOT NULL THEN excluded.password_hash ELSE profiles.password_hash END",
            (user_id, name, password_hash, time.time()),
        )
        self._conn.commit()

    async def get_profile(self, user_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT user_id, name, password_hash, credits, demo_unlimited, created "
            "FROM profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        profile = dict(row)
        profile["credits"] = int(profile.get("credits") or 0)
        profile["demo_unlimited"] = bool(profile.get("demo_unlimited"))
        return profile

    # ---------- billing: credits ----------

    async def get_credits(self, user_id: str) -> int:
        row = self._conn.execute("SELECT credits FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        return int(row["credits"]) if row and row["credits"] is not None else 0

    async def is_demo(self, user_id: str) -> bool:
        row = self._conn.execute("SELECT demo_unlimited FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        return bool(row["demo_unlimited"]) if row else False

    async def set_demo_unlimited(self, user_id: str, enabled: bool = True) -> None:
        self._conn.execute("UPDATE profiles SET demo_unlimited = ? WHERE user_id = ?", (int(enabled), user_id))
        self._conn.commit()

    async def grant_credits(self, user_id: str, amount: int, reason: str) -> int:
        if amount < 0:
            raise ValueError("grant amount must be non-negative")
        cur = self._conn.execute(
            "UPDATE profiles SET credits = credits + ? WHERE user_id = ?",
            (amount, user_id),
        )
        if cur.rowcount == 0:                  # no such profile: fail loud, never log a phantom grant
            self._conn.rollback()
            raise KeyError(user_id)
        self._conn.execute(
            "INSERT INTO credit_transactions (user_id, delta, reason, created) VALUES (?, ?, ?, ?)",
            (user_id, amount, reason, time.time()),
        )
        self._conn.commit()
        return await self.get_credits(user_id)

    async def deduct_credits(self, user_id: str, amount: int, reason: str) -> bool:
        if await self.is_demo(user_id):       # Judge/demo bypass: never charged, always allowed.
            return True
        if amount < 0:
            raise ValueError("deduct amount must be non-negative")
        # Atomic guard: folding the balance check into the WHERE clause makes the
        # check and the debit a single statement, so two concurrent deducts can't
        # both pass the check and overspend. rowcount == 0 => insufficient funds.
        cur = self._conn.execute(
            "UPDATE profiles SET credits = credits - ? WHERE user_id = ? AND credits >= ?",
            (amount, user_id, amount),
        )
        if cur.rowcount == 0:
            self._conn.rollback()
            return False
        self._conn.execute(
            "INSERT INTO credit_transactions (user_id, delta, reason, created) VALUES (?, ?, ?, ?)",
            (user_id, -amount, reason, time.time()),
        )
        self._conn.commit()
        return True

    # ---------- billing: content unlocks ----------

    async def has_unlock(self, user_id: str, scope: str, ref_id: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM content_unlocks "
            "WHERE user_id = ? AND scope = ? AND ref_id = ?",
            (user_id, scope, ref_id),
        ).fetchone()
        return row is not None

    async def add_unlock(
        self, user_id: str, scope: str, ref_id: str, credits_spent: int
    ) -> None:
        self._conn.execute(
            "INSERT INTO content_unlocks "
            "(user_id, scope, ref_id, credits_spent, created) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, scope, ref_id) DO NOTHING",
            (user_id, scope, ref_id, credits_spent, time.time()),
        )
        self._conn.commit()

    async def remove_unlock(self, user_id: str, scope: str, ref_id: str) -> None:
        self._conn.execute(
            "DELETE FROM content_unlocks "
            "WHERE user_id = ? AND scope = ? AND ref_id = ?",
            (user_id, scope, ref_id),
        )
        self._conn.commit()

    async def list_unlocks(self, user_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT scope, ref_id, credits_spent, created FROM content_unlocks "
            "WHERE user_id = ? ORDER BY created DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------- billing: attempt counting ----------

    async def count_attempts(self, user_id: str, module_id: str) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM sessions "
            "WHERE user_id = ? AND module_id = ?",
            (user_id, module_id),
        ).fetchone()
        return int(row["n"]) if row and row["n"] is not None else 0

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
        self._conn.execute(
            "INSERT INTO purchases "
            "(order_id, user_id, pack_id, credits, amount_paise, status, created) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(order_id) DO NOTHING",
            (order_id, user_id, pack_id, credits, amount_paise, status, time.time()),
        )
        self._conn.commit()

    async def get_purchase(self, order_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT order_id, user_id, pack_id, credits, amount_paise, status, created "
            "FROM purchases WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        return dict(row) if row else None

    async def mark_purchase_paid(self, order_id: str) -> bool:
        """Latch a purchase to 'paid'. Returns True only on the transition so
        the webhook grants credits exactly once even under Razorpay retries."""
        cur = self._conn.execute(
            "UPDATE purchases SET status = 'paid' "
            "WHERE order_id = ? AND status != 'paid'",
            (order_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    # ---------- sessions ----------

    async def create_session(
        self,
        session_id: str,
        user_id: str,
        task_type: str,
        module_id: str,
        node_id: str,
    ) -> None:
        self._conn.execute(
            "INSERT INTO sessions "
            "(session_id, user_id, task_type, module_id, node_id, started) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT(session_id) DO NOTHING",
            (session_id, user_id, task_type, module_id, node_id, time.time()),
        )
        self._conn.commit()

    async def end_session(
        self, session_id: str, final_summary: str = "", avg_score: float = 0.0
    ) -> None:
        self._conn.execute(
            "UPDATE sessions SET ended = ?, final_summary = ?, avg_score = ? "
            "WHERE session_id = ?",
            (time.time(), final_summary, avg_score, session_id),
        )
        self._conn.commit()

    # ---------- turns ----------

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
        self._conn.execute(
            "INSERT INTO turns "
            "(session_id, user_id, node_id, score, on_task, english, affect, ts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                user_id,
                node_id,
                score,
                int(on_task),
                int(english),
                affect,
                time.time(),
            ),
        )
        self._conn.commit()

    async def get_turns(self, session_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT session_id, user_id, node_id, score, on_task, english, affect, ts "
            "FROM turns WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # ---------- mastery ----------

    async def upsert_mastery(
        self,
        user_id: str,
        node_id: str,
        ema: float,
        attempts: int,
        clean_pass: bool = False,
    ) -> None:
        self._conn.execute(
            "INSERT INTO mastery (user_id, node_id, ema, attempts, clean_pass, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, node_id) DO UPDATE SET "
            "ema = excluded.ema, attempts = excluded.attempts, "
            "clean_pass = mastery.clean_pass OR excluded.clean_pass, "
            "updated_at = excluded.updated_at",
            (user_id, node_id, ema, attempts, int(clean_pass), time.time()),
        )
        self._conn.commit()

    async def get_progression(self, user_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT node_id, ema, attempts, clean_pass "
            "FROM mastery WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    async def get_module_passrate(
        self, user_id: str, node_ids: list[str]
    ) -> tuple[int, int]:
        if not node_ids:
            return (0, 0)
        placeholders = ",".join("?" * len(node_ids))
        row = self._conn.execute(
            f"SELECT SUM(clean_pass) AS clean, COUNT(*) AS total FROM mastery "
            f"WHERE user_id = ? AND node_id IN ({placeholders})",
            (user_id, *node_ids),
        ).fetchone()
        if not row or row["total"] is None:
            return (0, 0)
        return (int(row["clean"] or 0), int(row["total"] or 0))

    # ---------- weaknesses (fixed-taxonomy aggregation) ----------

    async def bump_weakness(
        self,
        user_id: str,
        task_type: str,
        skill_id: str,
        score: float,
        raw: str = "",
    ) -> None:
        sid = coerce_skill_id(skill_id)
        self._conn.execute(
            "INSERT INTO weaknesses "
            "(user_id, task_type, skill_id, hit_count, last_score, last_seen, last_raw) "
            "VALUES (?, ?, ?, 1, ?, ?, ?) "
            "ON CONFLICT(user_id, task_type, skill_id) DO UPDATE SET "
            "hit_count = weaknesses.hit_count + 1, "
            "last_score = excluded.last_score, "
            "last_seen = excluded.last_seen, "
            "last_raw = excluded.last_raw",
            (user_id, task_type, sid, score, time.time(), raw),
        )
        self._conn.commit()

    async def get_weaknesses(
        self, user_id: str, task_type: str | None = None
    ) -> list[dict]:
        if task_type is None:
            rows = self._conn.execute(
                "SELECT user_id, task_type, skill_id, hit_count, last_score, "
                "last_seen, last_raw FROM weaknesses WHERE user_id = ? "
                "ORDER BY hit_count DESC, last_seen DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT user_id, task_type, skill_id, hit_count, last_score, "
                "last_seen, last_raw FROM weaknesses WHERE user_id = ? AND task_type = ? "
                "ORDER BY hit_count DESC, last_seen DESC",
                (user_id, task_type),
            ).fetchall()
        return [dict(r) for r in rows]

    # ---------- memory (recency, no pgvector) ----------

    async def write_memory(
        self,
        user_id: str,
        session_id: str,
        node_id: str,
        content: str,
        task_type: str = "",
        score: float = 0.0,
    ) -> bool:
        if not content.strip():
            return False
        # Parse the 3-line summary format into structured fields so qwen can
        # reference exact facts ("You scored 0.6 on comm_04 last time") rather
        # than parsing prose.
        parsed: dict[str, str] = {}
        for line in content.splitlines():
            if line.startswith("Strengths:"):
                parsed["strengths"] = line[len("Strengths:"):].strip()
            elif line.startswith("Watch:"):
                parsed["watch"] = line[len("Watch:"):].strip()
            elif line.startswith("Next focus:"):
                parsed["next_focus"] = line[len("Next focus:"):].strip()
        row = {
            "node_id": node_id,
            "score": round(score, 4),
            "strengths": parsed.get("strengths", ""),
            "watch": parsed.get("watch", ""),
            "next_focus": parsed.get("next_focus", ""),
            "date": time.strftime("%Y-%m-%d"),
            "raw": content,
        }
        self._conn.execute(
            "INSERT INTO memory (user_id, session_id, task_type, node_id, content, ts) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, session_id, task_type, node_id, json.dumps(row), time.time()),
        )
        self._conn.commit()
        return True

    async def load_context(self, user_id: str, task_type: str, k: int = 3) -> list[dict]:
        """Most recent k session memory rows for this user+task_type, newest-first.

        Returns structured dicts with keys: node_id, score, strengths, watch,
        next_focus, date, raw. Legacy plain-text rows are wrapped in a raw-only
        dict so callers always get a list[dict]."""
        rows = self._conn.execute(
            "SELECT content, node_id FROM memory WHERE user_id = ? AND task_type = ? "
            "ORDER BY ts DESC LIMIT ?",
            (user_id, task_type, k),
        ).fetchall()
        result = []
        for r in rows:
            try:
                parsed = json.loads(r["content"])
                if isinstance(parsed, dict):
                    result.append(parsed)
                    continue
            except (json.JSONDecodeError, TypeError):
                pass
            # Legacy plain-text row
            result.append({"node_id": r["node_id"] or "", "score": 0.0,
                            "strengths": "", "watch": "", "next_focus": "",
                            "date": "", "raw": r["content"]})
        return result

    # ---------- test-item cache (Phase 4 Layer B precache) ----------

    async def cache_test_items(
        self,
        user_id: str,
        task_type: str,
        items: list[dict],
        ts: float | None = None,
    ) -> None:
        """Store the precomputed probe bank for a TEST task type (overwrites)."""
        self._conn.execute(
            "INSERT INTO test_items (user_id, task_type, items, cached_at) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, task_type) DO UPDATE SET "
            "items = excluded.items, cached_at = excluded.cached_at",
            (user_id, task_type, json.dumps(items), ts if ts is not None else time.time()),
        )
        self._conn.commit()

    async def get_cached_test_items(
        self, user_id: str, task_type: str, max_age: float | None = None
    ) -> list[dict] | None:
        """Return the cached probe bank, or None on miss / stale (older than max_age)."""
        row = self._conn.execute(
            "SELECT items, cached_at FROM test_items "
            "WHERE user_id = ? AND task_type = ?",
            (user_id, task_type),
        ).fetchone()
        if not row:
            return None
        if max_age is not None and (time.time() - row["cached_at"]) > max_age:
            return None
        return json.loads(row["items"])
