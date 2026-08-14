"""Opt-in compatibility helpers for providers without structured tool output.

This module is deliberately not wired into the live architect path yet. It gives
provider adapters a narrow, testable boundary: request JSON, extract one object,
and validate the complete Storyboard schema without weakening visual fields.
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from api.schemas import Storyboard

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.IGNORECASE | re.DOTALL)


class ArchitectCompatibilityError(ValueError):
    """Raised when compatibility-mode architect output is unusable."""


def json_mode_prompt(system_prompt: str) -> str:
    """Converts only the output-transport instruction to JSON mode."""
    marker = "You must output a structured storyboard using the final_result tool."
    replacement = (
        "Return the structured storyboard as valid JSON matching the requested schema. "
        "Do not use tools or Markdown fencing."
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
            return Storyboard.model_validate(payload)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc

    detail = str(last_error) if last_error else "no JSON object found"
    raise ArchitectCompatibilityError(
        f"Compatibility architect output failed Storyboard validation: {detail}"
    ) from last_error
