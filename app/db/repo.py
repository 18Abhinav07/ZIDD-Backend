"""Persistence repository — thin async SQL over the 5 tables.

Pure data access: no pedagogy, no AI. The service layer owns flow; this owns
rows. Every function takes an AsyncSession so the caller controls the txn
boundary. All writes are best-effort under the same degrade-gracefully rule:
the engine must run even if Postgres is unreachable (dev/offline), so the
service wraps these in try/except and continues on failure.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# ---------- profiles ----------

async def ensure_profile(session: AsyncSession, user_id: str, name: str = "", password_hash: str | None = None) -> None:
    await session.execute(
        text(
            """
            INSERT INTO learner_profiles (user_id, display_name, password_hash)
            VALUES (:uid, :name, :phash)
            ON CONFLICT (user_id) DO UPDATE SET
            display_name = CASE WHEN excluded.display_name != '' THEN excluded.display_name ELSE learner_profiles.display_name END,
            password_hash = CASE WHEN excluded.password_hash IS NOT NULL THEN excluded.password_hash ELSE learner_profiles.password_hash END
            """
        ),
        {"uid": user_id, "name": name, "phash": password_hash},
    )
    await session.commit()


async def get_profile(session: AsyncSession, user_id: str) -> dict | None:
    result = await session.execute(
        text(
            "SELECT user_id, credits, demo_unlimited, password_hash, display_name as name "
            "FROM learner_profiles WHERE user_id = :uid"
        ),
        {"uid": user_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def deduct_credit(
    session: AsyncSession, user_id: str, amount: int, reason: str
) -> bool:
    """Spend `amount` credits. Returns True if allowed/charged.

    Judge/demo bypass (architecture-v3 §621): demo_unlimited profiles are
    NEVER charged and ALWAYS allowed — zero paywalls for XPRIZE judges.
    """
    profile = await get_profile(session, user_id)
    if profile is None:
        return False
    if profile["demo_unlimited"]:
        return True
    # Atomic spend: the balance check and the decrement are a single guarded
    # UPDATE (`credits >= :amt`). A Python-side read-then-write (TOCTOU) lets two
    # concurrent spends both pass the check and both subtract — double-spend. The
    # WHERE guard makes the row engine arbitrate: at most one wins, and
    # rowcount == 0 means insufficient funds at write time.
    result = await session.execute(
        text(
            "UPDATE learner_profiles SET credits = credits - :amt "
            "WHERE user_id = :uid AND credits >= :amt"
        ),
        {"amt": amount, "uid": user_id},
    )
    if result.rowcount == 0:
        return False
    await session.execute(
        text(
            "INSERT INTO credit_transactions (user_id, delta, reason) "
            "VALUES (:uid, :delta, :reason)"
        ),
        {"uid": user_id, "delta": -amount, "reason": reason},
    )
    await session.commit()
    return True


# ---------- sessions ----------

async def create_session(
    session: AsyncSession, session_id: str, user_id: str, node_id: str
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO sessions (session_id, user_id, competency_node)
            VALUES (:sid, :uid, :node)
            ON CONFLICT (session_id) DO NOTHING
            """
        ),
        {"sid": session_id, "uid": user_id, "node": node_id},
    )
    await session.commit()


async def end_session(
    session: AsyncSession,
    session_id: str,
    turn_count: int,
    final_mastery: float,
    summary: str,
) -> None:
    await session.execute(
        text(
            """
            UPDATE sessions
            SET ended_at = now(), turn_count = :tc,
                final_mastery = :fm, summary = :sm
            WHERE session_id = :sid
            """
        ),
        {"sid": session_id, "tc": turn_count, "fm": final_mastery, "sm": summary},
    )
    await session.commit()


# ---------- competency mastery ----------

async def upsert_mastery(
    session: AsyncSession,
    user_id: str,
    node_id: str,
    mastery: float,
    attempts: int,
    clean_pass: bool,
) -> None:
    await session.execute(
        text(
            """
            INSERT INTO competency_nodes
                (user_id, competency_node, mastery, attempts, clean_pass, updated_at)
            VALUES (:uid, :node, :m, :a, :cp, now())
            ON CONFLICT (user_id, competency_node) DO UPDATE
            SET mastery = EXCLUDED.mastery,
                attempts = EXCLUDED.attempts,
                clean_pass = competency_nodes.clean_pass OR EXCLUDED.clean_pass,
                updated_at = now()
            """
        ),
        {"uid": user_id, "node": node_id, "m": mastery, "a": attempts, "cp": clean_pass},
    )
    await session.commit()


