"""Async SQLAlchemy engine for Supabase transaction pooler.

CRITICAL constraints (do not change without reading architecture-v3):
  - Port 6543 (transaction pooler) only. Never direct :5432.
  - NullPool mandatory — transaction pooler manages pooling server-side;
    a client-side pool double-pools and breaks under serverless.
  - statement_cache_size=0 mandatory — asyncpg prepared-statement cache is
    incompatible with the transaction pooler (statements not pinned to a conn).
  - prepared_statement_name_func mandatory — even uncached, asyncpg names every
    prepared statement `__asyncpg_stmt_N__`; pgbouncer reuses a backend conn
    that may already hold that name -> DuplicatePreparedStatementError. Unique
    UUID names per prepare avoid the collision.
"""
from uuid import uuid4

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.async_database_url,
            poolclass=NullPool,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
            },
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker:
    return async_sessionmaker(get_engine(), expire_on_commit=False)
