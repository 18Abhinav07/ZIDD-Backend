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
_SEARCH_SQL = text(
    """
    SELECT m.session_id, m.competency_node AS node_id, m.content,
           s.task_type, s.module_id
    FROM memory_entries AS m
    LEFT JOIN sessions AS s ON s.session_id = m.session_id
    WHERE m.user_id = :user_id
    ORDER BY m.embedding <=> CAST(:qvec AS vector)
    LIMIT :k
    """
)

_CAREER_SEARCH_SQL = text(
    """
    SELECT m.session_id, m.competency_node AS node_id, m.content,
           s.task_type, s.module_id
    FROM memory_entries AS m
    LEFT JOIN sessions AS s ON s.session_id = m.session_id
    WHERE m.user_id = :user_id
      AND (
        s.task_type = :task_type
        OR (
          s.task_type IS NULL
          AND :legacy_prefix <> ''
          AND m.competency_node LIKE :legacy_prefix ESCAPE '\\'
        )
      )
    ORDER BY CASE WHEN s.task_type = :task_type THEN 0 ELSE 1 END,
             m.embedding <=> CAST(:qvec AS vector)
    LIMIT :k
    """
)

_CAREER_TASK_TYPES = {"interview_prep", "interview_test", "gd_prep", "gd_test"}
_LEGACY_PREP_PREFIX = {"interview_prep": "int\\_%", "gd_prep": "gd\\_%"}

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

    Career task types are filtered through the durable sessions row. Legacy Career
    memories without a session task type may supplement Prep only by node prefix;
    they never masquerade as exact Test history.
    """
    qvec = await embed(f"{node_id} progress and recurring issues")
    if qvec is None:
        return []
    try:
        params = {"user_id": user_id, "qvec": str(qvec), "k": k}
        statement = _SEARCH_SQL
        if node_id in _CAREER_TASK_TYPES:
            statement = _CAREER_SEARCH_SQL
            params.update({
                "task_type": node_id,
                "legacy_prefix": _LEGACY_PREP_PREFIX.get(node_id, ""),
            })
        result = await session.execute(statement, params)
        rows = result.mappings().all()
    except Exception:
        return []
    return [dict(row) for row in rows]
