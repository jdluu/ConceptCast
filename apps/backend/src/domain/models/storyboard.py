"""Domain models for visual orchestrations and storyboard definitions.

Defines the abstract visual representation of scenes and objects that the
Manim engine eventually renders.
"""

from pydantic import BaseModel, Field


class VisualObject(BaseModel):
    """A declaratively defined entity in a Manim animation.

    Attributes:
        name: Internal name of the object.
        type: Manim type (e.g., 'Circle', 'Axes').
        position: Relative position constant or coordinate.
        color: Visual color constant or hex string.
        label: Text label associated with the object.
    """

    name: str = Field(..., description="Internal name")
    type: str = Field(..., description="Manim type (e.g., 'Circle')")
    position: str = Field(..., description="Relative position")
    color: str | None = Field(None, description="Visual color or hex string")
    label: str | None = Field(None, description="Associated text label")


class Scene(BaseModel):
    """Definition for a single animation sequence.

    Attributes:
        scene_id: Sequential ID of the scene.
        title: Descriptive title.
        description: Abstract visual description.
        narration: Voiceover text to be synchronized.
        objects: List of visual objects to render.
    """

    scene_id: int = Field(..., description="Sequential ID of the scene")
    title: str = Field(..., description="Descriptive title")
    description: str = Field(..., description="Visual overview")
    narration: str = Field(..., description="Voiceover script")
    objects: list[VisualObject] = Field(
        default_factory=list, description="Visual entities in the scene"
    )


class Storyboard(BaseModel):
    """The full visual orchestration plan for an animation.

    Attributes:
        concept_title: Main topic title.
        scenes: Ordered sequence of scenes.
    """

    concept_title: str = Field(..., description="Title of the concept")
    scenes: list[Scene] = Field(..., description="Ordered animation sequences")
