"""Core domain models for pedagogical curriculum planning.

Defines the structure for teaching steps, full curriculum plans, and the results
of pedagogical audits.
"""

from typing import Any

from pydantic import BaseModel, Field


class TeachingStep(BaseModel):
    """A granular educational unit within a curriculum sequence.

    Attributes:
        step_id: Sequential ID of the step.
        concept: The specific sub-concept being taught.
        visual_metaphor: Visual analogy to represent the concept.
        narration: Voiceover script for this step.
    """

    step_id: int = Field(..., description="Sequential ID of the step")
    concept: str = Field(..., description="The specific sub-concept being taught")
    visual_metaphor: str = Field(..., description="Visual analogy")
    narration: str = Field(..., description="Voiceover script for this step")


class CurriculumPlan(BaseModel):
    """A structured educational roadmap for a complex topic.

    Attributes:
        concept_title: Title of the main concept.
        target_audience: Level of the target audience.
        teaching_steps: Ordered pedagogical steps.
    """

    concept_title: str = Field(..., description="Title of the main concept")
    target_audience: str = Field(..., description="Level (e.g., 'Undergraduate CS')")
    teaching_steps: list[TeachingStep] = Field(..., description="Ordered steps")


class ValidationResult(BaseModel):
    """Pedagogical audit results for a curriculum plan.

    Attributes:
        is_valid: Whether the plan passes pedagogical standards.
        feedback: Constructive feedback or validation errors.
        suggestions: List of actionable improvement suggestions.
        metadata: Additional diagnostic information.
        scores: Qualitative scores for different aspects.
        issues: Specific issues identified during the audit.
    """

    is_valid: bool = Field(
        ..., description="Whether the plan passes pedagogical standards"
    )
    feedback: str = Field(..., description="Constructive feedback or validation errors")
    suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    scores: dict[str, Any] = Field(default_factory=dict)
    issues: list[dict[str, str]] = Field(default_factory=list)
