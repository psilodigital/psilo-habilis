# v1 Thin Slice — Architecture

> Blueprint-driven worker execution with one worker, one client, one route.

## What This Is

The v1 thin slice is the smallest working version of the Psilodigital Worker Platform's blueprint-driven orchestration model. It proves that:

1. Worker behavior is defined in reusable **blueprints** (worker packs)
2. Clients instantiate blueprints with **company-specific overrides**
3. The **worker-gateway** resolves and merges configuration at runtime
4. Execution flows through a clean **runtime adapter boundary**
5. Responses follow a **structured contract**

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

### Client: `psilodigital`

Located in `clients/psilodigital/`. The internal dogfooding client:

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

Defined in `clients/psilodigital/workers/inbox-worker.instance.yaml`. Links the `psilodigital` client to the `inbox-worker@1.0.0` blueprint with overrides:

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
  ├─ 2. Resolve client from clients/{clientId}/company.yaml
  │     Validate client exists
  │
  ├─ 3. Resolve instance from clients/{clientId}/workers/{worker}.instance.yaml
  │     Validate instance exists and is enabled
  │
  ├─ 4. Load client context files (company-profile.md, brand-voice.md)
  │
  ├─ 5. Merge config: blueprint defaults → instance overrides → run overrides
  │
  ├─ 6. Validate taskKind against blueprint's supported taskKinds
  │
  ├─ 7. Execute via runtime adapter (stub or agentzero)
  │
  └─ 8. Return structured WorkerRunResponse
```

## Config Merging

Three layers, later wins:

| Layer | Source | Example |
|---|---|---|
| Blueprint defaults | `pack.yaml → defaults` | `timeoutSeconds: 120` |
| Instance overrides | `*.instance.yaml → overrides` | `timeoutSeconds: 90` |
| Run overrides | Request body `runOverrides` | `timeoutSeconds: 60` |

## Runtime Adapter Boundary

The gateway delegates execution through an abstract `RuntimeAdapter` interface:

```
RuntimeAdapter (abstract)
├── StubRuntimeAdapter    ← v1 default, deterministic simulation
└── AgentZeroAdapter      ← scaffolded, not yet active
```

**Stub adapter** returns deterministic results based on keyword matching in the input message. No AI model is called. This is explicit and honest — the stub is clearly labeled in every response via `metadata.runtimeAdapter: "stub"` and `metadata.modelUsed: "stub/deterministic"`.

**Agent Zero adapter** is scaffolded with clear TODOs for what needs to happen to make it real. See `gateway/adapters/agentzero.py`.

## Orchestration Contracts

Defined in both Python (gateway) and TypeScript (for future dashboard/frontend):

- `packages/orchestration-contracts/src/worker-run-request.ts`
- `packages/orchestration-contracts/src/worker-run-response.ts`
- `apps/worker-gateway/gateway/models.py` (Python equivalents)

## How to Run Locally

```sh
# From apps/worker-gateway/
pip install -r requirements.txt
HABILIS_REPO_ROOT=/path/to/habilis uvicorn app:app --port 8090
```

## How to Run the Smoke Test

```sh
# Start the gateway first (see above), then:
bash infra/scripts/smoke-v1.sh localhost:8090
```

## What Is Real vs Stubbed

| Component | Status |
|---|---|
| Blueprint resolution from YAML | Real |
| Client resolution from YAML | Real |
| Instance resolution + validation | Real |
| Config merging (3 layers) | Real |
| Task kind validation | Real |
| Request/response contract | Real |
| Structured JSON logging | Real |
| Error handling (missing client, bad task kind, etc.) | Real |
| Email classification (intent, urgency) | Stubbed (keyword matching) |
| Reply drafting | Stubbed (template) |
| Model calls via LiteLLM | Not connected in v1 |
| Agent Zero execution | Scaffolded, not active |
| Approval workflow | Contract defined, not enforced |
| Memory persistence | Policy defined, not implemented |
