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

### 1. Blueprint-Driven Worker Thin Slice
- [ ] Create worker blueprint schema (`pack.yaml`)
- [ ] Create client company schema (`company.yaml`)
- [ ] Create worker instance schema (`worker.instance.yaml`)
- [ ] Create `worker-packs/inbox-worker/`
- [ ] Create `clients/psilodigital/`
- [ ] Add shared orchestration contracts
- [ ] Add `POST /v1/workers/run` in worker-gateway
- [ ] Validate blueprint + client-instance resolution locally

### 2. Runtime Adapter Boundary
- [ ] Formalize runtime adapter interface
- [ ] Route worker-gateway through Agent Zero adapter or clear stub
- [ ] Document what is real vs stubbed
- [ ] Prepare project-aware Agent Zero execution model

### 3. Real Model Path
- [ ] Add one provider API key
- [ ] Verify LiteLLM can make real model calls
- [ ] Verify worker-gateway -> Agent Zero -> LiteLLM flow

### 4. Paperclip Integration
- [ ] Confirm Paperclip wake/callback contract
- [ ] Configure HTTP adapter to gateway
- [ ] Test Paperclip-originated wake -> gateway -> runtime -> callback

### 5. Multi-Tenancy Foundation (Config-First)
- [ ] Company/client scoping in gateway
- [ ] One client folder per company
- [ ] One Agent Zero project per company
- [ ] Per-client overrides and limits
- [ ] Defer DB-backed tenant model until after thin slice works

### 6. Dashboard App (Next.js)
- [ ] Scaffold dashboard
- [ ] Workspace overview
- [ ] Worker status view
- [ ] Thin-slice run/test UI

### 7. Connector Layer
- [ ] Connector SDK structure
- [ ] First connector strategy
- [ ] Workspace-scoped permissions
- [ ] MCP integration direction

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
