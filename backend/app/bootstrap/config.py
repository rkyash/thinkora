"""Bootstrap configuration — timeouts, retries, and service definitions."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BootstrapConfig:
    """Configuration for the auto-bootstrap system."""

    # ─── Timeouts ────────────────────────────────────────────
    docker_compose_timeout: int = 120       # Max seconds to wait for docker compose up
    service_health_timeout: int = 90        # Max seconds to wait for all services healthy
    single_service_timeout: int = 30        # Max seconds per individual service health check
    health_check_interval: float = 2.0      # Seconds between health check polls

    # ─── Docker ──────────────────────────────────────────────
    compose_file: str = "docker-compose.dev.yml"
    compose_project: str = "thinkora"
    required_services: list[str] = field(
        default_factory=lambda: ["postgres", "redis", "qdrant"]
    )

    # ─── Migrations ──────────────────────────────────────────
    auto_migrate: bool = True
    migration_timeout: int = 60

    # ─── Worker ──────────────────────────────────────────────
    auto_start_worker: bool = True
    worker_concurrency: int = 2

    # ─── Feature flags ───────────────────────────────────────
    skip_bootstrap: bool = False  # Set THINKORA_SKIP_BOOTSTRAP=true to disable


BOOTSTRAP_CONFIG = BootstrapConfig()
