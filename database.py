import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

raw_url = os.environ.get("DATABASE_URL")

if not raw_url:
    raise RuntimeError(
        "DATABASE_URL is not set.\n"
        "Fix: Go to Render Dashboard → your Postgres service → Connect → "
        "copy Internal Database URL → paste it as DATABASE_URL in your Web Service Environment tab."
    )

# Render gives postgres:// — asyncpg requires postgresql+asyncpg://
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_url.startswith("postgresql://") and "+asyncpg" not in raw_url:
    raw_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(raw_url, echo=False, pool_pre_ping=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
