from typing import Any, Literal

from pydantic import BaseModel, Field


class TeachingStep(BaseModel):
    """
    Represents a single step in the pedagogical sequence.

    Attributes:
        step_id (int): Sequential ID of the step.
        concept (str): The specific sub-concept being taught.
        visual_metaphor (str): Visual analogy used for explanation.
        narration (str): Voiceover script for this step.
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

    Attributes:
        concept_title (str): Title of the main concept.
        target_audience (str): Target audience level (e.g., 'Undergraduate CS').
        teaching_steps (list[TeachingStep]): Ordered list of teaching steps.
    """

    concept_title: str = Field(..., description="Title of the main concept")
    target_audience: str = Field(..., description="Level (e.g., 'Undergraduate CS')")
    teaching_steps: list[TeachingStep] = Field(..., description="Ordered steps")


class ValidationResult(BaseModel):
    """
    Pedagogical validation results for a curriculum plan.

    Attributes:
        is_valid (bool): Whether the plan passes pedagogical standards.
        feedback (str): Constructive feedback or validation errors.
        suggestions (list[str]): Specific ideas for improvement.
        metadata (dict): Additional metadata about the validation process.
        scores (dict): Quantitative scores for pedagogical aspects.
        issues (list[dict]): Detailed list of identified issues.
    """

    is_valid: bool = Field(
        ..., description="Whether the plan passes pedagogical standards"
    )
    feedback: str = Field(..., description="Constructive feedback or validation errors")
    suggestions: list[str] = Field(
        default_factory=list, description="Specific improvement ideas"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the validation process",
    )
    scores: dict[str, Any] = Field(
        default_factory=dict,
        description="Quantitative scores for different pedagogical aspects",
    )
    issues: list[dict[str, str]] = Field(
        default_factory=list,
        description="Detailed list of identified issues, each as a dictionary",
    )


class VisualObject(BaseModel):
    """
    Represents a visual entity in a Manim scene.

    Attributes:
        name (str): Internal name for the object (e.g., 'main_graph').
        type (str): Manim class type (e.g., 'Axes', 'Dot').
        position (str): Relative position or coordinates.
        color (str | None): Color specification (Hex or Manim constant).
        label (str | None): Optional text or Latex label.
    """

    name: str = Field(..., description="Internal name (e.g., 'main_graph')")
    type: str = Field(
        ..., description="Manim type (e.g., 'Axes', 'FunctionGraph', 'Dot')"
    )
    position: str = Field(
        ..., description="Relative position (e.g., 'ORIGIN', 'UP * 2')"
    )
    color: str | None = Field(None, description="Hex or Manim color constant")
    label: str | None = Field(None, description="Latex or text label")


class Scene(BaseModel):
    """
    A single scene in the storyboard, mapping to a Manim Scene class.

    Attributes:
        scene_id (int): Sequential ID of the scene.
        title (str): Short title of the scene.
        description (str): Detailed visual description of the scene action.
        narration (str): Voiceover script for this scene.
        objects (list[VisualObject]): List of visual entities in the scene.
    """

    scene_id: int
    title: str = Field(..., description="Short title of the scene")
    description: str = Field(
        ..., description="Detailed description of what happens visually"
    )
    narration: str = Field(..., description="Voiceover script for this scene")
    objects: list[VisualObject] = Field(
        default_factory=list, description="Visual entities"
    )


class Storyboard(BaseModel):
    """
    A complete visual orchestration of a curriculum.

    Attributes:
        concept_title (str): Title of the concept being visualized.
        scenes (list[Scene]): Ordered list of scenes.
    """

    concept_title: str
    scenes: list[Scene]


class ThoughtLog(BaseModel):
    """
    Represents a single thought streamed from an agent.
    """

    agent: str
    phase: str
    content: str
    ts: str


class AnimationReview(BaseModel):
    """Result of an AI review comparing a rendered frame to a storyboard."""

    approved: bool = Field(..., description="Whether the animation frame is acceptable")
    issues: list[str] = Field(
        default_factory=list, description="List of visual discrepancies found"
    )
    revision_instructions: str = Field(
        ..., description="Specific instructions for the animator to fix the issues"
    )


class JobSummary(BaseModel):
    """Lightweight job representation for the jobs list."""

    job_id: str
    topic: str
    status: str
    mode: str
    created_at: str
    retry_count: int
    error: str | None


class JobListResponse(BaseModel):
    jobs: list[JobSummary]


class JobStatus(BaseModel):
    """
    Status tracking model for a ConceptCast generation job.

    Attributes:
        job_id (str): Unique UUID for the job.
        status (str): Current processing status (planning, validating, etc.).
        current_step (str | None): Detail on the specific sub-step execution.
        plan (CurriculumPlan | None): The curriculum plan data.
        validation (ValidationResult | None): Generation validation data.
        storyboard (Storyboard | None): The storyboard data.
        manim_code (str | None): The generated Manim Python code.
        video_url (str | None): URL to the final rendered video.
        error (str | None): Error message if the job failed.
        mode (str): Execution mode ('live' for API calls, 'mock' for simulation).
        streamed_thoughts (list[ThoughtLog]): Live stream of agent thoughts.
    """

    job_id: str
    streamed_thoughts: list[ThoughtLog] = Field(
        default_factory=list,
        description="Live stream of agent thoughts (agent, phase, content, ts).",
    )
    status: Literal[
        "planning",
        "validating",
        "architecting",
        "rendering",
        "reviewing",
        "completed",
        "failed",
        "pending_retry",
    ]
    current_step: str | None = None
    plan: CurriculumPlan | None = None
    validation: ValidationResult | None = None
    storyboard: Storyboard | None = None
    manim_code: str | None = None
    video_url: str | None = None
    error: str | None = None
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

    Attributes:
        topic (str): The main concept to explain.
        target_audience (str): The intended audience knowledge level.
        provider (str | None): Explicit AI model provider to use.
        model_id (str | None): Explicit model ID to use.
    """

    topic: str = Field(..., description="The main concept to explain")
    target_audience: str = Field(
        "Undergraduate CS", description="Optional knowledge level"
    )
    provider: str | None = Field(None, description="Explicit model provider")
    model_id: str | None = Field(None, description="Explicit model ID")


class ProviderModels(BaseModel):
    provider: str
    models: list[str]
    display_name: str | None = None


class AvailableModelsResponse(BaseModel):
    available: list[ProviderModels]
