# Codebase Concerns

**Analysis Date:** 2026-04-19

## Tech Debt

**Agent Zero Token Management:**
- Issue: Token generation logic duplicated between manual retrieval and programmatic generation (`sha256(runtime_id:login:password)[:16]`)
- Files: `apps/worker-gateway/gateway/adapters/agentzero.py`
- Impact: If token algorithm changes in A0, must update gateway code. Manual token retrieval still documented as fallback.
- Fix approach: Consolidate to single token derivation method, remove manual retrieval instructions once confirmed stable

**Stub Adapter Classification Logic:**
- Issue: Email classification uses basic keyword matching instead of proper NLP
- Files: `apps/worker-gateway/gateway/adapters/stub.py` (lines 56-127)
- Impact: Stub results don't represent real-world complexity. Tests may pass with stub but fail with real adapter.
- Fix approach: Mark as deprecated once Agent Zero adapter is default everywhere. Stub useful only for offline dev.

**Paperclip-to-Blueprint Mapping:**
- Issue: `/paperclip/wake` endpoint assumes agent ID equals blueprint ID, but no actual mapping exists
- Files: `apps/worker-gateway/app.py` (wake endpoint around line 400+), `docs/tasks.md` line 259
- Impact: Paperclip wake events cannot resolve to correct worker-pack blueprint without manual ID alignment
- Fix approach: Create `agent_id -> blueprint_id` mapping table or convention (e.g., `paperclip-agents/{id}.yaml`)

**Token Usage Tracking:**
- Issue: `tokens_used` always returns 0 from Agent Zero adapter
- Files: `apps/worker-gateway/gateway/adapters/agentzero.py` line 146
- Impact: No cost tracking or budget enforcement possible
- Fix approach: Parse token usage from A0 response if available, or calculate via LiteLLM proxy usage endpoint

**Database Store Untested in Production:**
- Issue: `DbConfigStore` implemented but only tested in unit tests, not with live Postgres
- Files: `apps/worker-gateway/gateway/store/db_store.py`, `docs/tasks.md` line 263
- Impact: Unknown if migrations work correctly, connection pooling sufficient, or queries performant
- Fix approach: Integration test with real Postgres, smoke test with `CONFIG_STORE=db`

**Redis Provisioned But Unused:**
- Issue: Redis container runs but no application code uses it yet
- Files: `docker-compose.yml` lines 23-36, `docs/tasks.md` line 261
- Impact: Wastes memory/storage. Unclear what it's reserved for.
- Fix approach: Document intended use (queue, cache, session store) or remove until needed

**Dashboard Product Scope Narrow:**
- Issue: Dashboard only covers auth, worker overview, run history, connector setup — not full product workflows
- Files: `apps/dashboard/src/`, `docs/tasks.md` line 262
- Impact: Not production-ready for actual customers
- Fix approach: Expand based on user workflows (approvals, notifications, worker config UI, billing)

## Known Bugs

**Paperclip Health Check False Positive:**
- Symptoms: Gateway reports Paperclip as "ok" even when returning 403 Forbidden (auth required)
- Files: `apps/worker-gateway/app.py` (healthz endpoint), `docs/tasks.md` line 266
- Trigger: Paperclip in `authenticated` mode, gateway health check calls `/` or `/api/health`
- Workaround: Check Paperclip logs manually. Health endpoint not critical for local dev.
- Fix: Use Paperclip API key in health check, or switch to unauthenticated endpoint

**Postgres Port Conflict:**
- Symptoms: Local dev fails if system Postgres runs on 5432
- Files: `docker-compose.yml` line 14, `.env.example`
- Trigger: Default `POSTGRES_PORT=5433` maps to 5433:5432, but if user changes to 5432:5432, conflict occurs
- Workaround: Use `POSTGRES_PORT=5433` (current default)
- Fix: Document port mapping clearly in setup docs

