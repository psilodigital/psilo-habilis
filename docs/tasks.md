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

---

## In Progress

_Nothing currently in progress._

---

## Next Up — Priority Order

### 1. Real Agent Zero Integration
- [ ] Confirm A0 `/api_message` supports project scoping
- [ ] Implement persona/playbook prompt assembly in A0 adapter
- [ ] Parse A0 free-text response into structured Classification + Artifacts
- [ ] Add A0 context cleanup after each run
- [ ] Switch default adapter from `stub` to `agentzero` via env var
- [ ] Test full flow: gateway → A0 → LiteLLM → structured response

### 2. Real Model Path
- [ ] Add one provider API key
- [ ] Verify LiteLLM can make real model calls
- [ ] Verify worker-gateway → Agent Zero → LiteLLM flow

### 3. Paperclip Integration
- [ ] Confirm Paperclip wake/callback contract
- [ ] Configure HTTP adapter to gateway
- [ ] Test Paperclip-originated wake → gateway → runtime → callback

### 4. Multi-Tenancy Foundation (Config-First)
- [ ] One Agent Zero project per company
- [ ] Per-client overrides and limits
- [ ] Defer DB-backed tenant model until after thin slice works

### 5. Dashboard App (Next.js)
- [ ] Scaffold dashboard
- [ ] Workspace overview
- [ ] Worker status view
- [ ] Thin-slice run/test UI

### 6. Connector Layer
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
| Runtime adapter | Stub adapter returns deterministic results, no real AI | Expected for v1; switch to A0 adapter next |
| A0 structured output | A0 returns free text, not structured JSON | Need parsing layer in A0 adapter |
| A0 project scoping | Not confirmed if A0 supports per-client projects | Required for multi-tenancy |
| Paperclip callback | URL `/api/runs/{runId}/complete` is a guess | Callback may fail in real integration |
| Paperclip auth | No auth header validation on wake endpoint | Any caller can trigger wakes |
| Agent Zero token | Must be manually copied from UI after first boot | Cannot fully automate setup |
| Provider keys | None set — model calls will fail | Expected for now; add before testing |
| Dashboard | Empty placeholder only | No product surface yet |
| Config source | YAML files on disk, not DB | Fine for v1; migrate later |
| HTTPS | Not in local dev | Coolify/Caddy handles in production |
