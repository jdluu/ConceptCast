import ast

import structlog
from pydantic_ai import RunContext

from domain.models.workflow import GlobalContext

logger = structlog.get_logger(__name__)


def count_animation_types(node: ast.AST) -> dict[str, int]:
    """Recursively walks an AST to count instances of specific animation classes."""
    counts: dict[str, int] = {}

    animation_classes = {
        # Basic
        "Create",
        "Write",
        "FadeIn",
        "FadeOut",
        "Uncreate",
        "DrawBorderThenFill",
        # Transform/Dynamic
        "Transform",
        "ReplacementTransform",
        "TransformFromCopy",
        "TransformMatchingTex",
        "TransformMatchingShapes",
        "MoveToTarget",
        # Movement/Attention
        "ApplyMethod",
        "Rotate",
        "ScaleInPlace",
        "Circumscribe",
        "Indicate",
        "Flash",
        # Grouping
        "AnimationGroup",
        "Succession",
        "LaggedStart",
    }

    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            # Check if calling an animation class directly, e.g. Create(mob)
            if isinstance(child.func, ast.Name):
                func_name = child.func.id
                if func_name in animation_classes:
                    counts[func_name] = counts.get(func_name, 0) + 1

            # Check if calling a method, e.g. self.play() or mob.animate.foo()
            elif isinstance(child.func, ast.Attribute):
                attr_name = child.func.attr
                if attr_name == "play":
                    counts["play_calls"] = counts.get("play_calls", 0) + 1
                elif attr_name == "wait":
                    counts["wait_calls"] = counts.get("wait_calls", 0) + 1
                elif attr_name == "animate":
                    counts["animate_property"] = counts.get("animate_property", 0) + 1
                elif attr_name == "add_updater":
                    counts["updaters"] = counts.get("updaters", 0) + 1

    return counts


async def analyze_animation_dynamism(_ctx: RunContext[GlobalContext], code: str) -> str:
    """Analyzes Manim Python code to evaluate its visual dynamism and pacing.

    This tool parses the code (without running it) to count transitions, grouping,
    and movement. Use this to objectively verify if a scene is 'boring' (e.g. only
    using static additions or basic Create/Write calls) and provide actionable
    feedback to the Animator to use ReplacementTransform, LaggedStart, or .animate.

    Args:
        code: The Python code of the Manim scene to analyze.

    Returns:
        A formatted report detailing the animation metrics and dynamism score.
    """
    logger.info("analyze_animation_dynamism_called")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"Cannot analyze dynamism: Syntax Error in code: {e}"

    metrics = count_animation_types(tree)

    if not metrics:
        return "Warning: No animation primitives found. This code may just render a static frame."

    play_calls = metrics.get("play_calls", 0)
    wait_calls = metrics.get("wait_calls", 0)
    updaters = metrics.get("updaters", 0)
    animate_prop = metrics.get("animate_property", 0)

    # Categorize animations
    basic_anims = sum(
        metrics.get(k, 0) for k in ["Create", "Write", "FadeIn", "DrawBorderThenFill"]
    )
    transform_anims = sum(
        metrics.get(k, 0)
        for k in [
            "Transform",
            "ReplacementTransform",
            "TransformFromCopy",
            "TransformMatchingTex",
            "TransformMatchingShapes",
            "MoveToTarget",
        ]
    )
    group_anims = sum(
        metrics.get(k, 0) for k in ["AnimationGroup", "Succession", "LaggedStart"]
    )
    attention_anims = sum(
        metrics.get(k, 0) for k in ["Circumscribe", "Indicate", "Flash", "Rotate"]
    )

    # Generate report
    report = ["--- ANIMATION DYNAMISM REPORT ---"]
    report.append(f"Total play() calls: {play_calls}")
    report.append(f"Total wait() calls: {wait_calls}")

    report.append("\nBreakdown:")
    report.append(f"- Basic Appearances (Create/Write/Fade): {basic_anims}")
    report.append(f"- Dynamic Transforms (Morphing/Replacing): {transform_anims}")
    report.append(f"- Group Sequencing (LaggedStart/Succession): {group_anims}")
    report.append(f"- Attention/Movement: {attention_anims}")
    report.append(f"- Property Animations (.animate): {animate_prop}")
    report.append(f"- Continuous Updaters: {updaters}")

    report.append("\nAnalysis:")

    score = 0
    if transform_anims > 0:
        score += 2
    if group_anims > 0:
        score += 2
    if animate_prop > 0:
        score += 1
    if updaters > 0:
        score += 3
    if attention_anims > 0:
        score += 1

    if basic_anims > 0 and score == 0:
        report.append(
            "❌ LOW DYNAMISM: Scene relies purely on basic appearances. "
            "Consider using ReplacementTransform to morph objects, or LaggedStart "
            "to stagger their entry. Use .animate for smooth property changes."
        )
    elif score <= 2:
        report.append(
            "⚠️ MODERATE DYNAMISM: Scene has some movement, but could be more engaging. "
            "Consider grouping independent animations into a LaggedStart, or adding "
            "subtle .animate movements."
        )
    else:
        report.append("✅ HIGH DYNAMISM: Scene uses advanced transitions and pacing.")

    return "\n".join(report)


