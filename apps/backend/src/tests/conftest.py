from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session_factory(test_engine):
    return sessionmaker(
        bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )


@pytest.fixture
async def db_session(test_session_factory) -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest.fixture
async def async_client(
    test_session_factory, db_session
) -> AsyncGenerator[AsyncClient, None]:
    """Creates an AsyncClient with the testing database dependency override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Patch app state AFTER lifespan startup (which might have set it to real DB)
        app.state.db_session_factory = test_session_factory
        yield client
        # Cleanup is automatic when app shuts down or just let it be

    app.dependency_overrides.clear()
