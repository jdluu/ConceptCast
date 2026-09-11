"""Probe one real Qwen animator scene without creating a workflow job."""

from __future__ import annotations

import argparse
import ast
import json
import sqlite3
from pathlib import Path

from api.schemas import Scene
from domain.agents.animator import extract_python_code, generate_manim_code
from domain.models.workflow import GlobalContext
from infra.ai.factory import get_concept_model
from infra.ai.tools.analysis import statically_check_layout_collisions


def latest_storyboard(topic: str) -> tuple[dict, dict]:
    db = Path(__file__).resolve().parents[4] / "data" / "conceptcast.db"
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT plan, storyboard FROM jobs "
            "WHERE topic LIKE ? AND storyboard IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1",
            (f"%{topic}%",),
        ).fetchone()
    if not row:
        raise RuntimeError(f"No stored storyboard found for topic: {topic}")
    return json.loads(row[0]), json.loads(row[1])


async def main(topic: str, model_id: str) -> None:
    _plan, storyboard_data = latest_storyboard(topic)
    scene = storyboard_data["scenes"][0]
    model = get_concept_model("nano", model_id)
    if model is None:
        raise RuntimeError("Nano model is unavailable")
    ctx = GlobalContext(
        topic=storyboard_data.get("concept_title", topic),
    )
    scene_model = Scene.model_validate(scene)
    raw, usage = await generate_manim_code(
        target_scene=scene_model,
        model=model,
        ctx=ctx,
        scene_id=scene.get("scene_id", 1),
    )
    extracted = extract_python_code(raw)
    print("probe_status=received")
    print(f"requests={usage.requests}")
    print(f"raw_chars={len(raw)}")
    print(f"extracted_chars={len(extracted)}")
    try:
        ast.parse(extracted)
        print("compile_status=ok")
    except SyntaxError as exc:
        print(f"compile_status=failed:{exc}")
    print(f"raw_prefix={raw[:500]!r}")
    print(f"extracted_prefix={extracted[:500]!r}")
    print(
        f"layout_collisions={statically_check_layout_collisions(extracted, scene.get('scene_id', 1), ctx)}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="backpropagation")
    parser.add_argument("--model-id", default="qwen/qwen3.5-122b-a10b:thinking")
    args = parser.parse_args()
    import asyncio

    asyncio.run(main(args.topic, args.model_id))
