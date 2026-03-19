import json
from collections import OrderedDict

import structlog
from pydantic_ai import RunContext, ToolDefinition

from domain.models.workflow import GlobalContext
from infra.settings import get_settings

from .docs_client import get_manim_docs_context

logger = structlog.get_logger(__name__)

# Curated fallback when CONTEXT7_API_KEY is not set. With Context7 we use
# Manim Community docs at /websites/manim_community_en_stable instead.
MANIM_DOCS: dict[str, str] = {
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

_DOC_QUERY_CACHE: OrderedDict[str, str] = OrderedDict()
_DOC_QUERY_CACHE_MAX = 128


def _cache_get(query: str) -> str | None:
    value = _DOC_QUERY_CACHE.get(query)
    if value is None:
        return None
    _DOC_QUERY_CACHE.move_to_end(query)
    return value


def _cache_set(query: str, content: str) -> None:
    _DOC_QUERY_CACHE[query] = content
    _DOC_QUERY_CACHE.move_to_end(query)
    if len(_DOC_QUERY_CACHE) > _DOC_QUERY_CACHE_MAX:
        _DOC_QUERY_CACHE.popitem(last=False)


async def prepare_manim_docs(
    ctx: RunContext[GlobalContext], tool_def: ToolDefinition
) -> ToolDefinition | None:
    """Prepares and filters Manim documentation for the current storyboard.

    This 'prepare' callback dynamically adjusts the tool's description
    to include only those Manim types that are mentioned in the storyboard,
    reducing token usage and focusing the agent's attention.

    Args:
        ctx: Run context containing the global workflow state.
        tool_def: The definition of the search tool being prepared.

    Returns:
        The modified ToolDefinition with an contextually relevant description.
    """
    deps = getattr(ctx, "deps", None)
    if deps is None:
        logger.debug("prepare_manim_docs_missing_deps")
        return tool_def

    storyboard = deps.storyboard
    if not storyboard or not storyboard.scenes:
        return tool_def

    mentioned_types = {obj.type for scene in storyboard.scenes for obj in scene.objects}

    relevant_docs = {k: v for k, v in MANIM_DOCS.items() if k in mentioned_types}
    doc_summary = "\n".join([f"- {k}: {v}" for k, v in relevant_docs.items()])

    tool_def.description = (
        f"Search for Manim syntax. Curated context for this storyboard:\n{doc_summary}"
    )

    return tool_def


async def search_manim_docs(_ctx: RunContext[GlobalContext], query: str) -> str:
    """Keyword or semantic search for Manim Community documentation.

    Leverages Context7 for external documentation retrieval if an API key
    is present. Otherwise, performs a simple keyword match against the
    curated `MANIM_DOCS` list.

    Args:
        _ctx: Run context containing the global workflow state.
        query: Search term or question regarding Manim syntax/objects.

    Returns:
        JSON string containing the retrieved documentation.
    """
    normalized_query = " ".join(query.strip().split()).lower()
    cached = _cache_get(normalized_query)
    if cached is not None:
        return json.dumps({"documentation": cached, "source": "cache"})

    api_key = get_settings().context7_api_key
    if api_key:
        content = await get_manim_docs_context(query, api_key=api_key)
    else:
        matches = [
            f"{k}: {v}"
            for k, v in MANIM_DOCS.items()
            if normalized_query in k.lower() or normalized_query in v.lower()
        ]
        content = (
            "\n".join(matches)
            if matches
            else "No specific matches found. Use standard Manim Community syntax."
        )
    _cache_set(normalized_query, content)
    return json.dumps({"documentation": content, "source": "live"})
