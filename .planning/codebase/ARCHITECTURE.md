# Architecture

**Analysis Date:** 2026-04-19

## Pattern Overview

**Overall:** Multi-tenant microservices orchestration platform with configuration-driven worker execution

**Key Characteristics:**
- Docker Compose-based service orchestration with health-checked dependencies
- Configuration-as-code with YAML-driven blueprints and multi-tenant instance overrides
- Adapter pattern for pluggable runtime execution (stub, Agent Zero)
- Data-driven worker behavior via policy composition and prompt assembly
- Strong separation between control plane (Paperclip), orchestration (worker-gateway), and execution (Agent Zero)

## Layers

**Infrastructure Layer:**
- Purpose: Shared data and model services
- Location: `services/postgres`, `services/redis`, `services/litellm`
- Contains: PostgreSQL 17, Redis 7, LiteLLM proxy
- Depends on: Nothing (foundational services)
- Used by: All application services

**Control Plane:**
- Purpose: Agent lifecycle and scheduling (Paperclip)
- Location: `services/paperclip/`
- Contains: paperclipai CLI runtime, HTTP adapter wake endpoints
- Depends on: Postgres, LiteLLM
- Used by: Worker-gateway (receives wake events)

**Orchestration Layer:**
- Purpose: Worker execution gateway and configuration resolution
- Location: `apps/worker-gateway/`
- Contains: FastAPI service, runtime adapters, config stores, connector management
- Depends on: Postgres, Paperclip, LiteLLM, Agent Zero
- Used by: Dashboard, Paperclip (HTTP adapter), external callers

**Execution Layer:**
- Purpose: Actual AI worker runtime
- Location: External Agent Zero container (`services/agentzero/`)
- Contains: Agent Zero platform with MCP server integration
- Depends on: LiteLLM (for model access)
- Used by: Worker-gateway (via `/api_message` POST)

**Connector Layer:**
- Purpose: External service integrations (Gmail, etc.)
- Location: `services/gmail-mcp/`
- Contains: MCP-compatible HTTP servers with OAuth credential management
- Depends on: Worker-gateway (for credential lookup)
- Used by: Agent Zero (via MCP protocol)

**Configuration Layer:**
- Purpose: Multi-tenant worker definitions and client customizations
- Location: `worker-packs/`, `clients/`
- Contains: Blueprint YAMLs, policy files, persona/playbook markdown, client instances
- Depends on: Nothing (pure configuration)
- Used by: Worker-gateway resolver

**Presentation Layer:**
- Purpose: Customer-facing product interface
- Location: `apps/dashboard/` (Next.js 16)
- Contains: React app with Better Auth, Drizzle ORM, worker management UI
- Depends on: Postgres, worker-gateway
- Used by: End users

**Shared Libraries:**
- Purpose: Cross-service type contracts and utilities
- Location: `packages/`
- Contains: `orchestration-contracts`, `shared-types`, `worker-definitions`, `connector-sdk`, `config`
- Depends on: Nothing (pure types/utilities)
- Used by: Dashboard, worker-gateway (future)

## Data Flow

**Worker Execution Flow (Blueprint-Driven):**

