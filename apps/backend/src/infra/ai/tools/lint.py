import re
import tempfile
from pathlib import Path

from loguru import logger
from pydantic_ai import RunContext

from domain.models.workflow import GlobalContext
from infra.engines.sandbox import local_sandbox

_LOWERCASE_COLOR_RE = re.compile(
    r'(?:color|fill_color|stroke_color)\s*=\s*["\']([a-z]+)["\']'
)


async def lint_manim_code(_ctx: RunContext[GlobalContext], code: str) -> str:
    """Lints generated Manim code within a sandboxed environment.

    Performs static and dynamic checks to ensure the code is valid Python
    and follows Manim-specific rules (e.g., uppercase color constants).

    Args:
        _ctx: Run context containing the global workflow state.
        code: The generated Python code to validate.

    Returns:
        A diagnostic report detailing any errors found, or 'Passed' if clean.
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
