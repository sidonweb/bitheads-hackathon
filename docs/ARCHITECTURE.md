# AI Experiment Copilot — Architecture

## System Overview

```mermaid
flowchart TB
    subgraph Users["Users"]
        PM["Product Manager"]
    end

    subgraph Frontends["React Frontends"]
        DASH["PM Dashboard<br/>:5174"]
        ECOM["E-Commerce Storefront<br/>:5173"]
    end

    subgraph Backends["FastAPI Backends"]
        COP["Copilot Backend<br/>:3001"]
        EAPI["E-Com Backend<br/>:3002"]
    end

    subgraph AgentLayer["AI Agent Layer"]
        LG["LangGraph ReAct Agent"]
        PW["Playwright MCP<br/>:8931"]
    end

    subgraph Data["PostgreSQL :5432"]
        EXP[("experiments")]
        EVT[("universal_events")]
    end

    PM -->|"chat · hypothesis · analyze · apply verdict"| DASH
    PM -->|"browse variants A/B"| ECOM

    DASH -->|"REST /chat /analyze /lifecycle /evals"| COP
    ECOM -->|"POST /events · GET /flag"| EAPI

    COP --> LG
    LG -->|"browser tools"| PW
    PW -->|"inspect variant URLs"| ECOM

    LG -->|"SELECT only<br/>agent_readonly"| EVT
    LG -->|"SELECT only<br/>agent_readonly"| EXP

    COP -->|"CRUD experiments<br/>copilot_role"| EXP
    COP -->|"read metrics<br/>copilot_role"| EVT

    EAPI -->|"write events · flags<br/>ecom_role"| EVT
    EAPI -->|"migrations · seed<br/>schema owner"| EXP
```

## Agent Analysis Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor PM as Product Manager
    participant D as Dashboard
    participant C as Copilot Backend
    participant A as LangGraph Agent
    participant P as Playwright MCP
    participant S as Storefront
    participant DB as PostgreSQL

    PM->>D: Click Analyze
    D->>C: POST /experiments/exp_1/analyze
    C->>A: Run agent workflow

    A->>P: Open variant A & B URLs
    P->>S: Browser inspect
    S-->>P: Page diff / UI context
    P-->>A: Visual context

    A->>DB: SELECT DISTINCT event_name
    DB-->>A: Available telemetry events

    A->>A: Infer success metric<br/>(page diff + chat context)
    A->>DB: Aggregate exposures & conversions per variant
    DB-->>A: Variant counts

    A->>A: run_statistics (z-test)
    A->>A: decide → Scale / Continue / Stop / Rollback

    A-->>C: Structured decision + reasoning
    C->>DB: Log eval telemetry
    C-->>D: Decision card + SDUI blocks
    D-->>PM: Explainable verdict
```

## Data & Security Model

```mermaid
flowchart LR
    subgraph Clients
        ECOM["E-Com Backend<br/>ecom_role"]
        COP["Copilot Backend<br/>copilot_role"]
        AGT["LangGraph Agent<br/>agent_readonly"]
    end

    subgraph Postgres
        EXP[("experiments")]
        EVT[("universal_events")]
    end

    ECOM -->|"INSERT events<br/>SELECT/UPDATE flags"| EVT
    ECOM -->|"migrations · seed"| EXP

    COP -->|"CRUD"| EXP
    COP -->|"SELECT metrics"| EVT

    AGT -->|"SELECT only<br/>5s statement_timeout"| EVT
    AGT -->|"SELECT only"| EXP

    style AGT fill:#dbeafe,stroke:#2563eb
```

## Experiment Lifecycle (Copilot Features)

```mermaid
flowchart LR
    GOAL["Business Goal"] --> HYP["Generate Hypothesis"]
    HYP --> CFG["Recommend Config<br/>metric · URLs · preflight"]
    CFG --> LAUNCH["Launch / Simulate Traffic"]
    LAUNCH --> MON["Monitor Metrics<br/>auto-refresh dashboard"]
    MON --> ANA["One-Click Analyze"]
    ANA --> VER["Verdict<br/>Scale · Continue · Stop · Rollback"]
    VER --> ACT["Apply Recommendation<br/>traffic split 0% or 100%"]
    ACT --> EVAL["Eval Telemetry<br/>/evals dashboard"]

    style ANA fill:#2563eb,color:#fff
    style VER fill:#2563eb,color:#fff
    style EVAL fill:#0f172a,color:#fff
```

## Key Design Decisions

| Principle | Implementation |
|-----------|----------------|
| **Metric inferred, not configured** | `primary_metric` is NULL at seed; agent discovers events via SQL and picks metric from page diff |
| **Deterministic math** | LLM writes SQL and prose; z-test and verdict rules live in `statistics.py` |
| **Universal telemetry** | Single `universal_events` table — any client POSTs the same event shape |
| **Defense in depth** | Agent uses `agent_readonly` Postgres role; mutations rejected at DB layer |
| **Browser fallback** | Playwright MCP inspects real variant pages; falls back to chat-only if unavailable |
