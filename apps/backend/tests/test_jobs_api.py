"""Integration tests for the job-related API endpoints.

Covers job creation idempotency, active status retry guards, and preview
state transitions.
"""

from collections.abc import AsyncGenerator, Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from infra.database import get_db
from infra.models.job import JobRecord
from main import app


@pytest.fixture
async def override_db(
    engine: AsyncEngine,
) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Overrides the FastAPI database dependency with the session-scoped engine.

    Args:
        engine: The session-scoped AsyncEngine.

    Yields:
        The async session maker for creating db transactions.
    """
    test_session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    app.state.db_session_factory = test_session_factory

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with test_session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _override_get_db
    yield test_session_factory
    app.dependency_overrides.clear()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provides an AsyncClient for hitting API endpoints.

    Yields:
        An instance of httpx.AsyncClient.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest.fixture(autouse=True)
def mock_process_job_logic() -> Generator[None, None, None]:
    """Mocks the background process job logic to keep tests isolated.

    Yields:
        None.
    """
    with (
        patch("api.routes.jobs_crud.process_job_logic", new_callable=AsyncMock) as _,
    ):
        yield


@pytest.mark.asyncio
async def test_create_job_success(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Tests that a job is successfully created when using unique parameters."""
    payload = {
        "topic": "Neural Networks",
    }
    response = await client.post("/jobs/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "Neural Networks"
    assert data["status"] == "planning"

    async with override_db() as db:
        res = await db.execute(
            select(JobRecord).where(JobRecord.job_id == data["job_id"])
        )
        job = res.scalar_one_or_none()
        assert job is not None
        assert job.topic == "Neural Networks"


@pytest.mark.asyncio
async def test_create_job_idempotency(
    client: AsyncClient,
    override_db: async_sessionmaker[AsyncSession],  # noqa: ARG001
) -> None:
    """Verifies that duplicate requests return the same job within 1 hour."""
    payload = {
        "topic": "Bubble Sort",
    }

    # Create first job
    res1 = await client.post("/jobs/create", json=payload)
    assert res1.status_code == 200
    job_1 = res1.json()

    # Request same topic within 1 hour
    res2 = await client.post("/jobs/create", json=payload)
    assert res2.status_code == 200
    job_2 = res2.json()

    assert job_1["job_id"] == job_2["job_id"]


@pytest.mark.asyncio
async def test_create_job_expired_idempotency(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Verifies that duplicates older than 1 hour result in a new job."""
    async with override_db() as db:
        old_job = JobRecord(
            job_id="old-job-123",
            topic="Bubble Sort",
            user_prompt="Bubble Sort",
            status="completed",
            mode="live",
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db.add(old_job)
        await db.commit()

    payload = {
        "topic": "Bubble Sort",
    }
    res = await client.post("/jobs/create", json=payload)
    assert res.status_code == 200
    new_job = res.json()

    assert new_job["job_id"] != "old-job-123"


@pytest.mark.asyncio
async def test_create_job_failed_no_idempotency(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Verifies that a failed job does not trigger idempotency."""
    async with override_db() as db:
        failed_job = JobRecord(
            job_id="failed-job-123",
            topic="Bubble Sort",
            user_prompt="Bubble Sort",
            status="failed",
            mode="live",
            created_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        db.add(failed_job)
        await db.commit()

    payload = {
        "topic": "Bubble Sort",
    }
    res = await client.post("/jobs/create", json=payload)
    assert res.status_code == 200
    new_job = res.json()

    assert new_job["job_id"] != "failed-job-123"


@pytest.mark.asyncio
async def test_retry_job_guards(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Asserts that retry succeeds on failed/paused jobs but fails on others."""
    # 1. Non-existent job
    res = await client.post("/jobs/nonexistent/retry")
    assert res.status_code == 404

    # 2. Running job (planning)
    async with override_db() as db:
        running_job = JobRecord(
            job_id="running-job",
            topic="React Hooks",
            status="planning",
        )
        db.add(running_job)
        await db.commit()

    res = await client.post("/jobs/running-job/retry")
    assert res.status_code == 400

    # 3. Failed job
    async with override_db() as db:
        failed_job = JobRecord(
            job_id="failed-job",
            topic="React Hooks",
            status="failed",
        )
        db.add(failed_job)
        await db.commit()

    res = await client.post("/jobs/failed-job/retry")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "pending_retry"


@pytest.mark.asyncio
async def test_create_job_omits_hitl(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]  # noqa: ARG001
) -> None:
    """HITL removal: creation works without hitl_enabled and never echoes it."""
    res = await client.post(
        "/jobs/create", json={"topic": "Verify Topic"}
    )
    assert res.status_code == 200
    data = res.json()
    assert "hitl_enabled" not in data
    assert data["status"] == "planning"


@pytest.mark.asyncio
async def test_review_endpoint_removed(client: AsyncClient) -> None:
    """HITL removal: the review gate route is gone."""
    res = await client.post("/jobs/whatever/review", json={"action": "approve"})
    assert res.status_code == 404


