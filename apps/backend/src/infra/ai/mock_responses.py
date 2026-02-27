import json
from api.schemas import CurriculumPlan, Storyboard, ValidationResult, TeachingStep, Scene, VisualObject

# Realistic fragments for the Analyst agent
MOCK_PLANS = {
    "default": CurriculumPlan(
        concept_title="Understanding Quantum Entanglement",
        target_audience="General Audience",
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="The Spin Property",
                visual_metaphor="Rotating spheres with glowing axes",
                narration="Imagine two particles, like tiny spinning tops. In the quantum world, their spin can be linked in a way that defies classical logic."
            ),
            TeachingStep(
                step_id=2,
                concept="Superposition",
                visual_metaphor="A blurry, shifting state between two colors",
                narration="Until measured, a particle exists in multiple states at once. This uncertainty is the heart of quantum mechanics."
            ),
            TeachingStep(
                step_id=3,
                concept="Non-locality",
                visual_metaphor="A bridge of light connecting two distant points",
                narration="Entanglement means that measuring one particle instantly determines the state of the other, no matter the distance between them."
            )
        ]
    )
}

# Realistic fragments for the Validator agent
MOCK_VALIDATIONS = {
    "default": ValidationResult(
        is_valid=True,
        feedback="The logical flow is sound and the visual metaphors are highly effective for a general audience.",
        suggestions=["Consider adding a brief recap of classical probability for contrast."]
    )
}

# Realistic fragments for the Architect agent
MOCK_STORYBOARDS = {
    "default": Storyboard(
        concept_title="Understanding Quantum Entanglement",
        scenes=[
            Scene(
                scene_id=0,
                title="Introduction to Quantum Void",
                description="Opening shot: Two particles appearing in a void.",
                narration="In the vastness of the quantum void, particles are never truly alone.",
                objects=[
                    VisualObject(name="p1", type="Circle", color="BLUE", position="LEFT"),
                    VisualObject(name="p2", type="Circle", color="RED", position="RIGHT")
                ]
            )
        ]
    )
}

# Realistic fragments for the Animator agent (Manim code)
MOCK_MANIM_CODE = """
from manim import *

class QuantumEntanglement(Scene):
    def construct(self):
        # Create particles
        p1 = Circle(color=BLUE, fill_opacity=0.5).shift(LEFT * 2)
        p2 = Circle(color=RED, fill_opacity=0.5).shift(RIGHT * 2)
        
        # Animations
        self.play(Create(p1), Create(p2))
        self.wait(1)
        
        # Narration transition
        title = Text("Quantum Entanglement", font_size=36).to_edge(UP)
        self.play(Write(title))
        self.wait(2)
"""

def inject_topic(text: str, topic: str) -> str:
    """Simple helper to replace 'Quantum Entanglement' with the user topic."""
    if not topic:
        return text
    return text.replace("Quantum Entanglement", topic).replace("quantum entanglement", topic.lower())

def get_realistic_response(prompt: str, output_type: type, topic: str | None = None) -> str:
    """Returns a realistic-looking mock response based on the output type requested."""
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
    
    if topic:
        return inject_topic(MOCK_MANIM_CODE, topic)
    return MOCK_MANIM_CODE
