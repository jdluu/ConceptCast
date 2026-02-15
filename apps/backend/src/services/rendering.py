import ast
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from core.exceptions import AnimationGenerationError
from core.settings import get_settings

# Opening code fence (optional "python" / "py")
_CODE_FENCE_START = re.compile(r"^\s*```(?:python|py)?\s*\n?", re.IGNORECASE)

# Allowed modules for import
_ALLOWED_MODULES = {
    "manim",
    "math",
    "numpy",
    "random",
    "datetime",
    "itertools",
    "typing",
}

# Builtin functions that are explicitly banned
_BANNED_BUILTINS = {
    "exec",
    "eval",
    "compile",
    "open",
    "input",
    "breakpoint",
    "getattr",
    "setattr",
    "delattr",
    "__import__",
    "globals",
    "locals",
    "vars",
    "memoryview",
}


class ASTSanitizer(ast.NodeVisitor):
    """
    AST-based sanitizer to ensure generated Manim code does not perform
    unsafe operations like arbitrary IO, system calls, or dynamic execution.
    """

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            base_module = alias.name.split(".")[0]
            if base_module not in _ALLOWED_MODULES:
                raise RuntimeError(f"Import of module '{alias.name}' is not allowed.")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            base_module = node.module.split(".")[0]
            if base_module not in _ALLOWED_MODULES:
                raise RuntimeError(
                    f"Import from module '{node.module}' is not allowed."
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # Check for calls to banned builtins (e.g., eval("..."))
        if isinstance(node.func, ast.Name) and node.func.id in _BANNED_BUILTINS:
            raise RuntimeError(f"Call to unsafe builtin '{node.func.id}' is forbidden.")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Block access to private/dunder attributes which are often used in jailbreaks
        # e.g., __subclasses__, __bases__, __globals__
        # We allow __init__ and standard Manim/Python dunders might be needed,
        # but for generated code, simple access is safer.
        # Stricter: Block anything starting with __ except known safe ones?
        # For now, block specific dangerous ones.
        if node.attr in {
            "__subclasses__",
            "__bases__",
            "__globals__",
            "__code__",
            "__closure__",
            "__func__",
            "__self__",
            "__module__",
            "__dict__",
        }:
            raise RuntimeError(
                f"Access to unsafe attribute '{node.attr}' is forbidden."
            )
        self.generic_visit(node)


def _sanitize_code(code: str) -> None:
    """
    Scans generated Manim code using AST parsing to validate safety.
    Raises RuntimeError if unsafe patterns are detected.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise RuntimeError(f"Syntax error in generated code: {e}") from e

    sanitizer = ASTSanitizer()
    sanitizer.visit(tree)


def extract_and_validate_manim_code(raw: str) -> str:
    """
    Extracts raw Python from animator output (strips markdown fences) and validates.

    - Removes leading ```python / ``` and trailing ``` so Manim receives valid .py.
    - Validates Python syntax with ast.parse.
    - Ensures a class named SceneGen exists (required for rendering).

    Args:
        raw: The animator output (may be wrapped in markdown code blocks).

    Returns:
        str: Cleaned, validated Python code.

    Raises:
        RuntimeError: If code cannot be extracted, is invalid Python,
            or missing SceneGen.
    """
    code = raw.strip()
    # Strip opening fence (e.g. ```python or ```)
    if _CODE_FENCE_START.match(code):
        code = _CODE_FENCE_START.sub("", code, count=1)
    # Strip trailing fence
    if code.endswith("```"):
        code = code[: code.rfind("```")].rstrip()
    code = code.strip()
    if not code:
        raise RuntimeError(
            "Animator output was empty or only contained markdown fences. "
            "Expected raw Python code with a SceneGen class."
        )
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise RuntimeError(
            f"Generated Manim code has a Python syntax error: {e}. "
            "Animator must return only valid Python with a class SceneGen(Scene)."
        ) from e

    # AST validation (sanitization + structure check)
    sanitizer = ASTSanitizer()
    try:
        sanitizer.visit(tree)
    except RuntimeError as e:
        raise RuntimeError(f"Code validation failed: {e}") from e

    has_scene_gen = any(
        isinstance(node, ast.ClassDef) and node.name == "SceneGen"
        for node in ast.walk(tree)
    )
    if not has_scene_gen:
        raise RuntimeError(
            "Generated code must define a class named SceneGen inheriting from Scene. "
            "Animator must return only raw Python code."
        )
    return code


def _quality_to_flag(quality: str) -> str:
    normalized = quality.strip().lower()
    mapping = {
        "ql": "-ql",
        "low": "-ql",
        "dev": "-ql",
        "qm": "-qm",
        "medium": "-qm",
        "prod": "-qh",
        "production": "-qh",
        "qh": "-qh",
        "high": "-qh",
    }
    return mapping.get(normalized, "-ql")


@dataclass
class VideoResult:
    """Result of a full-quality video render."""

    video_url: str
    thumbnail_url: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class PreviewResult:
    """Result of a low-quality preview render."""

    success: bool
    logs: str
    frame_path: Path | None
    error: str | None


async def render_storyboard(code: str, job_id: str) -> VideoResult:
    """
    Renders the Manim animation for the given code.

    Args:
        code: The Manim Python code to execute.
        job_id: Unique job identifier for artifact isolation.

    Returns:
        VideoResult: Object containing URLs and metadata.

    Raises:
        AnimationGenerationError: If rendering fails or code is invalid.
    """
    # 1. Validate and sanitize code
    try:
        validated_code = extract_and_validate_manim_code(code)
    except Exception as e:
        raise AnimationGenerationError(f"Invalid Manim code: {e}") from e

    # 2. Setup job directory
    # host_data_dir is the path on the host machine where data is stored
    # We need this for Docker volume mounting when running in a container
    host_data_dir = os.getenv("HOST_DATA_DIR")
    base_dir = Path("/app/data") if host_data_dir else get_settings().data_dir

    job_dir = base_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    code_file = job_dir / "scene.py"
    code_file.write_text(validated_code)

    # 3. Execute in Sandbox
    logger.info(f"Starting render for job {job_id}")

    # If running in Docker (HOST_DATA_DIR set), we need to pass the host path
    host_job_dir = Path(host_data_dir) / "jobs" / job_id if host_data_dir else None

    # Retry logic for transient rendering issues
    max_retries = 2
    last_error = None

    from services.sandbox import docker_sandbox

    for attempt in range(max_retries + 1):
        try:
            result = docker_sandbox.run_rendering(
                job_dir=job_dir,
                code_file="scene.py",
                scene_name="SceneGen",
                host_job_dir=host_job_dir,
                quality_flag=_quality_to_flag(
                    get_settings().render_quality
                ),  # Use configured quality
            )

            if not result:
                # If sandbox failed to start (e.g. no docker), we error out
                raise AnimationGenerationError("Rendering sandbox unavailable")

            # Check for output file
            # Manim -ql produces 480p15 video strings in
            # media/videos/scene/480p15/SceneGen.mp4
            # We need to find where it actually went.
            # With --media_dir ., it should be in
            # ./videos/scene/480p15/SceneGen.mp4 if code uses defaults?
            # Actually, defaults are media/videos/...
            # Let's find the .mp4 file
            video_files = list(job_dir.glob("**/*.mp4"))
            if not video_files:
                logger.error(
                    f"Manim finished but no video found. Logs:\n"
                    f"{result.stdout}\n{result.stderr}"
                )
                raise AnimationGenerationError(
                    "Manim finished but produced no video file."
                )

            video_path = video_files[0]

            # Move/Rename to a standard location: {job_dir}/video.mp4
            final_video_path = job_dir / "video.mp4"
            shutil.move(str(video_path), str(final_video_path))

            # Cleanup media dir? kept for debugging/cache

            # Generate thumbnail and extract metadata
            thumbnail_url = _generate_thumbnail(final_video_path, job_id)
            metadata = _get_video_metadata(final_video_path)

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


async def render_preview(code: str, job_id: str) -> PreviewResult:
    """
    Generates a low-quality preview execution to capture logs and potential errors.
    Does not halt on video missing, but returns logs for analysis.
    """
    # 1. Validate
    try:
        validated_code = extract_and_validate_manim_code(code)
    except Exception as e:
        return PreviewResult(success=False, logs=str(e), frame_path=None, error=str(e))

    # 2. Setup (Reuse logic - simpler path)
    host_data_dir = os.getenv("HOST_DATA_DIR")
    base_dir = Path("/app/data") if host_data_dir else get_settings().data_dir
    job_dir = base_dir / "jobs" / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    code_file = job_dir / "scene.py"
    code_file.write_text(validated_code)

    host_job_dir = Path(host_data_dir) / "jobs" / job_id if host_data_dir else None

    # 3. Run with low quality
    try:
        from services.sandbox import docker_sandbox

        result = docker_sandbox.run_rendering(
            job_dir=job_dir,
            code_file="scene.py",
            scene_name="SceneGen",
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

        # Check success by looking for video OR just return logs
        video_files = list(job_dir.glob("**/*.mp4"))
        success = len(video_files) > 0

        # Future: extract the last frame image for vision analysis
        # For now, just return None for frame_path

        combined_logs = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

        return PreviewResult(
            success=success,
            logs=combined_logs,
            frame_path=None,
            error=None if success else "No video output produced",
        )

    except RuntimeError as e:
        return PreviewResult(success=False, logs=str(e), frame_path=None, error=str(e))


def _get_video_metadata(video_path: Path) -> dict[str, Any]:
    """Extracts resolution, duration, bitrate, etc. using ffprobe."""
    import json
    import subprocess

    try:
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        video_stream = next(
            (s for s in data["streams"] if s["codec_type"] == "video"), {}
        )
        format_data = data.get("format", {})

        return {
            "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}",
            "duration": float(format_data.get("duration", 0)),
            "bitrate": format_data.get("bit_rate"),
            "file_size": f"{int(format_data.get('size', 0)) // (1024 * 1024)}MB",
            "format": format_data.get("format_name"),
        }
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return {}


def _generate_thumbnail(video_path: Path, job_id: str) -> str | None:
    """Generates a JPG thumbnail from the middle of the video."""
    import subprocess

    thumb_path = video_path.parent / "thumbnail.jpg"
    try:
        # Seek to 1 second in or half way
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-ss",
            "00:00:01",
            "-vframes",
            "1",
            "-q:v",
            "2",
            str(thumb_path),
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        return f"/jobs/artifacts/{job_id}/thumbnail.jpg"
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None
