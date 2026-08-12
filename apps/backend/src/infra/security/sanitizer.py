import ast
import json
import re

# Opening code fence (optional "python" / "py")
_CODE_FENCE_START = re.compile(r"^\s*```(?:python|py)?\s*\n?", re.IGNORECASE)

# Allowed modules for import
_ALLOWED_MODULES = {
    "manim",
    "math",
    "numpy",
    "random",
    "datetime",
    "itertools",
    "functools",
    "string",
    "typing",
}

# Builtin functions that are explicitly banned
_BANNED_BUILTINS = {
    "exec",
    "eval",
    "compile",
    "open",
    "input",
    "breakpoint",
    "getattr",
    "setattr",
    "delattr",
    "__import__",
    "globals",
    "locals",
    "vars",
    "memoryview",
}

# Dangerous dunder attributes
_DANGEROUS_ATTRIBUTES = {
    "__subclasses__",
    "__bases__",
    "__globals__",
    "__code__",
    "__closure__",
    "__func__",
    "__self__",
    "__module__",
    "__dict__",
}

_LEGACY_MANIM_METHOD_FIXES = {
    "fade_in": "Use self.play(FadeIn(mobject)) for Manim Community v0.20.1.",
    "fade_out": "Use self.play(FadeOut(mobject)) for Manim Community v0.20.1.",
}

_DISALLOWED_MANIM_CLASSES = {
    "ImageMobject",
    "SVGMobject",
}

# Regex to detect lowercase color kwarg values, e.g. color="red" which
# will raise at runtime. Manim constants are always CAPS (RED, BROWN, etc.).
_LOWERCASE_COLOR_RE = re.compile(
    r'(?:color|fill_color|stroke_color)\s*=\s*["\']([a-z]+)["\']'
)
_CODE_FENCE_BLOCK_RE = re.compile(
    r"```(?:python|py)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL
)
_DIVIDER_LINE_RE = re.compile(r"^(\s*)([-=*~_]{3,})\s*$")


