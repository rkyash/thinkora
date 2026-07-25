"""
Docker Compose management — start, build, and manage infrastructure containers.
"""

import subprocess

from app.core.logging import logger
from app.bootstrap.detector import EnvironmentState


def ensure_infrastructure(
    state: EnvironmentState,
    compose_file: str,
    project_name: str,
    timeout: int = 120,
) -> bool:
    """
    Ensure all Docker infrastructure services are running.
    Returns True if successful, False otherwise.
    """
    if state.containers_running:
        logger.info("bootstrap_infra_already_running", msg="All containers already running")
        return True

    if not state.docker_installed:
        logger.error("bootstrap_docker_missing", msg=(
            "Docker is not installed. Please install Docker: https://docs.docker.com/get-docker/"
        ))
        return False

    if not state.docker_running:
        logger.error("bootstrap_docker_stopped", msg=(
            "Docker daemon is not running. Please start Docker Desktop or the Docker service."
        ))
        return False

    if state.compose_command is None:
        logger.error("bootstrap_compose_missing", msg=(
            "Docker Compose not found. Install it: https://docs.docker.com/compose/install/"
        ))
        return False

    compose_cmd = state.compose_command
    project_root = state.project_root

    # Determine if we need to build or just start
    if state.is_first_run or state.needs_build:
        logger.info("bootstrap_pulling_images", msg="Pulling/building Docker images...")
        _run_compose(compose_cmd, compose_file, project_name, project_root, ["pull"])

    # Start services
    logger.info("bootstrap_starting_infra", msg="Starting infrastructure services...")
    success = _run_compose(
        compose_cmd, compose_file, project_name, project_root,
        ["up", "-d", "--wait"],
        timeout=timeout,
    )

    if success:
        logger.info("bootstrap_infra_started", msg="Infrastructure services started successfully")
    else:
        logger.error("bootstrap_infra_failed", msg="Failed to start infrastructure services")

    return success


def _run_compose(
    compose_cmd: list[str],
    compose_file: str,
    project_name: str,
    project_root: str,
    args: list[str],
    timeout: int = 120,
) -> bool:
    """Run a docker compose command."""
    cmd = [*compose_cmd, "-f", compose_file, "-p", project_name, *args]
    logger.info("bootstrap_compose_cmd", cmd=" ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=project_root,
        )
        if result.returncode != 0:
            logger.error(
                "bootstrap_compose_error",
                stderr=result.stderr[:500] if result.stderr else "",
                cmd=" ".join(cmd),
            )
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("bootstrap_compose_timeout", timeout=timeout, cmd=" ".join(cmd))
        return False
    except FileNotFoundError:
        logger.error("bootstrap_compose_not_found", cmd=" ".join(cmd))
        return False
