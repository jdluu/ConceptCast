import json
from typing import Any

import pytest

from domain.agents.architect_compat import (
    ArchitectCompatibilityError,
    extract_storyboard_json,
    json_mode_prompt,
)

PROMPT = "Architect rules.\nYou must output a structured storyboard using the final_result tool."


VALID: dict[str, Any] = {
    "concept_title": "Fourier Transform",
    "scenes": [
        {
            "scene_id": 1,
            "title": "Frequency components",
            "description": "Axes with a colorful waveform and labeled frequencies.",
            "narration": "We decompose the signal into frequencies.",
            "duration": 6,
            "objects": [
                {
                    "name": "axes",
                    "type": "Axes",
                    "position": "ORIGIN",
                    "color": "BLUE",
                    "label": "Frequency",
                    "parameters": {"x_range": [-3, 3]},
                }
            ],
        }
    ],
}


def test_json_mode_prompt_changes_only_output_transport() -> None:
    converted = json_mode_prompt(PROMPT)
    assert "final_result" not in converted
    assert "valid JSON" in converted
    assert "scene_id" in converted
    assert "visual detail" in converted
    assert converted.startswith("Architect rules.")


def test_extract_storyboard_json_validates_full_visual_schema() -> None:
    storyboard = extract_storyboard_json("```json\n" + json.dumps(VALID) + "\n```")
    assert storyboard.scenes[0].objects[0].type == "Axes"
    assert storyboard.scenes[0].duration == 6


def test_extract_storyboard_json_normalizes_documented_qwen_aliases() -> None:
    qwen = {
        "project": {
            "concept_title": "Fourier Transform",
            "scenes": [
                {
                    "step_id": 1,
                    "concept": "Frequency",
                    "scene_description": "A NumberLine and moving Dot.",
                    "narration": "Frequency changes over time.",
                    "duration": 6,
                    "objects": [
                        {
                            "id": "axis",
                            "type": "NumberLine",
                            "position": "ORIGIN",
                            "properties": {"x_range": [-5, 5]},
                        }
                    ],
                }
            ],
        }
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.scenes[0].scene_id == 1
    assert storyboard.scenes[0].objects[0].name == "axis"
    assert storyboard.scenes[0].objects[0].parameters["x_range"] == [-5, 5]


def test_extract_storyboard_json_normalizes_storyboard_wrapper_and_visual_aliases() -> (
    None
):
    qwen = {
        "storyboard": {
            "project_title": "Probe",
            "scenes": [
                {
                    "step_id": 1,
                    "concept": "Change",
                    "visual_description": "A moving dot on a NumberLine.",
                    "narration": "The value changes.",
                    "duration": 5,
                    "manim_objects": [
                        {
                            "type": "Dot",
                            "id": "moving_dot",
                            "position": "ORIGIN",
                            "properties": {"radius": 0.2},
                        }
                    ],
                }
            ],
        }
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.concept_title == "Probe"
    assert storyboard.scenes[0].description.startswith("A moving dot")
    assert storyboard.scenes[0].objects[0].name == "moving_dot"


def test_extract_storyboard_json_preserves_coordinate_position_objects() -> None:
    qwen = {
        **VALID,
        "scenes": [
            {
                **VALID["scenes"][0],
                "objects": [
                    {
                        "id": "dot",
                        "type": "Dot",
                        "position": {"center": [0, 1, 0]},
                    }
                ],
            }
        ],
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.scenes[0].objects[0].position == '{"center":[0,1,0]}'


def test_extract_storyboard_json_normalizes_project_metadata_and_missing_ids() -> None:
    qwen = {
        "project_metadata": {"concept_title": "Probe"},
        "scenes": [
            {
                "scene_id": 1,
                "description": "A dot moves.",
                "narration": "The dot moves.",
                "objects": [{"type": "Dot", "position": "ORIGIN"}],
            }
        ],
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.concept_title == "Probe"
    assert storyboard.scenes[0].objects[0].name == "dot_1"


def test_extract_storyboard_json_preserves_layout_notes_and_string_properties() -> None:
    qwen = {
        "storyboard": {
            "concept_title": "Probe",
            "scenes": [
                {
                    "step_id": 1,
                    "layout": "Centered NumberLine with a moving Dot.",
                    "pedagogical_note": "Movement shows change.",
                    "objects": [
                        {
                            "type": "NumberLine",
                            "position": "ORIGIN",
                            "properties": "x_range=[-5, 5]",
                        }
                    ],
                }
            ],
        }
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.scenes[0].description.startswith("Centered NumberLine")
    assert storyboard.scenes[0].narration == "Movement shows change."
    assert storyboard.scenes[0].objects[0].parameters["raw"] == "x_range=[-5, 5]"


def test_extract_storyboard_json_preserves_structured_descriptions() -> None:
    qwen = {
        **VALID,
        "scenes": [
            {
                **VALID["scenes"][0],
                "description": {"description": "A moving axis.", "alignment": "CENTER"},
            }
        ],
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    assert storyboard.scenes[0].description == "A moving axis."


def test_extract_storyboard_json_normalizes_coordinate_and_extent_boxes() -> None:
    qwen = {
        **VALID,
        "scenes": [
            {
                **VALID["scenes"][0],
                "objects": [
                    {
                        "id": "box",
                        "type": "Rectangle",
                        "position": [0, 1, 0],
                        "bounding_box": [-2, -1, 2, 3],
                    }
                ],
            }
        ],
    }
    storyboard = extract_storyboard_json(json.dumps(qwen))
    obj = storyboard.scenes[0].objects[0]
    assert obj.position == "[0,1,0]"
    assert obj.bounding_box == (4.0, 4.0)


def test_extract_storyboard_json_normalizes_xywh_bounding_boxes() -> None:
    qwen = {
        **VALID,
        "scenes": [
            {
                **VALID["scenes"][0],
                "objects": [
                    {
                        "id": "box",
                        "type": "Rectangle",
                        "position": "ORIGIN",
                        "bounding_box": {"x": 0, "y": 0, "width": 5, "height": 2},
                    }
                ],
            }
        ],
    }
    obj = extract_storyboard_json(json.dumps(qwen)).scenes[0].objects[0]
    assert obj.bounding_box == (5.0, 2.0)


def test_extract_storyboard_json_rejects_missing_required_field() -> None:
    invalid_scene: dict[str, Any] = {**VALID["scenes"][0]}
    invalid_scene.pop("description")
    invalid = {**VALID, "scenes": [invalid_scene]}
    with pytest.raises(ArchitectCompatibilityError, match="Storyboard validation"):
        extract_storyboard_json(json.dumps(invalid))


def test_json_mode_prompt_rejects_unrecognized_prompt() -> None:
    with pytest.raises(ArchitectCompatibilityError, match="expected final_result"):
        json_mode_prompt("Architect rules only.")
