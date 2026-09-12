"""Opt-in compatibility helpers for providers without structured tool output.

This module is deliberately not wired into the live architect path yet. It gives
provider adapters a narrow, testable boundary: request JSON, extract one object,
and validate the complete Storyboard schema without weakening visual fields.
"""

from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic import ValidationError
from pydantic_ai import Agent
from pydantic_ai.usage import RunUsage, UsageLimits

from api.schemas import Storyboard
from domain.models.workflow import GlobalContext
from infra.ai.base import BaseConceptModel
from infra.ai.factory import NanoConceptModel
from infra.ai.streaming import run_agent_streamed

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)


class ArchitectCompatibilityError(ValueError):
    """Raised when compatibility-mode architect output is unusable."""


def json_mode_prompt(system_prompt: str) -> str:
    """Converts only the output-transport instruction to JSON mode."""
    marker = "You must output a structured storyboard using the final_result tool."
    replacement = (
        "Return valid JSON only, with no tools or Markdown fencing. Use exactly the "
        "ConceptCast schema field names: concept_title, scenes, scene_id, title, "
        "description, narration, duration, objects, name, type, position, color, "
        "label, parameters, and bounding_box. Every scene must include a meaningful "
        "description, narration, and at least one visual object; every object must "
        "include a non-empty name, type, and position. Preserve creative visual "
        "detail in descriptions, labels, parameters, and animation ideas."
    )
    if marker not in system_prompt:
        raise ArchitectCompatibilityError(
            "Architect prompt does not contain the expected final_result instruction."
        )
    return system_prompt.replace(marker, replacement, 1)


def extract_storyboard_json(raw: str) -> Storyboard:
    """Extracts and strictly validates one complete Storyboard JSON object."""
    candidates = _JSON_BLOCK_RE.findall(raw)
    if not candidates:
        candidates = [raw.strip()]

    last_error: Exception | None = None
    for candidate in reversed(candidates):
        try:
            payload: Any = json.loads(candidate)
            return Storyboard.model_validate(_normalize_qwen_payload(payload))
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc

    detail = str(last_error) if last_error else "no JSON object found"
    raise ArchitectCompatibilityError(
        f"Compatibility architect output failed Storyboard validation: {detail}"
    ) from last_error


def _normalize_qwen_payload(payload: Any) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Normalize only documented Qwen architect aliases into Storyboard fields."""
    if not isinstance(payload, dict):
        raise ArchitectCompatibilityError("Storyboard JSON must be an object.")
    for wrapper_key in ("project", "storyboard"):
        if isinstance(payload.get(wrapper_key), dict):
            payload = payload[wrapper_key]
            break
    metadata = payload.get("project_metadata")
    if isinstance(metadata, dict):
        payload = {**payload, **metadata}
    if "project_title" in payload and "concept_title" not in payload:
        payload = {**payload, "concept_title": payload["project_title"]}
    scenes = payload.get("scenes")
    if not isinstance(scenes, list):
        return dict(payload)

    normalized_scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, dict):
            raise ArchitectCompatibilityError(
                "Each storyboard scene must be an object."
            )
        scene_copy = dict(scene)
        scene_copy.setdefault("scene_id", scene_copy.pop("step_id", index))
        for description_key in ("scene_description", "visual_description"):
            if description_key in scene_copy:
                scene_copy.setdefault("description", scene_copy.pop(description_key))
                break
        if "visual_composition" in scene_copy:
            scene_copy.setdefault("description", scene_copy.pop("visual_composition"))
        if "layout" in scene_copy:
            scene_copy.setdefault("description", scene_copy.pop("layout"))
        if "layout_description" in scene_copy:
            scene_copy.setdefault("description", scene_copy.pop("layout_description"))
        if "pedagogical_note" in scene_copy:
            scene_copy.setdefault("narration", scene_copy.pop("pedagogical_note"))
        if isinstance(scene_copy.get("description"), dict):
            description = scene_copy["description"]
            scene_copy["description"] = (
                description.get("description")
                if isinstance(description.get("description"), str)
                else json.dumps(description, separators=(",", ":"))
            )
        scene_copy.setdefault("title", scene_copy.get("concept", f"Scene {index}"))
        objects = scene_copy.get("objects", scene_copy.pop("manim_objects", None))
        if isinstance(objects, list):
            normalized_objects: list[dict[str, Any]] = []
            for object_index, obj in enumerate(objects, start=1):
                if not isinstance(obj, dict):
                    raise ArchitectCompatibilityError(
                        "Each storyboard visual object must be an object."
                    )
                obj_copy = dict(obj)
                obj_copy.setdefault(
                    "name",
                    obj_copy.pop(
                        "id", f"{obj_copy.get('type', 'object').lower()}_{object_index}"
                    ),
                )
                obj_copy.setdefault("parameters", obj_copy.pop("properties", {}))
                if isinstance(obj_copy.get("parameters"), str):
                    obj_copy["parameters"] = {"raw": obj_copy["parameters"]}
                if isinstance(obj_copy.get("position"), (dict, list)):
                    obj_copy["position"] = json.dumps(
                        obj_copy["position"], separators=(",", ":")
                    )
                bounding_box = obj_copy.get("bounding_box")
                if isinstance(bounding_box, list) and len(bounding_box) == 4:
                    left, bottom, right, top = bounding_box
                    if all(isinstance(value, int | float) for value in bounding_box):
                        obj_copy["bounding_box"] = (right - left, top - bottom)
                elif isinstance(bounding_box, dict) and all(
                    isinstance(bounding_box.get(key), int | float)
                    for key in ("width", "height")
                ):
                    obj_copy["bounding_box"] = (
                        bounding_box["width"],
                        bounding_box["height"],
                    )
                normalized_objects.append(obj_copy)
            scene_copy["objects"] = normalized_objects
        normalized_scenes.append(scene_copy)

    result = dict(payload)
    result["scenes"] = normalized_scenes
    return result


async def generate_storyboard_json_mode(
    *,
    system_prompt: str,
    prompt: str,
    model: BaseConceptModel,
    on_thought: Callable[[str, str, str], Awaitable[None]] | None = None,
    ctx: GlobalContext | None = None,
    usage_limits: UsageLimits | None = None,
) -> tuple[Storyboard, RunUsage]:
    """Generates a storyboard through plain text, then validates it locally.

    This adapter deliberately exposes no tools and requests a string from
    PydanticAI. It is intended for OpenAI-compatible endpoints that reject
    tool-based structured output while still returning valid JSON text.
    """
    agent = Agent(
        model.model,
        system_prompt=json_mode_prompt(system_prompt),
        output_type=str,
        deps_type=GlobalContext,
        retries=2,
    )
    stream = not isinstance(model, NanoConceptModel)
    raw, usage = await run_agent_streamed(
        "architect",
        agent,
        prompt,
        on_thought=on_thought,
        deps=ctx,
        usage_limits=usage_limits,
        stream=stream,
    )
    if not isinstance(raw, str):
        raise ArchitectCompatibilityError(
            f"Expected JSON text from compatibility architect, got {type(raw).__name__}."
        )
    return extract_storyboard_json(raw), usage
