"""Domain models for visual orchestrations and storyboard definitions.

Defines the abstract visual representation of scenes and objects that the
Manim engine eventually renders.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class VisualObject(BaseModel):
    """A declaratively defined entity in a Manim animation.

    Attributes:
        name: Internal name of the object.
        type: Manim type (e.g., 'Circle', 'Axes').
        position: Relative position constant or coordinate.
        color: Visual color constant or hex string.
        label: Text label associated with the object.
        parameters: Optional dictionary of specific Manim parameters (e.g., {'radius': 1.0}).
    """

    name: str = Field(..., description="Internal name")
    type: str = Field(..., description="Manim type (e.g., 'Circle')")
    position: str = Field(..., description="Relative position")
    color: str | None = Field(None, description="Visual color or hex string")
    label: str | None = Field(None, description="Associated text label")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Detailed Manim parameters"
    )

    @field_validator("name", "type", "position")
    @classmethod
    def validate_non_empty_core_fields(cls, value: str) -> str:
        normalized = value.strip()
        if normalized.lower() in {"", "__missing__", "missing", "tbd", "n/a", "..."}:
            raise ValueError(
                "VisualObject core fields must be non-empty and non-placeholder."
            )
        return normalized


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

    @field_validator("scenes")
    @classmethod
    def validate_scenes(cls, v: list[Scene]) -> list[Scene]:
        """Ensures that at least one scene is defined."""
        if not v:
            raise ValueError("Storyboard must contain at least one scene.")
        return v
