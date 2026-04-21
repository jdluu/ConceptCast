"""Domain models for visual orchestrations and storyboard definitions.

Defines the abstract visual representation of scenes and objects that the
Manim engine eventually renders.
"""

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
        bounding_box: Optional (width, height) of the object for spatial tracking.
    """

    name: str = Field(..., description="Internal name")
    type: str = Field(..., description="Manim type (e.g., 'Circle')")
    position: str = Field(..., description="Relative position")
    color: str | None = Field(None, description="Visual color or hex string")
    label: str | None = Field(None, description="Associated text label")
    parameters: dict[str, object] = Field(
        default_factory=dict, description="Detailed Manim parameters"
    )
    bounding_box: tuple[float, float] | None = Field(
        default=None, description="(width, height) of the object for spatial tracking"
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

    def is_structurally_valid(self) -> tuple[bool, list[str]]:
        """Performs non-LLM structural validation of the storyboard.

        Checks for sequential scene IDs, missing objects, and empty text fields.

        Returns:
            tuple: (is_valid: bool, issues: list[str])
        """
        issues: list[str] = []
        if not self.scenes:
            issues.append("Storyboard must contain at least one scene.")
            return False, issues

        scene_ids = [s.scene_id for s in self.scenes]
        if scene_ids != sorted(scene_ids):
            issues.append("Scene IDs must be strictly increasing.")
        if scene_ids and scene_ids[0] != 1:
            issues.append("Scene IDs must start at 1.")
        if len(set(scene_ids)) != len(scene_ids):
            issues.append("Scene IDs must be unique.")

        for scene in self.scenes:
            prefix = f"Scene {scene.scene_id}:"
            if not (scene.title or "").strip():
                issues.append(f"{prefix} missing title.")
            if not (scene.description or "").strip():
                issues.append(f"{prefix} missing description.")
            if not (scene.narration or "").strip():
                issues.append(f"{prefix} missing narration.")
            if not scene.objects:
                issues.append(f"{prefix} missing visual objects.")

        return len(issues) == 0, issues
