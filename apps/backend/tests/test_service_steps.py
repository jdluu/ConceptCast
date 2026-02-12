from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas import CurriculumPlan, JobRequest, Storyboard, TeachingStep
from core.database import JobRecord
from services.orchestrator import _step_animating, _step_architecting, _step_planning


@pytest.fixture
def mock_job_request() -> JobRequest:
    return JobRequest(
        topic="Test Topic",
        target_audience="Test Audience",
        provider="mock",
        model_id="mock-model",
    )


@pytest.fixture
def mock_job_record() -> JobRecord:
    return JobRecord(
        job_id="test-job-123",
        status="planning",
        plan=None,
        storyboard=None,
        manim_code=None,
    )


@pytest.fixture
def mock_params() -> dict[str, Any]:
    return {"param1": "value1", "param2": "value2"}


@pytest.fixture
def mock_update_job() -> AsyncMock:
    return AsyncMock()


@pytest.mark.asyncio
async def test_step_planning_execution(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that planning step calls generate_curriculum when no plan exists."""
    # Arrange
    expected_plan = CurriculumPlan(
        concept_title="Test Topic",
        target_audience="Test Audience",
        teaching_steps=[
            TeachingStep(step_id=1, concept="C1", visual_metaphor="V1", narration="N1")
        ],
    )

    with patch(
        "services.orchestrator.generate_curriculum", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = expected_plan

        # Act
        result = await _step_planning(
            mock_job_request, mock_job_record, mock_update_job
        )

        # Assert
        mock_gen.assert_awaited_once()
        mock_update_job.assert_called()  # Should verify specific calls
        assert result == expected_plan


@pytest.mark.asyncio
async def test_step_planning_checkpoint(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that planning step returns existing plan if already present."""
    # Arrange
    existing_plan = CurriculumPlan(
        concept_title="Existing", target_audience="Audience", teaching_steps=[]
    )
    mock_job_record.plan = existing_plan.model_dump()

    with patch(
        "services.orchestrator.generate_curriculum", new_callable=AsyncMock
    ) as mock_gen:
        # Act
        result = await _step_planning(
            mock_job_request, mock_job_record, mock_update_job
        )

        # Assert
        mock_gen.assert_not_awaited()
        assert result.concept_title == "Existing"


@pytest.mark.asyncio
async def test_step_architecting_execution(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that architecting step calls generate_storyboard."""
    # Arrange
    plan = CurriculumPlan(concept_title="T", target_audience="A", teaching_steps=[])
    expected_storyboard = Storyboard(concept_title="T", scenes=[])
    with patch(
        "services.orchestrator.generate_storyboard", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = expected_storyboard

        # Act
        result = await _step_architecting(
            plan, mock_job_request, mock_job_record, mock_update_job
        )

        # Assert
        mock_gen.assert_awaited_once()
        assert result == expected_storyboard


@pytest.mark.asyncio
async def test_step_animating_execution(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that animating step calls generate_manim_code."""
    # Arrange
    storyboard = Storyboard(concept_title="T", scenes=[])
    expected_code = "class TestScene(Scene): pass"
    with patch(
        "services.orchestrator.generate_manim_code", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = expected_code

        # Act
        result = await _step_animating(
            storyboard, mock_job_request, mock_job_record, mock_update_job
        )

        # Assert
        mock_gen.assert_awaited_once()
        assert result == expected_code
