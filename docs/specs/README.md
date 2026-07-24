# Feature Specs — Experiment Copilot v1.5

All feature documentation lives in **`docs/specs/`** — requirements (what/why), implementation specs (how), tasks, and test plans in one place per FR.

> **Last synced with `main`:** 2026-07-25 (`fd65a9d`) — review [Baseline on main](#baseline-on-main) before approving FRs.

## How to use

1. Read [00-engineering-standards.md](./00-engineering-standards.md) first (applies to all features).
2. Read [Baseline on main](#baseline-on-main) — several capabilities shipped since FRs were first written.
3. Open a feature folder — start with `requirements.md` (what/why), then `index.md` (how).
4. Implement `tasks/` in order; run cases in `tests/test-plan.md`.
5. Mark status: `Draft` → `Approved` → `In Progress` → `Done`.
6. Use [REFINEMENT.md](./REFINEMENT.md) for team approval and implementation order.

## Folder structure

```
docs/specs/
  README.md
  00-engineering-standards.md
  REFINEMENT.md
  FR-XX-feature-name/
    requirements.md       # What/why (original FR doc)
    index.md              # Overview, architecture, task index, acceptance criteria
    tasks/
      01-….md             # Location · build spec · design spec · done-when
    tests/
      test-plan.md        # Manual + edge + regression cases
```

## Feature index

| FR | Folder | Priority | Tasks | Tests | Status |
|----|--------|----------|-------|-------|--------|
| FR-01 | [hypothesis-from-goals](./FR-01-hypothesis-from-goals/) | P0 | 5 | 12 | Draft |
| FR-02 | [metric-config-recommendations](./FR-02-metric-config-recommendations/) | P0 | 5 | 12 | Draft |
| FR-03 | [preflight-validation](./FR-03-preflight-validation/) | P0 | 5 | 12 | Draft |
| FR-04 | [sql-data-agent](./FR-04-sql-data-agent/) | P0 | 6 | 12 | Draft |
| FR-05 | [agent-guardrails-errors](./FR-05-agent-guardrails-errors/) | P0 | 6 | 12 | Draft |
| FR-06 | [streaming-chat](./FR-06-streaming-chat/) | P1 | 5 | 14 | Draft |
| FR-07 | [apply-recommendation](./FR-07-apply-recommendation/) | P1 | 4 | 13 | Draft |
| FR-08 | [auto-refresh-metrics](./FR-08-auto-refresh-metrics/) | P1 | 5 | 15 | **Partial** |
| FR-09 | [executive-summary](./FR-09-executive-summary/) | P2 | 4 | 10 | Draft |
| FR-10 | [one-click-analyze](./FR-10-one-click-analyze/) | P2 | 5 | 10 | Draft |
| FR-11 | [chat-markdown-ui](./FR-11-chat-markdown-ui/) | P1 | 5 | 12 | Draft |
| FR-12 | [dynamic-variant-urls](./FR-12-dynamic-variant-urls/) | P0 | 6 | 12 | Done |
| FR-13 | [sdui-chat-widgets](./FR-13-sdui-chat-widgets/) | P1 | 7 | 13 | Draft |

**Effort:** XS < 30m · S 30–60m · M 1–2h · L 2h+

## Implementation order

See [REFINEMENT.md](./REFINEMENT.md) — start with **FR-12 → FR-05 → FR-11 → FR-04**.

## Baseline on main

These are **already shipped** on `main` and are **not** separate FR work (but FRs must align with them):

| Area | What exists | Implication for FRs |
|------|-------------|---------------------|
| **Agent URLs** | Variant URLs come from **PM chat**, not experiment config | FR-03 URL checks need request-body or optional stored URLs; FR-10 `/analyze` must supply URLs |
| **Browser tool** | Single `inspect_variant_pages` tool (persistent Playwright session) | FR-04/FR-06 tool labels should use this name |
| **Topic guardrail** | System prompt declines off-topic questions | Partial overlap with FR-05; still need structured errors + tool budget |
| **Session isolation** | `ChatIn.sessionId` → LangGraph thread `{exp_id}:{session_id}` | FR-06 streaming must pass `sessionId` |
| **Dashboard sessions** | SessionSidebar, rename/pin/delete, localStorage | Out of scope for FRs |
| **Event matrix** | `GET /experiments/{id}` returns `eventMatrix` | Complements FR-08 |
| **Auto-refresh** | `App.jsx` polls every 30s while mounted | **FR-08 partially done** — polish only |
| **Demo reset** | `POST /demo/clear-chat` clears agent threads when `DEMO_MODE` | No FR needed |

## Cross-cutting docs

| Document | Scope |
|----------|--------|
| [00-engineering-standards.md](./00-engineering-standards.md) | Errors, guardrails, API contracts, logging, security |
| [FR-05 requirements](./FR-05-agent-guardrails-errors/requirements.md) | Agent tool limits, graceful failures, user messaging |
| [REFINEMENT.md](./REFINEMENT.md) | Team approval worksheet, phases, cut line |

## Architecture (current)

```
dashboard (5174)  →  copilot-backend (3001)  →  Postgres
ecom-web (5173)   →  ecom-backend (3002)     →  Postgres (events)
copilot-backend   →  playwright-mcp (8931)   →  variant URLs (from chat)
```

**Agent workflow:** PM pastes variant A/B URLs in chat → `inspect_variant_pages` → infer metric from page diff + event data → aggregate → `run_statistics` → `submit_decision`.

Determinism boundary: **LLM explains and orchestrates; Python computes stats and verdicts.**

## Explicitly out of scope (v1.5)

- Live raw event stream / CleverTap-style feed
- Real audience segmentation enforcement
- Multi-tenant auth
- Full feature-flag platform integration
- Automated overlap resolution across many experiments
- Playwright journey auto-discovery (rolled back on main)
