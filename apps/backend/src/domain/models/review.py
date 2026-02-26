from pydantic import BaseModel, Field


class AnimationReview(BaseModel):
    """Automated review comparing rendered output to the storyboard."""

    approved: bool = Field(..., description="Whether the animation is acceptable")
    issues: list[str] = Field(default_factory=list)
    revision_instructions: str = Field(..., description="Instructions to fix issues")
