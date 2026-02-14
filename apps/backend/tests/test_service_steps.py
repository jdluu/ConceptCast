from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas import (
    AnimationReview,
    CurriculumPlan,
    JobRequest,
    Storyboard,
    TeachingStep,
)
from core.database import JobRecord
from services.workflow_steps import (
    step_animating,
    step_architecting,
    step_planning,
    step_rendering,
)


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
        mode="live",
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
    expected_plan = CurriculumPlan(
        concept_title="Test Topic",
        target_audience="Test Audience",
        teaching_steps=[
            TeachingStep(step_id=1, concept="C1", visual_metaphor="V1", narration="N1")
        ],
    )
    mock_model = MagicMock()

    with (
        patch("services.workflow_steps.get_model", return_value=mock_model),
        patch(
            "services.workflow_steps.generate_curriculum", new_callable=AsyncMock
        ) as mock_gen,
    ):
        mock_gen.return_value = expected_plan

        async def noop_on_thought(_a: str, _p: str, _c: str) -> None:
            pass

        result = await step_planning(
            mock_job_request, mock_job_record, mock_update_job, noop_on_thought
        )

        mock_gen.assert_awaited_once()
        assert result == expected_plan


@pytest.mark.asyncio
async def test_step_planning_checkpoint(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that planning step returns existing plan if already present."""
    existing_plan = CurriculumPlan(
        concept_title="Existing", target_audience="Audience", teaching_steps=[]
    )
    mock_job_record.plan = existing_plan.model_dump()

    async def noop_on_thought(_a: str, _p: str, _c: str) -> None:
        pass

    with patch(
        "services.workflow_steps.generate_curriculum", new_callable=AsyncMock
    ) as mock_gen:
        result = await step_planning(
            mock_job_request, mock_job_record, mock_update_job, noop_on_thought
        )

        mock_gen.assert_not_awaited()
        assert result.concept_title == "Existing"


@pytest.mark.asyncio
async def test_step_architecting_execution(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that architecting step calls generate_storyboard."""
    plan = CurriculumPlan(concept_title="T", target_audience="A", teaching_steps=[])
    expected_storyboard = Storyboard(concept_title="T", scenes=[])
    mock_model = MagicMock()

    async def noop_on_thought(_a: str, _p: str, _c: str) -> None:
        pass

    with (
        patch("services.workflow_steps.get_model", return_value=mock_model),
        patch(
            "services.workflow_steps.generate_storyboard", new_callable=AsyncMock
        ) as mock_gen,
    ):
        mock_gen.return_value = expected_storyboard

        result = await step_architecting(
            plan, mock_job_request, mock_job_record, mock_update_job, noop_on_thought
        )

        mock_gen.assert_awaited_once()
        assert result == expected_storyboard


@pytest.mark.asyncio
async def test_step_animating_execution(
    mock_job_request: JobRequest, mock_job_record: JobRecord, mock_update_job: AsyncMock
) -> None:
    """Test that animating step calls generate_manim_code."""
    storyboard = Storyboard(concept_title="T", scenes=[])
    expected_code = "from manim import *\nclass SceneGen(Scene): pass"
    mock_model = MagicMock()

    async def noop_on_thought(_a: str, _p: str, _c: str) -> None:
        pass

    with (
        patch("services.workflow_steps.get_model", return_value=mock_model),
        patch(
            "services.workflow_steps.generate_manim_code", new_callable=AsyncMock
        ) as mock_gen,
        patch(
            "services.workflow_steps.render_preview", new_callable=AsyncMock
        ) as mock_render,
        patch(
            "services.workflow_steps.review_animation", new_callable=AsyncMock
        ) as mock_review,
    ):
        mock_gen.return_value = expected_code
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.logs = "logs"
        mock_result.frame_path = "preview.png"
        mock_render.return_value = mock_result
        mock_review.return_value = AnimationReview(
            approved=True, issues=[], revision_instructions=""
        )

        result = await step_animating(
            storyboard,
            mock_job_request,
            mock_job_record,
            mock_update_job,
            noop_on_thought,
        )

        mock_gen.assert_awaited_once()
        assert result == expected_code
