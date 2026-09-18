import asyncio
import platform
import shutil
import subprocess
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import structlog
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

MANIM_IMAGE = "docker.io/manimcommunity/manim:v0.20.1"


class SandboxResult(BaseModel):
    """Encapsulates the execution output from a sandboxed Manim run."""

    stdout: str
    stderr: str


class LocalSandbox:
    """Isolated execution environment for Manim animations.

    Supports Podman, Docker, or local Manim installation.
    """

    def __init__(self) -> None:
        """Initializes the sandbox execution strategy."""
        self.container_tool: Literal["podman", "docker"] | None = None
        if shutil.which("podman"):
            self.container_tool = "podman"
        elif shutil.which("docker"):
            self.container_tool = "docker"

        self.is_linux = platform.system().lower() == "linux"
        self._podman_ok_cache: bool | None = None

    def _podman_ok(self) -> bool:
        """Checks if podman can actually start containers (namespace support)."""
        if self._podman_ok_cache is not None:
            return self._podman_ok_cache
        try:
            result = subprocess.run(
                [
                    "podman",
                    "run",
                    "--rm",
                    "docker.io/library/alpine:latest",
                    "echo",
                    "ok",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self._podman_ok_cache = result.returncode == 0
        except Exception:
            self._podman_ok_cache = False
        return self._podman_ok_cache

    def is_healthy(self) -> bool:
        """Verifies if a container tool or local Manim installation is available.

        Returns:
            bool: True if the environment is capable of rendering animations.
        """
        return self.container_tool is not None or shutil.which("manim") is not None

    def _get_base_cmd(self, job_dir: Path, cidfile: Path | None = None) -> list[str]:
        """Constructs the base container command with platform-specific optimizations.

        Handles volume mounting using POSIX-compliant paths and applies Linux-specific
        permission flags for Podman.

        Args:
            job_dir: The directory containing the Manim code and assets.
            cidfile: Optional path podman writes the container ID to. Recorded so a
                killed client process can still be reaped by container ID.

        Returns:
            list[str]: The command prefix for running a container, or empty if using local Manim.
        """
        if not self.container_tool:
            return []

        # Podman may be broken (ownership corruption, namespace issues) — probe it
        if self.container_tool == "podman" and not self._podman_ok():
            logger.warning("podman_broken_falling_back_to_local_manim")
            self.container_tool = None
            return []

        cmd = [self.container_tool, "run", "--rm"]

        # `--rm` only fires while the CLIENT survives to observe the exit. Killing
        # the client detaches the container, which then runs forever with nothing
        # left to remove it. Recording the ID makes cleanup possible after a kill.
        if cidfile is not None:
            cmd.extend(["--cidfile", str(cidfile.absolute())])

        # Linux-specific Podman optimization for permission handling in shared volumes
        if self.container_tool == "podman" and self.is_linux:
            cmd.append("--userns=keep-id")

        # Map volume. Use as_posix() for cross-platform path strings.
        cmd.extend(["-v", f"{job_dir.absolute().as_posix()}:/manim"])
        cmd.append(MANIM_IMAGE)
        return cmd

    def _new_cidfile(self, job_dir: Path) -> Path:
        """Returns an unused path for podman's ``--cidfile``.

        Podman refuses to start when the target exists, so the name is randomised
        and a leftover file from an earlier run can never collide with a new one.
        """
        return job_dir / f".manim-cid-{uuid.uuid4().hex}"

    def _force_remove(self, container_id: str) -> bool:
        """Force-removes one container by ID. Returns True on success."""
        if not self.container_tool:
            return False
        try:
            result = subprocess.run(
                [self.container_tool, "rm", "-f", "-t", "2", container_id],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
        except Exception as exc:
            logger.error(
                "sandbox_container_remove_failed",
                container_id=container_id,
                error=str(exc),
            )
            return False
        return result.returncode == 0

    def _reap_container(self, cidfile: Path) -> bool:
        """Force-removes the container recorded in *cidfile*. Idempotent.

        Returns False without shelling out when the file is absent, which is the
        normal case: ``--rm`` already removed the container and podman deleted the
        cidfile along with it.
        """
        if not self.container_tool:
            return False
        try:
            container_id = cidfile.read_text().strip()
        except OSError:
            return False
        if not container_id:
            return False
        if self._force_remove(container_id):
            cidfile.unlink(missing_ok=True)
            logger.info("sandbox_container_reaped", container_id=container_id[:12])
            return True
        logger.error("sandbox_container_reap_failed", container_id=container_id)
        return False

    def reap_orphans(self) -> int:
        """Removes leftover Manim containers from earlier runs. Returns the count.

        Orphans have no client left that could ever claim them, so the only way to
        recover them is a sweep by image. Safe to call between runs.
        """
        if not self.container_tool:
            return 0
        try:
            listed = subprocess.run(
                [
                    self.container_tool,
                    "ps",
                    "-a",
                    "--filter",
                    f"ancestor={MANIM_IMAGE}",
                    "-q",
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            orphans = [cid for cid in listed.stdout.split() if cid]
        except Exception as exc:
            logger.error("sandbox_orphan_reap_failed", error=str(exc))
            return 0

        removed = sum(1 for cid in orphans if self._force_remove(cid))
        if removed:
            logger.warning("sandbox_orphan_containers_reaped", count=removed)
        return removed

    async def _terminate(
        self, process: asyncio.subprocess.Process, cidfile: Path
    ) -> None:
        """Kills the client process AND the container it started.

        ``process.kill()`` alone only kills the ``podman run`` client; the
        container keeps running detached, which is how renders leaked and stayed
        ``Up`` for days at 0% CPU.
        """
        process.kill()
        await process.wait()
        await asyncio.to_thread(self._reap_container, cidfile)

    async def run_check(
        self,
        job_dir: Path,
        code_file: str,
        timeout: int = 30,
    ) -> SandboxResult:
        """Performs a lightweight syntax and integrity check on the generated code.

        Uses py_compile to catch basic syntax errors before attempting full rendering.

        Args:
            job_dir: Root directory for the rendering job.
            code_file: The name of the Python file to check.
            timeout: Maximum allowed check duration in seconds.

        Returns:
            SandboxResult: The stdout and stderr from the check.
        """
        cidfile = self._new_cidfile(job_dir)
        try:
            base_cmd = self._get_base_cmd(job_dir, cidfile)
            if base_cmd:
                cmd = base_cmd + ["python3", "-m", "py_compile", code_file]
            else:
                cmd = ["python3", "-m", "py_compile", code_file]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=job_dir if not base_cmd else None,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )
            except TimeoutError:
                await self._terminate(process, cidfile)
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
        finally:
            # Idempotent: a no-op when --rm already cleaned up the container.
            await asyncio.to_thread(self._reap_container, cidfile)

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
        process timeouts. Supports both containerized and local execution.

        Args:
            job_dir: Root directory for the rendering job.
            code_file: Python file containing the Scene definitions.
            scene_name: The specific Scene class to render.
            host_job_dir: Legacy parameter for host-relative pathing (unused).
            quality_flag: Manim quality flag (e.g., -ql, -qm, -qh).
            log_callback: Optional function to receive live log lines for progress tracking.
            timeout: Maximum allowed rendering duration in seconds.

        Returns:
            SandboxResult | None: The execution results, or None if the tool is unavailable.
        """
        cidfile = self._new_cidfile(job_dir)
        try:
            base_cmd = self._get_base_cmd(job_dir, cidfile)
            if base_cmd:
                cmd = base_cmd + [
                    "manim",
                    quality_flag,
                    "--media_dir",
                    ".",
                    code_file,
                    scene_name,
                ]
            else:
                manim_bin = shutil.which("manim")
                if not manim_bin:
                    venv_manim = (
                        Path(__file__).resolve().parents[3] / ".venv" / "bin" / "manim"
                    )
                    manim_bin = str(venv_manim) if venv_manim.exists() else "manim"
                cmd = [
                    manim_bin,
                    quality_flag,
                    "--media_dir",
                    ".",
                    code_file,
                    scene_name,
                ]

            logger.info(
                "sandbox_render_execution_started",
                command=" ".join(cmd),
                tool=self.container_tool or "local",
            )
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=job_dir if not base_cmd else None,
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
                await self._terminate(process, cidfile)
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
        finally:
            # Idempotent: a no-op when --rm already cleaned up the container.
            await asyncio.to_thread(self._reap_container, cidfile)


# Global singleton for sandbox execution
local_sandbox = LocalSandbox()
