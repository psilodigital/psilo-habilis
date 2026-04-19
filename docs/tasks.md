# Habilis — Task Tracker

> Living document. Update after every work session.
> Last updated: 2026-04-19

---

## Completed

### Infrastructure Foundation
- [x] Initial project structure (docker-compose, Makefile, scripts)
- [x] Postgres 17 + Redis 7 as internal services
- [x] LiteLLM as unified model gateway with config
- [x] Paperclip as separate control plane service
- [x] Agent Zero as separate worker runtime
- [x] Worker-gateway FastAPI bridge service
- [x] Docker networking (`workerstack` bridge)
- [x] Healthchecks on all services
- [x] `make setup` for secret generation
- [x] Smoke test script (13 checks, all passing)

### Monorepo Scaffold
- [x] Restructure to `apps/`, `packages/`, `services/`, `infra/` layout
- [x] Move worker-gateway → `apps/worker-gateway/`
- [x] Move paperclip → `services/paperclip/`
- [x] Move litellm → `services/litellm/`
- [x] Move scripts → `infra/scripts/`
- [x] Create placeholder dirs for dashboard, packages, agentzero
- [x] Update all path references (docker-compose, Makefile, CLAUDE.md, README)
- [x] Validate docker-compose config after restructure

### LiteLLM Config
- [x] Model routes: gpt-4.1-mini, gpt-4.1, claude-sonnet-4-5, gemini-2.5-flash, groq-llama-3.3-70b, openrouter-auto
- [x] Worker aliases: `worker-default` (gpt-4.1-mini), `worker-strong` (claude-sonnet-4-5)
- [x] `drop_params: true` for cross-provider compatibility
- [x] `allow_requests_on_db_unavailable: true` so LiteLLM boots without DB

### Worker Gateway (v0.3.0 → v1.0.0)
- [x] `POST /paperclip/wake` — accepts Paperclip wake events, processes async
- [x] `GET /healthz` — downstream checks (agentzero + litellm)
- [x] `GET /` — root status for load balancers
- [x] `GET /info` — service metadata and observability
- [x] Agent Zero integration via `POST /api_message`
- [x] Paperclip callback on completion
- [x] Structured JSON logging
- [x] Token resolution (explicit token or base64 fallback)

### Environment & Config
- [x] `.env.example` with all vars grouped by service
- [x] `make setup` generates random secrets
- [x] Postgres init creates `paperclip`, `litellm`, `dashboard`, `gateway` databases
- [x] `.gitignore` covers Python, Node, Next.js, editor files

