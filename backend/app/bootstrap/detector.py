"""
Environment detection — checks Docker, Docker Compose, running containers,
and determines what actions are needed.
"""

import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field

from app.core.logging import logger


@dataclass
class EnvironmentState:
    """Snapshot of the current development environment."""
    docker_installed: bool = False
    docker_running: bool = False
    compose_command: list[str] | None = None  # ["docker", "compose"] or ["docker-compose"]
    containers_exist: bool = False
    containers_running: bool = False
    services_status: dict[str, str] | None = None  # service -> "running"|"exited"|"missing"
    is_first_run: bool = True
    needs_build: bool = False
    project_root: str = ""


def detect_environment(compose_file: str, project_name: str) -> EnvironmentState:
    """Detect the current state of the development environment."""
    state = EnvironmentState()
    state.project_root = _find_project_root()

    # 1. Docker binary
    state.docker_installed = shutil.which("docker") is not None
    if not state.docker_installed:
        logger.warning("bootstrap_no_docker", msg="Docker is not installed")
        return state

    # 2. Docker daemon running
    state.docker_running = _is_docker_running()
    if not state.docker_running:
        logger.warning("bootstrap_docker_not_running", msg="Docker daemon is not running")
        return state

    # 3. Docker Compose variant
    state.compose_command = _detect_compose_command()
    if state.compose_command is None:
        logger.warning("bootstrap_no_compose", msg="Docker Compose not found")
        return state

    # 4. Container status
    state.services_status = _get_services_status(
        state.compose_command, compose_file, project_name, state.project_root
    )
    if state.services_status:
        state.containers_exist = any(s != "missing" for s in state.services_status.values())
        state.containers_running = all(s == "running" for s in state.services_status.values())
        state.is_first_run = not state.containers_exist
    else:
        state.is_first_run = True

    return state


def _find_project_root() -> str:
    """Walk up from backend/ to find the project root (where docker-compose.dev.yml lives)."""
    # If we're running from backend/, go up one level
    cwd = os.getcwd()
    if os.path.basename(cwd) == "backend":
        return os.path.dirname(cwd)
    # If docker-compose.dev.yml exists in cwd, we're at root
    if os.path.exists(os.path.join(cwd, "docker-compose.dev.yml")):
        return cwd
    # Try parent
    parent = os.path.dirname(cwd)
    if os.path.exists(os.path.join(parent, "docker-compose.dev.yml")):
        return parent
    return cwd


def _is_docker_running() -> bool:
    """Check if Docker daemon is responsive."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True, timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _detect_compose_command() -> list[str] | None:
    """Detect whether 'docker compose' (v2) or 'docker-compose' (legacy) is available."""
    # Try v2 first
    try:
        result = subprocess.run(
            ["docker", "compose", "version"],
            capture_output=True, timeout=10,
        )
        if result.returncode == 0:
            return ["docker", "compose"]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Try legacy
    if shutil.which("docker-compose"):
        try:
            result = subprocess.run(
                ["docker-compose", "version"],
                capture_output=True, timeout=10,
            )
            if result.returncode == 0:
                return ["docker-compose"]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    return None


def _get_services_status(
    compose_cmd: list[str],
    compose_file: str,
    project_name: str,
    project_root: str,
) -> dict[str, str]:
    """Get status of each service defined in the compose file."""
    try:
        result = subprocess.run(
            [*compose_cmd, "-f", compose_file, "-p", project_name, "ps", "--format", "json"],
            capture_output=True, text=True, timeout=15,
            cwd=project_root,
        )
        if result.returncode != 0:
            return {}

        statuses: dict[str, str] = {}
        output = result.stdout.strip()
        if not output:
            return {}

        # docker compose ps --format json can return one JSON per line or a JSON array
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, list):
                    for item in obj:
                        name = item.get("Service", item.get("service", ""))
                        state = item.get("State", item.get("state", "unknown"))
                        if name:
                            statuses[name] = state
                else:
                    name = obj.get("Service", obj.get("service", ""))
                    state = obj.get("State", obj.get("state", "unknown"))
                    if name:
                        statuses[name] = state
            except json.JSONDecodeError:
                continue
        return statuses
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {}
