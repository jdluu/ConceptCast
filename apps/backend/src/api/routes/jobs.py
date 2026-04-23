"""Composite router for all job-related API endpoints.

Assembles the CRUD, SSE event streaming, and review sub-routers into a single
router mounted by the application under the ``/jobs`` prefix.
"""

from fastapi import APIRouter

from api.routes.jobs_crud import router as crud_router
from api.routes.jobs_events import router as events_router
from api.routes.jobs_review import router as review_router

router = APIRouter()

router.include_router(crud_router)
router.include_router(events_router)
router.include_router(review_router)
