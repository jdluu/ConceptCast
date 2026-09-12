from domain.models.curriculum import CurriculumPlan
from domain.models.workflow import BoundingBox, GlobalContext, SceneOccupancy
from infra.ai.tools.analysis import statically_check_layout_collisions


def create_mock_ctx() -> GlobalContext:
    plan = CurriculumPlan(
        concept_title="derivatives",
        teaching_steps=[],
    )
    return GlobalContext(
        topic="derivatives",
        plan=plan,
        style={},
        lexicon={},
        decisions=[],
    )


def test_statically_check_layout_collisions_no_occupancy() -> None:
    ctx = create_mock_ctx()
    code = """
class SceneGen(Scene):
    def construct(self):
        circle = Circle()
"""
    errors = statically_check_layout_collisions(code, scene_id=1, ctx=ctx)
    assert len(errors) == 0


def test_statically_check_layout_collisions_with_constant_ignoring() -> None:
    # Scene occupancies has a reserved box at ORIGIN [0.0, 0.0]
    box = BoundingBox(center="ORIGIN", width=1.0, height=1.0, label="center_text")
    occupancy = SceneOccupancy(scene_id=1, reserved_boxes=[box])

    ctx = create_mock_ctx()
    ctx.scene_occupancy = {1: occupancy}

    # This code defines non-visual constant assignments (colors, floats, self) which should be ignored
    code = """
class SceneGen(Scene):
    def construct(self):
        self.camera.background_color = "#181825"
        cube_color = "#fab387"
        shadow_color = "#11111b"
        duration = 5.0
"""
    errors = statically_check_layout_collisions(code, scene_id=1, ctx=ctx)
    # They should not be flagged as collisions at ORIGIN!
    assert len(errors) == 0


def test_statically_check_layout_collisions_with_real_collision() -> None:
    # Scene occupancies has a reserved box at ORIGIN [0.0, 0.0]
    box = BoundingBox(center="ORIGIN", width=2.0, height=1.5, label="center_text")
    occupancy = SceneOccupancy(scene_id=1, reserved_boxes=[box])

    ctx = create_mock_ctx()
    ctx.scene_occupancy = {1: occupancy}

    # This code instantiates a real Mobject at ORIGIN, causing a collision
    code = """
class SceneGen(Scene):
    def construct(self):
        circle = Circle() # Default position is ORIGIN [0.0, 0.0]
"""
    errors = statically_check_layout_collisions(code, scene_id=1, ctx=ctx)
    assert len(errors) == 1
    assert "Layout collision: variable 'circle'" in errors[0]


def test_statically_check_layout_collisions_container_exemption() -> None:
    # Scene occupancy has reserved container boxes:
    # 1. graph_axes centered at ORIGIN (width 6, height 5)
    # 2. machine_body centered at ORIGIN (width 3, height 2)
    box1 = BoundingBox(center="ORIGIN", width=6.0, height=5.0, label="graph_axes")
    box2 = BoundingBox(center="ORIGIN", width=3.0, height=2.0, label="machine_body")
    occupancy = SceneOccupancy(scene_id=1, reserved_boxes=[box1, box2])

    ctx = create_mock_ctx()
    ctx.scene_occupancy = {1: occupancy}

    # This code instantiates elements inside these containers at default ORIGIN
    # which would normally overlap, but should be ignored by the exemptions
    code = """
class SceneGen(Scene):
    def construct(self):
        axes = Axes()             # Substring and container keyword
        machine = Square()         # Substring
        gear1 = Circle()           # Contained in machine_body (container body)
        point_B = Dot()           # Contained in graph_axes (container axes)
"""
    errors = statically_check_layout_collisions(code, scene_id=1, ctx=ctx)
    assert len(errors) == 0
