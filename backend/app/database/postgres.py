"""
PostgreSQL / Tiger Cloud async connection setup.
Uses SQLAlchemy 2.0 async API with asyncpg driver.
"""
import re
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from app.core.config import get_settings

settings = get_settings()

# Create async engine with connection pooling
engine = create_async_engine(
    settings.tiger_database_url,
    pool_size=settings.tiger_pool_size,
    max_overflow=settings.tiger_pool_overflow,
    echo=settings.debug,
    future=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_tiger_schema():
    """
    Run the migration SQL to create all tables, hypertables, and aggregates.
    Safe to call on every startup (idempotent).
    """
    import os
    migration_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "migrations", "001_init.sql"
    )
    with open(migration_path, "r") as f:
        sql = f.read()

    # Smart SQL splitter — handles DO $$ ... END $$ blocks
    statements = []
    current = []
    in_do_block = False

    for line in sql.split('\n'):
        stripped = line.strip()

        if stripped.upper().startswith('DO $$'):
            in_do_block = True
        if stripped == 'END $$;':
            in_do_block = False

        current.append(line)

        if stripped.endswith(';') and not in_do_block:
            statement = '\n'.join(current).strip()
            if statement and not statement.startswith('--'):
                statements.append(statement)
            current = []

    if current:
        statement = '\n'.join(current).strip()
        if statement and not statement.startswith('--'):
            statements.append(statement)

    async with engine.begin() as conn:
        for i, statement in enumerate(statements):
            try:
                await conn.execute(text(statement))
            except Exception as e:
                error_msg = str(e)
                if "already exists" in error_msg.lower() or "duplicate" in error_msg.lower():
                    print(f"  ⚠️  Statement {i+1} skipped (already exists): {statement[:80]}...")
                else:
                    print(f"  ❌ Statement {i+1} failed: {error_msg[:200]}")
                    raise

    print("✅ Tiger schema initialized successfully")


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
    Usage:
        @router.get("/reviews")
        async def list_reviews(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db_connection():
    """Gracefully dispose of the connection pool."""
    await engine.dispose()