"""Domain models for the Global Context Object (GCO).

The GCO acts as the shared blackboard for the Agent Council, maintaining
consistency across pedagogical steps, visual styles, and spatial layouts.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .curriculum import CurriculumPlan
from .storyboard import Storyboard


class GlobalStyle(BaseModel):
    """Defines the visual 'brand' and stylistic constraints of the video."""

    primary_font: str = "Sans"
    background_color: str = "#181825"  # Catppuccin Mocha Mantle
    default_stroke_width: float = 2.0
    color_palette: list[str] = [
        "#89b4fa",  # Blue
        "#fab387",  # Peach
        "#f38ba8",  # Maroon
        "#a6e3a1",  # Green
        "#94e2d5",  # Teal
    ]
    theme: Literal["standard", "dark", "light", "high_contrast"] = "standard"


class BoundingBox(BaseModel):
    """Represents a reserved area on the Manim screen to prevent overlaps."""

    center: str  # Manim coordinate string e.g. "UP * 2 + LEFT * 3"
    width: float
    height: float
    label: str  # e.g. "Main Title", "Core Diagram"


class SceneOccupancy(BaseModel):
    """Tracks reserved areas for a specific scene index."""

    scene_id: int
    reserved_boxes: list[BoundingBox] = Field(default_factory=list)


class VisualSymbol(BaseModel):
    """A standardized visual representation of a concept to ensure consistency."""

    concept: str
    manim_class: str  # e.g. "Circle", "Rectangle", "Brace"
    color: str  # e.g. "BLUE", "#2364AA"
    stroke_width: float = 2.0
    fill_opacity: float = 0.5
    metadata: dict[str, object] = Field(default_factory=dict)


class ErrorEvent(BaseModel):
    """Records a failure to guide the council's retry and correction logic."""

    agent: str
    step: str
    error_type: str  # e.g. "SyntaxError", "ValidationFailure"
    message: str
    context: dict[str, object] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DecisionLog(BaseModel):
    """Captures the rationale behind architectural or pedagogical choices."""

    agent: str
    rationale: str
    implications: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class WorkflowMetrics(BaseModel):
    """Real-time tracking of resource usage and timing across the council."""

    total_tokens: int = 0
    estimated_cost: float = 0.0
    start_time: datetime = Field(default_factory=datetime.utcnow)
    step_durations: dict[str, float] = Field(default_factory=dict)


class GlobalContext(BaseModel):
    """The root GCO shared across all agents in the ConceptCast council."""

    # 1. Semantic Intent & Branding
    topic: str
    user_prompt: str | None = None
    target_audience: str
    style: GlobalStyle = Field(default_factory=GlobalStyle)
    key_takeaways: list[str] = Field(default_factory=list)

    # 2. Structural State (Artifacts)
    plan: CurriculumPlan | None = None
    storyboard: Storyboard | None = None
    manim_code: str | None = None

    # 3. Visual Lexicon (Object Consistency)
    lexicon: dict[str, VisualSymbol] = Field(default_factory=dict)

    # 4. Spatial Map (Anti-Overlap)
    scene_occupancy: dict[int, SceneOccupancy] = Field(default_factory=dict)

    # 5. Resilience & Memory
    error_buffer: list[ErrorEvent] = Field(default_factory=list)
    decisions: list[DecisionLog] = Field(default_factory=list)

    # 6. Operational Health
    metrics: WorkflowMetrics = Field(default_factory=WorkflowMetrics)

    def add_error(self, agent: str, step: str, error: Exception) -> None:
        """Logs a failure into the buffer for shared learning."""
        self.error_buffer.append(
            ErrorEvent(
                agent=agent,
                step=step,
                error_type=type(error).__name__,
                message=str(error),
            )
        )

    def reserve_space(
        self, scene_id: int, center: str, width: float, height: float, label: str
    ) -> None:
        """Blocks out screen real estate for a specific scene."""
        if scene_id not in self.scene_occupancy:
            self.scene_occupancy[scene_id] = SceneOccupancy(scene_id=scene_id)
        self.scene_occupancy[scene_id].reserved_boxes.append(
            BoundingBox(center=center, width=width, height=height, label=label)
        )
