from api.schemas import (
    AnimationReview,
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    ValidationResult,
    VisualObject,
)

MOCK_PLANS = {
    "default": CurriculumPlan(
        concept_title="Understanding Quantum Entanglement",
        target_audience="General Audience",
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="The Spin Property",
                visual_metaphor="Rotating spheres with glowing axes",
                narration=(
                    "Imagine two particles, like tiny spinning tops. In the quantum "
                    "world, their spin can be linked in a way that defies classical "
                    "logic."
                ),
            ),
            TeachingStep(
                step_id=2,
                concept="Superposition",
                visual_metaphor="A blurry, shifting state between two colors",
                narration=(
                    "Until measured, a particle exists in multiple states at once. "
                    "This uncertainty is the heart of quantum mechanics."
                ),
            ),
            TeachingStep(
                step_id=3,
                concept="Non-locality",
                visual_metaphor="A bridge of light connecting two distant points",
                narration=(
                    "Entanglement means that measuring one particle instantly "
                    "determines the state of the other, no matter the distance "
                    "between them."
                ),
            ),
        ],
    )
}

MOCK_VALIDATIONS = {
    "default": ValidationResult(
        is_valid=True,
        feedback=(
            "The logical flow is sound and the visual metaphors are highly "
            "effective for a general audience."
        ),
        suggestions=[
            "Consider adding a brief recap of classical probability for contrast."
        ],
    )
}

MOCK_STORYBOARDS = {
    "default": Storyboard(
        concept_title="Understanding Quantum Entanglement",
        scenes=[
            Scene(
                scene_id=0,
                title="Introduction to Quantum Void",
                description="Opening shot: Two particles appearing in a void.",
                narration=(
                    "In the vastness of the quantum void, particles are "
                    "never truly alone."
                ),
                objects=[
                    VisualObject(
                        name="p1",
                        type="Circle",
                        color="BLUE",
                        position="LEFT",
                        label=None,
                    ),
                    VisualObject(
                        name="p2",
                        type="Circle",
                        color="RED",
                        position="RIGHT",
                        label=None,
                    ),
                ],
            )
        ],
    )
}

MOCK_MANIM_CODE = """
from manim import *

class SceneGen(Scene):
    def construct(self):
        # Concept: {{concept_title}}
        # Create particles
        p1 = Circle(color=BLUE, fill_opacity=0.5).shift(LEFT * 2)
        p2 = Circle(color=RED, fill_opacity=0.5).shift(RIGHT * 2)
        
        # Animations
        self.play(Create(p1), Create(p2))
        self.wait(1)
        
        # Narration transition
        title = Text("{{concept_title}}", font_size=36).to_edge(UP)
        self.play(Write(title))
        self.wait(2)
"""

MOCK_REVIEWS = {
    "default": AnimationReview(
        approved=True,
        issues=[],
        revision_instructions=(
            "The animation perfectly matches the storyboard requirements."
        ),
    )
}


def inject_topic(text: str, topic: str) -> str:
    """Injects the user's topic into a text template.

    Args:
        text: The template text containing '{{concept_title}}'.
        topic: The topic name to inject.

    Returns:
        The template with placeholders replaced by the actual topic.
    """
    if not topic:
        return text.replace("{{concept_title}}", "ConceptCast")
    return text.replace("{{concept_title}}", topic)


def get_realistic_response(
    _prompt: str, output_type: type, topic: str | None = None
) -> str:
    """Retrieves a realistic mock response for demonstration and testing.

    Args:
        prompt: The input prompt (currently ignored in the mock).
        output_type: The expected Pydantic model class for the output.
        topic: The topic requested by the user.

    Returns:
        A JSON string or plain text representing the mock response.
    """
    if output_type == CurriculumPlan:
        plan = MOCK_PLANS["default"]
        if topic:
            plan.concept_title = topic
        return plan.model_dump_json()

    if output_type == ValidationResult:
        return MOCK_VALIDATIONS["default"].model_dump_json()

    if output_type == Storyboard:
        sb = MOCK_STORYBOARDS["default"]
        if topic:
            sb.concept_title = topic
        return sb.model_dump_json()

    if output_type == AnimationReview:
        return MOCK_REVIEWS["default"].model_dump_json()

    if topic:
        return inject_topic(MOCK_MANIM_CODE, topic)
    return MOCK_MANIM_CODE
