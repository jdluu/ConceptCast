"""Public API schema layer for the ConceptCast system.

Consolidates and re-exports internal domain models and API-specific schemas
to provide a consistent interface for the web layer.
"""

# Re-exporting domain models that are used in the API
from domain.models.curriculum import (
    CurriculumPlan as CurriculumPlan,
)
from domain.models.curriculum import (
    TeachingStep as TeachingStep,
)
from domain.models.curriculum import (
    ValidationResult as ValidationResult,
)
from domain.models.review import AnimationReview as AnimationReview
from domain.models.storyboard import (
    Scene as Scene,
)
from domain.models.storyboard import (
    Storyboard as Storyboard,
)
from domain.models.storyboard import (
    VisualObject as VisualObject,
)

from .common import (
    AvailableModelsResponse as AvailableModelsResponse,
)
from .common import (
    ProviderModels as ProviderModels,
)
from .common import (
    ThoughtLog as ThoughtLog,
)
from .jobs import (
    JobListResponse as JobListResponse,
)
from .jobs import (
    JobRequest as JobRequest,
)
from .jobs import (
    JobStatus as JobStatus,
)
from .jobs import (
    JobSummary as JobSummary,
)
