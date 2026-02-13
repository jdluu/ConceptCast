import asyncio
import re
from pathlib import Path

from loguru import logger

# Patterns that should never appear in generated Manim code.
# This is a heuristic blocklist, not a true sandbox.
_BLOCKED_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bimport\s+(os|sys|subprocess|shutil|socket|http|requests|urllib|importlib|pickle)\b"),
    re.compile(r"\bfrom\s+(os|sys|subprocess|shutil|socket|http|requests|urllib|importlib|pickle)\b"),
    re.compile(r"\b__import__\s*\("),
    re.compile(r"\bexec\s*\("),
    re.compile(r"\beval\s*\("),
    re.compile(r"\bcompile\s*\("),
    re.compile(r"\bopen\s*\("),
    re.compile(r"\binput\s*\("),
    re.compile(r"\bbreakpoint\s*\("),
    re.compile(r"\bgetattr\s*\("),
]


def _sanitize_code(code: str) -> None:
    """
    Scans generated Manim code for dangerous patterns before execution.

    Checks against a blocklist of imports and builtins that should never
    appear in legitimate Manim animation code.

    Args:
        code: The generated Python code to validate.

    Raises:
        RuntimeError: If any blocked pattern is detected.
    """
    for pattern in _BLOCKED_PATTERNS:
        match = pattern.search(code)
        if match:
            raise RuntimeError(
                f"Generated code contains unsafe pattern: '{match.group()}'. "
                "Aborting execution."
            )


async def render_storyboard(code: str, job_id: str) -> str:
    """
    Renders a Manim scene from the provided code asynchronously.
    Artifacts are stored in the project-root data/jobs/{job_id} directory.

    Args:
        code: The generated Manim Python code.
        job_id: Unique ID of the job.

    Returns:
        str: Relative path to the rendered video file.

    Raises:
        RuntimeError: If code sanitization or rendering fails.
    """
    _sanitize_code(code)

    # Use project-root data/jobs folder
    project_root = Path(__file__).parent.parent.parent.parent.parent
    job_dir = project_root / "data" / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    code_file = job_dir / "scene.py"
    code_file.write_text(code)

    logger.info(f"Rendering job {job_id} in {job_dir}...")

    # Execute rendering in Docker sandbox for security
    from services.sandbox import docker_sandbox

    try:
        render_output = docker_sandbox.run_rendering(
            job_dir=job_dir,
            code_file="scene.py",
            scene_name="SceneGen"
        )
        
        if render_output is None:
            # Fallback for environments without Docker (e.g., local dev)
            logger.warning("Docker sandbox unavailable, falling back to local execution (UNSAFE)")
            process = await asyncio.create_subprocess_exec(
                "manim",
                "-ql",
                "--media_dir",
                ".",
                str(code_file),
                "SceneGen",
                cwd=str(job_dir),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"Local rendering failed: {stderr.decode()}")

    except Exception as e:
        logger.error(f"Sandbox execution failed for job {job_id}: {e}")
        raise RuntimeError(f"Rendering failed: {str(e)}")

    # Locate the output video
    # Manim structure with --media_dir .: job_dir/videos/scene/480p15/SceneGen.mp4
    video_output = job_dir / "videos" / "scene" / "480p15" / "SceneGen.mp4"
    if not video_output.exists():
        raise RuntimeError(
            f"Rendering finished but output file not found at {video_output}"
        )

    # Move to top-level of job directory for easier serving
    final_path = job_dir / "video.mp4"
    video_output.rename(final_path)

    logger.info(f"Successfully rendered video for job {job_id} at {final_path}")
    return f"/jobs/{job_id}/video.mp4"
