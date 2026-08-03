"""
PostgreSQL / Tiger Cloud async connection setup.
Uses SQLAlchemy 2.0 async API with asyncpg driver.
"""
# pyrefly: ignore [missing-import]
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# pyrefly: ignore [missing-import]
from sqlalchemy import text
from app.core.config import get_settings

settings = get_settings()

# Build SSL connect args for asyncpg if using cloud database
connect_args = {}
if "tigerdb" in settings.tiger_database_url or "neon" in settings.tiger_database_url or "aws" in settings.tiger_database_url:
    connect_args = {"ssl": "require"}

# Create async engine with connection pooling
engine = create_async_engine(
    settings.tiger_database_url,
    pool_size=settings.tiger_pool_size,
    max_overflow=settings.tiger_pool_overflow,
    echo=settings.debug,
    future=True,
    connect_args=connect_args,  # SSL for cloud databases
)

# Async session factory — used as a FastAPI dependency
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
    async with engine.begin() as conn:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                await conn.execute(text(statement))
        print("✅ Tiger schema initialized successfully")


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that yields an async database session.
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