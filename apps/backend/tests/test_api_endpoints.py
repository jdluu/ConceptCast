import os
import time
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from api.schemas import (
    AnimationReview,
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    VisualObject,
)
from core.database import Base, engine
from core.settings import get_settings
from main import app


# For tests, we'll use the same engine but clear the tables
@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


# --- Mocks for logic in service.py ---


@pytest.fixture
def mock_analyst() -> Generator[AsyncMock, None, None]:
    with patch(
        "services.workflow_steps.generate_curriculum", new_callable=AsyncMock
    ) as mock:
        mock.return_value = CurriculumPlan(
            concept_title="Test Concept",
            target_audience="Test Audience",
            teaching_steps=[
                TeachingStep(
                    step_id=1,
                    concept="Concept 1",
                    visual_metaphor="Metaphor 1",
                    narration="Narration 1",
                )
            ],
        )
        yield mock


@pytest.fixture
def mock_architect() -> Generator[AsyncMock, None, None]:
    with patch(
        "services.workflow_steps.generate_storyboard", new_callable=AsyncMock
    ) as mock:
        mock.return_value = Storyboard(
            concept_title="Test Concept",
            scenes=[
                Scene(
                    scene_id=1,
                    title="Scene 1",
                    description="Desc 1",
                    narration="Narr 1",
                    objects=[
                        VisualObject(
                            name="Circle",
                            type="Circle",
                            position="ORIGIN",
                            color="RED",
                            label="A",
                        )
                    ],
                )
            ],
        )
        yield mock


@pytest.fixture
def mock_animator() -> Generator[AsyncMock, None, None]:
    with patch(
        "services.workflow_steps.generate_manim_code", new_callable=AsyncMock
    ) as mock:
        mock.return_value = "from manim import *\nclass SceneGen(Scene): pass"
        yield mock


@pytest.fixture
def mock_rendering() -> Generator[AsyncMock, None, None]:
    with patch("services.workflow_steps.render_storyboard") as mock:
        mock.return_value = "/jobs/artifacts/mock_job_id/video.mp4"
        yield mock


@pytest.fixture
def mock_preview_rendering() -> Generator[AsyncMock, None, None]:
    with patch("services.workflow_steps.render_preview", new_callable=AsyncMock) as mock:
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.logs = "logs"
        mock_result.frame_path = "preview.png"
        mock.return_value = mock_result
        yield mock


# --- Tests ---


@pytest.fixture
def mock_reviewer() -> Generator[AsyncMock, None, None]:
    with patch(
        "services.workflow_steps.review_animation", new_callable=AsyncMock
    ) as mock:
        mock.return_value = AnimationReview(
            approved=True, issues=[], revision_instructions=""
        )
        yield mock


@pytest.mark.asyncio
async def test_read_root() -> None:
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to ConceptCast Council"}


@pytest.mark.asyncio
async def test_create_job_invalid_input() -> None:
    with TestClient(app) as client:
        response = client.post("/jobs/create", json={"invalid_field": "Test Topic"})
        assert response.status_code == 422  # Unprocessable Entity
        error_detail = response.json()["detail"][0]
        assert error_detail["loc"] == ["body", "topic"]
        assert error_detail["msg"] == "Field required"


@pytest.mark.asyncio
async def test_create_and_get_job(
    mock_analyst: AsyncMock,
    mock_architect: AsyncMock,
    mock_animator: AsyncMock,
    mock_rendering: AsyncMock,
    mock_preview_rendering: AsyncMock,
    mock_reviewer: AsyncMock,
) -> None:
    # Simulate a valid API key to force "live" mode
    # Clear the settings cache so env var changes are picked up
    get_settings.cache_clear()
    with (
        patch.dict(os.environ, {"GOOGLE_API_KEY": "valid_test_key"}),
        TestClient(app) as client,
    ):
        # 1. Create Job (provider and model_id required for live mode)
        response = client.post(
            "/jobs/create",
            json={
                "topic": "Test Topic",
                "provider": "google",
                "model_id": "gemini-2.5-flash",
            },
        )
        assert response.status_code == 200

        job_data = response.json()
        job_id = job_data["job_id"]

        # 1.1 Poll for completion
        max_retries = 30
        for _ in range(max_retries):
            response = client.get(f"/jobs/{job_id}/status")
            job_data = response.json()
            if job_data["status"] == "completed":
                break
            if job_data["status"] == "failed":
                pytest.fail(f"Job failed: {job_data.get('error')}")
            time.sleep(0.1)

        assert job_data["status"] == "completed"

        # 2. Get Job Status
        response = client.get(f"/jobs/{job_id}/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["video_url"] == "/jobs/artifacts/mock_job_id/video.mp4"

        # 3. Get Job Plan
        response = client.get(f"/jobs/{job_id}/plan")
        assert response.status_code == 200
        plan = response.json()
        assert plan["concept_title"] == "Test Concept"
