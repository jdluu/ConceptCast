"""Entry point for the ConceptCast FastAPI application.

Configures middleware, routes, CORS settings, static file serving, and
the application lifespan for database and broker initialization.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.middleware.logging import LoggingMiddleware
from api.routes import ai_models, health, jobs
from infra.database import AsyncSessionLocal, init_db
from infra.logging import configure_logging
from infra.settings import get_settings
from infra.tasks import broker

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages the FastAPI application lifecycle.

    Args:
        app: The FastAPI application instance.
    """
    await init_db()
    if not broker.is_worker_process:
        await broker.startup()

    app.state.db_session_factory = AsyncSessionLocal
    yield

    if not broker.is_worker_process:
        await broker.shutdown()


app = FastAPI(title="ConceptCast Backend", lifespan=lifespan)

settings = get_settings()

# Benchmark v2: when trace dir is configured via settings, export it (plus pins)
# into the process environment so the per-call tracer activates. Env vars take
# precedence if the runner set them explicitly.
if settings.benchmark_trace_dir and not os.environ.get("BENCH_TRACE_DIR"):
    os.environ["BENCH_TRACE_DIR"] = settings.benchmark_trace_dir

cors_origins = settings.cors_origins.split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

settings.jobs_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/jobs/artifacts",
    StaticFiles(directory=str(settings.jobs_dir)),
    name="job_artifacts",
)

app.include_router(health.router)
app.include_router(ai_models.router, prefix="/models", tags=["models"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

_FRONTEND_DIST = os.environ.get("FRONTEND_DIST")
_FRONTEND_DIST_PATH = Path(_FRONTEND_DIST) if _FRONTEND_DIST else None

if _FRONTEND_DIST_PATH and _FRONTEND_DIST_PATH.is_dir():

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse | dict[str, str]:
        """Serves the Single Page Application assets.

        Args:
            full_path: Requested file path.

        Returns:
            The requested static file if it exists; otherwise index.html.
        """
        if _FRONTEND_DIST_PATH is None:
            return {"detail": "Frontend assets not found"}

        if full_path and not full_path.startswith(".."):
            candidate = (_FRONTEND_DIST_PATH / full_path).resolve()
            if candidate.is_file() and candidate.is_relative_to(_FRONTEND_DIST_PATH):
                return FileResponse(candidate)

        return FileResponse(_FRONTEND_DIST_PATH / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
