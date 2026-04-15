# Habilis — Architecture Decisions

> Record of key decisions and their rationale. Append-only — never delete entries.
> Newest at the bottom.

---

## ADR-001: Modular Multi-Service Architecture

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** Use separate services for control plane (Paperclip), worker runtime (Agent Zero), model gateway (LiteLLM), and orchestration bridge (worker-gateway). Do not collapse into a monolith.

**Rationale:** Each layer has a different job, different scaling profile, and may need to be replaced independently. Paperclip is a third-party control plane. Agent Zero is a third-party runtime. LiteLLM is a third-party gateway. Keeping them separate means any one can be swapped without rewriting the others.

**Consequences:** More operational complexity (6+ containers). Requires explicit integration boundaries. Worth it for long-term separability.

---

## ADR-002: LiteLLM as Single Model Gateway

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** All model traffic flows through LiteLLM. No service calls providers directly.

**Rationale:** Centralizes API key management, enables model routing/fallback, provides cost tracking, and decouples workers from provider specifics. A business should activate a worker, not pick a model.

**Consequences:** All services need `LITELLM_MASTER_KEY`. Agent Zero must be configured to use LiteLLM as an OpenAI-compatible endpoint. Worker aliases (`worker-default`, `worker-strong`) allow changing the underlying model without touching worker code.

---

## ADR-003: Worker-Gateway as Orchestration Boundary

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** The worker-gateway is the explicit HTTP bridge between Paperclip (control plane) and Agent Zero (runtime). Paperclip never calls Agent Zero directly.

**Rationale:** Creates a stable, observable, debuggable integration point. The gateway can translate Paperclip's wake contract into Agent Zero's API format. If either side changes, only the gateway needs updating.

**Consequences:** Adds one hop of latency. Provides full logging and observability of the orchestration boundary. Can add request validation, rate limiting, and tenant scoping here.

---

## ADR-004: Docker Compose for Local + Production

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** Use a single `docker-compose.yml` for both local development and Coolify deployment. No separate compose files per environment.

**Rationale:** Coolify's Docker Compose build pack reads the same file. Environment differences handled via `.env` variables. Reduces drift between local and production.

**Consequences:** Must keep compose file Coolify-compatible (no local-only hacks). Environment-specific config goes in env vars only.

---

## ADR-005: Monorepo with apps/packages/services/infra

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** Organize as a monorepo with `apps/` (products), `packages/` (shared code), `services/` (infrastructure), `infra/` (ops).

**Rationale:** Keeps everything in one repo while maintaining clear boundaries. `apps/` is what we build (dashboard, worker-gateway). `services/` is what we configure (paperclip, litellm, agentzero). `packages/` is shared libraries. `infra/` is operational tooling.

**Consequences:** No monorepo tooling (Turborepo, Nx) yet — not needed at current scale. May add later when `packages/` has real shared code.

---

## ADR-006: Worker Model Aliases in LiteLLM

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** Define `worker-default` and `worker-strong` as LiteLLM model aliases. Workers request these aliases, not specific provider models.

**Rationale:** Decouples worker logic from model selection. Can change the underlying model (e.g., swap `worker-default` from GPT-4.1-mini to Gemini Flash) without touching any worker code or config.

**Consequences:** Must keep aliases in `services/litellm/config.yaml` updated. Workers should never hardcode provider-specific model names.

---

## ADR-007: Postgres Internal-Only, No Host Port

**Date:** 2026-04-05
**Status:** Accepted

**Decision:** Postgres and Redis are not exposed to the host. Only accessible within the Docker network.

**Rationale:** Security. No reason for external access in normal operation. Services connect via internal DNS (`postgres:5432`, `redis:6379`).

**Consequences:** To debug Postgres directly, use `make shell-postgres` or add a temporary port mapping. Acceptable tradeoff.

---

## ADR-008: Dashboard as Separate Next.js App

**Date:** 2026-04-05
**Status:** Planned

