# Coolify Deployment Guide

Target: Hetzner VPS via Coolify using the Docker Compose build pack.

## Service Exposure Map

| Service | Public Domain | Internal Only | Port |
|---|---|---|---|
| Dashboard | `app.yourdomain.com` | | 3000 |
| Paperclip | `paperclip.yourdomain.com` | | 3100 |
| LiteLLM | `llm.yourdomain.com` | | 4000 |
| Worker Gateway | | Yes | 8080 |
| Agent Zero | | Yes (debug only) | 80 |
| Postgres | | Yes | 5432 |
| Redis | | Yes | 6379 |

## Coolify Setup

1. Create a new service in Coolify
2. Select **Docker Compose** build pack
3. Point to this repository
4. Set all environment variables from `.env.example` in Coolify's env UI
5. Deploy

## Required Environment Variables

Set these in Coolify's environment variable UI (never commit secrets):

### Mandatory

| Variable | Notes |
|---|---|
| `POSTGRES_PASSWORD` | Strong random password |
| `LITELLM_MASTER_KEY` | Must start with `sk-` |
| `PAPERCLIP_AGENT_JWT_SECRET` | Long random hex string |
| `AGENTZERO_AUTH_PASSWORD` | Strong random password |

### At Least One Provider Key

| Variable | Provider |
|---|---|
| `OPENAI_API_KEY` | OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic |
| `GOOGLE_API_KEY` | Google AI |
| `GROQ_API_KEY` | Groq |
| `OPENROUTER_API_KEY` | OpenRouter |

### Optional

| Variable | Default | Purpose |
|---|---|---|
| `LITELLM_IMAGE_TAG` | `main-stable` | Pin to specific LiteLLM version |
| `PAPERCLIP_DEPLOYMENT_MODE` | `authenticated` | Use `authenticated` for production |
| `LITELLM_LOG` | `ERROR` | Log verbosity |

## Persistent Volumes

These named volumes must persist across deployments:

| Volume | Service | Contains |
|---|---|---|
| `postgres_data` | Postgres | All database data |
| `redis_data` | Redis | AOF persistence |
| `paperclip_data` | Paperclip | Instance config, state |
| `agentzero_usr` | Agent Zero | User data, memory, settings |

## Startup Order

Docker Compose `depends_on` with healthchecks handles ordering:

1. **postgres** + **redis** (no dependencies)
2. **litellm** + **paperclip** (depend on postgres healthy)
3. **agentzero** (no DB dependency)
4. **worker-gateway** (depends on litellm + paperclip + agentzero healthy)
5. **dashboard** (depends on postgres + redis healthy)

## Post-Deploy Steps

1. **Paperclip hardening**: Shell into the Paperclip container and run:
   ```sh
   paperclipai configure --section server
   ```

2. **Agent Zero token**: Log into Agent Zero UI, copy API token, set `AGENTZERO_API_TOKEN` in Coolify env, redeploy worker-gateway.

3. **Agent Zero model config**: In Agent Zero UI, set model provider to OpenAI Compatible with base URL `http://litellm:4000`.

4. **Paperclip adapter**: Configure HTTP adapter pointing to `http://worker-gateway:8080/paperclip/wake`.

## Security Considerations

- Postgres and Redis have no public port mappings — accessible only within the Docker network
- Agent Zero should remain internal unless explicitly needed for debugging
- Worker Gateway is internal — Paperclip reaches it over the Docker network
- LiteLLM requires `LITELLM_MASTER_KEY` for all API calls
- Paperclip uses JWT-based auth (`PAPERCLIP_AGENT_JWT_SECRET`)
- All inter-service communication happens over the `workerstack` bridge network

## Monitoring

Health check URLs accessible from within Coolify:

| Service | Health URL |
|---|---|
| Worker Gateway | `http://worker-gateway:8080/healthz` |
| LiteLLM | `http://litellm:4000/health/liveliness` |
| Paperclip | `http://paperclip:3100/api/health` |
| Postgres | `pg_isready` (Docker healthcheck) |
| Redis | `redis-cli ping` (Docker healthcheck) |
