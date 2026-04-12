# System architecture (Mermaid)

Layered view of the Psilodigital Worker Platform: product surface, control plane, execution boundary, reusable worker definitions, runtime, models, tools, and shared infrastructure.

The same diagrams are stored as standalone Mermaid sources under [`mermaid/`](mermaid/) (`.mermaid` files) for editors, [Mermaid Live Editor](https://mermaid.live), and the Mermaid CLI (`mmdc`). Keep those files in sync when you change the fenced blocks below.

Related: [Mission & mental model](../mission.md#architecture), [v1 thin slice](v1-thin-slice.md).

---

## System architecture

**Source:** [mermaid/system-architecture.mermaid](mermaid/system-architecture.mermaid)

Users interact with the Dashboard; Paperclip orchestrates work; the Worker Gateway resolves blueprints and routes execution to Agent Zero; LiteLLM fronts model providers; MCP and connectors reach external systems; Postgres, Redis, and files hold state and context.

```mermaid
flowchart TB
    subgraph U["Users"]
        SMB["Client Business Users"]
        PSI["Psilodigital Internal Team"]
    end

    subgraph APP["Product Surface"]
        DASH["Dashboard App<br/>Next.js"]
    end

    subgraph CTRL["Control Plane"]
        PAPER["Paperclip<br/>Companies • Teams • Tasks • Budgets • Approvals"]
    end

    subgraph ORCH["Execution Boundary"]
        GATE["Worker Gateway<br/>Blueprint Resolution • Merge Logic • Runtime Routing"]
    end

    subgraph DEF["Reusable Product Layer"]
        PACKS["Worker Packs<br/>inbox-worker<br/>content-worker<br/>booking-ops-worker"]
        CLIENTS["Company Instances<br/>psilodigital<br/>client-a<br/>client-b"]
        CONTRACTS["Shared Contracts<br/>WorkerRunRequest / WorkerRunResponse"]
    end

    subgraph RUN["Runtime Layer"]
        A0["Agent Zero<br/>Worker Runtime"]
        PROJ1["Project: Psilodigital"]
        PROJ2["Project: Client A"]
        PROJ3["Project: Client B"]
    end

    subgraph MODEL["Model Layer"]
        LLM["LiteLLM Gateway"]
        OPENAI["OpenAI"]
        ANTH["Anthropic"]
        GOOGLE["Google"]
        GROQ["Groq / Others"]
    end

    subgraph TOOLS["Tool / Connector Layer"]
        MCP["MCP / Connector SDK"]
        GMAIL["Gmail / Email"]
        CAL["Calendar"]
        CRM["CRM"]
        BOOK["PsiloBooking API"]
        DOCS["Docs / Knowledge"]
    end

    subgraph DATA["State / Infra"]
        PG["Postgres"]
        REDIS["Redis"]
        FILES["Files / Context / Config"]
    end

    SMB --> DASH
    PSI --> DASH

    DASH --> PAPER
    DASH --> GATE

    PAPER --> GATE

    GATE --> PACKS
    GATE --> CLIENTS
    GATE --> CONTRACTS

    GATE --> A0
    A0 --> PROJ1
    A0 --> PROJ2
    A0 --> PROJ3

    A0 --> LLM
    LLM --> OPENAI
    LLM --> ANTH
    LLM --> GOOGLE
    LLM --> GROQ

    A0 --> MCP
    MCP --> GMAIL
    MCP --> CAL
    MCP --> CRM
    MCP --> BOOK
    MCP --> DOCS

    PAPER --> PG
    GATE --> PG
    GATE --> REDIS
    GATE --> FILES
    A0 --> FILES
    LLM --> PG
```

---

## Blueprint → company instance model

**Source:** [mermaid/blueprint-company-instance.mermaid](mermaid/blueprint-company-instance.mermaid)

One **worker blueprint** (versioned pack, e.g. `inbox-worker@1.0.0`) is instantiated per company. Each instance gets its own **context**: documentation, tone, tool allowlists, secrets, and memory — without copying the whole pack for every tenant.

```mermaid
flowchart LR
    BP["Worker Blueprint<br/>inbox-worker@1.0.0"] --> I1["Psilodigital Instance<br/>psilodigital.inbox-worker"]
    BP --> I2["Client A Instance<br/>client-a.inbox-worker"]
    BP --> I3["Client B Instance<br/>client-b.inbox-worker"]

    I1 --> C1["Psilodigital Context<br/>docs • tone • tools • secrets • memory"]
    I2 --> C2["Client A Context<br/>docs • tone • tools • secrets • memory"]
    I3 --> C3["Client B Context<br/>docs • tone • tools • secrets • memory"]
```

---

## Request flow

**Source:** [mermaid/request-flow.mermaid](mermaid/request-flow.mermaid)

End-to-end path for blueprint-driven execution: load blueprint and company instance, merge and validate, run in Agent Zero against the correct project, model via LiteLLM, tools as needed, return a structured `WorkerRunResponse`.

The Worker Gateway also exposes `POST /paperclip/wake` for legacy Paperclip wake events; new integrations should prefer `POST /v1/workers/run`.

```mermaid
sequenceDiagram
    participant P as Paperclip / Dashboard
    participant G as Worker Gateway
    participant B as Worker Blueprint
    participant C as Company Instance
    participant A as Agent Zero
    participant L as LiteLLM
    participant T as Tools / Connectors

    P->>G: POST /v1/workers/run
    G->>B: Load blueprint
    G->>C: Load company + worker instance
    G->>G: Merge config + validate request
    G->>A: Execute worker for company project
    A->>L: Request model through gateway
    L-->>A: Model response
    A->>T: Use tools if needed
    T-->>A: Tool results
    A-->>G: Structured worker result
    G-->>P: WorkerRunResponse
```

---

## Internal company / client tenancy model

**Source:** [mermaid/tenancy-model.mermaid](mermaid/tenancy-model.mermaid)

A single platform deployment hosts multiple **companies**. Each company enables a subset of **workers**; each worker maps to an **Agent Zero project** so runs, secrets, and context stay isolated per tenant.

```mermaid
flowchart TB
    ROOT["One Psilodigital Platform Deployment"]

    ROOT --> CO1["Company: Psilodigital"]
    ROOT --> CO2["Company: Client A"]
    ROOT --> CO3["Company: Client B"]

    CO1 --> W11["Inbox Worker"]
    CO1 --> W12["Content Worker"]
    CO1 --> W13["Engineering Worker"]

    CO2 --> W21["Inbox Worker"]
    CO2 --> W22["Booking Ops Worker"]

    CO3 --> W31["Inbox Worker"]
    CO3 --> W32["Admin Worker"]

    W11 --> P11["Agent Zero Project: psilodigital"]
    W21 --> P21["Agent Zero Project: client-a"]
    W31 --> P31["Agent Zero Project: client-b"]
```

---

## Shortest path summary

```
Dashboard / Paperclip
        ↓
   Worker Gateway
        ↓
Blueprint + Company Instance Resolution
        ↓
     Agent Zero
        ↓
      LiteLLM
        ↓
  Model Providers + Tools
```

---

## Rendering these diagrams

- **GitHub / GitLab**: Mermaid is rendered in Markdown by default on many hosts.
- **Local preview**: VS Code with a Mermaid preview extension, or paste into [mermaid.live](https://mermaid.live).
- **Standalone files**: Open any `mermaid/*.mermaid` file in an editor that supports Mermaid, or run the [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) against a file, for example:  
  `npx -y @mermaid-js/mermaid-cli -i docs/architecture/mermaid/system-architecture.mermaid -o system-architecture.svg`
