from pydantic import BaseModel, Field


class VisualObject(BaseModel):
    """A declaratively defined entity in a Manim animation."""

    name: str = Field(..., description="Internal name")
    type: str = Field(..., description="Manim type (e.g., 'Circle')")
    position: str = Field(..., description="Relative position")
    color: str | None = Field(None)
    label: str | None = Field(None)


class Scene(BaseModel):
    """Definition for a single high-quality animation sequence."""

    scene_id: int
    title: str
    description: str
    narration: str
    objects: list[VisualObject] = Field(default_factory=list)


class Storyboard(BaseModel):
    """The full visual orchestration plan ready for animation."""

    concept_title: str
    scenes: list[Scene]
