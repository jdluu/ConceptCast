import os

# Mocking the agent since we don't have API keys in this env
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from schemas import CurriculumPlan, TeachingStep

client = TestClient(app)


@pytest.fixture
def mock_analyst():
    with patch("main.generate_curriculum", new_callable=AsyncMock) as mock:
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


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to ConceptCast Council"}


def test_create_and_get_job(mock_analyst):
    # Simulate a valid API key to force "live" mode, which uses the mock_analyst
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "valid_test_key"}):
        # 1. Create Job
        response = client.post("/jobs/create", json={"topic": "Test Topic"})
        assert response.status_code == 200
        job_data = response.json()
        job_id = job_data["job_id"]
        assert job_data["status"] == "reviewing"

        # 2. Get Job Status
        response = client.get(f"/jobs/{job_id}/status")
        assert response.status_code == 200
        assert response.json()["status"] == "reviewing"

    # 3. Get Job Plan
    response = client.get(f"/jobs/{job_id}/plan")
    assert response.status_code == 200
    plan = response.json()
    assert plan["concept_title"] == "Test Concept"
