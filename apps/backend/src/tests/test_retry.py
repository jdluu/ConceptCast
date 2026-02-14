import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import JobRecord
from services.orchestrator import prepare_job_for_retry


@pytest.mark.asyncio
async def test_job_retry_flow(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create a job that is "failed"
    job = JobRecord(
        job_id="failed-job-123",
        topic="Retry Logic",
        target_audience="Devs",
        status="failed",
        mode="mock",
        provider="mock",
        model_id="mock-gpt",
        plan={
            "concept_title": "Retry",
            "target_audience": "Devs",
            "teaching_steps": [],
        },
        error="Something went wrong",
        retry_count=0,
    )
    db_session.add(job)
    await db_session.commit()

    # 3. Verify DB state
    db_session.expire_all()
    await db_session.execute(
        select(JobRecord).where(JobRecord.job_id == "failed-job-123")
    )
    # 2. Call the retry endpoint
    response = await async_client.post(f"/jobs/{job.job_id}/retry")
    assert response.status_code == 200
    data = response.json()

    assert data["job_id"] == "failed-job-123"
    assert (
        data["status"] == "pending_retry"
    )  # Endpoint returns this before background task updates it

    # Let's verify the DB state
    await db_session.refresh(job)

    assert job.retry_count == 1
    assert job.error is None
    # detailed status check might be tricky due to background task race,
    # but initially it should be reset.


@pytest.mark.asyncio
async def test_prepare_job_for_retry_logic(db_session: AsyncSession):
    # Unit test for the service function
    job = JobRecord(
        job_id="retry-unit-test",
        topic="Unit Test",
        status="failed",
        mode="mock",
        retry_count=2,
        manim_code="Bad code",
        video_url="http://bad.url",
        error="Error",
        streamed_thoughts=[{"msg": "old"}],
    )
    db_session.add(job)
    await db_session.commit()

    # Create a session factory mock/wrapper since function expects factory
    async def session_factory():
        return db_session

    # We need a context manager for the factory
    class MockFactory:
        def __call__(self):
            return self

        async def __aenter__(self):
            return db_session

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # prepare_job_for_retry expects a callable that returns an async context manager
    updated_job = await prepare_job_for_retry("retry-unit-test", MockFactory())

    assert updated_job.status == "pending_retry"
    assert updated_job.retry_count == 3
    assert updated_job.manim_code is None
    assert updated_job.video_url is None
    assert updated_job.error is None
    assert updated_job.streamed_thoughts == []
