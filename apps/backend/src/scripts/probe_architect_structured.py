#!/usr/bin/env python3
"""Probe one structured architect request without creating a workflow job."""

from __future__ import annotations

import asyncio
import sys

from api.schemas import CurriculumPlan, TeachingStep
from domain.agents.architect import generate_storyboard
from infra.ai.factory import get_concept_model


async def main() -> int:
    model_id = sys.argv[1] if len(sys.argv) > 1 else "qwen/qwen3.5-122b-a10b:thinking"
    plan = CurriculumPlan(
        concept_title="Structured-output probe",
        target_audience="General Audience",
        teaching_steps=[
            TeachingStep(
                step_id=1,
                concept="A changing quantity",
                visual_metaphor="An object moving along a number line",
                narration="We represent a changing quantity visually.",
                estimated_duration=4,
            )
        ],
    )
    # This request is intentionally made outside the job/orchestrator path.
    model = get_concept_model(provider_name="nano", model_id=model_id)
    if model is None:
        print("probe_status=configuration_error")
        return 2
    try:
        storyboard, usage = await generate_storyboard(plan, model)
    except Exception as exc:
        print("probe_status=failed")
        print(f"error_type={type(exc).__name__}")
        print(f"error={exc}")
        return 1
    print("probe_status=structured_output_supported")
    print(f"scene_count={len(storyboard.scenes)}")
    print(f"requests={usage.requests}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
