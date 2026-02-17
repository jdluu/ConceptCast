import asyncio
import re
import shutil
from collections.abc import Awaitable, Callable, Coroutine
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from loguru import logger

from infra.engines.sandbox import local_sandbox
from infra.exceptions import AnimationGenerationError
from infra.media.processor import generate_thumbnail, get_video_metadata
from infra.security.sanitizer import sanitize_manim_code
from infra.settings import get_settings


@dataclass
class VideoResult:
    """The successful outcome of a full-quality video rendering process."""

    video_url: str
    thumbnail_url: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class PreviewResult:
    """The outcome of a low-quality preview execution, primarily for debugging."""

    success: bool
    logs: str
    frame_path: Path | None
    error: str | None


SCENE_NAME = "SceneGen"
CODE_FILENAME = "scene.py"


def _prepare_render_environment(code: str, job_id: str) -> tuple[Path, Path | None]:
    """Validates Manim code and prepares the job directory for sandbox execution."""
    try:
        validated_code = sanitize_manim_code(code)
    except Exception as e:
        raise AnimationGenerationError(f"Invalid Manim code: {e}") from e

    settings = get_settings()
    job_dir = settings.jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    code_file = job_dir / CODE_FILENAME
    code_file.write_text(validated_code)

    return job_dir, None


async def render_storyboard(
    code: str,
    job_id: str,
    update_job: Callable[[dict[str, Any]], Awaitable[Any]] | None = None,
    resolution: str = "720p",
    frame_rate: int = 30,
) -> VideoResult:
    """Renders a Manim animation with production-quality settings."""
    job_dir, host_job_dir = _prepare_render_environment(code, job_id)

    # 3. Execute in Sandbox
    logger.info(f"Starting render for job {job_id}")

    # Retry logic for transient rendering issues
    max_retries = 2
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            quality_flag = "-qh" if resolution == "1080p" else "-qm"

            def progress_callback(log_line: str) -> None:
                if update_job and ("%" in log_line or "|" in log_line):
                    match = re.search(r"(\d+)%", log_line)
                    if match:
                        progress = int(match.group(1))
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                coro = cast(
                                    Coroutine[Any, Any, Any],
                                    update_job({"render_progress": progress}),
                                )
                                loop.create_task(coro)
                        except Exception as e:
                            logger.debug(f"Progress update failed: {e}")

            result = await local_sandbox.run_rendering(
                job_dir=job_dir,
                code_file=CODE_FILENAME,
                scene_name=SCENE_NAME,
                host_job_dir=host_job_dir,
                quality_flag=quality_flag,
                log_callback=progress_callback,
            )

            if not result:
                raise AnimationGenerationError("Rendering sandbox unavailable")

            video_files = list(job_dir.glob("**/*.mp4"))
            if not video_files:
                logger.error(
                    f"Manim finished but no video found. Logs:\n{result.stderr}"
                )
                raise AnimationGenerationError("Manim produced no video file.")

            video_path = video_files[0]
            final_video_path = job_dir / "video.mp4"
            shutil.move(str(video_path), str(final_video_path))

            thumbnail_url = generate_thumbnail(final_video_path, job_id)
            metadata = get_video_metadata(final_video_path)

            return VideoResult(
                video_url=f"/jobs/artifacts/{job_id}/video.mp4",
                thumbnail_url=thumbnail_url,
                metadata=metadata,
            )

        except RuntimeError as e:
            logger.warning(f"Render attempt {attempt + 1} failed: {e}")
            last_error = e
            if attempt < max_retries:
                continue

    raise AnimationGenerationError(
        f"Rendering failed after retries. Last error: {last_error}"
    )


async def mock_render_storyboard(job_id: str) -> VideoResult:
    """Simulates a rapid render for mock mode, bypassing the sandbox."""
    logger.info(f"Simulating rapid render for mock job {job_id}")
    await asyncio.sleep(2)  # Short artificial delay for realism
    return VideoResult(
        video_url="/static/sample_video.mp4",
        thumbnail_url="/static/sample_thumbnail.jpg",
        metadata={
            "width": 1280,
            "height": 720,
            "fps": 30,
            "duration": 5.0,
            "file_size": 1024 * 1024,
        },
    )


async def render_preview(code: str, job_id: str) -> PreviewResult:
    """Executes a low-quality render to capture logs and validate Manim code."""
    try:
        job_dir, host_job_dir = _prepare_render_environment(code, job_id)
    except AnimationGenerationError as e:
        return PreviewResult(
            success=False, logs=e.message, frame_path=None, error=e.message
        )
    except Exception as e:
        return PreviewResult(success=False, logs=str(e), frame_path=None, error=str(e))

    # Run with low quality
    try:
        result = await local_sandbox.run_rendering(
            job_dir=job_dir,
            code_file=CODE_FILENAME,
            scene_name=SCENE_NAME,
            host_job_dir=host_job_dir,
            quality_flag="-ql",
        )

        if not result:
            return PreviewResult(
                success=False,
                logs="Sandbox unavailable",
                frame_path=None,
                error="Sandbox unavailable",
            )

        video_files = list(job_dir.glob("**/*.mp4"))
        success = len(video_files) > 0
        combined_logs = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

        return PreviewResult(
            success=success,
            logs=combined_logs,
            frame_path=None,
            error=None if success else "No video output produced",
        )

    except RuntimeError as e:
        return PreviewResult(success=False, logs=str(e), frame_path=None, error=str(e))


async def mock_render_preview() -> PreviewResult:
    """Simulates a rapid preview for mock mode."""
    return PreviewResult(
        success=True,
        logs="[MOCK] Rapid preview successful",
        frame_path=None,
        error=None,
    )
