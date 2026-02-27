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
            logger.error(f"Engine health check failed: {e}")
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
                    "docker.io/manimcommunity/manim:latest",
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
                logger.error(f"Syntax check timed out after {timeout}s")
                return SandboxResult(
                    stdout="", stderr=f"Check timed out after {timeout}s"
                )

            return SandboxResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
            )
        except Exception as e:
            logger.error(f"Syntax check failed: {e}")
            return SandboxResult(stdout="", stderr=str(e))

    async def run_rendering(
        self,
        job_dir: Path,
        code_file: str,
        scene_name: str = "SceneGen",
        host_job_dir: Path | None = None,
        quality_flag: str = "-ql",
        log_callback: Callable[[str], Any] | None = None,
        timeout: int = 300,
    ) -> SandboxResult | None:
        """Executes Manim rendering via Podman or local subprocess."""
        try:
            if self.use_podman:
                cmd = [
                    "podman",
                    "run",
                    "--rm",
                    "--userns=keep-id",
                    "-v",
                    f"{job_dir.absolute()}:/manim",
                    "docker.io/manimcommunity/manim:latest",
                    "manim",
                    quality_flag,
                    "--media_dir",
                    ".",
                    code_file,
                    scene_name,
                ]
            else:
                cmd = ["manim", quality_flag, "--media_dir", ".", code_file, scene_name]

            logger.info(f"Sandbox executing: {' '.join(cmd)}")
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
                logger.error(f"Rendering timed out after {timeout}s")
                raise RuntimeError(f"Rendering timed out after {timeout}s") from None

            if process.returncode != 0:
                err_msg = stderr_str or stdout_str
                logger.error(f"Rendering failed (code {process.returncode}): {err_msg}")
                raise RuntimeError(f"Rendering failed: {err_msg}")

            return SandboxResult(stdout=stdout_str, stderr=stderr_str)

        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            logger.error(f"Execution failed: {e}")
            raise RuntimeError(f"Execution failed: {str(e)}") from e


# Global singleton for sandbox execution
local_sandbox = LocalSandbox()
