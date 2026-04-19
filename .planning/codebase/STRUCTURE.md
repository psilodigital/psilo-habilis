# Codebase Structure

**Analysis Date:** 2026-04-19

## Directory Layout

```
habilis/
├── apps/                       # Application services
│   ├── dashboard/             # Next.js 16 customer UI (port 3000)
│   └── worker-gateway/        # Python/FastAPI orchestration gateway (port 8080)
├── services/                   # Infrastructure and runtime services
│   ├── paperclip/             # Control plane (port 3100)
│   ├── litellm/               # Model proxy (port 4000)
│   ├── agentzero/             # Worker runtime placeholder (port 50080, external image)
│   └── gmail-mcp/             # Gmail connector MCP server (port 8090)
├── packages/                   # Shared TypeScript libraries (pnpm workspace)
│   ├── orchestration-contracts/   # Worker execution API types
│   ├── shared-types/          # Cross-service domain types
│   ├── worker-definitions/    # Blueprint/policy schemas
│   ├── connector-sdk/         # Connector builder SDK
│   ├── config/                # Shared config utilities
│   └── ui/                    # Shared UI components (planned)
├── worker-packs/              # Blueprint definitions (product SKUs)
│   └── inbox-worker/          # Email triage worker blueprint
├── clients/                   # Multi-tenant client configurations
│   └── psilodigital/          # Example tenant
│       ├── company.yaml       # Company metadata
│       ├── context/           # Prompt context files
│       └── workers/           # Worker instance overrides
├── infra/                     # Deployment and infrastructure
│   ├── postgres/init/         # DB init SQL scripts
│   ├── scripts/               # Setup, smoke tests
│   ├── docker/                # Dockerfile fragments
│   ├── coolify/               # Deployment configs
│   └── env/                   # Environment templates
├── docs/                      # Project documentation
│   ├── mission.md             # Product vision and principles
│   ├── tasks.md               # Living task tracker
│   ├── decisions.md           # Architecture Decision Records
│   └── architecture/          # Architecture diagrams
├── .claude/                   # Claude agent configurations
│   ├── agents/                # Agent definitions
│   ├── commands/              # Custom commands
│   └── get-shit-done/         # GSD workflow templates
├── .planning/                 # Generated codebase analysis (this document)
│   └── codebase/
├── docker-compose.yml         # Full stack orchestration
├── Makefile                   # Developer shortcuts
├── .env.example               # Environment variable template
└── pnpm-workspace.yaml        # Monorepo workspace config
```

## Directory Purposes

