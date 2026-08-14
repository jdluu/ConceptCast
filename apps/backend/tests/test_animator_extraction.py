import json

from domain.agents.animator import extract_python_code


def test_extract_python_code_accepts_known_json_code_wrapper() -> None:
    code = "from manim import *\nclass SceneGen(Scene):\n    pass\n"
    assert extract_python_code(json.dumps({"code": code})) == code.strip()


def test_extract_python_code_accepts_fenced_json_code_wrapper() -> None:
    code = "from manim import *\nclass SceneGen(Scene):\n    pass\n"
    raw = "```json\n" + json.dumps({"manim_code": code}) + "\n```"
    assert extract_python_code(raw) == code.strip()


def test_extract_python_code_does_not_select_arbitrary_json_text() -> None:
    raw = json.dumps({"explanation": "from manim import *"})
    assert extract_python_code(raw) == raw
