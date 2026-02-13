import os
from pathlib import Path

import pytest
from services.sandbox import docker_sandbox


@pytest.mark.asyncio
async def test_docker_sandbox_rendering(tmp_path):
    """Verifies that the Docker sandbox can render a simple Manim scene.
    
    This test requires Docker to be running and the manimcommunity/manim image to be available.
    """
    if not docker_sandbox.client:
        pytest.skip("Docker not available")

    # Create a dummy Manim script
    code = """from manim import *

class SceneGen(Scene):
    def construct(self):
        circle = Circle()
        self.play(Create(circle))
"""
    job_dir = tmp_path / "job_test"
    job_dir.mkdir()
    code_file = job_dir / "scene.py"
    code_file.write_text(code)

    try:
        # Run rendering in sandbox
        output = docker_sandbox.run_rendering(
            job_dir=job_dir,
            code_file="scene.py",
            scene_name="SceneGen"
        )
        
        assert output is not None
        # Check if output video exists
        # Manim structure with --media_dir .: job_dir/videos/scene/480p15/SceneGen.mp4
        video_path = job_dir / "videos" / "scene" / "480p15" / "SceneGen.mp4"
        assert video_path.exists()
        
    except Exception as e:
        pytest.fail(f"Sandbox rendering failed: {e}")