1. Dashboard POSTs to worker-gateway `POST /v1/workers/run` with `{companyId, workerInstanceId, blueprintId, blueprintVersion, taskKind, input, runOverrides}`
2. Worker-gateway resolver loads:
   - Blueprint from `worker-packs/{id}/pack.yaml`
   - Company config from `clients/{companyId}/company.yaml`
   - Instance config from `clients/{companyId}/workers/{name}.instance.yaml`
   - Company context files from `clients/{companyId}/context/*.md`
   - Blueprint assets (persona.md, playbook.md, policies/*.yaml, agents/*.yaml)
3. Config merger combines (blueprint defaults → instance overrides → run overrides)
4. Connector resolver fetches encrypted credentials if needed, issues session tokens
5. Runtime adapter (Agent Zero) receives merged config + prompt assembly
6. Agent Zero executes via LiteLLM, optionally calling MCP servers (gmail-mcp)
7. Response parser extracts artifacts and classification from Agent Zero output
8. Worker-gateway returns structured response with metadata

**Paperclip Wake Flow:**

1. Paperclip HTTP adapter sends `POST /paperclip/wake` with `{agentId, runId, context}`
2. Worker-gateway validates authorization header (JWT from `PAPERCLIP_AGENT_JWT_SECRET`)
3. Executes via runtime adapter with hardcoded "inbound_email_triage" task
4. Returns synchronous response (no callback needed)

**Connector OAuth Flow:**

1. Dashboard initiates OAuth via Google provider
2. OAuth callback posts credentials to worker-gateway `POST /v1/connectors/credentials`
3. Worker-gateway encrypts and stores in connector_store (Postgres table `connector_credentials`)
4. MCP server (gmail-mcp) requests credentials via internal API `GET /internal/connectors/{companyId}/{connectorId}/credentials`
5. Worker-gateway validates `X-Internal-Secret` header, decrypts and returns credentials

**State Management:**
- Postgres schemas: `paperclip`, `litellm`, `dashboard`, `gateway` (separate databases)
- Redis: Planned for session/cache, not yet integrated
- File-based config: Worker packs and client configs (YAML on disk, mounted read-only in Docker)
- Ephemeral state: Agent Zero conversation memory in `/a0/usr` volume

## Key Abstractions

**RuntimeAdapter:**
- Purpose: Pluggable backend for worker task execution
- Examples: `apps/worker-gateway/gateway/adapters/stub.py`, `apps/worker-gateway/gateway/adapters/agentzero.py`
- Pattern: Abstract base class with `execute()` method returning `RuntimeResult`

**ConfigStore:**
- Purpose: Multi-tenant configuration persistence (file or DB)
- Examples: `apps/worker-gateway/gateway/store/file_store.py`, `apps/worker-gateway/gateway/store/db_store.py`
- Pattern: Abstract interface for company/instance CRUD

**Blueprint:**
- Purpose: Reusable worker definition (product SKU)
- Examples: `worker-packs/inbox-worker/pack.yaml`
- Pattern: YAML manifest with defaults, taskKinds, policies, persona/playbook assets

**Worker Instance:**
- Purpose: Company-specific customization of a blueprint
- Examples: `clients/psilodigital/workers/inbox-worker.instance.yaml`
- Pattern: YAML file with overrides for model, temperature, approval flags

**Connector:**
- Purpose: OAuth-secured external service integration
- Examples: Gmail MCP server (`services/gmail-mcp/`)
- Pattern: MCP-compatible HTTP server with credential encryption and session tokens

**Policy:**
- Purpose: Declarative constraints for worker behavior
- Examples: `worker-packs/inbox-worker/policies/tool-policy.yaml`, `approval-policy.yaml`
- Pattern: YAML files with allow/deny lists for tools, models, memory

## Entry Points

**Worker Gateway (FastAPI):**
- Location: `apps/worker-gateway/app.py`
- Triggers: HTTP POST from dashboard or Paperclip
- Responsibilities: Config resolution, adapter dispatch, response formatting

**Dashboard (Next.js):**
- Location: `apps/dashboard/src/app/` (App Router)
- Triggers: User browser requests
- Responsibilities: Authentication, UI rendering, worker-gateway API calls

**Paperclip (CLI Runtime):**
- Location: `services/paperclip/Dockerfile` (installs `paperclipai` globally)
- Triggers: Docker entrypoint command `paperclipai run --no-repair`
- Responsibilities: Agent scheduling, heartbeat wake events

**Agent Zero:**
- Location: External Docker image `agent0ai/agent-zero`
- Triggers: POST `/api_message` from worker-gateway
- Responsibilities: LLM execution, tool calling, MCP integration

**Gmail MCP:**
- Location: `services/gmail-mcp/server.py` (assumed)
- Triggers: Agent Zero MCP requests
- Responsibilities: Gmail API integration with OAuth credentials

## Error Handling

**Strategy:** Structured error responses with error codes and HTTP status propagation

**Patterns:**
- `ResolutionError` exceptions for config loading failures (BLUEPRINT_NOT_FOUND, COMPANY_NOT_FOUND, INSTANCE_DISABLED)
- `RuntimeResult.is_error` property for adapter execution failures
- HTTP 401/403 for auth failures (wake endpoint, internal connector API)
- HTTP 503 for missing dependencies (connector_store unavailable)
- Pydantic validation errors for malformed request bodies

## Cross-Cutting Concerns

**Logging:** Structured JSON logging via Python `logging` module (`gateway.logging.logger`)

**Validation:** Pydantic models for all API requests/responses (`gateway.models`)

**Authentication:**
- Paperclip wake: JWT validation via `PAPERCLIP_AGENT_JWT_SECRET`
- Internal APIs: Shared secret header (`X-Internal-Secret`)
- Dashboard: Better Auth with OAuth providers

---

*Architecture analysis: 2026-04-19*
