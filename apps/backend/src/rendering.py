import asyncio
from pathlib import Path

from loguru import logger


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
        RuntimeError: If rendering fails.
    """
    # Use project-root data/jobs folder
    project_root = Path(__file__).parent.parent.parent.parent
    job_dir = project_root / "data" / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    code_file = job_dir / "scene.py"
    code_file.write_text(code)

    logger.info(f"Rendering job {job_id} in {job_dir}...")

    # Run Manim command asynchronously
    process = await asyncio.create_subprocess_exec(
        "manim",
        "-ql",
        "--media_dir",
        str(job_dir),
        str(code_file),
        "SceneGen",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        logger.error(f"Manim rendering failed for job {job_id}: {error_msg}")
        raise RuntimeError(f"Manim rendering failed: {error_msg}")

    # Locate the output video
    # Manim structure: job_dir/videos/scene/480p15/SceneGen.mp4
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
