# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Habilis (internally "Psilodigital Worker Stack") is a Docker Compose-based infrastructure stack that wires together:

- **Paperclip** — control plane for agent orchestration (Node.js, port 3100)
- **LiteLLM** — unified model gateway proxying OpenAI, Anthropic, Google, Groq (port 4000)
- **Agent Zero** — separate worker runtime/UI (port 50080)
- **worker-gateway** — Python/FastAPI webhook bridge between Paperclip and Agent Zero (port 8080)
- **Postgres 17** + **Redis 7** — shared infrastructure

The worker-gateway is intentionally a thin stub. Its purpose is to receive Paperclip HTTP adapter wake events (`POST /paperclip/wake`) and bridge them to Agent Zero or custom orchestration logic.

## Commands

```sh
# Copy env and fill secrets
cp .env.example .env

# Build and run the full stack
docker compose up --build

# Rebuild a single service
docker compose up --build worker-gateway

# View logs for a specific service
docker compose logs -f worker-gateway

# Shell into a running container
docker exec -it psilo-paperclip sh
docker exec -it psilo-worker-gateway bash

# Paperclip first-time bootstrap (runs automatically, but can be manual)
paperclipai onboard --yes

# Paperclip server configuration
paperclipai configure --section server
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
                    │ (FastAPI     │
                    │  stub)       │
                    └──────┬───────┘
                           │ (bridge logic — TODO)
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
- `worker-gateway/app.py` — the entire gateway service (single file, FastAPI)
- `litellm/config.yaml` — model routing config (which providers/models are available)
- `paperclip/Dockerfile` — installs `paperclipai` CLI globally via npm
- `infra/postgres/init/01-create-dbs.sql` — creates `paperclip` and `litellm` databases on first boot

## Environment Variables

`LITELLM_MASTER_KEY` must start with `sk-`. `PAPERCLIP_AGENT_JWT_SECRET` and `AGENTZERO_AUTH_PASSWORD` are required with no defaults. Provider API keys (OpenAI, Anthropic, Google, Groq, OpenRouter) are optional — fill only the ones in use.

## Worker Gateway Details

- Python 3.12, FastAPI + Uvicorn
- Single endpoint: `POST /paperclip/wake` receives `{runId, agentId, companyId, ...}` from Paperclip
- Health check: `GET /healthz`
- The bridge logic (validating Paperclip auth, routing to Agent Zero, calling back results) is marked as TODO — this is the primary area for custom development

## Deployment

Target platform is Hetzner via Coolify using the Docker Compose build pack. Public-facing services: Paperclip, LiteLLM, and a future dashboard. Postgres, Redis, and Agent Zero should remain internal-only.
