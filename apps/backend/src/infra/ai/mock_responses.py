from typing import Any

from pydantic import BaseModel

from api.schemas import (
    AnimationReview,
    CurriculumPlan,
    Scene,
    Storyboard,
    TeachingStep,
    TeachingStepsDraft,
)
from domain.models.curriculum import ValidationResult
from infra.settings import get_settings

settings = get_settings()

MOCK_PLANS = {
    "default": CurriculumPlan(
        concept_title=f"Understanding {settings.mock_topic}",
        target_audience="General Audience",
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="The Spin Property",
                visual_metaphor="Rotating spheres with glowing axes",
                narration="Imagine two particles, like tiny spinning tops.",
            ),
            TeachingStep(
                step_id=2,
                concept="Superposition",
                visual_metaphor="A blurry, shifting state between two colors",
                narration="Until measured, a particle exists in multiple states.",
            ),
            TeachingStep(
                step_id=3,
                concept="Non-locality",
                visual_metaphor="A bridge of light connecting two distant points",
                narration="Entanglement means measuring one determines the other.",
            ),
            TeachingStep(
                step_id=4,
                concept="Quantum Gates",
                visual_metaphor="Crystal prisms refracting light beams",
                narration="Gates manipulate the state of entangled qubits.",
            ),
            TeachingStep(
                step_id=5,
                concept="Bell's Theorem",
                visual_metaphor="Statistical charts with impossible correlations",
                narration="Proving that local hidden variables don't exist.",
            ),
            TeachingStep(
                step_id=6,
                concept="Quantum Circuitry",
                visual_metaphor="Glowing blue lines on a dark obsidian substrate",
                narration="Building a computer from entangled particles.",
            ),
            TeachingStep(
                step_id=7,
                concept="Decoherence",
                visual_metaphor="Shattering glass becoming sand",
                narration="When the outside world breaks the delicate link.",
            ),
            TeachingStep(
                step_id=8,
                concept="Error Correction",
                visual_metaphor="Self-weaving golden threads",
                narration="Protecting information from quantum noise.",
            ),
            TeachingStep(
                step_id=9,
                concept="Superdense Coding",
                visual_metaphor="Compressing light into a single point",
                narration="Sending two bits using only one qubit.",
            ),
            TeachingStep(
                step_id=10,
                concept="Teleportation",
                visual_metaphor="A particle vanishing here and appearing there",
                narration="Moving information without moving matter.",
            ),
        ],
    )
}

MOCK_TEACHING_STEPS_DRAFTS = {
    "default": TeachingStepsDraft(teaching_steps=MOCK_PLANS["default"].teaching_steps)
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
        concept_title=f"Understanding {settings.mock_topic}",
        scenes=[
            Scene(
                scene_id=1,
                title="Quantum Void",
                description="Opening shot: Two particles appearing in a void.",
                narration="In the vastness of the quantum void.",
                objects=[],
            ),
            Scene(
                scene_id=2,
                title="Spin Alignment",
                description="Particles start spinning in synchrony.",
                narration="Watch as their fates become intertwined.",
                objects=[],
            ),
            Scene(
                scene_id=3,
                title="Measurement",
                description="A flash of light hits the first particle.",
                narration="One choice determines the entire system.",
                objects=[],
            ),
            Scene(
                scene_id=4,
                title="The Bridge",
                description="A glowing link forms between the spheres.",
                narration="Distance is no longer a barrier.",
                objects=[],
            ),
            Scene(
                scene_id=5,
                title="Quantum Gate",
                description="The particles pass through a prism.",
                narration="Logic transformed by quantum rules.",
                objects=[],
            ),
            Scene(
                scene_id=6,
                title="Correlation",
                description="Charts showing linked probabilities.",
                narration="Patterns that classical physics can't explain.",
                objects=[],
            ),
            Scene(
                scene_id=7,
                title="Computer Core",
                description="Zoom out to show a complex circuit.",
                narration="The foundation of a new era of computing.",
                objects=[],
            ),
            Scene(
                scene_id=8,
                title="The Noise",
                description="Static begins to cloud the vision.",
                narration="The challenge of decoherence.",
                objects=[],
            ),
            Scene(
                scene_id=9,
                title="Error Correction",
                description="Golden threads of light repair the static.",
                narration="Overcoming noise with quantum redundancy.",
                objects=[],
            ),
            Scene(
                scene_id=10,
                title="Teleportation",
                description="A particle vanishes and reappears instantly.",
                narration="The ultimate mastery of quantum information.",
                objects=[],
            ),
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


def inject_topic_recursively(obj: Any, topic: str) -> Any:
    """Recursively replaces topic keywords with the user's topic.

    Args:
        obj: The object (Pydantic model, list, or dict) to process.
        topic: The topic name to inject.

    Returns:
        The object with all topic placeholders replaced.
    """
    settings = get_settings()
    replacements = {
        settings.mock_topic: topic,
        "quantum": "core",
        "particles": "components",
        "particle": "component",
    }

    if isinstance(obj, str):
        res = obj
        for target, replacement in replacements.items():
            res = res.replace(target, replacement)
        return res

    if isinstance(obj, list):
        return [inject_topic_recursively(item, topic) for item in obj]

    if isinstance(obj, dict):
        return {k: inject_topic_recursively(v, topic) for k, v in obj.items()}

    if hasattr(obj, "__dict__") or isinstance(obj, BaseModel):
        # Handle Pydantic models and simple objects
        fields = obj.__dict__ if not isinstance(obj, BaseModel) else obj.model_fields
        for field_name in fields:
            val = getattr(obj, field_name)
            setattr(obj, field_name, inject_topic_recursively(val, topic))

    return obj


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
        plan = MOCK_PLANS["default"].model_copy(deep=True)
        if topic:
            plan = inject_topic_recursively(plan, topic)
        return plan.model_dump_json()

    if output_type == TeachingStepsDraft:
        draft = MOCK_TEACHING_STEPS_DRAFTS["default"].model_copy(deep=True)
        if topic:
            draft = inject_topic_recursively(draft, topic)
        return draft.model_dump_json()

    if output_type == ValidationResult:
        return MOCK_VALIDATIONS["default"].model_dump_json()

    if output_type == Storyboard:
        sb = MOCK_STORYBOARDS["default"].model_copy(deep=True)
        if topic:
            sb = inject_topic_recursively(sb, topic)
        return sb.model_dump_json()

    if output_type == AnimationReview:
        return MOCK_REVIEWS["default"].model_dump_json()

    # Handle Manim code injection
    manim_template = MOCK_MANIM_CODE
    if topic:
        # Replacement for the template placeholder
        manim_template = manim_template.replace("{{concept_title}}", topic)
        # Also handle any lingering default strings
        manim_template = manim_template.replace(settings.mock_topic, topic)
    else:
        manim_template = manim_template.replace("{{concept_title}}", "ConceptCast")

    return manim_template
