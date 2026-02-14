import json

from pydantic_ai import RunContext, ToolDefinition

from api.schemas import Storyboard
from core.context7 import get_manim_docs_context
from core.settings import get_settings

# Curated fallback when CONTEXT7_API_KEY is not set. With Context7 we use
# Manim Community docs at /websites/manim_community_en_stable instead.
MANIM_DOCS = {
    "Line": (
        "Line(start=LEFT, end=RIGHT, buff=0). "
        "A straight line segment between two points. "
        "Key methods: get_start(), get_end(), get_vector()."
    ),
    "Rectangle": (
        "Rectangle(color=WHITE, height=2.0, width=4.0). "
        "A quadrilateral with two sets of parallel sides. "
        "Key properties: height, width."
    ),
    "Square": (
        "Square(side_length=2.0). "
        "A special case of Rectangle with equal side lengths. "
        "Key parameter: side_length."
    ),
    "Circle": (
        "Circle(radius=1.0). "
        "A circular shape defined by a radius. "
        "Key methods: surround(), point_at_angle(), from_three_points()."
    ),
    "Dot": (
        "Dot(point=ORIGIN, radius=0.08, color=WHITE). "
        "A small circle representing a point. Key parameters: point, radius, color."
    ),
    "Polygon": (
        "Polygon(*vertices). "
        "A shape consisting of one closed loop of vertices. "
        "Key methods: get_vertices()."
    ),
    "RegularPolygon": (
        "RegularPolygon(n). "
        "An n-sided regular polygon. Key parameters: n (number of sides), start_angle."
    ),
    "Triangle": (
        "Triangle(). "
        "An equilateral triangle. A specialization of RegularPolygon with n=3."
    ),
    "Arrow": (
        "Arrow(start, end, tip_length=0.25). "
        "A line with a tip pointing from start to end. "
        "Key parameters: tip_length, stroke_width, buff."
    ),
    "DoubleArrow": (
        "DoubleArrow(start, end). Similar to Arrow but with tips on both ends."
    ),
    "CurvedArrow": (
        "CurvedArrow(start_point, end_point, angle=TAU/4). "
        "An arrow that follows a circular arc. Key parameter: angle."
    ),
    "Text": (
        "Text(text, font_size=48). "
        "Text rendered using Pango. Behaves like a VGroup of characters."
    ),
    "MathTex": (
        "MathTex(*tex_strings). "
        "A string compiled with LaTeX in math mode. "
        "Key methods: get_part_by_tex(), set_color_by_tex()."
    ),
    "Tex": (
        "Tex(*tex_strings). "
        "A string compiled with LaTeX in normal mode. "
        "Key methods: get_part_by_tex(), set_color_by_tex()."
    ),
    "NumberLine": (
        "NumberLine(x_range, length, include_numbers=False). "
        "A horizontal or vertical line with tick marks. "
        "Key methods: add_numbers(), n2p() (number to point)."
    ),
    "Axes": (
        "Axes(x_range, y_range, x_length, y_length). "
        "A set of x and y axes. "
        "Key methods: coords_to_point(), point_to_coords(), plot()."
    ),
    "ComplexPlane": (
        "ComplexPlane(x_range, y_range). "
        "A specialized NumberPlane for representing complex numbers."
    ),
    "NumberPlane": (
        "NumberPlane(x_range, y_range). "
        "A Cartesian plane with background lines. "
        "Key methods: get_axes(), get_lines_to_point()."
    ),
    "Arc": (
        "Arc(radius=1.0, start_angle=0, angle=TAU/4). "
        "A circular arc segment. Key properties: radius, start_angle, angle."
    ),
    "Sector": (
        "Sector(radius=1, angle=TAU/4, start_angle=0). A circular sector (pie slice)."
    ),
    "Create": (
        "Create(mobject, lag_ratio=0.0). Animation: Incrementally shows a VMobject by "
        "drawing its strokes."
    ),
    "Write": (
        "Write(mobject, reverse=False). Animation: Simulates hand-writing a Text or "
        "hand-drawing a VMobject."
    ),
    "FadeIn": (
        "FadeIn(mobject, shift=None, scale=None). Animation: Introduces a mobject by "
        "increasing its opacity."
    ),
    "FadeOut": (
        "FadeOut(mobject, shift=None, scale=None). Animation: Removes a mobject by "
        "decreasing its opacity."
    ),
    "Transform": (
        "Transform(mobject, target_mobject). "
        "Animation: Morphs one mobject into another."
    ),
    "ReplacementTransform": (
        "ReplacementTransform(mobject, target_mobject). Animation: Starting mobject is "
        "physically replaced by the target."
    ),
    "Rotate": (
        "Rotate(mobject, angle=PI/2). Animation: Rotates a mobject around an axis."
    ),
    "ScaleInPlace": (
        "ScaleInPlace(mobject, scale_factor). Animation: Scales a mobject without "
        "changing its center."
    ),
    "MoveToTarget": (
        "MoveToTarget(mobject). "
        "Animation: Animates a mobject to its generated target state."
    ),
    "ValueTracker": (
        "ValueTracker(value=0). A hidden mobject used to track and animate numerical "
        "values. Key methods: get_value(), set_value()."
    ),
}


async def prepare_manim_docs(
    ctx: RunContext[Storyboard], tool_def: ToolDefinition
) -> ToolDefinition | None:
    """
    Advanced Tool Pattern: Dynamically adjusts the tool description
    based on the Storyboard's current needs.

    Filters the Manim documentation to only include types referenced in
    the current storyboard scenes, preserving context window space.

    Args:
        ctx (RunContext): The tool execution context.
        tool_def (ToolDefinition): The original tool definition.

    Returns:
        ToolDefinition | None: The modified tool definition with context-aware docs.
    """
    storyboard = ctx.deps
    mentioned_types = set()
    for scene in storyboard.scenes:
        for obj in scene.objects:
            mentioned_types.add(obj.type)

    # Filter docs to only include relevant info to save context window
    relevant_docs = {k: v for k, v in MANIM_DOCS.items() if k in mentioned_types}

    doc_summary = "\n".join([f"- {k}: {v}" for k, v in relevant_docs.items()])
    tool_def.description = (
        f"Search for Manim syntax. Curated context for this storyboard:\n{doc_summary}"
    )

    return tool_def


async def search_manim_docs(ctx: RunContext[Storyboard], query: str) -> str:
    """
    Searches for Manim Community documentation.

    When CONTEXT7_API_KEY is set, uses Context7 API to retrieve relevant
    snippets from Manim Community docs. Otherwise falls back to keyword
    search over the curated MANIM_DOCS dict.
    When used with prepare=prepare_manim_docs, pydantic_ai requires the first
    parameter to be RunContext[Storyboard] so the tool is context-aware.

    Args:
        ctx: Run context (deps=Storyboard); used by prepare, not in body.
        query: The search term or question (e.g., 'Circle', 'FadeIn animation').

    Returns:
        str: JSON string with key "documentation" so providers 
        that parse tool results as JSON succeed.
    """
    api_key = get_settings().context7_api_key
    if api_key:
        content = await get_manim_docs_context(query, api_key=api_key)
    else:
        matches = [
            f"{k}: {v}"
            for k, v in MANIM_DOCS.items()
            if query.lower() in k.lower() or query.lower() in v.lower()
        ]
        content = (
            "\n".join(matches)
            if matches
            else "No specific matches found. Use standard Manim Community syntax."
        )
    return json.dumps({"documentation": content})
