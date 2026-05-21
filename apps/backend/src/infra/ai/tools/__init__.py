from .aesthetics import get_aesthetic_palette
from .analysis import analyze_animation_dynamism
from .lint import lint_manim_code
from .manim import prepare_manim_docs, search_manim_docs
from .patterns import lookup_manim_pattern

__all__ = [
    "prepare_manim_docs",
    "search_manim_docs",
    "lint_manim_code",
    "lookup_manim_pattern",
    "get_aesthetic_palette",
    "analyze_animation_dynamism",
]
