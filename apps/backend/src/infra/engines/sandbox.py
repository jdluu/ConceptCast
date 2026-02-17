import asyncio
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel


class SandboxResult(BaseModel):
    """Execution output from a local sandbox run."""
    stdout: str
    stderr: str


class LocalSandbox:
    """Isolated execution environment for Manim animations using local subprocess.

    This service provides a standardized interface for running AI-generated 
    Python code using the system's local Manim installation.
    """

    def __init__(self) -> None:
        """Initializes the sandbox."""
        pass

    def is_healthy(self) -> bool:
        """Verifies if the Manim engine is available in the system path."""
        try:
            # We don't use 'manim --version' here as it can be slow; 
            # just checking if the command exists is usually enough for a fast check.
            import shutil
            return shutil.which("manim") is not None
        except Exception as e:
            logger.error(f"Manim health check failed: {e}")
            return False

    async def run_rendering(
        self,
        job_dir: Path,
        code_file: str,
        scene_name: str = "SceneGen",
        host_job_dir: Path | None = None, # Left for interface compatibility
        quality_flag: str = "-ql",
        log_callback: Callable[[str], Any] | None = None,
    ) -> SandboxResult | None:
        """Executes Manim rendering via local subprocess.

        Args:
            job_dir (Path): Local directory containing the source code.
            code_file (str): The Python filename relative to job_dir.
            scene_name (str): The name of the Manim Scene class to render.
            host_job_dir (Path, optional): Placeholder for interface compatibility.
            quality_flag (str): Manim quality flag (e.g., '-ql', '-qh').
            log_callback (Callable, optional): Callback for streaming logs.

        Returns:
            Optional[SandboxResult]: The captured stdout and stderr.
        """
        try:
            cmd = ["manim", quality_flag, "--media_dir", ".", code_file, scene_name]
            logger.info(f"Starting rendering: {' '.join(cmd)} in {job_dir}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=job_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # If a callback is provided, we need to read the streams line-by-line
            if log_callback:
                stdout_lines = []
                stderr_lines = []

                async def read_stream(stream, callback, lines_list):
                    while True:
                        line = await stream.readline()
                        if not line:
                            break
                        decoded = line.decode("utf-8", errors="replace")
                        lines_list.append(decoded)
                        callback(decoded)

                await asyncio.gather(
                    read_stream(process.stdout, log_callback, stdout_lines),
                    read_stream(process.stderr, log_callback, stderr_lines)
                )
                await process.wait()
                
                stdout_str = "".join(stdout_lines)
                stderr_str = "".join(stderr_lines)
            else:
                stdout, stderr = await process.communicate()
                stdout_str = stdout.decode()
                stderr_str = stderr.decode()

            if process.returncode != 0:
                err_msg = stderr_str or stdout_str
                logger.error(f"Rendering failed (code {process.returncode}): {err_msg}")
                raise RuntimeError(f"Manim rendering failed: {err_msg}")

            return SandboxResult(stdout=stdout_str, stderr=stderr_str)

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise RuntimeError(f"Execution failed: {str(e)}") from e


# Global singleton for sandbox execution
local_sandbox = LocalSandbox()
