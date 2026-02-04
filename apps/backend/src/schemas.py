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
    artifacts: Optional[dict] = None
    mode: Literal["live", "mock"] = "live"
