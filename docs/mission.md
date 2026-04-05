# Habilis — Mission & Vision

## What This Is

Habilis (the Psilodigital Worker Platform) is a practical multi-tenant worker operating system for small and medium businesses.

It is not a generic AI playground, not an eval-first platform, and not a prompt experimentation tool.

## The Mission

Build a platform where businesses can "hire" AI workers for real operational jobs — inbox management, content creation, booking operations, CRM follow-up, and admin/accounting support.

## The Product Vision

A business should be able to log in, connect its tools, activate one or more workers, assign tasks, approve sensitive actions, track what happened, and understand the value created.

The experience should feel like managing digital employees, not stitching together prompts and APIs.

## Core Positioning

- We sell workers, not models
- We sell outcomes, not infrastructure
- We sell operational leverage for small businesses, not AI complexity
- The platform must be understandable to a non-technical business owner

## North Star

Create a reliable "company OS" where specialized workers can safely perform repeatable business work — using connectors, memory, tools, and model routing behind the scenes.

## Primary User

Small business owners and operators who want practical automation without needing to understand AI providers, prompts, agents, or cloud architecture.

## First Worker Types

- **Inbox Worker** — email triage, drafting, routing
- **Content Worker** — social media, blog posts, newsletters
- **Booking Ops Worker** — scheduling, confirmations, calendar management
- **CRM Follow-up Worker** — lead nurture, follow-up sequences, pipeline updates
- **Admin / Accounting Assistant** — invoicing, expense tracking, data entry

## First Verticals

- Tourism / booking businesses
- Service businesses
- Small agencies
- Admin-heavy small teams

## Product Principles

1. A business should never need to choose between 20 models
2. A business should activate a worker, not configure a research project
3. A worker should have a job, tools, limits, memory, and accountability
4. The system should show business value clearly
5. The UX should reduce fear and confusion around AI systems

## Non-Goals

- Do not optimize first for prompt experimentation
- Do not optimize first for benchmark evaluations
- Do not build a generic chatbot wrapper
- Do not expose raw infrastructure complexity to customers
- Do not assume highly technical users
- Do not let architecture drift into a monolith unless absolutely necessary

## What Success Looks Like

A small business can eventually say:

> "I activated an Inbox Worker and a Content Worker, connected my tools, approved a few actions, and now important repetitive work is being handled for me."

---

## Architecture

### Mental Model

| Layer | Role | Service |
|---|---|---|
| Product surface | What customers use | Dashboard (Next.js) |
| Control plane | Orchestration, tasks, approvals, budgets | Paperclip |
| Worker runtime | Execution engine for worker logic | Agent Zero |
| Model gateway | Unified, provider-agnostic model access | LiteLLM |
| Tools/Connectors | Actions into external systems | MCP + custom connectors |
| Data | System of record | Postgres |
| Coordination | Queues, transient state | Redis |

### System Diagram

```
                    ┌──────────────┐
                    │   Paperclip  │ :3100
                    │ (control     │
                    │  plane)      │
                    └──────┬───────┘
                           │ HTTP adapter POST
                           ▼
                    ┌──────────────┐
                    │   worker-    │ :8080
                    │   gateway    │
                    │  (FastAPI)   │
                    └──────┬───────┘
                           │ POST /api_message (X-API-KEY)
                           ▼
                    ┌──────────────┐
                    │  Agent Zero  │ :50080
                    │ (worker      │
                    │  runtime)    │
                    └──────────────┘

    ┌──────────┐                    ┌──────────┐
    │ Postgres │ :5432              │  Redis   │ :6379
    │ (17-alp) │                    │ (7-alp)  │
    └──────────┘                    └──────────┘

    ┌──────────┐
    │ LiteLLM  │ :4000
    │ (model   │
    │  proxy)  │
    └──────────┘
```

All services communicate over the `workerstack` Docker bridge network.

### Architecture Principles

1. **Modular first** — each service has a clear job and clean boundaries
2. **Compose-first local development** — runs locally through Docker Compose, deploys with Coolify on Hetzner
3. **Multi-tenant by design** — every business/workspace is isolated in data, memory, credentials, budgets, logs, and worker configuration
4. **Safe by default** — sensitive actions support approval gates, audit trails, and constrained permissions
5. **Provider-agnostic model access** — all model traffic flows through LiteLLM
6. **Worker-centric product design** — UX revolves around what workers exist, what they can do, what tasks they handled, what they cost, and what they produced
7. **Practical over clever** — boring, understandable, maintainable choices over impressive but fragile abstractions
8. **Strong internal boundaries** — dashboard, orchestration, model gateway, and worker runtimes are separable and replaceable

### Decision Framework

When making architecture or implementation decisions, prioritize in this order:

1. Clarity
2. Separability
3. Tenant safety
4. Local dev simplicity
5. Production deployability
6. Long-term maintainability
7. Elegance

---

## Codebase Vision

Monorepo with clear separation:

```
apps/
  dashboard/          # Next.js — the commercial product surface
  worker-gateway/     # FastAPI — bridge between orchestration and execution

packages/
  shared-types/       # Cross-service type definitions
  worker-definitions/ # Worker configs, schemas, capabilities
  connector-sdk/      # SDK for building connectors
  ui/                 # Shared UI components
  config/             # Shared configuration

services/
  paperclip/          # Control plane
  litellm/            # Model gateway
  agentzero/          # Worker runtime

infra/
  docker/             # Dockerfiles, compose configs
  coolify/            # Deployment configs
  scripts/            # Setup, smoke tests, utilities
  env/                # Environment templates
```

---

## Key Boundaries

### The Dashboard
The real product customers use. Should allow workspace creation, connector setup, worker activation, task history, approvals, usage/cost visibility, and business-facing reports.

### The Worker Gateway
Bridge between orchestration and execution. Paperclip wakes workers through a stable HTTP interface. The gateway translates orchestration requests into Agent Zero execution flows. Must be explicit, observable, and easy to debug.

### The Control Plane (Paperclip)
Manages company/workspace orchestration: tasks, assignment, approvals, budgets, visibility, auditability.

### The Runtime (Agent Zero)
Executes worker logic, tools, and skills. Remains a separate runtime, not embedded into the dashboard.

### The Model Layer (LiteLLM)
Single model access layer. Workers never directly depend on Anthropic, OpenAI, Google, etc. Routing, fallback, budgets, and provider switching happen centrally.

### The Connector Layer
Connectors are first-class product components. Uses MCP where it makes sense, custom APIs where needed. Connector permissions must be explicit and workspace-scoped.

---

## Quality Bar

- Understandable by a small business
- Maintainable by a small engineering team
- Deployable without heroic DevOps effort
