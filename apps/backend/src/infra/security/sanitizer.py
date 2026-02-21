import ast
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

# Regex to detect lowercase color kwarg values, e.g. color="red" which
# will raise at runtime. Manim constants are always CAPS (RED, BROWN, etc.).
_LOWERCASE_COLOR_RE = re.compile(
    r'(?:color|fill_color|stroke_color)\s*=\s*["\']([a-z]+)["\']'
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


def sanitize_manim_code(code: str) -> str:
    """Extracts, parses, and sanitizes AI-generated Manim Python code.

    This function strips markdown code fences, parses the code into an AST,
    runs the ASTSanitizer, and verifies the presence of the required
    'SceneGen' class.

    Args:
        code (str): Raw output from the AI animator, potentially containing
            markdown code fences.

    Returns:
        str: Cleaned and sanitized Python code ready for rendering.

    Raises:
        RuntimeError: If the input is empty, contains syntax errors, fails
            security validation, or lacks the mandatory 'SceneGen' class.
    """
    cleaned = code.strip()
    # Strip opening fence
    if _CODE_FENCE_START.match(cleaned):
        cleaned = _CODE_FENCE_START.sub("", cleaned, count=1)
    # Strip trailing fence
    if cleaned.endswith("```"):
        cleaned = cleaned[: cleaned.rfind("```")].rstrip()
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

    return cleaned
