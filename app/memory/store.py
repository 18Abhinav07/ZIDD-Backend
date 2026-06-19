"""pgvector memory store — write session summaries, retrieve relevant context.

Everything here degrades to a no-op/empty string if embeddings are off or the
table is missing, so the engine runs identically with or without memory. The
memory_entries table stores text + a 768-dim vector only — never raw audio.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.embed import embed

# Cosine distance (<=>) over pgvector; lower = closer. No IVFFlat index until
# >10K rows (architecture-v3 §408) — exact scan is fine at launch scale.
# Return competency_node alongside content so the caller can match a summary to a
# specific node (the 'welcome back' recap). We deliberately do NOT filter on an
# exact competency_node here: writes store the FINE node (e.g. int_05_why_this_role)
# while PgStore.load_context queries with the COARSE task_type (interview_prep), so
# an equality filter matched zero rows and silently returned nothing. We rank the
# user's summaries by embedding distance to a task-biased query instead, and let
# the caller pick the row whose node matches.
_SEARCH_SQL = text(
    """
    SELECT competency_node, content
    FROM memory_entries
    WHERE user_id = :user_id
    ORDER BY embedding <=> CAST(:qvec AS vector)
    LIMIT :k
    """
)

_INSERT_SQL = text(
    """
    INSERT INTO memory_entries (user_id, session_id, competency_node, content, embedding)
    VALUES (:user_id, :session_id, :node, :content, CAST(:vec AS vector))
    """
)


async def write_memory(
    session: AsyncSession,
    user_id: str,
    session_id: str,
    node_id: str,
    content: str,
) -> bool:
    """Persist a session summary with its embedding. Returns False if skipped."""
    if not content.strip():
        return False
    vec = await embed(content)
    if vec is None:
        return False
    try:
        await session.execute(
            _INSERT_SQL,
            {
                "user_id": user_id,
                "session_id": session_id,
                "node": node_id,
                "content": content,
                "vec": str(vec),
            },
        )
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        return False


async def load_context(
    session: AsyncSession, user_id: str, node_id: str, k: int = 3
) -> list[dict]:
    """Retrieve the k most relevant past summaries, each tagged with its node.

    Returns a list of {"node_id", "content"} dicts (newest/most-relevant first),
    or [] on any failure (no embeddings, no table, cold start) — the tutor simply
    runs without memory rather than erroring.

    `node_id` is the COARSE retrieval key (PgStore passes the task_type) used only
    to BIAS the semantic query; each returned row carries its TRUE competency_node
    so the caller can match a summary to a specific node (the welcome-back recap).
    """
    qvec = await embed(f"{node_id} progress and recurring issues")
    if qvec is None:
        return []
    try:
        result = await session.execute(
            _SEARCH_SQL,
            {"user_id": user_id, "qvec": str(qvec), "k": k},
        )
        rows = result.all()
    except Exception:
        return []
    return [{"node_id": r[0], "content": r[1]} for r in rows]
