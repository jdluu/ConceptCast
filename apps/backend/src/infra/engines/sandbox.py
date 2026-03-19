import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

MANIM_IMAGE = "docker.io/manimcommunity/manim:v0.20.1"


class SandboxResult(BaseModel):
    """Encapsulates the execution output from a sandboxed Manim run.

    Attributes:
        stdout: Standard output from the execution process.
        stderr: Standard error or diagnostic information from the process.
    """

    stdout: str
    stderr: str


class LocalSandbox:
    """Isolated execution environment for Manim animations.

    By default, it uses Podman to run a sandboxed container.
    If Podman is not available, it logs a warning and falls back
    to the local Manim installation.
    """

    def __init__(self) -> None:
        """Initializes the sandbox execution strategy."""
        import shutil

        self.use_podman = shutil.which("podman") is not None

    def is_healthy(self) -> bool:
        """Verifies if either Podman or local Manim is available."""
        try:
            import shutil

            if shutil.which("podman") is not None:
                return True
            return shutil.which("manim") is not None
        except Exception as e:
            logger.error("sandbox_engine_health_check_failed", error=str(e))
            return False

    async def run_check(
        self,
        job_dir: Path,
        code_file: str,
        timeout: int = 30,
    ) -> SandboxResult:
        """Performs a lightweight syntax and integrity check on the code."""
        try:
            if self.use_podman:
                cmd = [
                    "podman",
                    "run",
                    "--rm",
                    "--userns=keep-id",
                    "-v",
                    f"{job_dir.absolute()}:/manim",
                    MANIM_IMAGE,
                    "python3",
                    "-m",
                    "py_compile",
                    code_file,
                ]
            else:
                cmd = ["python3", "-m", "py_compile", code_file]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=job_dir if not self.use_podman else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except TimeoutError:
                process.kill()
                logger.error("sandbox_syntax_check_timeout", timeout_seconds=timeout)
                return SandboxResult(
                    stdout="", stderr=f"Check timed out after {timeout}s"
                )

            return SandboxResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
            )
        except Exception as e:
            logger.error("sandbox_syntax_check_failed", error=str(e))
            return SandboxResult(stdout="", stderr=str(e))

    async def run_rendering(
        self,
        job_dir: Path,
        code_file: str,
        scene_name: str = "SceneGen",
        host_job_dir: Path | None = None,  # noqa: ARG002
        quality_flag: str = "-ql",
        log_callback: Callable[[str], Any] | None = None,
        timeout: int = 300,
    ) -> SandboxResult | None:
        """Executes full Manim rendering for a specified scene.

        Orchestrates the rendering process, capturing live logs and handling
        process timeouts/errors. Supports both containerized and local modes.

        Args:
            job_dir: Root directory for the rendering job.
            code_file: Python file containing the Scene definitions.
            scene_name: The specific Scene class to render.
            host_job_dir: Optional host-relative path for volume mounting.
            quality_flag: Manim quality flag (e.g., -ql, -qm, -qh).
            log_callback: Optional function to receive live log lines.
            timeout: Maximum allowed rendering duration in seconds.

        Returns:
            A SandboxResult on success.

        Raises:
            RuntimeError: If rendering fails or times out.
        """
        try:
            if self.use_podman:
                cmd = [
                    "podman",
                    "run",
                    "--rm",
                    "--userns=keep-id",
                    "-v",
                    f"{job_dir.absolute()}:/manim",
                    MANIM_IMAGE,
                    "manim",
                    quality_flag,
                    "--media_dir",
                    ".",
                    code_file,
                    scene_name,
                ]
            else:
                cmd = ["manim", quality_flag, "--media_dir", ".", code_file, scene_name]

            logger.info(
                "sandbox_render_execution_started",
                command=" ".join(cmd),
                use_podman=self.use_podman,
            )
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=job_dir if not self.use_podman else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                if log_callback:
                    stdout_lines: list[str] = []
                    stderr_lines: list[str] = []

                    async def read_stream(
                        stream: Any,
                        callback: Callable[[str], Any],
                        lines_list: list[str],
                    ) -> None:
                        if not stream:
                            return
                        while True:
                            line = await stream.readline()
                            if not line:
                                break
                            decoded = line.decode("utf-8", errors="replace")
                            lines_list.append(decoded)
                            callback(decoded)

                    await asyncio.wait_for(
                        asyncio.gather(
                            read_stream(process.stdout, log_callback, stdout_lines),
                            read_stream(process.stderr, log_callback, stderr_lines),
                        ),
                        timeout=timeout,
                    )
                    await process.wait()

                    stdout_str = "".join(stdout_lines)
                    stderr_str = "".join(stderr_lines)
                else:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(), timeout=timeout
                    )
                    stdout_str = stdout.decode("utf-8", errors="replace")
                    stderr_str = stderr.decode("utf-8", errors="replace")
            except TimeoutError:
                process.kill()
                logger.error("sandbox_render_timeout", timeout_seconds=timeout)
                raise RuntimeError(f"Rendering timed out after {timeout}s") from None

            if process.returncode != 0:
                err_msg = stderr_str or stdout_str
                logger.error(
                    "sandbox_render_failed",
                    return_code=process.returncode,
                    error_message=err_msg,
                )
                raise RuntimeError(f"Rendering failed: {err_msg}")

            return SandboxResult(stdout=stdout_str, stderr=stderr_str)

        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.error("sandbox_execution_failed", error=str(e))
            raise RuntimeError(f"Execution failed: {str(e)}") from e


# Global singleton for sandbox execution
local_sandbox = LocalSandbox()
