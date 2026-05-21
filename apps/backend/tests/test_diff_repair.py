"""Unit tests for the search-and-replace diff-based repair patch utility.

Verifies correct application of single/multiple SEARCH/REPLACE blocks,
fallback to full rewrite when markers are missing, and mismatch handling.
"""

from services.workflow.utils import apply_search_replace_patch


def test_apply_single_patch_block() -> None:
    """Verifies that a single SEARCH/REPLACE block is correctly applied."""
    original_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        circle = Circle()
        self.play(Create(circle))
"""

    patch = """
<<<<<<< SEARCH
        circle = Circle()
        self.play(Create(circle))
=======
        square = Square()
        self.play(Create(square))
>>>>>>> REPLACE
"""

    result = apply_search_replace_patch(original_code, patch)
    assert "square = Square()" in result
    assert "circle = Circle()" not in result


def test_apply_multiple_patch_blocks() -> None:
    """Verifies that multiple non-contiguous SEARCH/REPLACE blocks are correctly applied."""
    original_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        circle = Circle()
        self.play(Create(circle))
        rect = Rectangle()
        self.play(Create(rect))
"""

    patch = """
<<<<<<< SEARCH
        circle = Circle()
        self.play(Create(circle))
=======
        square = Square()
        self.play(Create(square))
>>>>>>> REPLACE

Some conversational explanation here.

<<<<<<< SEARCH
        rect = Rectangle()
        self.play(Create(rect))
=======
        triangle = Triangle()
        self.play(Create(triangle))
>>>>>>> REPLACE
"""

    result = apply_search_replace_patch(original_code, patch)
    assert "square = Square()" in result
    assert "triangle = Triangle()" in result
    assert "circle = Circle()" not in result
    assert "rect = Rectangle()" not in result


def test_fallback_full_rewrite() -> None:
    """Asserts that if no SEARCH/REPLACE block is detected, the patch is treated as a full rewrite."""
    original_code = "print('old code')"
    patch = "print('new code')"

    result = apply_search_replace_patch(original_code, patch)
    assert result == patch


def test_patch_block_mismatch() -> None:
    """Verifies that a mismatched SEARCH block is ignored and logged without crashing."""
    original_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        circle = Circle()
"""

    # The search block contains 'square = Square()' which does not exist in original_code
    patch = """
<<<<<<< SEARCH
        square = Square()
        self.play(Create(square))
=======
        triangle = Triangle()
>>>>>>> REPLACE
"""

    result = apply_search_replace_patch(original_code, patch)
    # The code should be unmodified
    assert "circle = Circle()" in result
    assert "triangle = Triangle()" not in result
