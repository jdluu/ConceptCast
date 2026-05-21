import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

sys.path.append(str(Path(__file__).parent.parent))
from infra.models.job import JobRecord
from infra.settings import get_settings


async def nuke_db() -> None:
    settings = get_settings()
    db_url = settings.database_url
    if db_url.startswith("sqlite://"):
        db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        await session.execute(delete(JobRecord))
        await session.commit()
    print("Database nuked.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(nuke_db())
