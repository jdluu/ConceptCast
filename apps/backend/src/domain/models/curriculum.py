"""Core domain models for pedagogical curriculum planning.

Defines the structure for teaching steps, full curriculum plans, and the results
of pedagogical audits.
"""

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

    step_id: int | str = Field(..., description="Sequential ID of the step")
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

    def is_structurally_valid(self) -> tuple[bool, list[str]]:
        """Performs non-LLM structural validation of the curriculum plan.

        Checks for empty fields, placeholder text, and correct step counts.

        Returns:
            tuple: (is_valid: bool, issues: list[str])
        """
        issues: list[str] = []
        concept = (self.concept_title or "").strip().lower()
        
        if concept in _PLACEHOLDER_TEXT:
            issues.append("concept_title is empty or placeholder")
        
        # We are lenient with target_audience during structural checks
        # as it can be hydrated from the request.

        if not self.teaching_steps:
            issues.append("teaching_steps is empty")
        else:
            if not 5 <= len(self.teaching_steps) <= 10:
                issues.append(
                    f"teaching_steps length must be between 5 and 10 (got {len(self.teaching_steps)})"
                )
            for i, step in enumerate(self.teaching_steps, start=1):
                if not step.concept or not step.concept.strip():
                    issues.append(f"teaching_steps[{i}].concept is empty")
                if not step.visual_metaphor or not step.visual_metaphor.strip():
                    issues.append(f"teaching_steps[{i}].visual_metaphor is empty")
                if not step.narration or not step.narration.strip():
                    issues.append(f"teaching_steps[{i}].narration is empty")

        return len(issues) == 0, issues


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
        # Ensure we have a unique set of IDs, regardless of type
        ids = [step.step_id for step in self.teaching_steps]
        if len(set(ids)) != len(ids):
            raise ValueError(f"TeachingStep IDs must be unique. Found: {ids}")
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
    metadata: dict[str, object] = Field(default_factory=dict)
    scores: dict[str, object] = Field(default_factory=dict)
    issues: list[dict[str, str]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_consistency(self) -> "ValidationResult":
        if not self.is_valid and not self.suggestions and not self.issues:
            raise ValueError(
                "ValidationResult with is_valid=False must include suggestions or issues."
            )
        return self
