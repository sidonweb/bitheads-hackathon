# Refinement Worksheet

Use this before marking any FR as **Approved**. Review as a team; edit FR files in place when decisions are made.

> Synced with `main` @ `fd65a9d` (2026-07-25).

## Global decisions (answer once)

| # | Question | Decision |
|---|----------|----------|
| G1 | Implement order: FR-05 first (guardrails) before FR-04? | ☐ Yes ☐ No |
| G2 | Keep non-streaming `/chat` as fallback when FR-06 ships? | ☐ Yes ☐ No |
| G3 | Pre-flight (FR-03) block `/analyze` on hard fails? | ☐ Block ☐ Warn only |
| G4 | New code under `app/services/` for non-agent logic? | ☐ Yes ☐ No |
| G5 | Combined "Create experiment" API (FR-01 + FR-02) or separate endpoints? | ☐ Combined ☐ Separate |
| G6 | **URL model:** User input only — chat and/or explicit API body. No DB defaults, no prompt hardcoding. | ☑ **Decided: [FR-12](./FR-12-dynamic-variant-urls/requirements.md)** |
| G7 | **One-shot analyze:** URLs required in request body; 422 if missing. | ☑ **Decided: request body required** |
| G8 | **DB agent:** Fully dynamic schema discovery; remove hardcoded SQL from main prompt. | ☑ **Decided: [FR-04](./FR-04-sql-data-agent/requirements.md)** |
| G9 | **Chat UI:** Render assistant markdown. | ☑ **Decided: [FR-11](./FR-11-chat-markdown-ui/requirements.md)** |

## Already on main (do not re-implement)

- [x] Per-session chat isolation (`sessionId` + LangGraph thread)
- [x] Dashboard session sidebar (new/rename/pin/delete)
- [x] Event matrix API + `SimulationMetricsPanel`
- [x] 30s metrics poll in `App.jsx` (FR-08 core)
- [x] Topic scope guardrail in agent system prompt (partial FR-05)
- [x] `inspect_variant_pages` + checkout deep link (`?screen=checkout`)
- [x] Demo chat thread reset (`POST /demo/clear-chat`)

## Per-FR approval

| FR | Approve? | Owner | Notes |
|----|----------|-------|-------|
| FR-01 | ☐ | | |
| FR-02 | ☐ | | |
| FR-03 | ☐ | | Align C1/C2 with G6 |
| FR-04 | ☐ | | |
| FR-05 | ☐ | | Prompt guardrail exists; need tool budget + error shape |
| FR-06 | ☐ | | Must pass `sessionId` |
| FR-07 | ☐ | | |
| FR-08 | ☐ | | **Partial** — approve polish items only |
| FR-09 | ☐ | | |
| FR-10 | ☐ | | Requires URLs in analyze body (G7) |
| FR-11 | ☐ | | Markdown in ChatPanel |
| FR-12 | ☐ | | Remove `_deep_link_checkout` auto-assumption |

## Recommended implementation phases

### Phase 0 — Foundation (do first)

- FR-12 Dynamic variant URLs (prompt + `_deep_link_checkout` cleanup)
- FR-05 Agent guardrails & errors
- FR-11 Chat markdown UI (quick UX win)
- [00-engineering-standards.md](./00-engineering-standards.md) error shape in routes + dashboard

### Phase 1 — Lifecycle (problem statement breadth)

- FR-01 Hypothesis from goals
- FR-03 Pre-flight validation (respect chat-driven URL model per G6)
- FR-02 Metric recommendations (can follow FR-01)

### Phase 2 — Intelligence depth

- FR-04 SQL data sub-agent (dynamic schema; strip biased SQL from main prompt)
- FR-10 One-click Analyze (UI + G7 backend fix)

### Phase 3 — UX polish

- FR-08 Auto-refresh polish (last-updated, pause toggle — core poll already done)
- FR-07 Apply recommendation
- FR-09 Executive summary
- FR-06 Streaming chat (if time)

## Cut line if running out of time

**Must ship:** FR-12, FR-05, FR-04, FR-11, FR-01, FR-03, FR-07

**Nice to have:** FR-08 polish, FR-10, FR-09

**Defer:** FR-06

**Skip (already on main):** Session sidebar, event matrix table, 30s polling

## Open questions backlog

Consolidate all "Open questions" sections from individual FRs here during review:

1. G6 — Where do preflight and analyze get variant URLs when PM only pasted them in chat?
2. G7 — `/analyze` currently sends no URLs; agent will ask or fail — fix before demo?
3. Should FR-02 duplicate agent metric inference or complement it (save inferred metric to DB)?

## Definition of Done (all FRs)

- [ ] Code merged on feature branch
- [ ] Acceptance criteria checked manually
- [ ] Error path tested once
- [ ] No secrets in logs/responses
- [ ] FR status updated to Done in [README.md](./README.md)
