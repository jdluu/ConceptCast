"""Tests for sanitize_manim_code in infra/security/sanitizer.py."""

import pytest

from infra.security.sanitizer import sanitize_manim_code

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_CODE = """
from manim import *


class SceneGen(Scene):
    def construct(self):
        circle = Circle()
        circle.set_color(RED)
        self.add(circle)
        self.play(Create(circle))
"""


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_valid_code_passes() -> None:
    result = sanitize_manim_code(_VALID_CODE)
    assert "class SceneGen" in result


def test_strips_markdown_fences() -> None:
    fenced = f"```python\n{_VALID_CODE.strip()}\n```"
    result = sanitize_manim_code(fenced)
    assert not result.startswith("```")
    assert "class SceneGen" in result


# ---------------------------------------------------------------------------
# Color validation - the primary regression guard
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_kwarg",
    [
        'color="red"',
        "color='brown'",
        'fill_color="blue"',
        'stroke_color="green"',
    ],
)
def test_lowercase_color_raises(bad_kwarg: str) -> None:
    code = f"""
from manim import *


class SceneGen(Scene):
    def construct(self):
        c = Circle({bad_kwarg})
        self.add(c)
"""
    with pytest.raises(RuntimeError, match="Invalid color strings found"):
        sanitize_manim_code(code)


def test_hex_color_is_allowed() -> None:
    code = """
from manim import *


class SceneGen(Scene):
    def construct(self):
        c = Circle()
        c.set_color("#FF0000")
        self.add(c)
"""
    # Hex strings don't match the lowercase letter pattern, so they pass.
    result = sanitize_manim_code(code)
    assert "class SceneGen" in result


# ---------------------------------------------------------------------------
# Security checks
# ---------------------------------------------------------------------------


def test_disallowed_import_raises() -> None:
    code = """
import os
from manim import *


class SceneGen(Scene):
    def construct(self):
        pass
"""
    with pytest.raises(RuntimeError, match="not allowed"):
        sanitize_manim_code(code)


def test_banned_builtin_raises() -> None:
    code = """
from manim import *


class SceneGen(Scene):
    def construct(self):
        eval("1+1")
"""
    with pytest.raises(RuntimeError, match="unsafe builtin"):
        sanitize_manim_code(code)


def test_missing_scene_gen_raises() -> None:
    code = """
from manim import *


class WrongName(Scene):
    def construct(self):
        pass
"""
    with pytest.raises(RuntimeError, match="SceneGen"):
        sanitize_manim_code(code)


def test_empty_code_raises() -> None:
    with pytest.raises(RuntimeError, match="empty"):
        sanitize_manim_code("   ")
