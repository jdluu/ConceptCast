import os
from dataclasses import dataclass
from pathlib import Path

import docker
from loguru import logger


@dataclass
class SandboxResult:
    """Output from a Docker sandbox execution."""

    stdout: str
    stderr: str


class DockerSandbox:
    """Isolated execution environment for Manim using Docker.

    Provides a secure way to run AI-generated Python code by encapsulating
    it in a container with restricted resources and no network access.
    """

    def __init__(self, image: str = "manimcommunity/manim:latest") -> None:
        try:
            self.client = docker.from_env()
            self.image = image
            # Ensure image is available
            # self.client.images.pull(self.image) 
            # Pulling can be slow, assume pre-installed or pulled on first run
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def run_rendering(
        self,
        job_dir: Path,
        code_file: str,
        scene_name: str = "SceneGen",
        host_job_dir: Path | None = None,
        quality_flag: str = "-ql",
    ) -> SandboxResult | None:
        """Executes Manim rendering inside a Docker container.

        Args:
            job_dir: Directory containing the Manim code 
            (container path when backend runs in Docker).
            code_file: Name of the Python file (relative to job_dir).
            scene_name: Name of the Scene class to render.
            host_job_dir: When backend runs in Docker, pass the host path for this job 
                so the daemon can mount it. If set, used as the volume source 
                instead of job_dir.

        Returns:
            Optional[SandboxResult]: Captured output from the container, 
            or None if Docker is unavailable.

        Raises:
            RuntimeError: If rendering fails inside the container.
        """
        if not self.client:
            logger.warning(
                "Docker client not available. Falling back to local execution."
            )
            # Local fallback using subprocess
            import subprocess

            try:
                # Construct command for local execution
                # We need to run manim in the job_dir
                cmd = ["manim", quality_flag, "--media_dir", ".", code_file, scene_name]

                logger.info(f"Starting local execution: {' '.join(cmd)} in {job_dir}")

                result = subprocess.run(
                    cmd,
                    cwd=job_dir,
                    capture_output=True,
                    text=True,
                    check=False,  # We handle return code manually
                )

                if result.returncode != 0:
                    # Check for Manim errors in stderr/stdout
                    err_msg = result.stderr or result.stdout
                    logger.error(f"Local rendering failed: {err_msg}")
                    if "TypeError:" in err_msg or "AttributeError:" in err_msg:
                        raise RuntimeError(f"Manim API error: {err_msg}")
                    raise RuntimeError(f"Local rendering failed: {err_msg}")

                return SandboxResult(stdout=result.stdout, stderr=result.stderr)

            except Exception as e:
                logger.error(f"Local execution failed: {e}")
                raise RuntimeError(f"Local execution failed: {str(e)}") from e

        mount_src = str((host_job_dir or job_dir).absolute())
        volumes = {mount_src: {"bind": "/manim", "mode": "rw"}}

        try:
            logger.info(f"Starting Docker sandbox for {code_file} in {job_dir}")

            # Use project-relative output paths inside the container
            # The container user is usually 'manim' (UID 1000)
            # We might need to handle permissions if the host user isn't 1000
            user = f"{os.getuid()}:{os.getgid()}" if hasattr(os, "getuid") else None

            logs = self.client.containers.run(
                image=self.image,
                command=f"manim {quality_flag} --media_dir . {code_file} {scene_name}",
                volumes=volumes,
                working_dir="/manim",
                user=user,
                mem_limit="1g",
                nano_cpus=1000000000,  # 1.0 CPU
                network_disabled=True,
                remove=True,
                stdout=True,
                stderr=True,
            )

            # Docker returns bytes, we need to split stdout/stderr if possible.
            # However, .run(stdout=True, stderr=True) returns a single 
            # byte stream combined if detach=False. To get separate streams, 
            # we utilize the logs() method usually, but run() is blocking.
            # workaround: The simplified run() mixes them.
            # For iteration 1, we will treat the full output as both 
            # stdout/stderr mixture unless we switch to low-level API.
            # unless we switch to low-level API.
            # A simple improvement: use the returned bytes effectively.

            output = logs.decode("utf-8", errors="replace")
            logger.debug(f"Sandbox output: {output[:200]}...")

            # Since run() combines them, we put the full log in both for now
            # or try to parse. Manim usually writes render progress to stdout
            # and errors to stderr. Without extensive change, we pass full log.
            return SandboxResult(stdout=output, stderr=output)

        except docker.errors.ContainerError as e:
            # Container finished with non-zero exit code
            # e.stderr is available here specifically
            stderr_out = e.stderr.decode("utf-8") if e.stderr else str(e)
            logger.error(f"Sandbox rendering failed: {stderr_out}")

            # Preserve error type info for retry logic
            if "TypeError:" in stderr_out or "AttributeError:" in stderr_out:
                raise RuntimeError(f"Manim API error: {stderr_out}") from e
            raise RuntimeError(f"Sandbox rendering failed: {stderr_out}") from e
        except Exception as e:
            logger.error(f"Unexpected error in Docker sandbox: {e}")
            raise RuntimeError(f"Sandbox execution failed: {str(e)}") from e


# Global singleton for sandbox execution
docker_sandbox = DockerSandbox()
