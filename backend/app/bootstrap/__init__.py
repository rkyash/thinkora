"""
Thinkora Auto-Bootstrap — zero-config development environment setup.

This module is invoked during FastAPI lifespan startup. It automatically
detects, provisions, and validates all infrastructure dependencies.
"""

from app.bootstrap.orchestrator import run_bootstrap

__all__ = ["run_bootstrap"]
