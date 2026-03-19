"""Core domain models for pedagogical curriculum planning.

Defines the structure for teaching steps, full curriculum plans, and the results
of pedagogical audits.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

_PLACEHOLDER_TEXT = {"", "__missing__", "missing", "tbd", "n/a", "..."}
_MAX_NARRATION_CHARS = 700


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

    @field_validator("concept", "visual_metaphor", "narration")
    @classmethod
    def validate_non_placeholder_text(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.lower() in _PLACEHOLDER_TEXT:
            raise ValueError(
                "TeachingStep fields must be non-empty and non-placeholder."
            )
        return normalized

    @field_validator("narration")
    @classmethod
    def validate_narration_length(cls, value: str) -> str:
        if len(value) > _MAX_NARRATION_CHARS:
            raise ValueError(
                f"TeachingStep narration must be <= {_MAX_NARRATION_CHARS} characters."
            )
        return value


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


class TeachingStepsDraft(BaseModel):
    """Analyst output focused only on pedagogical step generation.

    Top-level curriculum metadata is deterministic and injected by the workflow.
    """

    teaching_steps: list[TeachingStep] = Field(
        ...,
        description="Ordered steps (5-10 items)",
        min_length=5,
        max_length=10,
    )

    @model_validator(mode="after")
    def validate_step_sequence(self) -> "TeachingStepsDraft":
        expected = 1
        for step in self.teaching_steps:
            if step.step_id != expected:
                raise ValueError(
                    "TeachingStep.step_id must be sequential starting at 1 "
                    f"(expected {expected}, got {step.step_id})."
                )
            expected += 1
        return self


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

    @model_validator(mode="after")
    def validate_consistency(self) -> "ValidationResult":
        if not self.is_valid and not self.suggestions and not self.issues:
            raise ValueError(
                "ValidationResult with is_valid=False must include suggestions or issues."
            )
        return self
