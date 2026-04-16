"""Custom exceptions providing structured error context for the ConceptCast system.

All exceptions inherit from ConceptCastException to provide consistent
machine-readable details alongside human-readable messages.
"""


class ConceptCastError(Exception):
    """Base exception for ConceptCast application entities.

    Attributes:
        message: A human-readable error description.
        details: Additional key-value pairs providing context about the error.
    """

    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ProviderAPIError(ConceptCastError):
    """Raised when an external AI provider API encounter a failure."""

    pass


class RenderingError(ConceptCastError):
    """Raised when the Manim or FFmpeg rendering process fails."""

    pass


class PlanGenerationError(ConceptCastError):
    """Raised when the curriculum planning phase fails to produce an output."""

    pass


class StoryboardGenerationError(ConceptCastError):
    """Raised when the storyboard generation phase fails."""

    pass


class AnimationGenerationError(ConceptCastError):
    """Raised when the animation code generation phase fails."""

    def __init__(
        self, message: str, details: dict[str, str] | None = None, logs: str | None = None
    ) -> None:
        super().__init__(message, details)
        self.logs = logs
