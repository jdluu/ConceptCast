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
    with pytest.raises(RuntimeError, match="Import from module 'subprocess' is not allowed"):
        sanitize_manim_code(banned_code)


def test_sanitize_banned_builtins() -> None:
    """Verifies that executing banned builtins raises a RuntimeError."""
    banned_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        eval("1 + 1")
"""
    with pytest.raises(RuntimeError, match="Call to unsafe builtin 'eval' is forbidden"):
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
    with pytest.raises(RuntimeError, match="Call to unsafe builtin 'getattr' is forbidden"):
        sanitize_manim_code(banned_code)

    banned_attr_code = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        x = self.__globals__
"""
    with pytest.raises(RuntimeError, match="Access to unsafe attribute '__globals__' is forbidden"):
        sanitize_manim_code(banned_attr_code)


def test_sanitize_missing_scene_gen() -> None:
    """Verifies that omitting the SceneGen class raises a RuntimeError."""
    no_scene_gen = """
from manim import *

class MyScene(Scene):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(RuntimeError, match="Required 'SceneGen' class missing"):
        sanitize_manim_code(no_scene_gen)


def test_sanitize_multiple_scene_gen() -> None:
    """Verifies that having more than one SceneGen class raises a RuntimeError."""
    multiple_scene_gen = """
from manim import *

class SceneGen(Scene):
    def construct(self) -> None:
        pass

class SceneGen(Scene):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(RuntimeError, match="Exactly one class named 'SceneGen' is required"):
        sanitize_manim_code(multiple_scene_gen)


def test_sanitize_scene_gen_base() -> None:
    """Verifies that SceneGen must inherit from Scene."""
    bad_base = """
from manim import *

class SceneGen(object):
    def construct(self) -> None:
        pass
"""
    with pytest.raises(RuntimeError, match="SceneGen must inherit from Scene"):
        sanitize_manim_code(bad_base)


def test_sanitize_scene_gen_construct() -> None:
    """Verifies that SceneGen must define construct(self)."""
    bad_construct = """
from manim import *

class SceneGen(Scene):
    def setup(self) -> None:
        pass
"""
    with pytest.raises(RuntimeError, match="SceneGen must define construct\\(self\\)"):
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
    assert "fill_color='BLUE'" in sanitized
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
