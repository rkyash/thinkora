.PHONY: dev worker test lint format migrate migration

dev:
	uvicorn app.main:app --reload --port 8000

build:
	docker build -t thinkora-backend:latest .

worker:
	celery -A app.workers.celery_app worker --loglevel=info

test:
	pytest tests/ -v --asyncio-mode=auto

lint:
	ruff check . && mypy app/

format:
	ruff format .

migrate:
	alembic upgrade head

migration:
	alembic revision --autogenerate -m "$(msg)"

celery:
	.venv/bin/celery -A app.workers.celery_app worker --loglevel=info

#pytest tests/test_notification.py -v --tb=short 2>&1 | head -80