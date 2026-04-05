# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Habilis (internally "Psilodigital Worker Stack") is a Docker Compose-based infrastructure stack that wires together:

- **Paperclip** — control plane for agent orchestration (Node.js, port 3100)
- **LiteLLM** — unified model gateway proxying OpenAI, Anthropic, Google, Groq (port 4000)
- **Agent Zero** — separate worker runtime/UI (port 50080)
- **worker-gateway** — Python/FastAPI webhook bridge between Paperclip and Agent Zero (port 8080)
- **Postgres 17** + **Redis 7** — shared infrastructure

The worker-gateway bridges Paperclip HTTP adapter wake events (`POST /paperclip/wake`) to Agent Zero via its External API (`POST /api_message`), with async processing and Paperclip callbacks.

## Commands

```sh
# Generate .env with random secrets
make setup

# Build and start the full stack
make build

# Run smoke tests
make test

# View all make targets
make help

# Rebuild a single service
docker compose up --build worker-gateway

# View logs for a specific service
make logs-worker-gateway

# Shell into a running container
make shell-paperclip
make shell-worker-gateway
```

## Architecture

```
                    ┌──────────────┐
                    │   Paperclip  │ :3100
                    │ (control     │
                    │  plane)      │
                    └──────┬───────┘
                           │ HTTP adapter POST
                           ▼
                    ┌──────────────┐
                    │   worker-    │ :8080
                    │   gateway    │
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │ POST /api_message (X-API-KEY)
                           ▼
                    ┌──────────────┐
                    │  Agent Zero  │ :50080
                    │ (worker      │
                    │  runtime)    │
                    └──────────────┘

    ┌──────────┐                    ┌──────────┐
    │ Postgres │ :5432              │  Redis   │ :6379
    │ (17-alp) │                    │ (7-alp)  │
    └──────────┘                    └──────────┘
            ▲                              ▲
    used by: paperclip, litellm    used by: (future dashboard)

    ┌──────────┐
    │ LiteLLM  │ :4000
    │ (model   │
    │  proxy)  │
    └──────────┘
```

All services communicate over the `workerstack` Docker bridge network. Container names follow the `psilo-*` convention.

## Key Files

- `docker-compose.yml` — full stack definition; all services, volumes, healthchecks
- `.env.example` — all required environment variables with defaults
- `Makefile` — dev workflow shortcuts (`make setup`, `make build`, `make test`, etc.)
- `worker-gateway/app.py` — bridge service (FastAPI, Agent Zero integration, Paperclip callbacks)
- `litellm/config.yaml` — model routing config (which providers/models are available)
- `paperclip/Dockerfile` — installs `paperclipai` CLI globally via npm
- `infra/postgres/init/01-create-dbs.sql` — creates `paperclip` and `litellm` databases on first boot
- `scripts/setup.sh` — generates `.env` with random secrets
- `scripts/smoke-test.sh` — post-boot validation (13 checks)

## Environment Variables

`LITELLM_MASTER_KEY` must start with `sk-`. `PAPERCLIP_AGENT_JWT_SECRET` and `AGENTZERO_AUTH_PASSWORD` are required with no defaults. Provider API keys (OpenAI, Anthropic, Google, Groq, OpenRouter) are optional — fill only the ones in use.

## Worker Gateway Details

- Python 3.12, FastAPI + Uvicorn + httpx + pydantic-settings
- `POST /paperclip/wake` — accepts Paperclip wake payload, returns 202, dispatches background task that calls Agent Zero `POST /api_message` and calls back to Paperclip with results
- `GET /healthz` — health check with downstream connectivity status (Agent Zero + LiteLLM)
- Configuration via environment variables (see `Settings` class in `app.py`)
- Structured JSON logging
- Remaining TODOs: Paperclip auth header validation, Paperclip callback endpoint confirmation

## Deployment

Target platform is Hetzner via Coolify using the Docker Compose build pack. Public-facing services: Paperclip, LiteLLM, and a future dashboard. Postgres, Redis, and Agent Zero should remain internal-only.
