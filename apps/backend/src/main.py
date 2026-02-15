import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import health, jobs, models
from core.database import AsyncSessionLocal, init_db
from core.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the FastAPI application lifecycle.

    Initializes the asynchronous database connection and stores the session factory
    in the application state for global access (e.g., in background tasks).

    Args:
        app: The FastAPI application instance.
    """
    await init_db()
    # Store session factory in app state for background tasks
    app.state.db_session_factory = AsyncSessionLocal
    yield


app = FastAPI(title="ConceptCast Backend", lifespan=lifespan)

cors_origins = get_settings().cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job Artifact Storage Configuration (PROJECT_ROOT set in Docker to /app)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", _PROJECT_ROOT))
JOBS_ROOT = PROJECT_ROOT / "data" / "jobs"
JOBS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/jobs/artifacts", StaticFiles(directory=str(JOBS_ROOT)), name="job_artifacts"
)

# Include Routers
app.include_router(health.router)
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

_FRONTEND_DIST = os.environ.get("FRONTEND_DIST")
_FRONTEND_DIST_PATH = Path(_FRONTEND_DIST) if _FRONTEND_DIST else None
if _FRONTEND_DIST_PATH and _FRONTEND_DIST_PATH.is_dir():
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """Serve SPA: static file if it exists, else index.html."""
        if full_path and not full_path.startswith(".."):
            candidate = (_FRONTEND_DIST_PATH / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(_FRONTEND_DIST_PATH):
                return FileResponse(candidate)
        return FileResponse(_FRONTEND_DIST_PATH / "index.html")