**Dashboard Standalone Output Path:**
- Symptoms: Docker runner couldn't find Next.js server after monorepo build
- Files: `apps/dashboard/Dockerfile`, fixed in task 176
- Trigger: Next 16 standalone output structure differs from Next 15
- Workaround: Already fixed — uses `apps/dashboard/server.js` correctly
- Note: Resolved, listed here for historical tracking

## Security Considerations

**Connector Encryption Key Storage:**
- Risk: `CONNECTOR_ENCRYPTION_KEY` stored in `.env`, no key rotation mechanism
- Files: `apps/worker-gateway/gateway/store/connector_store.py`, `.env.example` line 54
- Current mitigation: Fernet symmetric encryption at rest, gateway as single decryption point
- Recommendations: Add key rotation workflow, consider vault (HashiCorp Vault, AWS Secrets Manager) for production

**Gateway Internal Secret:**
- Risk: `GATEWAY_INTERNAL_SECRET` shared between gateway and MCP servers via plain env var
- Files: `services/gmail-mcp/server.py`, `.env.example` line 56
- Current mitigation: Services communicate over internal Docker network only
- Recommendations: Use mTLS or signed JWTs with asymmetric keys for internal service auth

**Session Token Lifespan:**
- Risk: 5-minute session tokens could be logged or leaked during A0 prompt context
- Files: `apps/worker-gateway/gateway/paperclip/auth.py` (JWT generation)
- Current mitigation: Short lifespan (5 min), scoped to single company/connector
- Recommendations: Add token revocation list if paranoid. Current risk is low.

**Agent Zero API Token in Logs:**
- Risk: If logs are verbose, A0 token may appear in request headers
- Files: `apps/worker-gateway/gateway/adapters/agentzero.py`
- Current mitigation: Log level is `info` by default, not `debug`
- Recommendations: Redact `X-API-KEY` header in structured logging

**No Rate Limiting:**
- Risk: `/v1/workers/run` and `/paperclip/wake` have no rate limits
- Files: `apps/worker-gateway/app.py`
- Current mitigation: None — relies on Paperclip throttling or external load balancer
- Recommendations: Add per-company rate limiting using Redis + slowapi or middleware

**OAuth Credentials in Database:**
- Risk: Gmail OAuth tokens stored encrypted, but DB dump exposes encryption key reference
- Files: `apps/worker-gateway/gateway/store/connector_store.py`
- Current mitigation: Fernet encryption, credentials table separate from other data
- Recommendations: Backup encryption keys separately from DB backups

## Performance Bottlenecks

**Synchronous Wake Endpoint:**
- Problem: `/paperclip/wake` now runs entire worker execution synchronously (was async background task)
- Files: `apps/worker-gateway/app.py` (wake endpoint), `docs/tasks.md` line 169
- Cause: Paperclip HTTP adapter expects synchronous 200 response, no callback mechanism
- Improvement path: If Paperclip adds callback support, revert to async background processing. Current approach works but blocks HTTP connection.

**Blueprint Asset Loading:**
- Problem: `load_blueprint_assets()` reads persona.md, playbook.md, policies from disk on every run
- Files: `apps/worker-gateway/gateway/resolver.py` lines 100+
- Cause: No caching layer for blueprint assets
- Improvement path: Add in-memory LRU cache keyed by blueprint ID + file mtime

**Prompt Assembly String Concatenation:**
- Problem: Large prompts assembled via string concatenation in PromptAssembler
- Files: `apps/worker-gateway/gateway/prompt.py`
- Cause: Python string concat creates intermediate copies
- Improvement path: Use `io.StringIO` for large prompt assembly, or template engine (Jinja2)

**Database Connection Pooling:**
- Problem: Each store (ConfigStore, RunStore, ConnectorStore) creates its own asyncpg connection
- Files: `apps/worker-gateway/gateway/store/*.py`
- Cause: No shared connection pool
- Improvement path: Use `asyncpg.create_pool()` in app lifespan, share across stores

## Fragile Areas

