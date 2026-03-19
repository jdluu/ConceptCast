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
        if isinstance(node.func, ast.Attribute):
            legacy_method = _LEGACY_MANIM_METHOD_FIXES.get(node.func.attr)
            if legacy_method:
                raise RuntimeError(
                    f"Unsupported Manim call '.{node.func.attr}()'. {legacy_method}"
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

    try:
        tree = ast.parse(cleaned)
    except SyntaxError as e:
        raise RuntimeError(f"Python syntax error: {e}") from e

    ASTSanitizer().visit(tree)

    # Fast-fail for lowercase color strings (common AI hallucination)
    # Manim constants are CAPS (e.g. RED, BLUE). Strings like "red" fail.
    bad_colors = _LOWERCASE_COLOR_RE.findall(cleaned)
    if bad_colors:
        raise RuntimeError(
            f"Invalid color strings found: {', '.join(bad_colors)}. "
            "Use uppercase Manim constants (e.g., RED, BROWN) or hex strings."
        )

    has_scene_gen = any(
        isinstance(node, ast.ClassDef) and node.name == "SceneGen"
        for node in ast.walk(tree)
    )
    if not has_scene_gen:
        raise RuntimeError("Required 'SceneGen' class missing.")

    scene_gen_classes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef) and node.name == "SceneGen"
    ]
    if len(scene_gen_classes) != 1:
        raise RuntimeError("Exactly one class named 'SceneGen' is required.")
    scene_gen = scene_gen_classes[0]

    def _base_name(base: ast.expr) -> str | None:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return None

    base_names = {_base_name(base) for base in scene_gen.bases}
    if "Scene" not in base_names:
        raise RuntimeError("SceneGen must inherit from Scene.")

    has_construct = any(
        isinstance(node, ast.FunctionDef)
        and node.name == "construct"
        and len(node.args.args) >= 1
        and node.args.args[0].arg == "self"
        for node in scene_gen.body
    )
    if not has_construct:
        raise RuntimeError("SceneGen must define construct(self).")

    return cleaned
