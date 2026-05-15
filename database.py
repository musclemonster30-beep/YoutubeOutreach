import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

def _build_url() -> str:
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Render Dashboard → Postgres service → Connect → "
            "copy Internal Database URL → paste into Web Service Environment tab."
        )
    if raw.startswith("postgres://"):
        raw = raw.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw.startswith("postgresql://") and "+asyncpg" not in raw:
        raw = raw.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw

DATABASE_URL = _build_url()

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