**Agent Zero Context Cleanup:**
- Files: `apps/worker-gateway/gateway/adapters/agentzero.py` lines 44-55
- Why fragile: Context termination runs in `finally` block. If A0 is down during cleanup, exception is swallowed (logged only).
- Safe modification: Always test with A0 unavailable to ensure cleanup failure doesn't break response
- Test coverage: Integration test `test_agentzero_integration.py` covers happy path, not cleanup failure

**Paperclip Bootstrap Flow:**
- Files: `docker-compose.yml` lines 74-81, `docs/tasks.md` lines 217-221
- Why fragile: Paperclip `onboard --yes --bind lan` runs once, creates `/paperclip/instances/default/config.json`. If config gets corrupted, must delete volume and re-bootstrap.
- Safe modification: Backup `/paperclip/instances/` before changing Paperclip env vars
- Test coverage: Not automated — manual smoke test only

**Database Migration Order:**
- Files: `apps/worker-gateway/alembic/versions/*.py`
- Why fragile: Alembic migrations must run before `CONFIG_STORE=db` or `RunStore` can initialize
- Safe modification: Run `alembic upgrade head` in Dockerfile CMD or docker-entrypoint, not manually
- Test coverage: No automated migration testing in CI

**Prompt Injection via Client Context:**
- Files: `apps/worker-gateway/gateway/prompt.py` (context injection), `worker-packs/*/context/*.md`
- Why fragile: Client context files (company-profile.md, brand-voice.md) are injected verbatim into prompts. Malicious markdown could inject instructions.
- Safe modification: Sanitize or escape client context before injection
- Test coverage: No adversarial prompt tests

**MCP Server Credential Lookup:**
- Files: `services/gmail-mcp/server.py` lines 50+
- Why fragile: If gateway `/internal/connectors/.../credentials` endpoint is down, MCP tools fail silently
- Safe modification: Add retry logic or circuit breaker in MCP server credential lookup
- Test coverage: No integration test for gateway downtime scenario

## Scaling Limits

**Single Worker Gateway Instance:**
- Current capacity: One FastAPI process, uvicorn single-worker
- Limit: ~100 concurrent requests before latency degrades (depends on A0 response time)
- Scaling path: Run multiple gateway replicas behind load balancer, use Redis for session state if needed

**LiteLLM as Single Point of Failure:**
- Current capacity: One LiteLLM container proxies all model requests
- Limit: If LiteLLM crashes, all workers are offline
- Scaling path: Run LiteLLM replicas (stateless), use DB for config/keys

**Postgres Connection Limits:**
- Current capacity: Default Postgres max_connections = 100
- Limit: Each gateway/dashboard instance uses 1-5 connections. 20 instances = exhausted.
- Scaling path: Use connection pooling (PgBouncer), increase max_connections, or separate read replicas

**Agent Zero Context Memory:**
- Current capacity: Each A0 context stores full conversation history in memory
- Limit: Long-running contexts (multi-turn workflows) consume RAM linearly
- Scaling path: Current mitigation = context terminated after each run. For multi-turn, add context pruning.

## Dependencies at Risk

**Paperclip (Control Plane):**
- Risk: Third-party project, development pace unknown
- Impact: If Paperclip development stalls or API changes drastically, control plane breaks
- Migration plan: Abstract Paperclip behind `ControlPlaneClient` interface, prepare to swap with custom control plane or Temporal.io

**Agent Zero (Runtime):**
- Risk: Third-party project, optimized for interactive UI not API-first execution
- Impact: API contract is undocumented (reverse-engineered). Future A0 versions may break `/api_message`.
- Migration plan: Abstract behind `RuntimeAdapter` interface (already done), prepare to swap with LangGraph, CrewAI, or custom agent loop.

**LiteLLM:**
- Risk: Actively developed but rapid release cadence = potential breaking changes
- Impact: Model routing config format or proxy behavior changes
- Migration plan: Pin `LITELLM_IMAGE_TAG` to stable versions, test upgrades in staging before production

**Better Auth (Dashboard):**
- Risk: Relatively new library (v1.x), less mature than NextAuth
- Impact: Security patches or breaking changes
- Migration plan: Switch to NextAuth v5 or Clerk if Better Auth becomes unmaintained

