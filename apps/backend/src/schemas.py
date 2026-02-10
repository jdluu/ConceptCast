from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class TeachingStep(BaseModel):
    """
    Represents a single step in the pedagogical sequence.
    """

    step_id: int = Field(..., description="Sequential ID of the step")
    concept: str = Field(..., description="The specific sub-concept being taught")
    visual_metaphor: str = Field(
        ..., description="Visual analogy (e.g., 'climbing a hill' for gradient descent)"
    )
    narration: str = Field(..., description="Voiceover script for this step")


class CurriculumPlan(BaseModel):
    """
    Top-level plan containing the full sequence of teaching steps for a topic.
    """

    concept_title: str = Field(..., description="Title of the main concept")
    target_audience: str = Field(..., description="Level (e.g., 'Undergraduate CS')")
    teaching_steps: List[TeachingStep] = Field(..., description="Ordered steps")


class ValidationResult(BaseModel):
    """
    Pedagogical validation results for a curriculum plan.
    """

    is_valid: bool = Field(
        ..., description="Whether the plan passes pedagogical standards"
    )
    feedback: str = Field(..., description="Constructive feedback or validation errors")
    suggestions: List[str] = Field(
        default_factory=list, description="Specific improvement ideas"
    )


class VisualObject(BaseModel):
    """
    Represents a visual entity in a Manim scene.
    """

    name: str = Field(..., description="Internal name (e.g., 'main_graph')")
    type: str = Field(
        ..., description="Manim type (e.g., 'Axes', 'FunctionGraph', 'Dot')"
    )
    position: str = Field(
        ..., description="Relative position (e.g., 'ORIGIN', 'UP * 2')"
    )
    color: Optional[str] = Field(None, description="Hex or Manim color constant")
    label: Optional[str] = Field(None, description="Latex or text label")


class Scene(BaseModel):
    """
    A single scene in the storyboard, mapping to a Manim Scene class.
    """

    scene_id: int
    title: str = Field(..., description="Short title of the scene")
    description: str = Field(
        ..., description="Detailed description of what happens visually"
    )
    narration: str = Field(..., description="Voiceover script for this scene")
    objects: List[VisualObject] = Field(
        default_factory=list, description="Visual entities"
    )


class Storyboard(BaseModel):
    """
    A complete visual orchestration of a curriculum.
    """

    concept_title: str
    scenes: List[Scene]


class JobStatus(BaseModel):
    """
    Status tracking model for a ConceptCast generation job.
    """

    job_id: str
    status: Literal[
        "planning",
        "validating",
        "architecting",
        "rendering",
        "reviewing",
        "completed",
        "failed",
    ]
    current_step: Optional[str] = None
    plan: Optional[dict] = None
    validation: Optional[dict] = None
    storyboard: Optional[dict] = None
    manim_code: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    mode: Literal["live", "mock"] = Field(
        "live",
        description=(
            "Execution mode: 'live' uses real AI APIs, "
            "'mock' uses local simulated responses"
        ),
    )


class JobRequest(BaseModel):
    """
    Request model for creating a new job.
    """

    topic: str = Field(..., description="The main concept to explain")
    target_audience: str = Field(
        "Undergraduate CS", description="Optional knowledge level"
    )
    provider: Optional[str] = Field(None, description="Explicit model provider")
    model_id: Optional[str] = Field(None, description="Explicit model ID")


class ProviderModels(BaseModel):
    provider: str
    models: List[str]


class AvailableModelsResponse(BaseModel):
    available: List[ProviderModels]
