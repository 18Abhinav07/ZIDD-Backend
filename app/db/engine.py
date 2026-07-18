"""Async SQLAlchemy engine for Supabase transaction pooler.

CRITICAL constraints:
  - Port 6543 (transaction pooler) only. Never direct :5432.
  - Keep the client pool small and bounded. We reuse a few TLS/auth connections
    to the pooler so hot auth requests do not spend seconds reconnecting, while
    still leaving server-side pooling to Supabase.
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

from app.config import get_settings

_engine: AsyncEngine | None = None
_migration_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker | None = None


def _create_engine(
    database_url: str,
    *,
    pool_size: int,
    max_overflow: int = 0,
) -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=settings.effective_db_pool_pre_ping,
        pool_recycle=1800,
        connect_args={
            "ssl": "require",
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
        },
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = _create_engine(
            settings.async_database_url,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
        )
    return _engine


def get_migration_engine() -> AsyncEngine:
    """Dedicated direct-connection engine for schema migrations."""

    global _migration_engine
    if _migration_engine is None:
        _migration_engine = _create_engine(
            get_settings().migration_async_database_url,
            pool_size=1,
        )
    return _migration_engine


def get_sessionmaker() -> async_sessionmaker:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker
