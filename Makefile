.PHONY: setup up-compose up-infra up-jobs up down-compose down-infra down-jobs down migrate status logs

COMPOSE_FILE := docker-compose.dev.yml

# ── Первичная установка ───────────────────────────────────────────────────────
setup: configure
	@echo "Installing HashiCorp binaries..."
	@./scripts/install_deps.sh

configure:
	@./scripts/configure.sh

# ── Docker Compose (stateful: Postgres, Redis, Kafka, OpenSearch, Nexus) ─────
up-compose:
	@echo "Starting stateful services..."
	docker compose -f $(COMPOSE_FILE) up -d
	@./scripts/wait_healthy.sh

down-compose:
	docker compose -f $(COMPOSE_FILE) down

logs:
	docker compose -f $(COMPOSE_FILE) logs -f $(svc)

# ── HashiCorp stack (Consul, Vault, Nomad) ────────────────────────────────────
up-infra:
	@echo "Starting Consul, Vault, Nomad..."
	@./infra/start_infra.sh

down-infra:
	@./infra/stop_infra.sh

# ── Nomad jobs (сервисы платформы) ───────────────────────────────────────────
up-jobs:
	@echo "Deploying services to Nomad..."
	@cd infra && ./start_jobs.sh

down-jobs:
	@cd infra && ./stop_jobs.sh

# ── Полный цикл ───────────────────────────────────────────────────────────────
up: up-compose up-infra up-jobs
	@echo ""
	@echo "Platform is ready."
	@echo "  Consul:  http://localhost:8500"
	@echo "  Vault:   http://localhost:8200"
	@echo "  Nomad:   http://localhost:4646"
	@echo "  Nexus:   http://localhost:8083"
	@echo "  Traefik: http://localhost:8090"

down: down-jobs down-infra down-compose
	@echo "Platform stopped."

# ── Migrations ────────────────────────────────────────────────────────────────
migrate:
	@cd infra && ./run_migrations.sh

# ── Статус ────────────────────────────────────────────────────────────────────
status:
	@echo "=== Docker Compose ==="
	@docker compose -f $(COMPOSE_FILE) ps
	@echo ""
	@echo "=== Nomad Jobs ==="
	@nomad status 2>/dev/null || echo "  Nomad not running"