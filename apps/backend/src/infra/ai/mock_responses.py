import json
from api.schemas import CurriculumPlan, Storyboard, ValidationResult

# Realistic fragments for the Analyst agent
MOCK_PLANS = {
    "default": CurriculumPlan(
        title="Understanding Quantum Entanglement",
        target_audience="General Audience",
        steps=[
            {
                "step_id": "step_1",
                "sub_concept": "The Spin Property",
                "visual_metaphor": "Rotating spheres with glowing axes",
                "narration_script": "Imagine two particles, like tiny spinning tops. In the quantum world, their spin can be linked in a way that defies classical logic."
            },
            {
                "step_id": "step_2",
                "sub_concept": "Superposition",
                "visual_metaphor": "A blurry, shifting state between two colors",
                "narration_script": "Until measured, a particle exists in multiple states at once. This uncertainty is the heart of quantum mechanics."
            },
            {
                "step_id": "step_3",
                "sub_concept": "Non-locality",
                "visual_metaphor": "A bridge of light connecting two distant points",
                "narration_script": "Entanglement means that measuring one particle instantly determines the state of the other, no matter the distance between them."
            }
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
        scenes=[
            {
                "id": "scene_0",
                "description": "Opening shot: Two particles appearing in a void.",
                "objects": [
                    {"id": "p1", "type": "Circle", "props": {"color": "BLUE", "fill_opacity": 0.5}, "position": "LEFT"},
                    {"id": "p2", "type": "Circle", "props": {"color": "RED", "fill_opacity": 0.5}, "position": "RIGHT"}
                ],
                "animations": [
                    {"object_id": "p1", "type": "Create", "duration": 1.0},
                    {"object_id": "p2", "type": "Create", "duration": 1.0}
                ],
                "narration": "In the vastness of the quantum void, particles are never truly alone."
            }
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

def get_realistic_response(prompt: str, output_type: type) -> str:
    \"\"\"Returns a realistic-looking mock response based on the output type requested.\"\"\"
    if output_type == CurriculumPlan:
        return MOCK_PLANS["default"].model_dump_json()
    if output_type == ValidationResult:
        return MOCK_VALIDATIONS["default"].model_dump_json()
    if output_type == Storyboard:
        return MOCK_STORYBOARDS["default"].model_dump_json()
    return MOCK_MANIM_CODE
