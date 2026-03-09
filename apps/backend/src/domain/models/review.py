"""Domain models for the iterative animation review process.

Defines the structured feedback and approval mechanisms for AI-generated
visual outputs.
"""

from pydantic import BaseModel, Field


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
