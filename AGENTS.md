# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Project Overview

Habilis (internally "Psilodigital Worker Platform") is a multi-tenant worker operating system for small and medium businesses, built as a Docker Compose-based modular stack:

- **Dashboard** — Next.js commercial product surface (planned, `apps/dashboard/`)
- **worker-gateway** — Python/FastAPI webhook bridge between Paperclip and Agent Zero (`apps/worker-gateway/`, port 8080)
- **Paperclip** — control plane for agent orchestration (`services/paperclip/`, Node.js, port 3100)
- **LiteLLM** — unified model gateway proxying OpenAI, Anthropic, Google, Groq (`services/litellm/`, port 4000)
- **Agent Zero** — separate worker runtime/UI (port 50080)
- **Postgres 17** + **Redis 7** — shared infrastructure

The worker-gateway bridges Paperclip HTTP adapter wake events (`POST /paperclip/wake`) to Agent Zero via its External API (`POST /api_message`), with async processing and Paperclip callbacks.

## Repository Structure

```
habilis/
├── apps/
│   ├── dashboard/            # Next.js — customer-facing product (planned)
│   └── worker-gateway/       # FastAPI — orchestration-to-execution bridge
├── packages/
│   ├── shared-types/         # Cross-service type definitions
│   ├── worker-definitions/   # Worker configs, schemas, capabilities
│   ├── connector-sdk/        # SDK for building connectors
│   ├── ui/                   # Shared UI components
│   └── config/               # Shared configuration
├── services/
│   ├── paperclip/            # Control plane (Dockerfile)
│   ├── litellm/              # Model gateway (config.yaml)
│   └── agentzero/            # Worker runtime (placeholder)
├── infra/
│   ├── postgres/init/        # DB init scripts
│   ├── docker/               # Additional Docker configs
│   ├── coolify/              # Deployment configs
│   ├── scripts/              # setup.sh, smoke-test.sh
│   └── env/                  # Environment templates
├── docs/                     # Mission, architecture, decisions
├── docker-compose.yml        # Full stack definition
├── Makefile                  # Dev workflow shortcuts
├── .env.example              # Environment variable template
└── AGENTS.md                 # This file
```

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
- `apps/worker-gateway/app.py` — bridge service (FastAPI, Agent Zero integration, Paperclip callbacks)
- `services/litellm/config.yaml` — model routing config (which providers/models are available)
- `services/paperclip/Dockerfile` — installs `paperclipai` CLI globally via npm
- `infra/postgres/init/01-create-dbs.sql` — creates `paperclip` and `litellm` databases on first boot
- `infra/scripts/setup.sh` — generates `.env` with random secrets
- `infra/scripts/smoke-test.sh` — post-boot validation (13 checks)
- `docs/mission.md` — full mission, vision, and architecture document

## Environment Variables

`LITELLM_MASTER_KEY` must start with `sk-`. `PAPERCLIP_AGENT_JWT_SECRET` and `AGENTZERO_AUTH_PASSWORD` are required with no defaults. Provider API keys (OpenAI, Anthropic, Google, Groq, OpenRouter) are optional — fill only the ones in use.

## Worker Gateway Details

- Python 3.12, FastAPI + Uvicorn + httpx + pydantic-settings
- `POST /paperclip/wake` — accepts Paperclip wake payload, returns 202, dispatches background task that calls Agent Zero `POST /api_message` and calls back to Paperclip with results
- `GET /healthz` — health check with downstream connectivity status (Agent Zero + LiteLLM)
- Configuration via environment variables (see `Settings` class in `app.py`)
- Structured JSON logging
- Remaining TODOs: Paperclip auth header validation, Paperclip callback endpoint confirmation

## Project Documentation

Read these docs at the start of every session to stay aligned:

- `docs/tasks.md` — **Living task tracker.** What is done, what is next, what is blocked. Update after every session.
- `docs/mission.md` — Mission, vision, product principles, architecture rules, decision framework.
- `docs/decisions.md` — Architecture Decision Records (ADRs). Append-only log of key choices and rationale.
- `docs/local-dev.md` — Local setup, service map, post-boot config, model aliases, troubleshooting.
- `docs/coolify.md` — Deployment mapping for Hetzner via Coolify.

**After every work session:** Update `docs/tasks.md` to reflect what was completed and what changed.

## Deployment

Target platform is Hetzner via Coolify using the Docker Compose build pack. Public-facing services: Paperclip, LiteLLM, and the dashboard. Postgres, Redis, and Agent Zero should remain internal-only.
