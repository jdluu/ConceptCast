import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infra.models.job import JobRecord


@pytest.mark.asyncio
async def test_create_job_record(session: AsyncSession) -> None:
    job = JobRecord(job_id="test-job-1", topic="Testing SQLAlchemy", status="planning")
    session.add(job)
    await session.commit()

    result = await session.execute(
        select(JobRecord).where(JobRecord.job_id == "test-job-1")
    )
    db_job = result.scalar_one()
    assert db_job.topic == "Testing SQLAlchemy"
    assert db_job.status == "planning"
