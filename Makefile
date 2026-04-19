.PHONY: help setup validate up build down clean logs status restart test test-gateway test-types

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Generate .env from .env.example with random secrets
	@bash infra/scripts/setup.sh

validate: ## Validate docker-compose.yml
	docker compose config --quiet && echo "docker-compose.yml is valid"

up: ## Start the stack (detached)
	docker compose up -d

build: ## Build and start the stack (detached)
	docker compose up --build -d

down: ## Stop the stack
	docker compose down

clean: ## Stop the stack and remove volumes
	docker compose down -v

logs: ## Tail logs for all services
	docker compose logs -f

status: ## Show service status
	docker compose ps

restart: ## Restart all services
	docker compose restart

test: ## Run smoke tests against running stack
	@bash infra/scripts/smoke-test.sh

test-gateway: ## Run worker-gateway unit tests
	cd apps/worker-gateway && python -m pytest tests/ -v --tb=short

test-types: ## Typecheck all TS packages
	pnpm turbo run typecheck

# --- v1 thin-slice shortcuts ---

gateway-dev: ## Run worker-gateway locally (port 8090, stub adapter)
	cd apps/worker-gateway && uvicorn app:app --host 127.0.0.1 --port 8090 --reload

gateway-smoke: ## Run v1 smoke tests against local gateway (port 8090)
	@bash infra/scripts/smoke-v1.sh localhost:8090

# --- Per-service shortcuts ---

logs-%: ## Tail logs for a specific service (e.g. make logs-worker-gateway)
	docker compose logs -f $*

restart-%: ## Restart a specific service (e.g. make restart-worker-gateway)
	docker compose restart $*

shell-postgres: ## Shell into postgres container
	docker exec -it psilo-postgres sh

shell-paperclip: ## Shell into paperclip container
	docker exec -it psilo-paperclip sh

shell-worker-gateway: ## Shell into worker-gateway container
	docker exec -it psilo-worker-gateway bash

shell-agentzero: ## Shell into agentzero container
	docker exec -it psilo-agentzero bash

shell-gmail-mcp: ## Shell into gmail-mcp container
	docker exec -it psilo-gmail-mcp bash