**Decision:** The customer-facing dashboard will be a separate Next.js app in `apps/dashboard/`, not embedded in Paperclip.

**Rationale:** Paperclip is a control plane, not a customer product. The dashboard is the product surface — it must be fully custom, brand-controlled, and designed for non-technical business users. Keeping it separate means Paperclip can be upgraded or replaced without rewriting the product.

**Consequences:** Dashboard needs its own DB schema, auth, and API layer. Communicates with Paperclip via API, not by sharing internals.

---

## ADR-009: pnpm + Turborepo for Monorepo Tooling

**Date:** 2026-04-14
**Status:** Accepted

**Decision:** Use pnpm workspaces with Turborepo for TypeScript package management and build orchestration. Python services (worker-gateway) live in the same monorepo but are managed independently.

**Rationale:** pnpm provides strict dependency isolation and fast installs. Turborepo adds cached builds and dependency-aware task execution across packages. The combination is lightweight yet powerful for a growing monorepo with shared TS packages.

**Consequences:** All TS packages must have `build` and `typecheck` scripts. Python services are unaffected by pnpm/Turbo. Root `package.json` exists for workspace management only.

---

## ADR-010: Prompt Assembly Module in Worker Gateway

**Date:** 2026-04-14
**Status:** Accepted

**Decision:** Create an adapter-agnostic `PromptAssembler` that constructs system + user prompts from blueprint assets (persona, playbook, policies, output schema) and client context. Paired with a `ResponseParser` for extracting structured data from free-text runtime responses.

**Rationale:** The Agent Zero adapter was sending flat prompt strings with no persona, playbook, or context injection. Proper prompt assembly is required for workers to behave according to their blueprint definitions. Making the assembler adapter-agnostic means any future runtime (not just Agent Zero) can use the same prompt construction.

**Consequences:** Blueprint asset loaders added to resolver. A0 adapter now depends on PromptAssembler. Response parsing uses a fallback chain: JSON code block → raw JSON → plain text artifact.

---

## ADR-011: Hybrid Config Store (YAML Blueprints + DB Tenants)

**Date:** 2026-04-14
**Status:** Accepted

**Decision:** Worker blueprints remain as YAML files on disk (versioned product definitions). Company and worker instance configs are abstracted behind a `ConfigStore` interface with two implementations: `FileConfigStore` (YAML on disk, default) and `DbConfigStore` (Postgres).

**Rationale:** Blueprints are developer-authored product definitions that benefit from version control. Company/instance configs are tenant data that will eventually be managed via the dashboard UI, requiring DB storage. The abstraction allows gradual migration without breaking existing functionality.

**Consequences:** `resolve_all()` is now async. `CONFIG_STORE=file` remains default. DB store requires `DATABASE_URL` and running Postgres with the gateway schema.

---

## ADR-012: Alembic for Gateway Database Migrations

**Date:** 2026-04-14
**Status:** Accepted

**Decision:** Use Alembic with SQLAlchemy for managing the gateway's Postgres schema migrations.

**Rationale:** Alembic is the standard migration tool for Python + Postgres. It provides versioned, reversible migrations and integrates with the existing Python toolchain. The gateway needs its own DB for company/instance configs and run history.

**Consequences:** Migration files live in `apps/worker-gateway/alembic/versions/`. `DATABASE_URL` env var configures the connection. Migrations must be run before using `CONFIG_STORE=db`.

---

## ADR-013: Separate Gateway Database

**Date:** 2026-04-14
**Status:** Accepted

**Decision:** The worker-gateway gets its own `gateway` database in the shared Postgres instance, separate from `paperclip`, `litellm`, and `dashboard` databases.

**Rationale:** Each service owns its data. The gateway stores company configs, worker instance configs, and run history — data that belongs to the orchestration boundary, not to Paperclip or LiteLLM. Separate databases enforce clean service boundaries.

**Consequences:** `infra/postgres/init/01-create-dbs.sql` creates the `gateway` database. Docker Compose passes `DATABASE_URL` to the worker-gateway service.
