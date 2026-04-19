# External Integrations

**Analysis Date:** 2026-04-19

## APIs & External Services

**LLM Providers:**
- OpenAI - GPT models (gpt-4.1, gpt-4.1-mini)
  - SDK/Client: LiteLLM proxy layer
  - Auth: `OPENAI_API_KEY` (optional)
  - Configured in: `services/litellm/config.yaml`

- Anthropic - Claude models (claude-sonnet-4-5)
  - SDK/Client: LiteLLM proxy layer
  - Auth: `ANTHROPIC_API_KEY` (optional)
  - Configured in: `services/litellm/config.yaml`

- Google - Gemini models (gemini-2.5-flash)
  - SDK/Client: LiteLLM proxy layer
  - Auth: `GOOGLE_API_KEY` (optional)
  - Configured in: `services/litellm/config.yaml`

- Groq - Fast inference (llama-3.3-70b-versatile)
  - SDK/Client: LiteLLM proxy layer
  - Auth: `GROQ_API_KEY` (optional)
  - Configured in: `services/litellm/config.yaml`

- OpenRouter - Multi-provider fallback
  - SDK/Client: LiteLLM proxy layer
  - Auth: `OPENROUTER_API_KEY` (optional)
  - Configured in: `services/litellm/config.yaml`

**Gmail API:**
- Google Gmail - Email reading via MCP connector
  - SDK/Client: google-api-python-client 2.160+
  - Auth: Google OAuth 2.0 (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`)
  - Implementation: `services/gmail-mcp/`
  - OAuth handler: `apps/worker-gateway/gateway/connectors/oauth_handler.py`

**Orchestration:**
- Paperclip - Control plane and HTTP adapter wake events
  - SDK/Client: paperclipai (npm global install)
  - Auth: `PAPERCLIP_AGENT_JWT_SECRET`
  - Endpoint: `POST /paperclip/wake` on worker-gateway (port 8080)
  - Public URL: `PAPERCLIP_PUBLIC_URL`

**Worker Runtime:**
- Agent Zero - Execution runtime with External API
  - SDK/Client: httpx (Python)
  - Auth: HTTP Basic Auth (`AGENTZERO_AUTH_LOGIN`, `AGENTZERO_AUTH_PASSWORD`) + optional API token (`AGENTZERO_API_TOKEN`)
  - Endpoint: `POST /api_message` on agentzero container (port 80)
  - Implementation: `apps/worker-gateway/gateway/adapters/agentzero.py`

**Monitoring:**
- Slack - Webhook notifications (optional)
  - Endpoint: `SLACK_WEBHOOK_URL` (LiteLLM errors)

## Data Storage

**Databases:**
- PostgreSQL 17-alpine
  - Connection: `postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/{db_name}`
  - Client: Drizzle ORM (TypeScript), SQLAlchemy (Python)
  - Databases: `paperclip`, `litellm`, `dashboard`, `gateway`
  - Init scripts: `infra/postgres/init/01-create-dbs.sql`

**File Storage:**
- Docker volumes only (no external file storage)
  - `paperclip_data:/paperclip` - Paperclip instance data
  - `agentzero_usr:/a0/usr` - Agent Zero user data
  - `postgres_data:/var/lib/postgresql/data` - Database persistence
  - `redis_data:/data` - Redis persistence

**Caching:**
- Redis 7-alpine
  - Connection: `redis:6379` (internal network)
  - Usage: Future dashboard caching (not yet implemented)
  - Client: Not configured yet

## Authentication & Identity

**Auth Provider:**
- better-auth 1.6.5 (Dashboard)
  - Implementation: Email/password authentication
  - Session: 7-day expiry
  - Storage: PostgreSQL via Drizzle adapter
  - Config: `apps/dashboard/src/lib/auth.ts`
  - Secret: `BETTER_AUTH_SECRET`

- Google OAuth (Connectors)
  - Implementation: OAuth 2.0 flow for Gmail connector
  - Credentials: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  - Handler: `apps/worker-gateway/gateway/connectors/oauth_handler.py`
  - Credential storage: Encrypted in PostgreSQL (Fernet encryption via `CONNECTOR_ENCRYPTION_KEY`)

- JWT (Service-to-service)
  - Paperclip agents: `PAPERCLIP_AGENT_JWT_SECRET`
  - Connector internal auth: `CONNECTOR_JWT_SECRET` (alias for encryption key)
  - Gateway internal: `GATEWAY_INTERNAL_SECRET` (service-to-service auth between gateway and MCP servers)

## Monitoring & Observability

**Error Tracking:**
- None (structured JSON logging only)

**Logs:**
- Structured JSON logging via Python `logging` module (worker-gateway, gmail-mcp)
- LiteLLM JSON logs (`json_logs: true` in `services/litellm/config.yaml`)
- Docker Compose stdout/stderr aggregation
- Log levels: `WORKER_GATEWAY_LOG_LEVEL`, `GMAIL_MCP_LOG_LEVEL`, `LITELLM_LOG`

## CI/CD & Deployment

**Hosting:**
- Hetzner via Coolify
  - Build pack: Docker Compose
  - Deployment config: `infra/coolify/` (planned)
  - Public services: Paperclip, LiteLLM, Dashboard
  - Internal services: Postgres, Redis, Agent Zero, worker-gateway, gmail-mcp

**CI Pipeline:**
- GitHub Actions (configuration in `.github/`)
  - Workflows: Not yet implemented

## Environment Configuration

**Required env vars:**
- `POSTGRES_PASSWORD` - Database authentication
- `LITELLM_MASTER_KEY` - Model gateway auth (must start with `sk-`)
- `PAPERCLIP_AGENT_JWT_SECRET` - Paperclip agent authentication
- `AGENTZERO_AUTH_PASSWORD` - Agent Zero UI/API password
- `BETTER_AUTH_SECRET` - Dashboard session signing (generate with `openssl rand -base64 32`)

**Secrets location:**
- `.env` file (local development, not committed)
- Coolify environment variables (production)
- Docker Compose environment variable injection

**Optional env vars:**
- Provider API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`
- OAuth credentials: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Connector encryption: `CONNECTOR_ENCRYPTION_KEY` (Fernet key for credential encryption)
- Internal auth: `GATEWAY_INTERNAL_SECRET`
- Monitoring: `SLACK_WEBHOOK_URL`

## Webhooks & Callbacks

**Incoming:**
- `POST /paperclip/wake` (worker-gateway:8080) - Paperclip HTTP adapter wake events
  - Payload: `PaperclipWakePayload` (defined in `apps/worker-gateway/gateway/models.py`)
  - Auth: JWT validation via `PAPERCLIP_AGENT_JWT_SECRET` (planned)
  - Handler: `apps/worker-gateway/app.py`

- `POST /v1/workers/run` (worker-gateway:8080) - Worker execution API
  - Payload: `WorkerRunRequest` (blueprint-driven)
  - Response: `WorkerRunResponse` with run metadata

- `POST /api_message` (agentzero:80) - Agent Zero external API
  - Used by: worker-gateway to wake Agent Zero
  - Auth: HTTP Basic Auth + optional API token

- `GET /mcp` (gmail-mcp:8090) - MCP server endpoint
  - Protocol: MCP over streamable HTTP
  - Consumer: Agent Zero (via `A0_SET_mcp_servers` environment variable)
  - Auth: Internal via `GATEWAY_INTERNAL_SECRET`

**Outgoing:**
- Paperclip callbacks - Worker-gateway calls back to Paperclip after Agent Zero completes
  - Client: `apps/worker-gateway/gateway/paperclip.py`
  - Endpoint: Paperclip base URL (`http://paperclip:3100`)
  - Status: TODO (endpoint confirmation needed)

- OAuth redirect endpoints - Google OAuth flow for Gmail connector
  - Handler: `apps/worker-gateway/gateway/connectors/oauth_handler.py`
  - Redirect URI: Configured in Google Cloud Console

## Network Architecture

**Docker Network:**
- `workerstack` bridge network - All services communicate via internal DNS
  - Service names resolve to container IPs (e.g., `postgres`, `litellm`, `paperclip`, `agentzero`)
  - Container naming: `psilo-*` convention

**Port Mappings:**
- Dashboard: 3000 (host) → 3000 (container)
- Paperclip: 3100 (host) → 3100 (container)
- LiteLLM: 4000 (host) → 4000 (container)
- Postgres: 5433 (host) → 5432 (container)
- Worker Gateway: 8080 (host) → 8080 (container)
- Agent Zero: 50080 (host) → 80 (container)
- Gmail MCP: Internal only (8090 in container)
- Redis: Internal only (6379 in container)

---

*Integration audit: 2026-04-19*
