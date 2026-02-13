import os
from pathlib import Path
from typing import Optional

import docker
from loguru import logger


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
            # self.client.images.pull(self.image) # Pulling can be slow, assume pre-installed or pulled on first run
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def run_rendering(
        self, 
        job_dir: Path, 
        code_file: str, 
        scene_name: str = "SceneGen"
    ) -> Optional[str]:
        """Executes Manim rendering inside a Docker container.

        Args:
            job_dir: Host directory containing the Manim code and where output will be stored.
            code_file: Name of the Python file (relative to job_dir).
            scene_name: Name of the Scene class to render.

        Returns:
            Optional[str]: Captured output from the container, or None if Docker is unavailable.

        Raises:
            RuntimeError: If rendering fails inside the container.
        """
        if not self.client:
            logger.error("Docker client not available. Falling back to local execution unsafe!")
            return None

        # Manim Docker image uses /manim as the default workdir
        # We mount the job_dir to /manim
        volumes = {
            str(job_dir.absolute()): {"bind": "/manim", "mode": "rw"}
        }

        try:
            logger.info(f"Starting Docker sandbox for {code_file} in {job_dir}")
            
            # Use project-relative output paths inside the container
            # The container user is usually 'manim' (UID 1000)
            # We might need to handle permissions if the host user isn't 1000
            user = f"{os.getuid()}:{os.getgid()}" if hasattr(os, "getuid") else None

            logs = self.client.containers.run(
                image=self.image,
                command=f"manim -ql --media_dir . {code_file} {scene_name}",
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
            
            output = logs.decode("utf-8")
            logger.debug(f"Sandbox output: {output}")
            return output

        except docker.errors.ContainerError as e:
            error_msg = e.stderr.decode("utf-8") if e.stderr else str(e)
            logger.error(f"Sandbox rendering failed: {error_msg}")
            raise RuntimeError(f"Sandbox rendering failed: {error_msg}")
        except Exception as e:
            logger.error(f"Unexpected error in Docker sandbox: {e}")
            raise RuntimeError(f"Sandbox execution failed: {str(e)}")


# Global singleton for sandbox execution
docker_sandbox = DockerSandbox()
