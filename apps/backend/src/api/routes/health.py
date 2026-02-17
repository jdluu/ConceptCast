import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from infra.engines.sandbox import local_sandbox
from infra.settings import get_settings
from infra.storage import check_db_health, get_db

router = APIRouter()


@router.get("/", response_model=dict[str, Any])
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Detailed health-check endpoint for production monitoring."""
    settings = get_settings()

    # 1. Database Check
    db_ok = await check_db_health()

    # 2. Manim Engine Check (Local Installation)
    manim_ok = local_sandbox.is_healthy()

    # 3. Storage Check
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
