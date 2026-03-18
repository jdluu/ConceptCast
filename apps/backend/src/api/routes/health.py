"""API endpoints for system health monitoring and diagnostic checks.

Verifies the operational status of the database, Manim engine, and storage
subsystems.
"""

import os
from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from infra.database import check_db_health, get_db
from infra.engines.sandbox import local_sandbox
from infra.settings import get_settings

router = APIRouter()


@router.get("/health", response_model=dict[str, Any])
async def health_check(
    response: Response,
    _db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, Any]:
    """Retrieves the health status of the application and its core services.

    Checks the connectivity of the database, the availability of the Manim engine,
    and the writability of the storage directory.

    Args:
        response: The FastAPI response object to modify the status code.
        db: The database session dependency.

    Returns:
        A dictionary containing the overall status and individual service statuses.
    """
    settings = get_settings()

    db_ok = await check_db_health()
    manim_ok = local_sandbox.is_healthy()

    storage_path = Path(settings.jobs_dir)
    storage_ok = os.access(storage_path, os.W_OK) if storage_path.exists() else True

    is_healthy = db_ok and manim_ok and storage_ok

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "services": {
            "database": "connected" if db_ok else "disconnected",
            "manim_engine": "available" if manim_ok else "unavailable",
            "storage": "writable" if storage_ok else "readonly",
        },
    }
