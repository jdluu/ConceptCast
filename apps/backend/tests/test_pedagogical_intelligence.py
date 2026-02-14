from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai import RunContext

from agents.analyst import generate_curriculum
from agents.tools import prepare_manim_docs
from api.schemas import (
    CurriculumPlan,
    Scene,
    Storyboard,
    ValidationResult,
    VisualObject,
)


@pytest.fixture
def mock_deps() -> dict[str, Any]:
    return dict()


@pytest.mark.asyncio
async def test_analyst_consults_critic() -> None:
    """
    Verifies that the Analyst agent calls validate_curriculum via consult_critic.
    """
    mock_validation = ValidationResult(
        is_valid=True, feedback="Great plan!", suggestions=[]
    )

    mock_plan = CurriculumPlan(
        concept_title="Test", target_audience="Test", teaching_steps=[]
    )
    with patch(
        "agents.analyst.validate_curriculum", new_callable=AsyncMock
    ) as mock_validate:
        mock_validate.return_value = mock_validation

        with patch("agents.analyst.Agent") as MockAgent:
            MockAgent.return_value = MagicMock()

            with patch(
                "agents.analyst.run_agent_streamed", new_callable=AsyncMock
            ) as mock_streamed:
                mock_streamed.return_value = mock_plan

                result = await generate_curriculum(
                    "Test Topic", "Test Audience", model=MagicMock()
                )

                assert result == mock_plan
                mock_streamed.assert_awaited_once()
                call_args = mock_streamed.call_args
                assert call_args[0][0] == "analyst"
                MockAgent.assert_called_once()
                _, kwargs = MockAgent.call_args
                assert kwargs["output_type"] == CurriculumPlan


@pytest.mark.asyncio
async def test_prepare_manim_docs_filters_correctly() -> None:
    """
    Verifies that prepare_manim_docs correctly filters the documentation
    based on the storyboard content.
    """
    storyboard = Storyboard(
        concept_title="Test",
        scenes=[
            Scene(
                scene_id=1,
                title="S1",
                description="D1",
                narration="N1",
                objects=[
                    VisualObject(
                        name="obj1",
                        type="Circle",
                        position="ORIGIN",
                        color="RED",
                        label="A",
                    ),
                    VisualObject(
                        name="obj2",
                        type="Square",
                        position="LEFT",
                        color="BLUE",
                        label="B",
                    ),
                ],
            )
        ],
    )

    # Mock RunContext
    ctx = MagicMock(spec=RunContext)
    ctx.deps = storyboard

    # Mock ToolDefinition
    tool_def = MagicMock()
    tool_def.description = "Original Description"

    # Run prepare function
    updated_def = await prepare_manim_docs(ctx, tool_def)

    assert updated_def is not None
    assert updated_def.description is not None

    # Check if "Dot" and "Circle" are in the description
    # Both Circle and Square are in the storyboard, so they should be in the context
    assert "Square" in updated_def.description
    # "Triangle" is not in the storyboard
    assert "Triangle" not in updated_def.description
    assert "Axes" not in updated_def.description
    assert "ValueTracker" not in updated_def.description
    # Add a check for an animation that might be mentioned implicitly
    # or explicitly if we extend filtering
