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
import threading
import time

from app.content.skills import coerce_skill_id

# Felt-memory recency: a weakness not re-encountered within this window is treated
# as resolved/stale and dropped from the surfaced set, so a single early failure
# can't stay the top assessment probe target forever. A persistent weakness keeps
# getting bumped, so its last_seen stays inside the window and it still surfaces.
_WEAKNESS_RECENCY_SECONDS = 30 * 24 * 60 * 60   # 30 days
# Cap the surfaced set so a long weakness tail can't bloat the prompt / probe seed.
_WEAKNESS_SURFACE_CAP = 5

# School per-skill mastery (Phase B1). School assessment skill tags
# (new_words / comprehension / asking_questions …) do NOT fit the communication/
# interview SkillID taxonomy — coerce_skill_id collapses every one of them to
# OTHER — so school skills get a DEDICATED, deterministic per-skill mastery EMA,
# folded from exact-graded assessment results. Recency-weighted and BIDIRECTIONAL:
# the EMA rises when a learner later passes a skill they once missed, unlike the
# increment-only weakness counter that only ever ages out by the clock.
_SCHOOL_MASTERY_ALPHA = 0.5    # assessments are strong, infrequent signals
_SCHOOL_PASS_MARK = 0.6        # a per-skill ratio below this is "weak"
_SCHOOL_WEAK_SURFACE_CAP = 5   # weakest-N surfaced to the live tutor
# Spaced review: a skill mastered (EMA >= this) but not practised within the
# staleness window is "due" for a quick refresher so it isn't lost to forgetting.
_SCHOOL_MASTERED_THRESHOLD = 0.8
_SCHOOL_REVIEW_STALE_SECONDS = 5 * 24 * 60 * 60   # 5 days

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
    user_id        TEXT,
    node_id        TEXT,
    ema            REAL,
    attempts       INTEGER,
    clean_pass     INTEGER DEFAULT 0,
    node_completed INTEGER DEFAULT 0,
    updated_at     REAL,
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
CREATE TABLE IF NOT EXISTS school_skill_mastery (
    user_id   TEXT,
    skill     TEXT,
    ema       REAL,
    attempts  INTEGER DEFAULT 0,
    last_seen REAL,
    PRIMARY KEY (user_id, skill)
);
CREATE TABLE IF NOT EXISTS school_results (
    user_id     TEXT,
    test_id     TEXT,
    class_no    INTEGER,
    kind        TEXT,
    score       REAL,
    passed      INTEGER DEFAULT 0,
    by_skill    TEXT DEFAULT '[]',
    weak_skills TEXT DEFAULT '[]',
    updated_at  REAL,
    PRIMARY KEY (user_id, test_id)
);
"""


class LocalStore:
    def __init__(self, db_path: str = ".zidd_local.db") -> None:
        self.db_path = db_path
        # Serializes the money-path write transactions (grant / deduct /
        # charge_and_unlock / mark_paid_and_grant) over the single shared
        # connection so one writer's rollback() can never discard another's
        # uncommitted write. A threading.Lock (NOT asyncio.Lock): the connection
        # is check_same_thread=False, so FastAPI's threadpool can touch it from
        # several OS threads, and asyncio primitives are not thread-safe AND bind
        # to one event loop. The guarded critical sections are pure synchronous
        # sqlite (no awaits), so a plain threading.Lock is both correct and
        # loop-independent. Acquired only AFTER any is_demo() read inside those
        # methods, so it is never re-entered (no deadlock).
        self._lock = threading.Lock()
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
            "ALTER TABLE mastery ADD COLUMN node_completed INTEGER DEFAULT 0",
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

    async def ping_writable(self) -> bool:
        """True iff the active SQLite file accepts a write right now.

        A REAL write probe (the /health field is named *writable*, not merely
        *reachable*): round-trip PRAGMA user_version — read the current value and
        write it straight back. That dirties and commits the DB header page
        without touching any schema or row; a read-only file raises on commit ->
        False. Held under the money-write lock so it never interleaves with a
        grant/charge transaction on the shared connection.
        """
        with self._lock:
            try:
                cur = self._conn.execute("PRAGMA user_version")
                version = int(cur.fetchone()[0])
                self._conn.execute(f"PRAGMA user_version = {version}")
                self._conn.commit()
                return True
            except Exception:
                return False

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
        with self._lock:
            cur = self._conn.execute(
                "UPDATE profiles SET credits = credits + ? WHERE user_id = ?",
                (amount, user_id),
            )
            if cur.rowcount == 0:              # no such profile: fail loud, never log a phantom grant
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
        with self._lock:
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

    async def charge_and_unlock(
        self,
        user_id: str,
        amount: int,
        reason: str,
        scope: str,
        ref_id: str,
    ) -> bool:
        """Deduct credits AND record an ACCESS unlock in ONE transaction.

        Atomic combination of deduct_credits + add_unlock so a learner can never
        pay (credits gone) without the unlock being recorded, nor get an unlock
        without paying. If the unlock insert raises, the whole transaction rolls
        back and credits are NOT deducted. Mirrors deduct_credits semantics: the
        is_demo bypass returns True without charging, and the atomic balance
        guard (credits >= amount) returns False on insufficient funds without
        touching the row.
        """
        if await self.is_demo(user_id):       # Judge/demo bypass: never charged, always allowed.
            return True
        if amount < 0:
            raise ValueError("deduct amount must be non-negative")
        with self._lock:
            try:
                # Insert the unlock FIRST and let ON CONFLICT arbitrate idempotency:
                # an already-owned (user, scope, ref) inserts 0 rows. Only a FRESH
                # unlock (rowcount == 1) is charged. A repeat (rowcount == 0) — e.g. a
                # concurrent double-start where both requests passed the gate's
                # not-owned check before either committed — returns True WITHOUT a
                # second debit, so the learner pays exactly once per unlock. This
                # closes the check-then-charge TOCTOU race at the store level rather
                # than trusting the gate's has_unlock read to be race-free.
                unlock_cur = self._conn.execute(
                    "INSERT INTO content_unlocks "
                    "(user_id, scope, ref_id, credits_spent, created) "
                    "VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(user_id, scope, ref_id) DO NOTHING",
                    (user_id, scope, ref_id, amount, time.time()),
                )
                if unlock_cur.rowcount == 0:
                    # Already owned: discard the no-op insert and do not charge again.
                    self._conn.rollback()
                    return True
                # Fresh unlock — now debit atomically. The balance check folds into
                # the WHERE clause so check and debit are a single statement.
                # rowcount == 0 => insufficient funds: roll back the unlock too.
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
            except Exception:
                # Any failure mid-transaction (e.g. the unlock insert) rolls back the
                # whole unit: credits are NOT deducted and no ledger/unlock row lands.
                self._conn.rollback()
                raise

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
        # Count STARTED sessions (FIX #4). An attempt is consumed the moment a
        # session is started — the production frontend never calls /session/end
        # (and TEST-mode sims record no per-turn rows), so `ended` is NULL for
        # essentially every real attempt. Filtering on `ended IS NOT NULL` made
        # this count permanently 0, silently bypassing the interview/GD ATTEMPT
        # meter forever. The gate counts BEFORE start_session inserts the current
        # session's row, so counting started rows yields exactly FREE_ATTEMPTS
        # free (1st sees 0, 2nd sees 1) then meters — no over-count.
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
        with self._lock:
            cur = self._conn.execute(
                "UPDATE purchases SET status = 'paid' "
                "WHERE order_id = ? AND status != 'paid'",
                (order_id,),
            )
            self._conn.commit()
            return cur.rowcount > 0

    async def mark_paid_and_grant(
        self, order_id: str, user_id: str, credits: int, reason: str
    ) -> bool:
        """Latch a purchase to 'paid' AND grant its credits in ONE transaction.

        Folds the idempotency latch and the credit grant into a single committed
        unit. The old two-step (mark_purchase_paid in one transaction, then
        grant_credits in another) had a fatal hole: a crash/error BETWEEN them
        left the order permanently 'paid' while credits were never granted — and
        Razorpay's retry then hit `WHERE status != 'paid'` → 0 rows → grant
        skipped forever (customer paid, no credits). Here either both land or
        neither does.

        Returns True only on the FIRST captured webhook for this order (credits
        granted exactly once); False on a retry where it is already paid (no
        double grant). Rolls the whole unit back and raises KeyError if the
        buyer's profile is missing, leaving the order UNPAID so a later retry or
        reconciliation can still grant.
        """
        if credits < 0:
            raise ValueError("grant amount must be non-negative")
        with self._lock:
            try:
                latch = self._conn.execute(
                    "UPDATE purchases SET status = 'paid' "
                    "WHERE order_id = ? AND status != 'paid'",
                    (order_id,),
                )
                if latch.rowcount == 0:
                    # Already paid (idempotent retry) — nothing to grant.
                    self._conn.rollback()
                    return False
                grant = self._conn.execute(
                    "UPDATE profiles SET credits = credits + ? WHERE user_id = ?",
                    (credits, user_id),
                )
                if grant.rowcount == 0:
                    # No such profile: undo the latch too so the grant is not lost.
                    self._conn.rollback()
                    raise KeyError(user_id)
                self._conn.execute(
                    "INSERT INTO credit_transactions (user_id, delta, reason, created) "
                    "VALUES (?, ?, ?, ?)",
                    (user_id, credits, reason, time.time()),
                )
                self._conn.commit()
                return True
            except Exception:
                self._conn.rollback()
                raise

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
        node_completed: bool = False,
    ) -> None:
        self._conn.execute(
            "INSERT INTO mastery (user_id, node_id, ema, attempts, clean_pass, node_completed, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, node_id) DO UPDATE SET "
            "ema = excluded.ema, attempts = excluded.attempts, "
            "clean_pass = mastery.clean_pass OR excluded.clean_pass, "
            "node_completed = mastery.node_completed OR excluded.node_completed, "
            "updated_at = excluded.updated_at",
            (user_id, node_id, ema, attempts, int(clean_pass), int(node_completed), time.time()),
        )
        self._conn.commit()

    async def get_last_active_node(self, user_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT node_id FROM mastery WHERE user_id = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
        return row["node_id"] if row else None

    async def get_progression(self, user_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT node_id, ema, attempts, clean_pass, node_completed "
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

    # ---------- school progress + per-skill mastery (assessment-driven) ----------

    async def record_assessment_result(
        self,
        user_id: str,
        test_id: str,
        class_no: int,
        kind: str,
        score: float,
        passed: bool,
        by_skill: list[dict],
    ) -> None:
        """Persist one chapter-test / milestone result and fold its per-skill
        ratios into a recency-weighted per-skill mastery EMA.

        `by_skill` is score_assessment's breakdown: [{"skill", "correct",
        "total"}, …]. Storing the result makes school progress durable (it
        survives a localStorage clear); the EMA gives the live 'Learn' tutor an
        honest, bidirectional read of each skill. UPSERTs on (user_id, test_id)
        so re-taking a test updates rather than duplicates. Multi-statement, so
        held under the write lock — a concurrent money-write commit on the shared
        connection must not flush a partial result+mastery state."""
        now = time.time()
        weak = sorted(
            s["skill"] for s in by_skill
            if int(s.get("total") or 0) and
            int(s.get("correct") or 0) / int(s["total"]) < _SCHOOL_PASS_MARK
        )
        with self._lock:
            self._conn.execute(
                "INSERT INTO school_results "
                "(user_id, test_id, class_no, kind, score, passed, by_skill, "
                "weak_skills, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(user_id, test_id) DO UPDATE SET "
                "class_no=excluded.class_no, kind=excluded.kind, "
                "score=excluded.score, passed=excluded.passed, "
                "by_skill=excluded.by_skill, weak_skills=excluded.weak_skills, "
                "updated_at=excluded.updated_at",
                (user_id, test_id, int(class_no), kind, float(score),
                 int(bool(passed)), json.dumps(by_skill), json.dumps(weak), now),
            )
            for s in by_skill:
                total = int(s.get("total") or 0)
                if total <= 0:
                    continue
                ratio = max(0.0, min(1.0, int(s.get("correct") or 0) / total))
                prev = self._conn.execute(
                    "SELECT ema, attempts FROM school_skill_mastery "
                    "WHERE user_id=? AND skill=?",
                    (user_id, s["skill"]),
                ).fetchone()
                if prev is None:
                    ema, attempts = ratio, 1
                else:
                    old = float(prev["ema"])
                    ema = old + (ratio - old) * _SCHOOL_MASTERY_ALPHA
                    attempts = int(prev["attempts"]) + 1
                self._conn.execute(
                    "INSERT INTO school_skill_mastery "
                    "(user_id, skill, ema, attempts, last_seen) VALUES (?, ?, ?, ?, ?) "
                    "ON CONFLICT(user_id, skill) DO UPDATE SET "
                    "ema=excluded.ema, attempts=excluded.attempts, "
                    "last_seen=excluded.last_seen",
                    (user_id, s["skill"], ema, attempts, now),
                )
            self._conn.commit()

    async def get_school_skill_mastery(self, user_id: str) -> list[dict]:
        """Per-skill mastery EMA for a learner, weakest-first."""
        rows = self._conn.execute(
            "SELECT skill, ema, attempts, last_seen FROM school_skill_mastery "
            "WHERE user_id=? ORDER BY ema ASC, attempts DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    async def get_school_weak_skills(
        self, user_id: str, threshold: float = _SCHOOL_PASS_MARK,
        limit: int = _SCHOOL_WEAK_SURFACE_CAP,
    ) -> list[str]:
        """The skills a learner is weakest at (EMA below threshold), weakest-first.

        Feeds the live 'Learn' coaching session so a school chapter is tutored
        against the learner's REAL weak spots from their test history, not blind."""
        rows = self._conn.execute(
            "SELECT skill FROM school_skill_mastery WHERE user_id=? AND ema < ? "
            "ORDER BY ema ASC, attempts DESC LIMIT ?",
            (user_id, threshold, limit),
        ).fetchall()
        return [r["skill"] for r in rows]

    async def get_school_results(
        self, user_id: str, class_no: int | None = None
    ) -> list[dict]:
        """Stored assessment results (durable progress / report card)."""
        if class_no is None:
            rows = self._conn.execute(
                "SELECT test_id, class_no, kind, score, passed, by_skill, "
                "weak_skills, updated_at FROM school_results WHERE user_id=? "
                "ORDER BY updated_at",
                (user_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT test_id, class_no, kind, score, passed, by_skill, "
                "weak_skills, updated_at FROM school_results "
                "WHERE user_id=? AND class_no=? ORDER BY updated_at",
                (user_id, int(class_no)),
            ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["passed"] = bool(d["passed"])
            d["by_skill"] = json.loads(d["by_skill"] or "[]")
            d["weak_skills"] = json.loads(d["weak_skills"] or "[]")
            out.append(d)
        return out

    async def get_school_review_skills(
        self, user_id: str,
        mastered_threshold: float = _SCHOOL_MASTERED_THRESHOLD,
        stale_seconds: float = _SCHOOL_REVIEW_STALE_SECONDS,
        limit: int = 3,
    ) -> list[str]:
        """Skills the learner MASTERED earlier (EMA >= threshold) but hasn't
        practised within the staleness window — due for a spaced refresher so a
        mastered skill isn't quietly lost to forgetting. Oldest-practised first.

        This is the longitudinal half of learning tracking: weak skills get
        targeted by get_school_weak_skills; strong-but-stale skills get re-checked
        by this, so the tutor fights forgetting instead of only chasing failures."""
        cutoff = time.time() - stale_seconds
        rows = self._conn.execute(
            "SELECT skill FROM school_skill_mastery WHERE user_id=? AND ema >= ? "
            "AND last_seen < ? ORDER BY last_seen ASC LIMIT ?",
            (user_id, mastered_threshold, cutoff, limit),
        ).fetchall()
        return [r["skill"] for r in rows]

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
        # Felt-memory recency + cap: only surface weaknesses re-encountered within
        # the window, capped to the strongest few. A single early failure that the
        # learner has since mastered (its last_seen falls behind the window) ages
        # out, so it can no longer dominate the prompt or be the top assessment
        # probe target forever. A genuinely persistent weakness keeps getting
        # bumped, so its last_seen stays recent and it still surfaces.
        cutoff = time.time() - _WEAKNESS_RECENCY_SECONDS
        if task_type is None:
            rows = self._conn.execute(
                "SELECT user_id, task_type, skill_id, hit_count, last_score, "
                "last_seen, last_raw FROM weaknesses WHERE user_id = ? AND last_seen >= ? "
                "ORDER BY hit_count DESC, last_seen DESC LIMIT ?",
                (user_id, cutoff, _WEAKNESS_SURFACE_CAP),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT user_id, task_type, skill_id, hit_count, last_score, "
                "last_seen, last_raw FROM weaknesses WHERE user_id = ? AND task_type = ? "
                "AND last_seen >= ? ORDER BY hit_count DESC, last_seen DESC LIMIT ?",
                (user_id, task_type, cutoff, _WEAKNESS_SURFACE_CAP),
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
