"""Domain models for the iterative animation review process.

Defines the structured feedback and approval mechanisms for AI-generated
visual outputs.
"""

from pydantic import BaseModel, Field, model_validator


class AnimationReview(BaseModel):
    """Automated review comparing rendered output to the storyboard.

    Attributes:
        approved: True if the animation is acceptable.
        issues: List of identified visual or technical problems.
        revision_instructions: Instructions for correction by the Animator.
    """

    approved: bool = Field(..., description="Whether the animation is acceptable")
    issues: list[str] = Field(
        default_factory=list, description="Specific problems found"
    )
    revision_instructions: str = Field(
        ..., description="Actionable instructions to fix issues"
    )

    @model_validator(mode="after")
    def validate_consistency(self) -> "AnimationReview":
        cleaned_issues = [issue.strip() for issue in self.issues if issue.strip()]
        self.issues = cleaned_issues

        if self.approved and not cleaned_issues:
            return self

        if not self.approved and not cleaned_issues:
            raise ValueError("AnimationReview with approved=False must include issues.")
        if not self.approved and not self.revision_instructions.strip():
            raise ValueError(
                "AnimationReview with approved=False must include revision instructions."
            )
        return self
