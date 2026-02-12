class ConceptCastException(Exception):
    """Base exception for ConceptCast application."""
    def __init__(self, message: str, details: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ProviderAPIError(ConceptCastException):
    """Raised when an external AI provider API fails."""
    pass

class RenderingError(ConceptCastException):
    """Raised when Manim or FFmpeg rendering fails."""
    pass

class PlanGenerationError(ConceptCastException):
    """Raised when curriculum planning fails."""
    pass

class StoryboardGenerationError(ConceptCastException):
    """Raised when storyboard generation fails."""
    pass

class AnimationGenerationError(ConceptCastException):
    """Raised when animation code generation fails."""
    pass
