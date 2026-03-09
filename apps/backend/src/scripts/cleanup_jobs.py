import shutil
import sys
from pathlib import Path

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(Path(__file__).parent.parent))
from infra.models.job import JobRecord
from infra.settings import get_settings


async def cleanup_job_data() -> None:
    settings = get_settings()
    data_jobs_dir = settings.data_dir / "jobs"
    legacy_artifacts_dir = data_jobs_dir / "artifacts"

    # 1. Gather all job IDs from database
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # type: ignore
    )

    async with async_session() as session:
        result = await session.execute(select(JobRecord.job_id))
        valid_job_ids = {row[0] for row in result.all()}

    logger.info(f"Found {len(valid_job_ids)} valid jobs in database.")

    # 2. Cleanup legacy artifacts folder if it exists
    if legacy_artifacts_dir.exists():
        logger.info("Checking legacy 'artifacts' subdirectory...")
        for folder in legacy_artifacts_dir.iterdir():
            if not folder.is_dir():
                continue

            job_id = folder.name
            if job_id in valid_job_ids:
                # Migrate to standard location if possible
                target = data_jobs_dir / job_id
                if not target.exists():
                    logger.info(
                        f"Migrating active job {job_id} from legacy artifacts folder..."
                    )
                    shutil.move(str(folder), str(target))
                else:
                    logger.warning(
                        f"Both legacy and standard folders exist for {job_id}. "
                        "Deleting legacy."
                    )
                    shutil.rmtree(folder)
            else:
                logger.info(f"Removing ghost job artifact folder: {job_id}")
                shutil.rmtree(folder)

        # Remove empty artifacts folder
        if not any(legacy_artifacts_dir.iterdir()):
            legacy_artifacts_dir.rmdir()
            logger.info("Removed empty legacy artifacts folder.")

    # 3. Cleanup data/jobs/ root
    for folder in data_jobs_dir.iterdir():
        if not folder.is_dir() or folder.name == "artifacts":
            continue

        job_id = folder.name
        if job_id not in valid_job_ids:
            # Special case for 'test-job-123' and others seen in screenshot
            logger.info(f"Removing ghost job folder: {job_id}")
            shutil.rmtree(folder)

    await engine.dispose()
    logger.success("Job data cleanup complete.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(cleanup_job_data())
