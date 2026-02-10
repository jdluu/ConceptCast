from schemas import (
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    ValidationResult,
    VisualObject,
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
    )
