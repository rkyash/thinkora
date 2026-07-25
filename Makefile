.PHONY: up down infra-up infra-down infra-status infra-logs

# ─── Full Stack ──────────────────────────────────────────────
up:
	./start.sh

down:
	docker compose -f docker-compose.dev.yml down
	@echo "Infrastructure stopped."

# ─── Infrastructure ───────────────────────────────────────────
infra-up:
	docker compose -f docker-compose.dev.yml up -d

infra-down:
	docker compose -f docker-compose.dev.yml down

infra-status:
	docker compose -f docker-compose.dev.yml ps

infra-logs:
	docker compose -f docker-compose.dev.yml logs -f
