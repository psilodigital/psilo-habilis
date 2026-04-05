# Habilis — Task Tracker

> Living document. Update after every work session.
> Last updated: 2026-04-05

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

### Worker Gateway (v0.3.0)
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
- [x] Postgres init creates `paperclip`, `litellm`, `dashboard` databases
- [x] `.gitignore` covers Python, Node, Next.js, editor files

### Documentation
- [x] `docs/mission.md` — full mission, vision, architecture principles
- [x] `docs/local-dev.md` — setup, service map, post-boot config, troubleshooting
- [x] `docs/coolify.md` — deployment mapping, env vars, volumes, security
- [x] `README.md` — updated with monorepo structure
- [x] `CLAUDE.md` — updated with new paths and structure

### Verification
- [x] All 6 services boot and pass healthchecks
- [x] Service-to-service networking confirmed
- [x] 13/13 smoke tests passing
- [x] Wake endpoint accepts and processes requests
- [x] docker-compose config validates

---

## In Progress

_Nothing currently in progress._

---

## Next Up — Priority Order

### 1. Dashboard App (Next.js)
Scaffold the customer-facing product surface.
- [ ] Initialize Next.js app in `apps/dashboard/`
- [ ] Add Dockerfile for dashboard
- [ ] Uncomment and wire dashboard in docker-compose.yml
- [ ] Connect to Postgres (`dashboard` DB — already created)
- [ ] Connect to Redis
- [ ] Basic auth/session setup
- [ ] First screen: workspace overview

### 2. Add Real Provider API Key
- [ ] Add at least one provider key to `.env`
- [ ] Verify LiteLLM can make real model calls
- [ ] Test `worker-default` alias end-to-end

### 3. Agent Zero Token + Model Config
- [ ] Copy API token from Agent Zero UI → `.env`
- [ ] Configure Agent Zero to route through LiteLLM (`http://litellm:4000`)
- [ ] Verify worker-gateway → Agent Zero → LiteLLM flow works

### 4. Paperclip HTTP Adapter Config
- [ ] Verify Paperclip adapter callback contract (exact URL path)
- [ ] Configure HTTP adapter pointing to `http://worker-gateway:8080/paperclip/wake`
- [ ] Test Paperclip-originated wake → gateway → Agent Zero → callback
- [ ] Update `_callback_to_paperclip()` URL if needed

### 5. Worker Definitions
- [ ] Define first worker type schemas in `packages/worker-definitions/`
- [ ] Inbox Worker definition (capabilities, tools, limits)
- [ ] Content Worker definition
- [ ] Worker type routing in worker-gateway

### 6. Multi-Tenancy Foundation
- [ ] Workspace/company model in Postgres
- [ ] Tenant isolation in worker-gateway (companyId scoping)
- [ ] Per-workspace credentials storage
- [ ] Per-workspace budget tracking concept

### 7. Connector Layer
- [ ] Design connector interface in `packages/connector-sdk/`
- [ ] First connector: email/IMAP (for Inbox Worker)
- [ ] MCP integration strategy
- [ ] Workspace-scoped connector permissions

### 8. Dashboard Product Features
- [ ] Worker activation flow
- [ ] Task history view
- [ ] Approval gates for sensitive actions
- [ ] Usage/cost visibility
- [ ] Connector setup UI

---

## Backlog — Future

- [ ] Shared types package (`packages/shared-types/`)
- [ ] Shared UI component library (`packages/ui/`)
- [ ] Shared config package (`packages/config/`)
- [ ] Worker memory/context persistence
- [ ] Audit trail / activity log
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
| Paperclip callback | URL `/api/runs/{runId}/complete` is a guess | Callback may fail in real integration |
| Paperclip auth | No auth header validation on wake endpoint | Any caller can trigger wakes |
| Agent Zero token | Must be manually copied from UI after first boot | Cannot fully automate setup |
| Provider keys | None set — model calls will fail | Expected for now; add before testing |
| Dashboard | Empty placeholder only | No product surface yet |
| Multi-tenancy | Architectural concept only | No workspace isolation implemented |
| packages/ | All empty placeholders | No shared code yet |
| HTTPS | Not in local dev | Coolify/Caddy handles in production |
