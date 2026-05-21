"""Integration tests for the job-related API endpoints.

Covers job creation idempotency, active status retry guards, and HITL review
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
        patch("api.routes.jobs_review.process_job_logic", new_callable=AsyncMock) as _,
    ):
        yield


@pytest.mark.asyncio
async def test_create_job_success(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Tests that a job is successfully created when using unique parameters."""
    payload = {
        "topic": "Neural Networks",
        "target_audience": "Undergraduate CS",
        "hitl_enabled": False,
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
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]  # noqa: ARG001
) -> None:
    """Verifies that duplicate requests return the same job within 1 hour."""
    payload = {
        "topic": "Bubble Sort",
        "target_audience": "High School",
        "hitl_enabled": True,
    }

    # Create first job
    res1 = await client.post("/jobs/create", json=payload)
    assert res1.status_code == 200
    job_1 = res1.json()

    # Request same topic/audience within 1 hour
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
            target_audience="High School",
            status="completed",
            mode="live",
            created_at=datetime.now(UTC) - timedelta(hours=2),
        )
        db.add(old_job)
        await db.commit()

    payload = {
        "topic": "Bubble Sort",
        "target_audience": "High School",
        "hitl_enabled": True,
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
            target_audience="High School",
            status="failed",
            mode="live",
            created_at=datetime.now(UTC) - timedelta(minutes=10),
        )
        db.add(failed_job)
        await db.commit()

    payload = {
        "topic": "Bubble Sort",
        "target_audience": "High School",
        "hitl_enabled": True,
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
async def test_review_job_guards_and_approvals(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Asserts that review gates validate state and transition statuses correctly."""
    # 1. Job not in awaiting_review state
    async with override_db() as db:
        running_job = JobRecord(
            job_id="not-awaiting",
            topic="Redux",
            status="planning",
        )
        db.add(running_job)
        await db.commit()

    bad_review_payload = {
        "action": "approve",
        "feedback": "Looks great",
    }
    res = await client.post("/jobs/not-awaiting/review", json=bad_review_payload)
    assert res.status_code == 400

    # 2. Awaiting review job approved with edited plan
    async with override_db() as db:
        paused_job = JobRecord(
            job_id="awaiting-job",
            topic="Redux",
            status="awaiting_review",
            plan={"concept_title": "Redux", "teaching_steps": []},
            storyboard={"scenes": []},
        )
        db.add(paused_job)
        await db.commit()

    edited_plan = {
        "concept_title": "Redux Explained Simply",
        "target_audience": "Undergraduate CS",
        "teaching_steps": [
            {
                "step_id": 1,
                "concept": "Store",
                "visual_metaphor": "A secure bank vault",
                "narration": "Store is the global state holder.",
                "estimated_duration": 10.0,
            }
        ],
    }
    approve_payload: dict[str, object] = {
        "action": "approve",
        "edited_plan": edited_plan,
    }
    res = await client.post("/jobs/awaiting-job/review", json=approve_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "architecting"
    assert data["current_step"] == "planning_complete"

    async with override_db() as db:
        db_res = await db.execute(
            select(JobRecord).where(JobRecord.job_id == "awaiting-job")
        )
        job = db_res.scalar_one()
        assert job.plan is not None
        assert job.plan["concept_title"] == "Redux Explained Simply"
        # Downstream storyboard must be invalidated (None)
        assert job.storyboard is None


@pytest.mark.asyncio
async def test_review_job_regenerate(
    client: AsyncClient, override_db: async_sessionmaker[AsyncSession]
) -> None:
    """Asserts that choosing regenerate resets plans and returns status to planning."""
    async with override_db() as db:
        paused_job = JobRecord(
            job_id="awaiting-regen",
            topic="Redux",
            status="awaiting_review",
            plan={"concept_title": "Redux", "teaching_steps": []},
            storyboard={"scenes": []},
        )
        db.add(paused_job)
        await db.commit()

    review_payload = {
        "action": "regenerate",
        "feedback": "Needs a better hook",
    }
    res = await client.post("/jobs/awaiting-regen/review", json=review_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "planning"

    async with override_db() as db:
        db_res = await db.execute(
            select(JobRecord).where(JobRecord.job_id == "awaiting-regen")
        )
        job = db_res.scalar_one()
        assert job.plan is None
        assert job.storyboard is None
