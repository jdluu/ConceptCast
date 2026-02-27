import asyncio
from collections.abc import Callable
from typing import Any

from api.schemas import (
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    ValidationResult,
    VisualObject,
)


async def run_mock_flow(
    topic: str,
    target_audience: str,
    update_job: Callable[[dict[str, Any]], Any],
    on_thought: Callable[[str, str, str], Any],
) -> None:
    """
    Executes the mock generation flow for testing or demonstration purposes.
    Simulates the exact timing and steps of a live run.
    """
    from datetime import UTC, datetime

    try:
        # Record start time
        await update_job({"started_at": datetime.now(UTC)})

        # Sane default timing for UI visualization
        sleep_mult = 1.0

        # Step 1: Planning
        await update_job({"status": "planning", "current_step": "planning"})

        await on_thought(
            "analyst", "Curriculum Design", f"Analyzing topic '{topic}'..."
        )
        await asyncio.sleep(1.5 * sleep_mult)

        await on_thought(
            "analyst", "Curriculum Design", "Identifying key pedagogical concepts..."
        )
        await asyncio.sleep(1.5 * sleep_mult)

        await on_thought("analyst", "Curriculum Design", "Structuring lesson plan...")
        await asyncio.sleep(1.0 * sleep_mult)

        plan = generate_mock_plan(
            topic, target_audience or "General Audience"
        )
        await update_job(
            {
                "plan": plan.model_dump(),
                "status": "validating",
                "current_step": "planning_complete",
            }
        )

        # Step 2: Validating
        await on_thought(
            "validator",
            "Validation",
            "Reviewing curriculum plan against pedagogical standards...",
        )
        await asyncio.sleep(1.5 * sleep_mult)

        validation = generate_mock_validation()
        await update_job(
            {
                "validation": validation.model_dump(),
                "status": "architecting",
                "current_step": "validating_complete",
            }
        )

        # Step 3: Architecting
        await on_thought(
            "architect", "Visual Design", "Translate concepts into visual metaphors..."
        )
        await asyncio.sleep(1.5 * sleep_mult)

        await on_thought(
            "architect",
            "Visual Design",
            "Drafting scene composition and transitions...",
        )
        await asyncio.sleep(1.5 * sleep_mult)

        storyboard = generate_mock_storyboard(plan)
        await update_job(
            {
                "storyboard": storyboard.model_dump(),
                "current_step": "orchestrator_architecting_complete",
                "status": "animating",
            }
        )

        # Step 4: Animating (Simulated Loop)
        await on_thought("animator", "Code Generation", "Initializing Manim scene...")
        await asyncio.sleep(1.5 * sleep_mult)

        await on_thought(
            "animator",
            "Code Generation",
            "Generating Pythagorean theorem visualization code...",
        )
        await asyncio.sleep(1.5 * sleep_mult)

        code = generate_mock_code()

        # Simulate a quick review cycle
        await update_job({"manim_code": code, "current_step": "animating_iter_1"})
        await on_thought(
            "reviewer", "Visual QA", "Reviewing generated animation code..."
        )
        await asyncio.sleep(1.0 * sleep_mult)
        await on_thought("reviewer", "Visual QA", "Code looks correct. Approving.")

        await update_job({"status": "rendering", "current_step": "animating_complete"})

        # Step 5: Rendering
        await on_thought("system", "Rendering", "Starting render process...")
        await asyncio.sleep(2.0 * sleep_mult)

        # Mock doesn't produce a real video URL unless we have a static asset?
        # For now, null video_url triggers "Mock runs skip rendering" message in UI.

        await update_job(
            {
                "video_url": None,
                "status": "completed",
                "mode": "mock",
                "current_step": "rendering_complete",
                "finished_at": datetime.now(UTC),
                "cost": 0.05,
                "thumbnail_url": "https://placehold.co/600x400/1e1e1e/white?text=Mock+Scene",
                "video_metadata": {
                    "resolution": "1080p",
                    "file_size": "14MB",
                    "format": "mp4",
                    "bitrate": "5.2Mbps",
                },
            }
        )

    except Exception as e:
        from datetime import UTC, datetime

        await update_job(
            {"status": "failed", "error": str(e), "finished_at": datetime.now(UTC)}
        )


def generate_mock_plan(topic: str, target_audience: str) -> CurriculumPlan:
    """
    Generates a deterministic mock curriculum plan for development/testing.

    Args:
        topic: The requested topic.
        target_audience: The target audience.

    Returns:
        CurriculumPlan: A structured mock plan.
    """
    return CurriculumPlan(
        concept_title=f"Mock: {topic}",
        target_audience=target_audience,
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="Introduction",
                visual_metaphor="Opening curtain",
                narration="Welcome to the concept.",
            ),
            TeachingStep(
                step_id=2,
                concept="Core Logic",
                visual_metaphor="Gears turning",
                narration="This is how it works.",
            ),
        ],
    )


def generate_mock_storyboard(plan: CurriculumPlan) -> Storyboard:
    """
    Generates a mock storyboard based on a curriculum plan.

    Args:
        plan: The curriculum plan.

    Returns:
        Storyboard: A mock storyboard.
    """
    return Storyboard(
        concept_title=plan.concept_title,
        scenes=[
            Scene(
                scene_id=1,
                title="Introduction Scene",
                description="A simple title screen fading into view.",
                narration=plan.teaching_steps[0].narration,
                objects=[
                    VisualObject(
                        name="title",
                        type="Text",
                        position="ORIGIN",
                        label=plan.concept_title,
                        color="WHITE",
                    )
                ],
            ),
            Scene(
                scene_id=2,
                title="Visual Explanation",
                description="Showing the core visual metaphor.",
                narration=plan.teaching_steps[1].narration,
                objects=[
                    VisualObject(
                        name="metaphor",
                        type="Circle",
                        position="ORIGIN",
                        color="#4F46E5",
                        label="Metaphor",
                    )
                ],
            ),
        ],
    )


def generate_mock_code() -> str:
    """
    Generates mock Manim code for testing.
    """
    return """
from manim import *

class SceneGen(Scene):
    def construct(self):
        text = Text("Mock Animation")
        self.play(Write(text))
        self.wait(1)
"""


def generate_mock_validation() -> ValidationResult:
    """
    Generates a mock passing validation result.
    """
    return ValidationResult(
        is_valid=True,
        feedback="Mock: Curriculum plan is pedagogically sound.",
        suggestions=["Everything looks great!"],
        metadata={},
        scores={},
        issues=[],
    )