## Missing Critical Features

**Worker Approval Flow:**
- Problem: `approvalStatus="pending"` artifacts exist but no UI or API to approve/reject
- Blocks: Production use of workers that draft emails or execute actions
- Fix: Build approval queue UI in dashboard, add `PATCH /v1/runs/{id}/artifacts/{index}/approve` endpoint

**Worker Memory/Context Persistence:**
- Problem: Each run is isolated, no cross-run memory or learning
- Blocks: Workers that need to "remember" past interactions or company-specific knowledge
- Fix: Implement persistent context store (vector DB like Pinecone, Weaviate, or Postgres + pgvector)

**Cost/Budget Enforcement:**
- Problem: No per-company spending limits or budget alerts
- Blocks: Preventing runaway costs if worker misconfigured or abused
- Fix: Track token usage (fix TODO in `agentzero.py`), add budget middleware, add alerts via Slack webhook

**Multi-Tenant Connector Scoping:**
- Problem: Gmail MCP server configured globally, session tokens provide isolation but setup is manual
- Blocks: Self-service connector onboarding for each company
- Fix: Dashboard OAuth flow already exists (task 210), needs testing + docs

**Monitoring and Alerting:**
- Problem: No production monitoring, metrics, or alerting
- Blocks: Detecting outages, performance degradation, or errors in production
- Fix: Add Prometheus + Grafana or Datadog integration, alert on high error rate / latency / LiteLLM downtime

**CI/CD Pipeline:**
- Problem: No automated testing or deployment pipeline
- Blocks: Confident releases, regression prevention
- Fix: GitHub Actions for test + build + deploy to Coolify via webhook or SSH

## Test Coverage Gaps

**Agent Zero Adapter Edge Cases:**
- What's not tested: A0 returns malformed JSON, timeout during execution, context cleanup failure
- Files: `apps/worker-gateway/gateway/adapters/agentzero.py`
- Risk: Unhandled exceptions break worker runs
- Priority: Medium — covered by happy path integration test, but error paths untested

**Database Store Implementations:**
- What's not tested: `DbConfigStore`, `RunStore`, `ConnectorStore` only have unit tests with mocked asyncpg
- Files: `apps/worker-gateway/gateway/store/*.py`
- Risk: Real Postgres behavior (transactions, connection errors, schema mismatches) unknown
- Priority: High — must test before using `CONFIG_STORE=db` in production

**Prompt Assembly Security:**
- What's not tested: Adversarial client context with prompt injection attempts
- Files: `apps/worker-gateway/gateway/prompt.py`
- Risk: Malicious context could override worker instructions
- Priority: High — security-critical

**MCP Server Error Handling:**
- What's not tested: Gmail MCP server when gateway is unreachable, OAuth token expired, Gmail API quota exceeded
- Files: `services/gmail-mcp/server.py`, `services/gmail-mcp/tools/gmail.py`
- Risk: Silent failures or uncaught exceptions during agent runs
- Priority: Medium — impacts worker reliability

**Dashboard Authentication:**
- What's not tested: Better Auth session expiry, password reset flow, account registration edge cases
- Files: `apps/dashboard/src/app/api/auth/[...all]/route.ts`
- Risk: Security vulnerabilities or poor UX
- Priority: Medium — covered by Better Auth library, but custom logic untested

**Paperclip Wake Endpoint:**
- What's not tested: Wake auth validation when `PAPERCLIP_VALIDATE_WAKE_AUTH=true`
- Files: `apps/worker-gateway/app.py` (wake endpoint), `apps/worker-gateway/gateway/paperclip/auth.py`
- Risk: Unauthorized wake requests if auth bypass exists
- Priority: High — security-critical

**Concurrent Request Handling:**
- What's not tested: Multiple simultaneous `/v1/workers/run` requests
- Files: `apps/worker-gateway/app.py`
- Risk: Database connection exhaustion, race conditions in stores
- Priority: Low — unlikely in MVP, critical for production scale

---

*Concerns audit: 2026-04-19*
