"""
Automatic database migration — detects pending migrations and applies them.
"""

import os
import subprocess

from app.bootstrap.detector import _find_project_root
from app.core.logging import logger


def needs_migration() -> bool:
    """Check if there are pending Alembic migrations."""
    backend_dir = _get_backend_dir()
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "check"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=backend_dir,
        )
        # alembic check returns 0 if no new migrations needed,
        # non-zero if migrations are pending
        return result.returncode != 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # If we can't check, assume we need to migrate
        return True


def run_migrations(timeout: int = 60) -> bool:
    """Run 'alembic upgrade head' to apply pending migrations."""
    backend_dir = _get_backend_dir()
    logger.info("bootstrap_running_migrations", msg="Applying database migrations...")

    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=backend_dir,
        )
        if result.returncode == 0:
            logger.info("bootstrap_migrations_applied", msg="Migrations applied successfully")
            if result.stdout:
                # Log last few lines of migration output
                lines = result.stdout.strip().splitlines()
                for line in lines[-5:]:
                    logger.info("bootstrap_migration_output", line=line)
            return True
        else:
            logger.error(
                "bootstrap_migrations_failed",
                stderr=result.stderr[:500] if result.stderr else "",
                returncode=result.returncode,
            )
            return False
    except subprocess.TimeoutExpired:
        logger.error("bootstrap_migrations_timeout", timeout=timeout)
        return False


def _get_backend_dir() -> str:
    """Get the backend directory path."""
    cwd = os.getcwd()
    # If we're already in backend/
    if os.path.basename(cwd) == "backend" and os.path.exists("alembic.ini"):
        return cwd
    # Try backend/ subdirectory
    backend = os.path.join(cwd, "backend")
    if os.path.exists(os.path.join(backend, "alembic.ini")):
        return backend
    # Try from project root
    root = _find_project_root()
    backend = os.path.join(root, "backend")
    if os.path.exists(os.path.join(backend, "alembic.ini")):
        return backend
    return cwd
