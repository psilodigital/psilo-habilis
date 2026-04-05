.PHONY: help setup validate up build down clean logs status restart test

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Generate .env from .env.example with random secrets
	@bash scripts/setup.sh

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
	@bash scripts/smoke-test.sh

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