### Documentation
- [x] `docs/mission.md` — full mission, vision, architecture principles
- [x] `docs/local-dev.md` — setup, service map, post-boot config, troubleshooting
- [x] `docs/coolify.md` — deployment mapping, env vars, volumes, security
- [x] `README.md` — updated with monorepo structure
- [x] `CLAUDE.md` — updated with new paths and structure
- [x] Open source community baseline — `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, `GOVERNANCE.md`
- [x] GitHub collaboration templates — issue forms, pull request template, `CODEOWNERS`, CI workflow, Dependabot
- [x] Sync high-level docs with live stack — dashboard included in architecture/service maps, Paperclip wake flow docs corrected
- [x] `THIRD_PARTY_NOTICES.md` — attribution for foundational upstream components and note on separate provider/API terms
- [x] Clarify Redis status in docs — provisioned in Compose, but not yet wired into the active runtime path

### Verification
- [x] All 6 services boot and pass healthchecks
- [x] Service-to-service networking confirmed
- [x] 13/13 smoke tests passing
- [x] Wake endpoint accepts and processes requests
- [x] docker-compose config validates

### v1 Blueprint-Driven Worker Thin Slice
- [x] Create worker blueprint schema (`pack.yaml`)
- [x] Create client company schema (`company.yaml`)
- [x] Create worker instance schema (`worker.instance.yaml`)
- [x] Create `worker-packs/inbox-worker/` with full blueprint
  - [x] pack.yaml, persona.md, playbook.md
  - [x] 3 agent configs (lead, classifier, reply-drafter)
  - [x] 4 policy files (approval, model, memory, tool)
  - [x] run-result.schema.json
- [x] Create `clients/psilodigital/` with full client config
  - [x] company.yaml
  - [x] workers/inbox-worker.instance.yaml
  - [x] context/company-profile.md, context/brand-voice.md
- [x] Add shared orchestration contracts (`packages/orchestration-contracts/`)
- [x] Add `POST /v1/workers/run` in worker-gateway
- [x] Blueprint + client + instance resolution from disk
- [x] Config merging: blueprint defaults → instance overrides → run overrides
- [x] Task kind validation against blueprint
- [x] Structured WorkerRunResponse contract
- [x] Validate all 8 test cases locally (3 happy path + 2 error + 3 info)

### v1 Runtime Adapter Boundary
- [x] Formalize `RuntimeAdapter` abstract interface
- [x] Implement `StubRuntimeAdapter` with deterministic simulation
- [x] Scaffold `AgentZeroAdapter` with clear TODOs
- [x] Document what is real vs stubbed
- [x] Gateway modularized into `gateway/` package (config, models, resolver, adapters)

### Monorepo Tooling (pnpm + Turborepo)
- [x] Root `package.json` with turbo scripts
- [x] `pnpm-workspace.yaml` workspace config
- [x] `turbo.json` build/typecheck/lint/test pipeline
- [x] `.npmrc` strict peer deps
- [x] All 4 TS packages build successfully

### TypeScript Package Scaffolding
- [x] `@habilis/shared-types` — Company, WorkerInstance, common enums
- [x] `@habilis/worker-definitions` — WorkerBlueprint, AgentDefinition, policies
- [x] `@habilis/config` — shared env schema (zod), constants
- [x] `@habilis/orchestration-contracts` — updated with build/tsconfig

### Worker Gateway: Prompt Assembly
- [x] `PromptAssembler` — assembles system + user prompts from persona, playbook, policies, context
- [x] `ResponseParser` — extracts JSON from A0 responses with code block / raw JSON / fallback strategies
- [x] Blueprint asset loaders in resolver (`load_persona`, `load_playbook`, `load_policies`, `load_output_schema`, `load_blueprint_assets`)
- [x] Agent Zero adapter updated to use PromptAssembler + ResponseParser

### Paperclip API Client
- [x] Typed `PaperclipClient` with health, companies, tasks, callbacks
- [x] Pydantic models for Paperclip entities and payloads
- [x] Auth helper — JWT header generation + wake auth validation
- [x] Wired into app lifecycle and wake endpoint
- [x] Config additions: `paperclip_jwt_secret`, `paperclip_validate_wake_auth`

### Hybrid Config Store
- [x] `ConfigStore` abstract base class
- [x] `FileConfigStore` — extracts existing disk-based logic
- [x] `DbConfigStore` — Postgres-backed via asyncpg
- [x] `resolver.resolve_all()` refactored to async, accepts ConfigStore
- [x] Config store selection via `CONFIG_STORE` env var (default: `file`)

### Database Schema
- [x] Alembic migration infrastructure
- [x] Migration 001: `companies`, `worker_instances`, `run_history` tables
- [x] Migration 002: seed psilodigital company + inbox-worker instance
- [x] `gateway` database added to Postgres init
- [x] `DATABASE_URL` + `CONFIG_STORE` added to docker-compose
- [x] `RunStore` for non-blocking audit trail

### Gateway Unit Tests
- [x] pytest infrastructure with pytest-asyncio, respx
- [x] 50 tests across 6 test files — all passing
- [x] `make test-gateway` and `make test-types` targets

### Real Agent Zero Integration (Task 1)
- [x] Reverse-engineered A0 API token: `sha256(runtime_id:login:password)[:16]` (base64url)
- [x] Confirmed `/api_message` contract: `{message, context_id?, lifetime_hours}` → `{response, context_id}`
- [x] Do NOT send `context_id` on first message (A0 creates new context, returns its ID)
- [x] Added `_terminate_context()` — cleanup via `/api_terminate_chat` after each run
- [x] Switched Docker default adapter to `agentzero` via `RUNTIME_ADAPTER` env var
- [x] Integration tests (`test_agentzero_integration.py`) with `@pytest.mark.integration`
- [x] Full flow verified: gateway → A0 → LiteLLM → OpenAI → structured response (10s)

### Real Model Path (Task 2)
- [x] OpenAI API key added to `.env`
- [x] A0 configured to use LiteLLM via `A0_SET_*` env vars (chat, util, browser models)
- [x] A0 `OPENAI_API_KEY` set to `LITELLM_MASTER_KEY` for LiteLLM auth
- [x] LiteLLM proxies `worker-default` → `openai/gpt-4o-mini` — confirmed working
- [x] Full pipeline: `/v1/workers/run` returns real AI-generated classification + draft

### Paperclip Integration (Task 3)
- [x] Explored Paperclip API: Better Auth (cookie), agent API keys (SHA256-hashed), HTTP adapter
- [x] Created company "Psilodigital" + agent "Inbox Worker" with HTTP adapter
- [x] Agent API key created and configured for gateway auth
- [x] HTTP adapter URL: `http://worker-gateway:8080/paperclip/wake`
- [x] Discovered Paperclip HTTP adapter is fire-and-forget (no callback needed)
- [x] Refactored `/paperclip/wake` from async background task to synchronous adapter pipeline
- [x] Made `companyId` optional in `PaperclipWakePayload` (Paperclip doesn't send it)
- [x] Cleaned up unused imports (`base64`, `BackgroundTasks`, `RunCallbackPayload`, `Artifact`)
- [x] Updated wake test to expect 200 (was 202)
- [x] Full E2E verified: Paperclip heartbeat → wake → A0 → LiteLLM → OpenAI → 200 OK

### Dashboard App — Thin Slice (Task 4)
- [x] Next.js 16.2 scaffold with App Router + Turbopack
- [x] pnpm workspace updated to include `apps/*`
- [x] shadcn/ui v4 (CLI v4, Base UI, Tailwind v4) with sidebar, card, table, badge, etc.
- [x] Drizzle ORM + Postgres — schema for Better Auth tables (user, session, account, verification)
- [x] Better Auth — email/password, Drizzle adapter, API route handler
- [x] `proxy.ts` auth gate — redirect to `/login` if no session cookie
- [x] Login + Register pages with shadcn Card + Input + Button
- [x] Dashboard layout with sidebar navigation (Workers, Run History) + user dropdown
- [x] Worker overview page — gateway status cards + configured worker cards
- [x] Run history page — table with status badges, duration, model, timestamps
- [x] Gateway `GET /v1/runs` endpoint — lists runs from `run_history` table
- [x] Gateway `RunStore` initialized in lifespan (auto-connect when `DATABASE_URL` set)
- [x] `next.config.ts` standalone output for Docker
- [x] Dockerfile (multi-stage: deps → build → runner) + docker-compose service
- [x] Fix dashboard Docker runner for Next 16 monorepo standalone output (`apps/dashboard/server.js`)
- [x] `.env` additions: `BETTER_AUTH_SECRET`, `DASHBOARD_PORT`
- [x] Postgres port exposed as `5433` for local dev (avoids conflict with local PG)
- [x] Build passes, dev server works, login page renders at `http://localhost:3000`

### Connector Layer (Task 5)
- [x] Evaluated A0 CLI connector (v1.9) — not applicable for service-to-service, HTTP API remains correct
- [x] Designed gateway-mediated MCP architecture (ADR-014)
- [x] `connector_credentials` table with Fernet encryption (migration 003)
- [x] `ConnectorStore` — encrypted credential CRUD via asyncpg
- [x] Session token service — short-lived JWTs for MCP tool auth
- [x] Gmail MCP server (`services/gmail-mcp/`) — Streamable HTTP transport
  - [x] `gmail_list_messages`, `gmail_get_message`, `gmail_search` tools
  - [x] Auth via session token → gateway internal API → decrypted OAuth credentials
  - [x] Dockerfile + docker-compose service (`psilo-gmail-mcp`)
- [x] Gateway internal credential lookup API (`GET /internal/connectors/.../credentials`)
- [x] Gateway connector CRUD endpoints (`POST/GET/DELETE /v1/connectors/...`)
- [x] Prompt assembly: connector auth token injection into system prompt
- [x] Agent Zero MCP config: Gmail connector wired via `A0_SET_mcp_servers`
- [x] `@habilis/connector-sdk` package — ConnectorDefinition, ConnectorRegistry types
- [x] Dashboard Gmail OAuth flow (`/api/connectors/gmail`)
- [x] Config additions: `CONNECTOR_ENCRYPTION_KEY`, `GATEWAY_INTERNAL_SECRET`, `GOOGLE_CLIENT_ID/SECRET`
- [x] `setup.sh` generates Fernet key + internal secret
- [x] 11 unit tests (session tokens, encryption, prompt injection) — all passing
- [x] 61/61 total gateway tests passing
- [x] ADR-014 (Gateway-Mediated MCP) + ADR-015 (Gmail Read-Only) documented

### Local Dev Reliability
- [x] Paperclip Docker bootstrap uses the supported `paperclipai onboard --yes --bind lan` flow
- [x] Removed ad-hoc Paperclip `config.json` mutation and switched to official `PAPERCLIP_PUBLIC_URL` wiring
- [x] Paperclip container healthcheck now uses `/` so authenticated mode does not flap on `/api/health`
- [x] Local and deployment docs now explain first-run Paperclip claim/bootstrap flow and when a full volume reset is required

---

## In Progress

_Nothing currently in progress._

---

## Next Up — Priority Order

---

## Backlog — Future

- [ ] Shared UI component library (`packages/ui/`)
- [ ] Connector SDK (`packages/connector-sdk/`)
- [ ] Worker memory/context persistence
- [ ] Rate limiting and budget enforcement
- [ ] Coolify deployment (first real deploy to Hetzner)
- [ ] Custom domain setup
- [ ] Monitoring and alerting
- [ ] CI/CD pipeline
- [ ] Worker performance metrics
- [ ] Business value reporting

---

## Known Gaps / Tech Debt

| Area | Gap | Impact |
|---|---|---|
| ~~Runtime adapter~~ | ~~Stub adapter returns deterministic results~~ | **Resolved** — A0 adapter is default in Docker |
| ~~A0 project scoping~~ | ~~Not confirmed if A0 supports per-client projects~~ | **Resolved** — A0 creates isolated contexts per run |
| ~~Paperclip callback~~ | ~~URL `/api/runs/{runId}/complete` is a guess~~ | **Resolved** — HTTP adapter is fire-and-forget, no callback |
| ~~Agent Zero token~~ | ~~Must be manually copied from UI~~ | **Resolved** — Token derived from `sha256(runtime_id:login:password)[:16]` |
| ~~Provider keys~~ | ~~None set — model calls will fail~~ | **Resolved** — OpenAI key configured, LiteLLM proxying |
| Blueprint assets for wake | `/paperclip/wake` uses agent ID as blueprint ID — no matching worker-pack | Create mapping from Paperclip agent → worker-pack blueprint |
| ~~Connector layer~~ | ~~No connector infrastructure~~ | **Resolved** — Gateway-mediated MCP with Gmail as first connector |
| Redis | Provisioned in Compose but not yet used by app code | Keep documented as reserved until queue/cache usage is implemented |
| Dashboard | Thin slice exists, but product workflows are still narrow | Expand beyond auth, worker overview, run history, and connector setup |
| DB config store | Implemented but untested with running Postgres | Test when stack is up |
| Run history | RunStore implemented but not wired into /v1/workers/run response path | Wire in when DB is confirmed |
| HTTPS | Not in local dev | Coolify/Caddy handles in production |
| Paperclip health check | Gateway reports Paperclip as "ok" even on 403 (auth required) | Needs API key for health endpoint |
