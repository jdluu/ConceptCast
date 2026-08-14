"""Unit tests for the Manim code sanitizer.

Verifies whitelisted imports, banned builtins, forbidden dunder attributes,
color auto-correction, and mandatory SceneGen structure.
"""

import pytest

from infra.security.sanitizer import sanitize_manim_code


def test_sanitize_valid_manim_code() -> None:
    """Verifies that standard, safe Manim code is successfully accepted."""
    valid_code = """
from manim import *
import math

class SceneGen(Scene):
    def construct(self) -> None:
        circle = Circle()
        self.play(Create(circle))
"""
    result = sanitize_manim_code(valid_code)
    assert "class SceneGen(Scene):" in result
    assert "self.play(Create(circle))" in result


def test_sanitize_banned_imports() -> None:
    """Verifies that importing non-whitelisted modules raises a RuntimeError."""
    banned_code = """
from manim import *
import os

class SceneGen(Scene):
    def construct(self) -> None:
        os.system("echo hacked")
"""
    with pytest.raises(RuntimeError, match="Import of module 'os' is not allowed"):
        sanitize_manim_code(banned_code)


def test_sanitize_banned_imports_from() -> None:
    """Verifies that importing from non-whitelisted modules raises a RuntimeError."""
    banned_code = """
from manim import *
from subprocess import Popen

class SceneGen(Scene):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(
        RuntimeError, match="Import from module 'subprocess' is not allowed"
    ):
        sanitize_manim_code(banned_code)


def test_sanitize_banned_builtins() -> None:
    """Verifies that executing banned builtins raises a RuntimeError."""
    banned_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        eval("1 + 1")
"""
    with pytest.raises(
        RuntimeError, match="Call to unsafe builtin 'eval' is forbidden"
    ):
        sanitize_manim_code(banned_code)


def test_sanitize_dangerous_attributes() -> None:
    """Verifies that accessing dangerous attributes raises a RuntimeError."""
    banned_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        getattr(self, "__globals__")
"""
    # getattr itself is banned, but let's also test direct attribute access
    with pytest.raises(
        RuntimeError, match="Call to unsafe builtin 'getattr' is forbidden"
    ):
        sanitize_manim_code(banned_code)

    banned_attr_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        x = self.__globals__
"""
    with pytest.raises(
        RuntimeError, match="Access to unsafe attribute '__globals__' is forbidden"
    ):
        sanitize_manim_code(banned_attr_code)


def test_sanitize_missing_scene_gen() -> None:
    """Verifies that omitting a class inheriting from Scene raises a RuntimeError."""
    no_scene_gen = """
from manim import *

class MyScene(object):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(
        RuntimeError,
        match="Required class inheriting from Scene or ThreeDScene missing",
    ):
        sanitize_manim_code(no_scene_gen)


def test_sanitize_multiple_scene_gen() -> None:
    """Verifies that having more than one class inheriting from Scene/ThreeDScene raises a RuntimeError."""
    multiple_scene_gen = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        pass

class AnotherScene(Scene):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(
        RuntimeError,
        match="Exactly one class inheriting from Scene or ThreeDScene is required",
    ):
        sanitize_manim_code(multiple_scene_gen)


def test_sanitize_scene_gen_base() -> None:
    """Verifies that a class that does not inherit from Scene or ThreeDScene is not matched."""
    bad_base = """
from manim import *

class SceneGen(object):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(
        RuntimeError,
        match="Required class inheriting from Scene or ThreeDScene missing",
    ):
        sanitize_manim_code(bad_base)


def test_sanitize_scene_gen_construct() -> None:
    """Verifies that the class must define construct(self)."""
    bad_construct = """
from manim import *

class CustomScene(Scene):
    def setup(self) -> None:
        pass
"""
    with pytest.raises(
        RuntimeError, match="CustomScene must define construct\\(self\\)"
    ):
        sanitize_manim_code(bad_construct)


def test_sanitize_lowercase_colors() -> None:
    """Asserts that lowercase color kwargs are auto-corrected to uppercase."""
    code_with_lowercase_color = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        circle = Circle(color="red", fill_color='blue', stroke_color="green")
        self.play(Create(circle))
