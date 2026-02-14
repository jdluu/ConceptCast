from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.schemas import AnimationReview, JobRequest, Storyboard
from core.database import JobRecord
from services.orchestrator import _step_animating
from services.rendering import PreviewResult


@pytest.fixture
def mock_storyboard():
    return Storyboard(concept_title="Test", scenes=[])


@pytest.fixture
def mock_job_request():
    return JobRequest(topic="Test", target_audience="Test")


@pytest.fixture
def mock_job_record():
    return JobRecord(job_id="test-job", status="animating")


def make_code(version: str) -> str:
    return f"""
from manim import *
class SceneGen(Scene):
    def construct(self):
        # {version}
        pass
"""


@pytest.mark.asyncio
async def test_animation_review_success_first_try(
    mock_storyboard, mock_job_request, mock_job_record
):
    # Mock dependencies
    update_job = AsyncMock()
    on_thought = AsyncMock()

    with (
        patch(
            "services.orchestrator.generate_manim_code", new_callable=AsyncMock
        ) as mock_gen,
        patch(
            "services.orchestrator.render_preview", new_callable=AsyncMock
        ) as mock_render,
        patch(
            "services.orchestrator.review_animation", new_callable=AsyncMock
        ) as mock_review,
        patch("services.orchestrator.get_settings") as mock_get_settings,
    ):
        # Setup settings
        mock_settings = MagicMock()
        mock_settings.animation_review_max_iterations = 3
        mock_settings.animation_review_enabled = True
        mock_get_settings.return_value = mock_settings

        # Setup mocks
        mock_gen.return_value = make_code("v1")
        mock_render.return_value = PreviewResult(
            success=True, logs="Success", frame_path="http://video.url", error=None
        )
        # Reviewer approves immediately
        mock_review.return_value = AnimationReview(
            approved=True, issues=[], revision_instructions="Looks good"
        )

        result = await _step_animating(
            mock_storyboard, mock_job_request, mock_job_record, update_job, on_thought
        )

        assert result == make_code("v1")
        assert mock_gen.call_count == 1
        assert mock_render.call_count == 1
        assert mock_review.call_count == 1


@pytest.mark.asyncio
async def test_animation_review_revision_loop(
    mock_storyboard, mock_job_request, mock_job_record
):
    # Mock dependencies
    update_job = AsyncMock()
    on_thought = AsyncMock()

    with (
        patch(
            "services.orchestrator.generate_manim_code", new_callable=AsyncMock
        ) as mock_gen,
        patch(
            "services.orchestrator.render_preview", new_callable=AsyncMock
        ) as mock_render,
        patch(
            "services.orchestrator.review_animation", new_callable=AsyncMock
        ) as mock_review,
        patch("services.orchestrator.get_settings") as mock_get_settings,
    ):
        # Setup settings
        mock_settings = MagicMock()
        mock_settings.animation_review_max_iterations = 3
        mock_settings.animation_review_enabled = True
        mock_get_settings.return_value = mock_settings

        # Setup mocks for 3 iterations:
        # 1. Gen v1 -> Render Fail -> Review (Fail)
        # 2. Gen v2 -> Render Success -> Review (Needs Change)
        # 3. Gen v3 -> Render Success -> Review (Approve)

        mock_gen.side_effect = [make_code("v1"), make_code("v2"), make_code("v3")]

        mock_render.side_effect = [
            PreviewResult(
                success=False,
                logs="Syntax Error",
                frame_path=None,
                error="Syntax Error",
            ),
            PreviewResult(
                success=True, logs="Rendered", frame_path="http://v2.url", error=None
            ),
            PreviewResult(
                success=True, logs="Rendered", frame_path="http://v3.url", error=None
            ),
        ]

        mock_review.side_effect = [
            AnimationReview(
                approved=False, issues=["Colors"], revision_instructions="Change color"
            ),  # Review 2 (v1 failed render)
            AnimationReview(
                approved=True, issues=[], revision_instructions="Perfect"
            ),  # Review 3
        ]

        result = await _step_animating(
            mock_storyboard, mock_job_request, mock_job_record, update_job, on_thought
        )

        assert result == make_code("v3")
        assert mock_gen.call_count == 3
        # Ensure hints were passed
        # call_args_list[0] is first call (no hint)
        # call_args_list[1] is second call (hint from render failure + review)
        # call_args_list[2] is third call (hint from review)

        _, kwargs1 = mock_gen.call_args_list[1]
        assert (
            "Syntax Error" in kwargs1["retry_hint"]
            or "Fix syntax error" in kwargs1["retry_hint"]
        )

        _, kwargs2 = mock_gen.call_args_list[2]
        assert "Change color" in kwargs2["retry_hint"]
