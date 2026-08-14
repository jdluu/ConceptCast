from domain.models.workflow import BoundingBox, GlobalContext, SceneOccupancy
from infra.ai.tools.analysis import statically_check_layout_collisions


def _ctx() -> GlobalContext:
    return GlobalContext(topic="test", target_audience="General Audience")


def test_layout_check_ignores_helper_data_assignments() -> None:
    ctx = _ctx()
    ctx.scene_occupancy[1] = SceneOccupancy(scene_id=1)
    code = """
from manim import *
import numpy as np
class SceneGen(Scene):
    def construct(self):
        xs = np.linspace(-2, 2, 5)
        points = [x * RIGHT for x in xs]
        self.play(Write(Text("Title")))
"""
    assert statically_check_layout_collisions(code, 1, ctx) == []


def test_layout_check_reads_constructor_point_coordinates() -> None:
    ctx = _ctx()
    box = BoundingBox(label="reserved_area", center="ORIGIN", width=0.5, height=0.5)
    ctx.scene_occupancy[1] = SceneOccupancy(scene_id=1, reserved_boxes=[box])
    code = """
from manim import *
class SceneGen(Scene):
    def construct(self):
        dot = Dot(point=[3, 3, 0])
        self.play(Create(dot))
"""
    assert statically_check_layout_collisions(code, 1, ctx) == []


def test_layout_check_still_tracks_mobject_assignments() -> None:
    ctx = _ctx()
    box = BoundingBox(label="reserved_area", center="ORIGIN", width=10.0, height=10.0)
    ctx.scene_occupancy[1] = SceneOccupancy(scene_id=1, reserved_boxes=[box])
    code = """
from manim import *
class SceneGen(Scene):
    def construct(self):
        title = Text("Title")
        self.play(Write(title))
"""
    assert statically_check_layout_collisions(code, 1, ctx)


def test_layout_check_ignores_helper_variable_with_mobject_like_method() -> None:
    ctx = _ctx()
    ctx.scene_occupancy[1] = SceneOccupancy(scene_id=1)
    code = """
from manim import *
class SceneGen(Scene):
    def construct(self):
        values = [1, 2, 3]
        self.play(Create(Dot()))
"""
    assert statically_check_layout_collisions(code, 1, ctx) == []


def test_context_default_occupancy_map_is_available() -> None:
    ctx = _ctx()
    assert isinstance(ctx.scene_occupancy, dict)
