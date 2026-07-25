"""
Celery worker management — start/stop worker as a background subprocess.
"""

import atexit
import os
import subprocess
import sys

from app.config import settings
from app.core.logging import logger

_worker_process: subprocess.Popen | None = None


def start_worker(concurrency: int = 2) -> bool:
    """Start Celery worker as a background subprocess (dev mode only)."""
    global _worker_process

    # If worker is managed externally (e.g., by start.sh), skip spawning
    if os.environ.get("THINKORA_WORKER_EXTERNAL", "").lower() in ("1", "true", "yes"):
        logger.info(
            "bootstrap_worker_external",
            msg="Worker managed externally by start.sh — skipping subprocess spawn",
        )
        return True

    if _worker_process is not None and _worker_process.poll() is None:
        logger.info("bootstrap_worker_already_running", pid=_worker_process.pid)
        return True

    if not settings.is_dev:
        logger.info("bootstrap_worker_skip_prod", msg="Worker not auto-started in production mode")
        return True

    backend_dir = _get_backend_dir()

    cmd = [
        sys.executable, "-m", "celery",
        "-A", "app.workers.celery_app",
        "worker",
        "--loglevel=info",
        f"--concurrency={concurrency}",
    ]

    logger.info("bootstrap_starting_worker", cmd=" ".join(cmd))

    try:
        _worker_process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Register cleanup
        atexit.register(stop_worker)

        logger.info("bootstrap_worker_started", pid=_worker_process.pid)
        return True
    except Exception as e:
        logger.error("bootstrap_worker_failed", error=str(e))
        return False


def stop_worker() -> None:
    """Stop the Celery worker subprocess."""
    global _worker_process

    if _worker_process is None:
        return

    if _worker_process.poll() is None:
        logger.info("bootstrap_stopping_worker", pid=_worker_process.pid)
        try:
            _worker_process.terminate()
            try:
                _worker_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                _worker_process.kill()
                _worker_process.wait(timeout=5)
            logger.info("bootstrap_worker_stopped")
        except Exception as e:
            logger.warning("bootstrap_worker_stop_error", error=str(e))

    _worker_process = None


def is_worker_running() -> bool:
    """Check if the managed worker subprocess is alive."""
    return _worker_process is not None and _worker_process.poll() is None


def _get_backend_dir() -> str:
    """Get the backend directory path."""
    cwd = os.getcwd()
    if os.path.basename(cwd) == "backend":
        return cwd
    backend = os.path.join(cwd, "backend")
    if os.path.isdir(backend):
        return backend
    return cwd
