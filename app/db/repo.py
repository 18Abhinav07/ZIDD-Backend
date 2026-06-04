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

async def ensure_profile(session: AsyncSession, user_id: str) -> None:
    await session.execute(
        text(
            """
            INSERT INTO learner_profiles (user_id)
            VALUES (:uid)
            ON CONFLICT (user_id) DO NOTHING
            """
        ),
        {"uid": user_id},
    )
    await session.commit()


async def get_profile(session: AsyncSession, user_id: str) -> dict | None:
    result = await session.execute(
        text(
            "SELECT user_id, credits, demo_unlimited "
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
    if profile["credits"] < amount:
        return False
    await session.execute(
        text(
            "UPDATE learner_profiles SET credits = credits - :amt "
            "WHERE user_id = :uid"
        ),
        {"amt": amount, "uid": user_id},
    )
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
