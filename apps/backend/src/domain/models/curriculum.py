from typing import Any

from pydantic import BaseModel, Field


class TeachingStep(BaseModel):
    """A granular educational unit within a curriculum sequence."""
    step_id: int = Field(..., description="Sequential ID of the step")
    concept: str = Field(..., description="The specific sub-concept being taught")
    visual_metaphor: str = Field(..., description="Visual analogy")
    narration: str = Field(..., description="Voiceover script for this step")

class CurriculumPlan(BaseModel):
    """A structured educational roadmap for a complex topic."""
    concept_title: str = Field(..., description="Title of the main concept")
    target_audience: str = Field(..., description="Level (e.g., 'Undergraduate CS')")
    teaching_steps: list[TeachingStep] = Field(..., description="Ordered steps")

class ValidationResult(BaseModel):
    """Pedagogical audit results for a curriculum plan."""
    is_valid: bool = Field(
        ..., description="Whether the plan passes pedagogical standards"
    )
    feedback: str = Field(..., description="Constructive feedback or validation errors")
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    scores: dict[str, Any] = Field(default_factory=dict)
    issues: list[dict[str, str]] = Field(default_factory=list)