**apps/**
- Purpose: User-facing and orchestration applications
- Contains: Python/FastAPI and Next.js services
- Key files: `worker-gateway/app.py`, `dashboard/src/app/page.tsx`

**services/**
- Purpose: Infrastructure and third-party runtime services
- Contains: Dockerfiles, config files for Paperclip, LiteLLM, Agent Zero, MCP servers
- Key files: `paperclip/Dockerfile`, `litellm/config.yaml`, `gmail-mcp/server.py`

**packages/**
- Purpose: Shared TypeScript libraries for type safety across services
- Contains: TypeScript source in `src/`, compiled output in `dist/`
- Key files: `orchestration-contracts/src/worker-run-request.ts`, `shared-types/src/company.ts`

**worker-packs/**
- Purpose: Reusable worker blueprint definitions (product catalog)
- Contains: YAML manifests, markdown personas/playbooks, policy files, agent configs
- Key files: `inbox-worker/pack.yaml`, `inbox-worker/persona.md`, `inbox-worker/policies/tool-policy.yaml`

**clients/**
- Purpose: Multi-tenant client customizations and context
- Contains: Company YAML files, worker instance overrides, context markdown files
- Key files: `psilodigital/company.yaml`, `psilodigital/workers/inbox-worker.instance.yaml`, `psilodigital/context/company-profile.md`

**infra/**
- Purpose: Deployment scripts, database migrations, environment setup
- Contains: Bash scripts, SQL files, Docker configs, Coolify manifests
- Key files: `scripts/setup.sh`, `scripts/smoke-test.sh`, `postgres/init/01-create-dbs.sql`

**docs/**
- Purpose: Product and technical documentation
- Contains: Markdown files for mission, architecture, decisions, tasks
- Key files: `mission.md`, `tasks.md`, `decisions.md`, `local-dev.md`

## Key File Locations

**Entry Points:**
- `apps/worker-gateway/app.py`: FastAPI application with lifespan manager
- `apps/dashboard/src/app/layout.tsx`: Next.js root layout
- `apps/dashboard/src/app/page.tsx`: Dashboard home page
- `docker-compose.yml`: Full stack definition (primary orchestration)

**Configuration:**
- `.env.example`: Environment variable template (all services)
- `docker-compose.yml`: Service definitions, ports, volumes, health checks
- `services/litellm/config.yaml`: Model routing and provider config
- `worker-packs/{id}/pack.yaml`: Blueprint manifest
- `clients/{companyId}/company.yaml`: Company metadata
- `clients/{companyId}/workers/{name}.instance.yaml`: Worker instance overrides

**Core Logic:**
- `apps/worker-gateway/gateway/resolver.py`: Config resolution and merging
- `apps/worker-gateway/gateway/adapters/agentzero.py`: Agent Zero runtime adapter
- `apps/worker-gateway/gateway/prompt.py`: Prompt assembly for Agent Zero
- `apps/worker-gateway/gateway/store/connector_store.py`: Encrypted credential storage
- `apps/worker-gateway/gateway/connectors/session.py`: Connector session token generation

**Testing:**
- `apps/worker-gateway/tests/`: Pytest test suite
- `infra/scripts/smoke-test.sh`: Post-boot integration tests (13 checks)
- `apps/worker-gateway/pyproject.toml`: Pytest configuration

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (e.g., `agentzero.py`, `file_store.py`)
- TypeScript modules: `kebab-case.ts` (e.g., `worker-run-request.ts`)
- Config files: `kebab-case.yaml` (e.g., `approval-policy.yaml`, `inbox-worker.instance.yaml`)
- Markdown docs: `kebab-case.md` (e.g., `company-profile.md`, `brand-voice.md`)
- Docker containers: `psilo-{service}` prefix (e.g., `psilo-paperclip`, `psilo-worker-gateway`)

**Directories:**
- Apps/services: `kebab-case` (e.g., `worker-gateway`, `gmail-mcp`)
- Python packages: `snake_case` (e.g., `gateway/adapters/`, `gateway/store/`)
- TypeScript packages: `kebab-case` (e.g., `orchestration-contracts`, `shared-types`)

## Where to Add New Code

**New Worker Blueprint:**
- Primary code: `worker-packs/{blueprint-id}/`
- Manifest: `worker-packs/{blueprint-id}/pack.yaml`
- Assets: `worker-packs/{blueprint-id}/persona.md`, `playbook.md`, `policies/*.yaml`, `agents/*.yaml`
- Tests: `infra/scripts/smoke-test.sh` (add validation)

**New Client Onboarding:**
- Company config: `clients/{companyId}/company.yaml`
- Context files: `clients/{companyId}/context/*.md`
- Worker instances: `clients/{companyId}/workers/{name}.instance.yaml`

**New Runtime Adapter:**
- Implementation: `apps/worker-gateway/gateway/adapters/{adapter_name}.py`
- Must extend: `gateway.adapters.base.RuntimeAdapter`
- Registration: Set `RUNTIME_ADAPTER={adapter_name}` in `.env`
- Tests: `apps/worker-gateway/tests/test_adapters.py`

**New MCP Connector:**
- Service directory: `services/{connector-name}-mcp/`
- Dockerfile: `services/{connector-name}-mcp/Dockerfile`
- Server implementation: `services/{connector-name}-mcp/server.py`
- Docker Compose: Add service definition in `docker-compose.yml`
- Requirements: `services/{connector-name}-mcp/requirements.txt`

**New Shared TypeScript Package:**
- Package directory: `packages/{package-name}/`
- Source: `packages/{package-name}/src/index.ts`
- Config: `packages/{package-name}/package.json`, `tsconfig.json`
- Build output: `packages/{package-name}/dist/`
- Workspace: Add to `pnpm-workspace.yaml` (auto-detected via `packages/*`)

**New Gateway Route:**
- Primary code: `apps/worker-gateway/app.py` (add FastAPI route handler)
- Models: `apps/worker-gateway/gateway/models.py` (request/response Pydantic models)
- Tests: `apps/worker-gateway/tests/test_routes.py`

**New Dashboard Page:**
- Implementation: `apps/dashboard/src/app/{route}/page.tsx`
- Layout: `apps/dashboard/src/app/{route}/layout.tsx` (if needed)
- Components: `apps/dashboard/src/components/{feature}/`
- API routes: `apps/dashboard/src/app/api/{endpoint}/route.ts`

**Utilities:**
- Python shared helpers: `apps/worker-gateway/gateway/` (module-level utilities)
- TypeScript shared utilities: `packages/config/src/` or create new package
- Bash scripts: `infra/scripts/{script-name}.sh`

## Special Directories

**node_modules/**
- Purpose: npm/pnpm dependencies
- Generated: Yes (via `pnpm install`)
- Committed: No (in `.gitignore`)

**dist/**
- Purpose: Compiled TypeScript output for packages
- Generated: Yes (via `pnpm turbo run build`)
- Committed: No (in `.gitignore`)

**__pycache__/**
- Purpose: Python bytecode cache
- Generated: Yes (Python runtime)
- Committed: No (in `.gitignore`)

**.next/**
- Purpose: Next.js build output
- Generated: Yes (via `next build`)
- Committed: No (in `.gitignore`)

**postgres_data/, redis_data/, paperclip_data/, agentzero_usr/**
- Purpose: Docker volume persistence
- Generated: Yes (Docker Compose runtime)
- Committed: No (Docker-managed volumes)

**alembic/versions/**
- Purpose: Database migration scripts
- Generated: Yes (via `alembic revision`)
- Committed: Yes (version-controlled schema changes)

**.planning/codebase/**
- Purpose: GSD-generated codebase analysis documents
- Generated: Yes (via `/gsd-map-codebase`)
- Committed: Yes (informs planning and execution)

**.claude/**
- Purpose: Claude agent configurations and custom commands
- Generated: No (hand-maintained)
- Committed: Yes (project-specific agent behavior)

**infra/postgres/init/**
- Purpose: PostgreSQL initialization scripts (run once on first boot)
- Generated: No (hand-maintained SQL)
- Committed: Yes (database schema bootstrapping)

---

*Structure analysis: 2026-04-19*
