import pytest

from services.rendering import extract_and_validate_manim_code


def test_valid_manim_code():
    code = """
from manim import *
import math

class SceneGen(Scene):
    def construct(self):
        c = Circle()
        self.play(Create(c))
"""
    assert extract_and_validate_manim_code(code) == code.strip()


def test_banned_import_os():
    code = """
import os
from manim import *

class SceneGen(Scene):
    def construct(self):
        pass
"""
    with pytest.raises(RuntimeError, match="Import of module 'os' is not allowed"):
        extract_and_validate_manim_code(code)


def test_banned_import_sys():
    code = """
from sys import modules
from manim import *

class SceneGen(Scene):
    def construct(self):
        pass
"""
    with pytest.raises(RuntimeError, match="Import from module 'sys' is not allowed"):
        extract_and_validate_manim_code(code)


def test_banned_builtin_eval():
    code = """
from manim import *

class SceneGen(Scene):
    def construct(self):
        eval("print('hello')")
"""
    with pytest.raises(
        RuntimeError, match="Call to unsafe builtin 'eval' is forbidden"
    ):
        extract_and_validate_manim_code(code)


def test_banned_builtin_exec():
    code = """
from manim import *

class SceneGen(Scene):
    def construct(self):
        exec("print('hello')")
"""
    with pytest.raises(
        RuntimeError, match="Call to unsafe builtin 'exec' is forbidden"
    ):
        extract_and_validate_manim_code(code)


def test_banned_dunder_attribute():
    code = """
from manim import *

class SceneGen(Scene):
    def construct(self):
        print([].__subclasses__())
"""
    # This might match "Access to unsafe attribute '__subclasses__' is forbidden"
    with pytest.raises(
        RuntimeError, match="Access to unsafe attribute '__subclasses__' is forbidden"
    ):
        extract_and_validate_manim_code(code)


def test_obfuscated_import():
    code = """
from manim import *

class SceneGen(Scene):
    def construct(self):
        __import__("os").system("echo hacked")
"""
    # __import__ is a banned builtin call
    with pytest.raises(
        RuntimeError, match="Call to unsafe builtin '__import__' is forbidden"
    ):
        extract_and_validate_manim_code(code)


def test_missing_scenegen_class():
    code = """
from manim import *

class MyScene(Scene):
    def construct(self):
        pass
"""
    with pytest.raises(
        RuntimeError, match="Generated code must define a class named SceneGen"
    ):
        extract_and_validate_manim_code(code)


def test_syntax_error():
    code = """
from manim import *
class SceneGen(Scene):
    def construct(self):
        if True
            pass
"""
    with pytest.raises(
        RuntimeError, match="Generated Manim code has a Python syntax error"
    ):
        extract_and_validate_manim_code(code)
