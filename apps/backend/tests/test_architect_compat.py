import json

import pytest

from domain.agents.architect_compat import (
    ArchitectCompatibilityError,
    extract_storyboard_json,
    json_mode_prompt,
)

PROMPT = "Architect rules.\nYou must output a structured storyboard using the final_result tool."


VALID = {
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
    assert converted.startswith("Architect rules.")


def test_extract_storyboard_json_validates_full_visual_schema() -> None:
    storyboard = extract_storyboard_json("```json\n" + json.dumps(VALID) + "\n```")
    assert storyboard.scenes[0].objects[0].type == "Axes"
    assert storyboard.scenes[0].duration == 6


def test_extract_storyboard_json_rejects_missing_required_field() -> None:
    invalid_scene = {**VALID["scenes"][0]}
    invalid_scene.pop("description")
    invalid = {**VALID, "scenes": [invalid_scene]}
    with pytest.raises(ArchitectCompatibilityError, match="Storyboard validation"):
        extract_storyboard_json(json.dumps(invalid))


def test_json_mode_prompt_rejects_unrecognized_prompt() -> None:
    with pytest.raises(ArchitectCompatibilityError, match="expected final_result"):
        json_mode_prompt("Architect rules only.")
