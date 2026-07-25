"""
Startup summary — displays a formatted report of all services and their health.
"""

from app.config import settings
from app.bootstrap.worker import is_worker_running


def print_summary(health_results: dict[str, bool], migration_ok: bool, worker_ok: bool) -> str:
    """Generate and print the startup summary. Returns the summary string."""

    # Parse DB host/port from DATABASE_URL
    db_url = settings.DATABASE_URL
    db_display = "localhost:5434"
    if "@" in db_url:
        host_part = db_url.split("@")[1].split("/")[0]
        db_display = host_part

    redis_display = settings.REDIS_URL.replace("redis://", "").split("/")[0]
    qdrant_display = f"{settings.QDRANT_HOST}:{settings.QDRANT_PORT}"

    def _status(ok: bool) -> str:
        return "✅" if ok else "❌"

    lines = [
        "",
        "=" * 56,
        "🚀 Thinkora Started Successfully",
        "=" * 56,
        "",
        f"  Backend API:        http://localhost:{settings.PORT}",
        f"  API Docs (Swagger): http://localhost:{settings.PORT}/docs",
        f"  ReDoc:              http://localhost:{settings.PORT}/redoc",
        f"  Frontend:           {settings.FRONTEND_URL}",
        "",
        f"  Database:           {db_display}",
        f"  Redis:              {redis_display}",
        f"  Qdrant:             {qdrant_display}",
        "",
        "  Health Status",
        "  " + "─" * 40,
        f"  Database         {_status(health_results.get('postgres', False))} {'Connected' if health_results.get('postgres') else 'Disconnected'}",
        f"  Redis            {_status(health_results.get('redis', False))} {'Connected' if health_results.get('redis') else 'Disconnected'}",
        f"  Qdrant           {_status(health_results.get('qdrant', False))} {'Connected' if health_results.get('qdrant') else 'Disconnected'}",
        f"  Migrations       {_status(migration_ok)} {'Applied' if migration_ok else 'Failed'}",
        f"  Celery Worker    {_status(worker_ok)} {'Running' if worker_ok else 'Not Running'}",
        "",
        "=" * 56,
        "  Ready for Development 🎉",
        "=" * 56,
        "",
    ]

    summary = "\n".join(lines)
    print(summary)
    return summary