"""
    sanitized = sanitize_manim_code(code_with_lowercase_color)
    assert 'color="RED"' in sanitized
    assert 'fill_color="BLUE"' in sanitized
    assert 'stroke_color="GREEN"' in sanitized


def test_sanitize_chatter_and_fences() -> None:
    """Asserts that markdown code fences and conversational filler are correctly stripped."""
    fence_code = """
Sure! Here is the Manim code you requested:
```python
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        pass
```
Let me know if you need any changes!
"""
    sanitized = sanitize_manim_code(fence_code)
    assert "Sure!" not in sanitized
    assert "class SceneGen(Scene):" in sanitized


def test_sanitize_add_numbers_num_range() -> None:
    """Verifies that calling add_numbers with num_range raises a RuntimeError."""
    bad_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        line = NumberLine()
        line.add_numbers(num_range=(-5, 6))
"""
    with pytest.raises(
        RuntimeError, match="add_numbers\\(\\) does not accept a 'num_range' parameter"
    ):
        sanitize_manim_code(bad_code)


def test_sanitize_regular_polygon_side_length() -> None:
    """Verifies that creating a RegularPolygon with side_length raises a RuntimeError."""
    bad_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        poly = RegularPolygon(n=3, side_length=2.0)
"""
    with pytest.raises(
        RuntimeError, match="RegularPolygon does not accept a 'side_length' parameter"
    ):
        sanitize_manim_code(bad_code)


def test_sanitize_divider_lines_auto_repair() -> None:
    """Verifies that divider lines missing leading '#' are auto-repaired and pass."""
    code_with_stray_dividers = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        title = Text("Test")
        
        ------------------------------------------------------------
        # 1. Start animations
        ------------------------------------------------------------
        self.play(Write(title))
"""
    # Without auto-repair, this would raise a RuntimeError/SyntaxError due to the stray dashes.
    sanitized = sanitize_manim_code(code_with_stray_dividers)
    assert "# ------------------------------------------------------------" in sanitized
    assert "class SceneGen(Scene):" in sanitized


def test_sanitize_normalize_indentation() -> None:
    """Verifies that class/method indentation inconsistencies are normalized and pass."""
    inconsistent_code = """
from manim import *

class SceneGen(Scene):
 def construct(self):
        self.clear()
        circle = Circle()
        self.play(Create(circle))
"""
    sanitized = sanitize_manim_code(inconsistent_code)
    assert "class SceneGen(Scene):" in sanitized
    # Indentation should be successfully parsed and formatted to standard 4/8 spaces by Ruff
    assert (
        "    def construct(self):" in sanitized
        or "    def construct(self) -> None:" in sanitized
    )
    assert "        self.clear()" in sanitized


def test_sanitize_unicode_space_normalization() -> None:
    """Verifies that narrow no-break space (U+202F) is normalized to a standard space."""
    code_with_unicode_spaces = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        self.wait(1.0) # There is a U+202F narrow no-break space before the hash
"""
    sanitized = sanitize_manim_code(code_with_unicode_spaces)
    assert "\u202f" not in sanitized
    assert "self.wait(1.0)" in sanitized


def test_sanitize_comment_auto_repair_en_dash() -> None:
    """Verifies that text lines with an en-dash missing the '#' are auto-commented."""
    code_with_stray_en_dash = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        title = Text("Title")
        
        0.5 s – grow the title from center
        self.play(Write(title))
"""
    sanitized = sanitize_manim_code(code_with_stray_en_dash)
    assert (
        "# 0.5 s – grow the title from center" in sanitized
        or "# 0.5s – grow the title from center" in sanitized
        or "– grow" in sanitized
    )


def test_sanitize_auto_imports_only_curated_names() -> None:
    """Known standard-library/numpy names are repaired without guessing."""
    code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        point = np.array([Path('.').name, pi])
        self.add(Text(str(point)))
"""
    sanitized = sanitize_manim_code(code)
    assert "import numpy as np" in sanitized
    assert "from pathlib import Path" in sanitized
    assert "from math import pi" in sanitized


def test_sanitize_reports_self_at_class_scope() -> None:
    """Class-scope self usage receives a targeted, non-mutating diagnostic."""
    code = """
from manim import *

class SceneGen(Scene):
    self.clear()

    def construct(self) -> None:
        self.wait(1)
"""
    with pytest.raises(RuntimeError, match="Name 'self' is used outside a method"):
        sanitize_manim_code(code)