class ASTSanitizer(ast.NodeVisitor):
    """AST-based sanitizer for validating AI-generated Manim code.

    This visitor inspects the Abstract Syntax Tree (AST) of the generated code
     to ensure it does not perform unsafe operations such as arbitrary IO,
    system calls, dynamic execution (exec/eval), or access to dangerous
    dunder attributes.

    Attributes:
        _ALLOWED_MODULES (Set[str]): Modules permitted for import.
        _BANNED_BUILTINS (Set[str]): Builtin functions explicitly forbidden.
        _DANGEROUS_ATTRIBUTES (Set[str]): Attributes forbidden from access.
    """

    def visit_Import(self, node: ast.Import) -> None:
        """Validates that all imported modules are within the allowed whitelist.

        Args:
            node (ast.Import): The import node to inspect.

        Raises:
            RuntimeError: If a module name is not in the allowed list.
        """
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module not in _ALLOWED_MODULES:
                raise RuntimeError(f"Import of module '{alias.name}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Validates that 'from x import y' statements target allowed modules.

        Args:
            node (ast.ImportFrom): The import-from node to inspect.

        Raises:
            RuntimeError: If the source module is not in the allowed list.
        """
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module not in _ALLOWED_MODULES:
                raise RuntimeError(
                    f"Import from module '{node.module}' is not allowed."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Checks for calls to banned builtin functions like 'eval' or 'exec'.

        Args:
            node (ast.Call): The function call node to inspect.

        Raises:
            RuntimeError: If an unsafe builtin function is called.
        """
        if isinstance(node.func, ast.Name) and node.func.id in _BANNED_BUILTINS:
            raise RuntimeError(f"Call to unsafe builtin '{node.func.id}' is forbidden.")
        if (
            isinstance(node.func, ast.Name)
            and node.func.id in _DISALLOWED_MANIM_CLASSES
        ):
            raise RuntimeError(
                f"Use of '{node.func.id}' is disallowed in ConceptCast policy."
            )
        if isinstance(node.func, ast.Name) and node.func.id == "RegularPolygon":
            for kw in node.keywords:
                if kw.arg == "side_length":
                    raise RuntimeError(
                        "RegularPolygon does not accept a 'side_length' parameter. "
                        "Use 'radius' to size the regular polygon instead."
                    )
        if isinstance(node.func, ast.Attribute):
            legacy_method = _LEGACY_MANIM_METHOD_FIXES.get(node.func.attr)
            if legacy_method:
                raise RuntimeError(
                    f"Unsupported Manim call '.{node.func.attr}()'. {legacy_method}"
                )
            if node.func.attr == "add_numbers":
                for kw in node.keywords:
                    if kw.arg == "num_range":
                        raise RuntimeError(
                            "add_numbers() does not accept a 'num_range' parameter. "
                            "Call add_numbers() without arguments; it automatically uses "
                            "the parent line's x_range."
                        )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Checks for forbidden attribute access (e.g., '__globals__').

        Args:
            node (ast.Attribute): The attribute access node to inspect.

        Raises:
            RuntimeError: If a dangerous attribute is accessed.
        """
        if node.attr in _DANGEROUS_ATTRIBUTES:
            raise RuntimeError(
                f"Access to unsafe attribute '{node.attr}' is forbidden."
            )
        self.generic_visit(node)


def format_python_code(code: str) -> str:
    """Attempts to auto-format Python code using Ruff to resolve minor syntax formatting issues.

    If formatting fails (e.g. due to actual syntax errors), returns the original code
    so that standard validation can return the exact syntax tracebacks to the model.
    """
    import subprocess
    from pathlib import Path

    from infra.settings import PROJECT_ROOT

    # Heuristically locate the local ruff executable inside the virtualenv
    ruff_path = PROJECT_ROOT / "apps" / "backend" / ".venv" / "bin" / "ruff"
    if not ruff_path.exists():
        ruff_path = Path("ruff")

    try:
        res = subprocess.run(
            [str(ruff_path), "format", "-"],
            input=code,
            text=True,
            capture_output=True,
            check=True,
        )
        return res.stdout
    except Exception:
        # Graceful fallback: return original code on formatting failure
        return code


def normalize_indentation(code: str) -> str:  # noqa: PLR0912
    """Standardizes class, method, and body indentation to be syntactically consistent.

    This ensures that Ruff format can parse and clean up the code successfully.
    """
    lines = code.splitlines()
    new_lines = []

    in_class = False
    in_method = False
    shift = 0

    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            new_lines.append(line)
            continue

        indent = len(line) - len(stripped)

        # Detect start of class block
        if stripped.startswith("class ") and (
            "(Scene" in stripped or "(ThreeDScene" in stripped
        ):
            in_class = True
            in_method = False
            shift = -indent
            new_lines.append(stripped)
            continue

        # Detect end of class block on top-level definitions
        if (
            in_class
            and indent == 0
            and not stripped.startswith("#")
            and not stripped.startswith('"""')
            and not stripped.startswith("'''")
            and (
                stripped.startswith("class ")
                or stripped.startswith("def ")
                or stripped.startswith("if __name__")
            )
        ):
            in_class = False
            in_method = False
            shift = 0


        if in_class:
            if stripped.startswith("def "):
                in_method = True
                shift = 4 - indent
                new_lines.append("    " + stripped)
                continue

            # If we are inside the class but before any method (e.g. class docstrings)
            if not in_method:
                if indent < 4:
                    new_lines.append("    " + stripped)
                else:
                    new_lines.append(line)
                continue

        # Apply shift if active
        if shift != 0:
            if shift > 0:
                new_lines.append(" " * shift + line)
            else:
                new_lines.append(line[min(-shift, indent) :])
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def sanitize_manim_code(code: str) -> str:  # noqa: C901, PLR0912
    """Extracts, parses, and sanitizes AI-generated Manim Python code.

    This function strips markdown code fences (even with prefix/suffix chatter),
    parses the code into an AST, runs the ASTSanitizer, and verifies the
    presence of the required 'SceneGen' class.

    Args:
        code (str): Raw output from the AI animator, potentially containing
            markdown code fences and conversational filler.

    Returns:
        str: Cleaned and sanitized Python code ready for rendering.

    Raises:
        RuntimeError: If the input is empty, contains syntax errors, fails
            security validation, or lacks the mandatory 'SceneGen' class.
    """
    cleaned = code.strip()

    # Some providers wrap code as a JSON string with escaped newlines.
    if (
        len(cleaned) >= 2
        and cleaned[0] == '"'
        and cleaned[-1] == '"'
        and "\\n" in cleaned
    ):
        try:
            loaded = json.loads(cleaned)
            if isinstance(loaded, str):
                cleaned = loaded.strip()
        except Exception:
            pass

    # Handle markdown code fences with potential prefix/suffix text
    if "```" in cleaned:
        match = _CODE_FENCE_BLOCK_RE.search(cleaned)
        if match:
            cleaned = match.group(1).strip()
        else:
            # If only one fence exists, take everything after first fence line.
            start_idx = cleaned.find("```")
            line_end = cleaned.find("\n", start_idx)
            content_start = line_end + 1 if line_end != -1 else start_idx + 3
            cleaned = cleaned[content_start:].strip()

    cleaned = cleaned.strip()

    if not cleaned:
        raise RuntimeError("Animator output was empty.")

    # Normalize non-standard unicode spaces and dashes in raw code
    cleaned = cleaned.replace("\u00a0", " ").replace("\u202f", " ")

    # Auto-repair stray divider/comment lines missing leading '#'
    repaired_lines = []
    for line in cleaned.splitlines():
        match = _DIVIDER_LINE_RE.match(line)
        if match:
            repaired_lines.append(f"{match.group(1)}# {match.group(2)}")
        elif (
            ("–" in line or "—" in line)
            and not line.strip().startswith("#")
            and '"' not in line
            and "'" not in line
        ):
            # Auto-repair comment lines missing leading '#' but containing en-dash/em-dash
            repaired_lines.append(
                f"{line[: len(line) - len(line.lstrip())]}# {line.strip()}"
            )
        else:
            repaired_lines.append(line)
    cleaned = "\n".join(repaired_lines)

    # Normalize class/method indentation to be syntactically consistent
    cleaned = normalize_indentation(cleaned)

    # Auto-format to resolve minor formatting/whitespace errors
    cleaned = format_python_code(cleaned)

    try:
        tree = ast.parse(cleaned)
    except SyntaxError as e:
        raise RuntimeError(f"Python syntax error: {e}") from e

    ASTSanitizer().visit(tree)

    # Auto-fix lowercase color strings (common AI hallucination).
    # Manim constants are CAPS (e.g. RED, BLUE). Strings like "red" fail at runtime.
    def _fix_color_match(match: re.Match[str]) -> str:
        return (
            match.group(0)
            .replace(f'"{match.group(1)}"', f'"{match.group(1).upper()}"')
            .replace(f"'{match.group(1)}'", f"'{match.group(1).upper()}'")
        )

    cleaned = _LOWERCASE_COLOR_RE.sub(_fix_color_match, cleaned)

    def _base_name(base: ast.expr) -> str | None:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return None

    scene_gen_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
        and any(_base_name(b) in {"Scene", "ThreeDScene"} for b in node.bases)
    ]
    if not scene_gen_classes:
        raise RuntimeError(
            "Required class inheriting from Scene or ThreeDScene missing."
        )
    if len(scene_gen_classes) != 1:
        raise RuntimeError(
            "Exactly one class inheriting from Scene or ThreeDScene is required."
        )
    scene_gen = scene_gen_classes[0]

    has_construct = any(
        isinstance(node, ast.FunctionDef)
        and node.name == "construct"
        and len(node.args.args) >= 1
        and node.args.args[0].arg == "self"
        for node in scene_gen.body
    )
    if not has_construct:
        raise RuntimeError(f"{scene_gen.name} must define construct(self).")

    return cleaned
