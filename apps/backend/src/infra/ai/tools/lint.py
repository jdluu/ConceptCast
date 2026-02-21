import re
import tempfile
from pathlib import Path

from loguru import logger
from pydantic_ai import RunContext

from api.schemas import Storyboard
from infra.engines.sandbox import local_sandbox

# Pattern for lowercase color kwarg values - these always fail in Manim.
# Valid colors are uppercase constants (RED, BLUE) or hex strings (#FF0000).
_LOWERCASE_COLOR_RE = re.compile(
    r'(?:color|fill_color|stroke_color)\s*=\s*["\']([a-z]+)["\']'
)


async def lint_manim_code(ctx: RunContext[Storyboard], code: str) -> str:
    """Lints generated Manim code in the sandboxed environment.

    Performs two checks:
    1. Python syntax via ``py_compile`` inside the Podman container.
    2. Heuristic scan for lowercase color strings (common AI hallucination).

    Args:
        ctx: Run context (deps=Storyboard).
        code: The Manim Python code to lint.

    Returns:
        str: A human-readable lint report, or 'Passed' when clean.
    """
    logger.info("Executing sandbox linting...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        code_file = tmp_path / "scene.py"
        code_file.write_text(code)

        result = await local_sandbox.run_check(tmp_path, "scene.py")

        if result.stderr:
            return f"Syntax/Import Error:\n{result.stderr}"

        matches = _LOWERCASE_COLOR_RE.findall(code)
        if matches:
            names = ", ".join(matches)
            return (
                f"Warning: Found lowercase color strings: {names}. "
                "Use uppercase constants (e.g. RED, BLUE, BROWN) or hex strings."
            )

    return "Passed: No syntax errors or common pitfalls detected."