async def get_progression(session: AsyncSession, user_id: str) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT competency_node as node_id, mastery as ema, attempts, clean_pass
            FROM competency_nodes
            WHERE user_id = :uid
            """
        ),
        {"uid": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_module_passrate(
    session: AsyncSession, user_id: str, node_ids: list[str]
) -> tuple[int, int]:
    """(clean_passes, total_attempted_nodes) for the module's text nodes.

    Pass-rate remediation (architecture-v3): if clean/total < 0.5 the service
    flags the module for a remediation pass.
    """
    result = await session.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE clean_pass) AS clean,
                COUNT(*) AS total
            FROM competency_nodes
            WHERE user_id = :uid AND competency_node = ANY(:nodes)
            """
        ),
        {"uid": user_id, "nodes": node_ids},
    )
    row = result.mappings().first()
    if not row:
        return (0, 0)
    return (int(row["clean"] or 0), int(row["total"] or 0))


# ---------- billing: credits ----------

async def get_credits(session: AsyncSession, user_id: str) -> int:
    result = await session.execute(
        text("SELECT credits FROM learner_profiles WHERE user_id = :u"),
        {"u": user_id},
    )
    row = result.mappings().first()
    return int(row["credits"]) if row else 0


async def set_demo_unlimited(
    session: AsyncSession, user_id: str, enabled: bool
) -> None:
    await session.execute(
        text("UPDATE learner_profiles SET demo_unlimited = :e WHERE user_id = :u"),
        {"e": enabled, "u": user_id},
    )
    await session.commit()


async def grant_credits(
    session: AsyncSession, user_id: str, amount: int, reason: str
) -> int:
    await session.execute(
        text(
            "UPDATE learner_profiles SET credits = credits + :amount "
            "WHERE user_id = :u"
        ),
        {"amount": amount, "u": user_id},
    )
    await session.execute(
        text(
            "INSERT INTO credit_transactions (user_id, delta, reason) "
            "VALUES (:u, :delta, :reason)"
        ),
        {"u": user_id, "delta": amount, "reason": reason},
    )
    await session.commit()
    return await get_credits(session, user_id)


# ---------- billing: content unlocks ----------

async def has_unlock(
    session: AsyncSession, user_id: str, scope: str, ref_id: str
) -> bool:
    result = await session.execute(
        text(
            "SELECT 1 FROM content_unlocks "
            "WHERE user_id = :u AND scope = :s AND ref_id = :r"
        ),
        {"u": user_id, "s": scope, "r": ref_id},
    )
    return result.first() is not None


async def add_unlock(
    session: AsyncSession,
    user_id: str,
    scope: str,
    ref_id: str,
    credits_spent: int,
) -> None:
    await session.execute(
        text(
            "INSERT INTO content_unlocks (user_id, scope, ref_id, credits_spent) "
            "VALUES (:u, :s, :r, :c) "
            "ON CONFLICT (user_id, scope, ref_id) DO NOTHING"
        ),
        {"u": user_id, "s": scope, "r": ref_id, "c": credits_spent},
    )
    await session.commit()


async def list_unlocks(session: AsyncSession, user_id: str) -> list[dict]:
    result = await session.execute(
        text(
            "SELECT scope, ref_id, credits_spent FROM content_unlocks "
            "WHERE user_id = :u"
        ),
        {"u": user_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def list_session_nodes(session: AsyncSession, user_id: str) -> list[str]:
    result = await session.execute(
        text("SELECT competency_node FROM sessions WHERE user_id = :u"),
        {"u": user_id},
    )
    return [row[0] for row in result.all()]


# ---------- billing: purchases ----------

async def record_purchase(
    session: AsyncSession,
    order_id: str,
    user_id: str,
    pack_id: str,
    credits: int,
    amount_paise: int,
    status: str = "created",
) -> None:
    await session.execute(
        text(
            "INSERT INTO purchases "
            "(order_id, user_id, pack_id, credits, amount_paise, status) "
            "VALUES (:o, :u, :p, :c, :a, :st) "
            "ON CONFLICT (order_id) DO NOTHING"
        ),
        {
            "o": order_id,
            "u": user_id,
            "p": pack_id,
            "c": credits,
            "a": amount_paise,
            "st": status,
        },
    )
    await session.commit()


async def get_purchase(session: AsyncSession, order_id: str) -> dict | None:
    result = await session.execute(
        text("SELECT * FROM purchases WHERE order_id = :o"),
        {"o": order_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def mark_purchase_paid(session: AsyncSession, order_id: str) -> bool:
    result = await session.execute(
        text(
            "UPDATE purchases SET status = 'paid' "
            "WHERE order_id = :o AND status != 'paid'"
        ),
        {"o": order_id},
    )
    await session.commit()
    return result.rowcount > 0
