# v1 Thin Slice — Architecture

> Blueprint-driven worker execution with one worker, one company, one route.

## What This Is

The v1 thin slice is the smallest working version of the Psilodigital Worker Platform's blueprint-driven orchestration model. It proves that:

1. Worker behavior is defined in reusable **blueprints** (worker packs)
2. Companies instantiate blueprints with **company-specific overrides**
3. The **worker-gateway** resolves and merges configuration at runtime
4. Execution flows through a clean **runtime adapter boundary**
5. Responses follow a **structured contract**

## Naming Convention

The public API uses `companyId` as the tenant identifier. This aligns with Paperclip's native `companyId` field. Internally, the resolver uses `company_id` (Python snake_case). The on-disk folder is `clients/<companyId>/` — "clients" is the folder convention, `companyId` is the API field.

## Components

### Worker Pack: `inbox-worker@1.0.0`

Located in `worker-packs/inbox-worker/`. Defines the reusable blueprint for email triage:

```
worker-packs/inbox-worker/
├── pack.yaml                    # Blueprint definition + defaults
├── persona.md                   # Worker identity and behavior rules
├── playbook.md                  # Step-by-step operational guide
├── agents/
│   ├── lead.yaml                # Orchestrator agent
│   ├── classifier.yaml          # Email classification agent
│   └── reply-drafter.yaml       # Reply composition agent
├── policies/
│   ├── approval-policy.yaml     # When human approval is needed
│   ├── model-policy.yaml        # Model routing rules
│   ├── memory-policy.yaml       # What to remember across runs
│   └── tool-policy.yaml         # Permitted tools and integrations
└── outputs/
    └── run-result.schema.json   # Structured output JSON Schema
```

### Company: `psilodigital`

Located in `clients/psilodigital/`. The internal dogfooding company:

```
clients/psilodigital/
├── company.yaml                 # Company identity + platform config
├── workers/
│   └── inbox-worker.instance.yaml   # Instance with overrides
└── context/
    ├── company-profile.md       # Injected into worker runs
    └── brand-voice.md           # Tone and style guidelines
```

### Worker Instance: `psilodigital.inbox-worker`

Defined in `clients/psilodigital/workers/inbox-worker.instance.yaml`. Links the `psilodigital` company to the `inbox-worker@1.0.0` blueprint with overrides:

- `timeoutSeconds`: 120 → 90
- `maxConcurrentRuns`: 3 → 2
- All other defaults inherited from blueprint

## Blueprint Resolution Flow

```
POST /v1/workers/run
  │
  ├─ 1. Resolve blueprint from worker-packs/{blueprintId}/pack.yaml
  │     Validate version match
  │
  ├─ 2. Resolve company from clients/{companyId}/company.yaml
  │     Validate company exists
  │
  ├─ 3. Resolve instance from clients/{companyId}/workers/{worker}.instance.yaml
  │     Validate instance exists and is enabled
  │
  ├─ 4. Load company context files (company-profile.md, brand-voice.md)
  │
  ├─ 5. Merge config (see precedence below)
  │
  ├─ 6. Validate taskKind against blueprint's supported taskKinds
  │
  ├─ 7. Execute via runtime adapter (stub or agentzero)
  │
  └─ 8. Return structured WorkerRunResponse
```

## Config Merge Precedence

Three layers, **later wins** (explicitly documented in `resolver.py`):

| Priority | Layer | Source | Example |
|---|---|---|---|
| 1 (lowest) | Blueprint defaults | `pack.yaml → defaults` | `timeoutSeconds: 120` |
| 2 | Instance overrides | `*.instance.yaml → overrides` | `timeoutSeconds: 90` |
| 3 (highest) | Run overrides | Request body `runOverrides` | `timeoutSeconds: 60` |

Merged keys: `model`, `maxTokens`, `temperature`, `approvalRequired`, `timeoutSeconds`.

## Runtime Adapter Boundary

The gateway delegates execution through an abstract `RuntimeAdapter` interface:

```
RuntimeAdapter (abstract)
├── StubRuntimeAdapter    ← v1 default, deterministic simulation
└── AgentZeroAdapter      ← scaffolded, not yet active
```

### Adapter Selection

Controlled by the `RUNTIME_ADAPTER` environment variable:

| Value | Behavior |
|---|---|
| `stub` (default) | Deterministic simulation, no external calls |
| `agentzero` | Live Agent Zero integration via `/api_message` |

**Stub adapter** returns deterministic results based on keyword matching in the input message. No AI model is called. This is explicit and honest — the stub is clearly labeled in every response via `metadata.runtimeAdapter: "stub"` and `metadata.modelUsed: "stub/deterministic"`.

**Agent Zero adapter** is scaffolded with clear TODOs for what needs to happen to make it real. See `gateway/adapters/agentzero.py`.

## Orchestration Contracts

Defined in both Python (gateway) and TypeScript (for future dashboard/frontend):

- `packages/orchestration-contracts/src/worker-run-request.ts`
- `packages/orchestration-contracts/src/worker-run-response.ts`
- `apps/worker-gateway/gateway/models.py` (Python equivalents)

## How to Run Locally

```sh
# From repo root:
make gateway-dev

# Or manually:
cd apps/worker-gateway
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8090 --reload

# With agentzero adapter:
RUNTIME_ADAPTER=agentzero uvicorn app:app --port 8090
```

## How to Run the Smoke Test

```sh
# Start the gateway first (make gateway-dev), then:
make gateway-smoke

# Or manually:
bash infra/scripts/smoke-v1.sh localhost:8090
```

## What Is Real vs Stubbed

| Component | Status |
|---|---|
| Blueprint resolution from YAML | Real |
| Company resolution from YAML | Real |
| Instance resolution + validation | Real |
| Config merging (3 layers, documented precedence) | Real |
| Task kind validation | Real |
| Request/response contract | Real |
| Runtime adapter env switch | Real |
| Structured JSON logging | Real |
| Error handling (missing company, bad task kind, etc.) | Real |
| Email classification (intent, urgency) | Stubbed (keyword matching) |
| Reply drafting | Stubbed (template) |
| Model calls via LiteLLM | Not connected in v1 |
| Agent Zero execution | Scaffolded, not active |
| Approval workflow | Contract defined, not enforced |
| Memory persistence | Policy defined, not implemented |
