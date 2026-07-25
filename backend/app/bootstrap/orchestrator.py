"""
Bootstrap orchestrator — coordinates the full auto-bootstrap sequence.

Called from the FastAPI lifespan. Handles:
1. Environment detection
2. Docker infrastructure provisioning
3. Service health checks
4. Database migrations
5. Celery worker startup
6. Startup summary
"""

import os

from app.bootstrap.config import BOOTSTRAP_CONFIG
from app.bootstrap.detector import detect_environment
from app.bootstrap.docker_manager import ensure_infrastructure
from app.bootstrap.health import wait_for_all_services
from app.bootstrap.migrations import run_migrations
from app.bootstrap.summary import print_summary
from app.bootstrap.worker import start_worker
from app.core.logging import logger


async def run_bootstrap() -> None:
    """
    Execute the complete auto-bootstrap sequence.

    This function is idempotent — running it multiple times is safe.
    It detects what's already running and only performs necessary actions.
    """
    config = BOOTSTRAP_CONFIG

    # Check for skip flag
    if os.environ.get("THINKORA_SKIP_BOOTSTRAP", "").lower() in ("1", "true", "yes"):
        logger.info("bootstrap_skipped", msg="Bootstrap skipped via THINKORA_SKIP_BOOTSTRAP")
        return

    logger.info("bootstrap_starting", msg="Starting Thinkora auto-bootstrap...")

    # ─── Step 1: Detect environment ──────────────────────────
    state = detect_environment(config.compose_file, config.compose_project)

    logger.info(
        "bootstrap_environment",
        docker_installed=state.docker_installed,
        docker_running=state.docker_running,
        compose_available=state.compose_command is not None,
        containers_running=state.containers_running,
        is_first_run=state.is_first_run,
        services=state.services_status,
    )

    # ─── Step 2: Ensure Docker infrastructure ────────────────
    if not state.containers_running and state.docker_installed:
        infra_ok = ensure_infrastructure(
            state=state,
            compose_file=config.compose_file,
            project_name=config.compose_project,
            timeout=config.docker_compose_timeout,
        )
        if not infra_ok:
            logger.error(
                "bootstrap_infra_failed",
                msg=(
                    "Could not start infrastructure. Please start services manually:\n"
                    "  docker compose -f docker-compose.dev.yml up -d"
                ),
            )
            # Don't abort — let health checks determine the outcome
    elif not state.docker_installed:
        logger.warning(
            "bootstrap_no_docker_available",
            msg=(
                "Docker is not available. Infrastructure services must be running externally.\n"
                "Required: PostgreSQL, Redis, Qdrant"
            ),
        )

    # ─── Step 3: Wait for service health checks ──────────────
    health_results = await wait_for_all_services(
        timeout=config.service_health_timeout,
        interval=config.health_check_interval,
    )

    all_healthy = all(health_results.values())
    if not all_healthy:
        unhealthy = [k for k, v in health_results.items() if not v]
        logger.error(
            "bootstrap_unhealthy_services",
            services=unhealthy,
            msg="Some services failed health checks. The application may not work correctly.",
        )

    # ─── Step 4: Run database migrations ─────────────────────
    migration_ok = False
    if health_results.get("postgres", False) and config.auto_migrate:
        migration_ok = run_migrations(timeout=config.migration_timeout)
    elif not health_results.get("postgres", False):
        logger.warning(
            "bootstrap_skip_migrations", msg="Skipping migrations — database not available"
        )

    # ─── Step 5: Start Celery worker ─────────────────────────
    worker_ok = False
    if config.auto_start_worker:
        worker_ok = start_worker(concurrency=config.worker_concurrency)
    else:
        logger.info("bootstrap_worker_disabled", msg="Worker auto-start disabled")

    # ─── Step 6: Print startup summary ───────────────────────
    print_summary(health_results, migration_ok, worker_ok)

    if all_healthy and migration_ok:
        logger.info("bootstrap_complete", msg="Auto-bootstrap completed successfully")
    else:
        logger.warning("bootstrap_partial", msg="Auto-bootstrap completed with warnings")
