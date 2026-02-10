import os
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app
from schemas import (
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    VisualObject,
)


# For tests, we'll use the same engine but clear the tables
@pytest.fixture(autouse=True)
def setup_db():
    # Make sure we are using the real engine from database.py but clear it
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    # We leave it for the next run or session cleanup


# --- Mocks for logic in service.py ---


@pytest.fixture
def mock_analyst():
    with patch("service.generate_curriculum", new_callable=AsyncMock) as mock:
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
def mock_architect():
    with patch("service.generate_storyboard", new_callable=AsyncMock) as mock:
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
                            name="obj1",
                            type="Dot",
                            position="ORIGIN",
                        )
                    ],
                )
            ],
        )
        yield mock


@pytest.fixture
def mock_animator():
    with patch("service.generate_manim_code", new_callable=AsyncMock) as mock:
        mock.return_value = "from manim import *"
        yield mock


@pytest.fixture
def mock_rendering():
    with patch("service.render_storyboard") as mock:
        mock.return_value = "/jobs/mock_job_id/video.mp4"
        yield mock


# --- Tests ---


def test_read_root():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to ConceptCast Council"}


def test_create_and_get_job(
    mock_analyst, mock_architect, mock_animator, mock_rendering
):
    # Simulate a valid API key to force "live" mode
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "valid_test_key"}):
        with TestClient(app) as client:
            # 1. Create Job
            response = client.post("/jobs/create", json={"topic": "Test Topic"})
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
            assert data["video_url"] == "/jobs/mock_job_id/video.mp4"

            # 3. Get Job Plan
            response = client.get(f"/jobs/{job_id}/plan")
            assert response.status_code == 200
            plan = response.json()
            assert plan["concept_title"] == "Test Concept"