def evaluate_vector_ast(node: ast.AST) -> list[float] | None:  # noqa: PLR0911
    """Statically evaluates standard Manim 2D vector expressions from AST."""
    if isinstance(node, ast.Name):
        name = node.id
        constants = {
            "ORIGIN": [0.0, 0.0],
            "UP": [0.0, 1.0],
            "DOWN": [0.0, -1.0],
            "LEFT": [-1.0, 0.0],
            "RIGHT": [1.0, 0.0],
            "UL": [-1.0, 1.0],
            "UR": [1.0, 1.0],
            "DL": [-1.0, -1.0],
            "DR": [1.0, -1.0],
        }
        return constants.get(name)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, int | float):
            return [node.value, node.value]
        return None

    if isinstance(node, ast.BinOp):
        left = evaluate_vector_ast(node.left)
        right = evaluate_vector_ast(node.right)
        if left is None or right is None:
            return None

        if isinstance(node.op, ast.Add):
            return [left[0] + right[0], left[1] + right[1]]
        if isinstance(node.op, ast.Sub):
            return [left[0] - right[0], left[1] - right[1]]
        if isinstance(node.op, ast.Mult):
            return [left[0] * right[0], left[1] * right[1]]
        if isinstance(node.op, ast.Div):
            if right[0] == 0 or right[1] == 0:
                return None
            return [left[0] / right[0], left[1] / right[1]]

    return None


class SpatialPositionTracker(ast.NodeVisitor):
    """AST Visitor that tracks positioning and shifts of Manim elements."""

    def __init__(self) -> None:
        self.positions: dict[str, list[float]] = {}
        self.dimensions: dict[str, list[float]] = {}

    def visit_Assign(self, node: ast.Assign) -> None:
        self.generic_visit(node)
        # Ignore literal constants (like color hex strings, numbers, etc.)
        if isinstance(node.value, ast.Constant):
            return
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                if var_name == "self":
                    continue
                if var_name not in self.positions:
                    self.positions[var_name] = [0.0, 0.0]
                if var_name not in self.dimensions:
                    self.dimensions[var_name] = [2.0, 1.5]  # Standard width & height

    def visit_Call(self, node: ast.Call) -> None:  # noqa: C901, PLR0912
        self.generic_visit(node)
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            target_var = None
            if isinstance(node.func.value, ast.Name):
                target_var = node.func.value.id

            if target_var and target_var in self.positions:

                if method_name == "shift" and node.args:
                    vec = evaluate_vector_ast(node.args[0])
                    if vec:
                        self.positions[target_var][0] += vec[0]
                        self.positions[target_var][1] += vec[1]

                elif method_name == "move_to" and node.args:
                    vec = evaluate_vector_ast(node.args[0])
                    if vec:
                        self.positions[target_var] = [vec[0], vec[1]]

                elif method_name == "to_edge" and node.args:
                    direction = evaluate_vector_ast(node.args[0])
                    if direction:
                        if direction[1] > 0:
                            self.positions[target_var][1] = 3.0
                        elif direction[1] < 0:
                            self.positions[target_var][1] = -3.0
                        if direction[0] < 0:
                            self.positions[target_var][0] = -5.5
                        elif direction[0] > 0:
                            self.positions[target_var][0] = 5.5

                elif method_name == "next_to" and len(node.args) >= 2:
                    other = node.args[0]
                    direction = evaluate_vector_ast(node.args[1])
                    if isinstance(other, ast.Name) and direction:
                        other_var = other.id
                        other_pos = self.positions.get(other_var, [0.0, 0.0])
                        other_dim = self.dimensions.get(other_var, [2.0, 1.5])
                        self_dim = self.dimensions[target_var]
                        buffer = 0.25
                        self.positions[target_var][0] = other_pos[0] + direction[0] * (
                            other_dim[0] / 2.0 + self_dim[0] / 2.0 + buffer
                        )
                        self.positions[target_var][1] = other_pos[1] + direction[1] * (
                            other_dim[1] / 2.0 + self_dim[1] / 2.0 + buffer
                        )


def parse_coordinate_string(coord_str: str) -> list[float]:
    """Parses a Manim coordinate string statically into 2D coordinates."""
    try:
        tree = ast.parse(coord_str.strip(), mode="eval")
        vec = evaluate_vector_ast(tree.body)
        if vec:
            return [vec[0], vec[1]]
    except Exception:
        pass
    return [0.0, 0.0]


def statically_check_layout_collisions(
    code: str, scene_id: int, ctx: GlobalContext
) -> list[str]:
    """Checks the Manim code for overlap/collision with pre-reserved bounds in GCO."""
    errors: list[str] = []
    if not ctx.scene_occupancy or scene_id not in ctx.scene_occupancy:
        return errors

    try:
        tree = ast.parse(code)
    except Exception:
        # Ignore syntax errors here; handled by the main compiler
        return errors

    tracker = SpatialPositionTracker()
    tracker.visit(tree)

    containers = {"axes", "graph", "grid", "plot", "number_line", "body", "bg", "background", "canvas", "frame"}
    occupancy = ctx.scene_occupancy[scene_id]
    for var_name, pos in tracker.positions.items():
        dim = tracker.dimensions[var_name]
        cx, cy = pos[0], pos[1]
        cw, ch = dim[0], dim[1]

        for box in occupancy.reserved_boxes:
            v_lower, b_lower = var_name.lower(), box.label.lower()
            if v_lower in b_lower or b_lower in v_lower:
                continue
            if any(c in v_lower or c in b_lower for c in containers):
                continue

            rx, ry = parse_coordinate_string(box.center)
            rw, rh = box.width, box.height

            # Box-to-box collision check (AABB)
            if abs(cx - rx) * 2.0 < (cw + rw) and abs(cy - ry) * 2.0 < (ch + rh):
                errors.append(
                    f"Layout collision: variable '{var_name}' at position [{cx:.2f}, {cy:.2f}] "
                    f"overlaps with reserved bounding box area '{box.label}' (centered at {box.center} "
                    f"with size {rw}x{rh})."
                )

    return errors
