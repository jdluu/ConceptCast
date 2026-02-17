import json
import subprocess
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel


class VideoMetadata(BaseModel):
    """Structured metadata for a rendered video.

    Attributes:
        resolution (str): The video dimensions (e.g., '1920x1080').
        duration (float): Length of the video in seconds.
        bitrate (Optional[str]): Average bitrate of the video stream.
        file_size (str): Human-readable file size (e.g., '12MB').
        format (Optional[str]): Video container format name.
    """

    resolution: str
    duration: float
    bitrate: str | None = None
    file_size: str
    format: str | None = None


def get_video_metadata(video_path: Path) -> dict[str, Any]:
    """Extracts technical metadata from a video file using ffprobe.

    Args:
        video_path (Path): Path to the video file to analyze.

    Returns:
        dict[str, Any]: A dictionary containing resolution, duration, bitrate,
            file_size, and format. Returns an empty dict if extraction fails.
    """
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
        result = subprocess.run(  # noqa: S603
            cmd, capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)

        video_stream: Any = next(
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


def generate_thumbnail(video_path: Path, job_id: str) -> str | None:
    """Generates a JPG preview thumbnail from a video file.

    Extracts a single frame from the 1-second mark of the video.

    Args:
        video_path (Path): Path to the source video file.
        job_id (str): The unique identifier for the job, used in the return path.

    Returns:
        Optional[str]: The public URL path to the generated thumbnail,
            or None if generation fails.
    """
    thumb_path = video_path.parent / "thumbnail.jpg"
    try:
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
        # Using subprocess to call external tool ffmpeg. Arguments are
        # explicitly listed,
        # so shell=False is safe and preferred.
        subprocess.run(cmd, capture_output=True, check=True)  # noqa: S603
        return f"/jobs/artifacts/{job_id}/thumbnail.jpg"
    except Exception as e:
        logger.error(f"Thumbnail generation failed: {e}")
        return None
