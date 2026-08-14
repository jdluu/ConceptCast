import pytest

from api.schemas import Scene, Storyboard, VisualObject
from domain.models.workflow import GlobalContext
from infra.exceptions import StoryboardGenerationError
from services.workflow.steps.architecting import _populate_scene_occupancy


def _storyboard(objects: list[VisualObject]) -> Storyboard:
    return Storyboard(
        concept_title="Test",
        scenes=[
            Scene(
                scene_id=1,
                title="Scene",
                description="A scene",
                narration="Explain it",
                duration=5,
                objects=objects,
            )
        ],
    )


def _obj(name: str, position: str, box: tuple[float, float]) -> VisualObject:
    return VisualObject(
        name=name,
        type="Rectangle",
        position=position,
        color="BLUE",
        label=name,
        bounding_box=box,
    )


def test_occupancy_accepts_non_overlapping_boxes() -> None:
    ctx = GlobalContext(topic="test", target_audience="General Audience")
    _populate_scene_occupancy(
        _storyboard(
            [_obj("left", "[-3,0,0]", (1, 1)), _obj("right", "[3,0,0]", (1, 1))]
        ),
        ctx,
    )
    assert len(ctx.scene_occupancy[1].reserved_boxes) == 2


def test_occupancy_rejects_impossible_overlapping_boxes() -> None:
    ctx = GlobalContext(topic="test", target_audience="General Audience")
    with pytest.raises(StoryboardGenerationError, match="overlaps"):
        _populate_scene_occupancy(
            _storyboard(
                [
                    _obj("title", "[0,0,0]", (10, 4)),
                    _obj("subtitle", "[0,-1.5,0]", (8, 2)),
                ]
            ),
            ctx,
        )
