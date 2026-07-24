# FR-10: One-Click Analyze — Test Plan

Minimum 8 detailed test cases. Requires FR-12 backend (URLs in body) deployed.

## Prerequisites

- Full stack running (`docker compose up -d --build`)
- Dashboard `http://localhost:5174`
- Valid variant URLs for demo storefront (user-entered):
  - A: `http://localhost:5173/?variant=A`
  - B: `http://localhost:5173/?variant=B`

---

### TC-01: Happy path — button triggers full analysis

| Field | Value |
|-------|--------|
| **Objective** | One-click analyze completes and shows Decision without chat. |
| **Steps** | 1. Open Experiment drawer. 2. Enter both variant URLs. 3. Click "Run full analysis". 4. Wait for completion. |
| **Expected** | Decision card appears in chat panel area. Verdict badge populated (e.g. SCALE on seed). No new user chat bubble created. |
| **Priority** | P0 |

---

### TC-02: Double-click prevention

| Field | Value |
|-------|--------|
| **Objective** | Rapid double-click does not fire duplicate analyze requests. |
| **Steps** | 1. Enter URLs. 2. Click "Run full analysis" twice quickly. 3. Monitor network tab or backend logs. |
| **Expected** | Only one `POST /analyze` request. Button disabled after first click until response. |
| **Priority** | P0 |

---

### TC-03: Loading state visible

| Field | Value |
|-------|--------|
| **Objective** | User sees in-progress feedback during long agent run. |
| **Steps** | 1. Start analyze. 2. Observe button before response returns. |
| **Expected** | Button shows loading label/spinner and is disabled. Cannot submit chat or second analyze (if shared busy). |
| **Priority** | P0 |

---

### TC-04: Missing Variant A URL — client validation

| Field | Value |
|-------|--------|
| **Objective** | UI blocks analyze when URL A empty. |
| **Steps** | 1. Leave Variant A URL blank. 2. Fill Variant B URL. 3. Attempt click. |
| **Expected** | Button disabled **or** immediate inline error; no network request. |
| **Priority** | P0 |

---

### TC-05: Missing URLs — backend 422

| Field | Value |
|-------|--------|
| **Objective** | API returns structured validation error when body incomplete. |
| **Steps** | `curl -s -X POST localhost:3001/experiments/exp_1/analyze -H 'Content-Type: application/json' -d '{}'` |
| **Expected** | HTTP 422. Body includes `error.code: VALIDATION_ERROR` and message about required URLs. Agent does not hang. |
| **Priority** | P0 |

---

### TC-06: FR-12 — no silent DB URL injection

| Field | Value |
|-------|--------|
| **Objective** | Analyze uses request body URLs, not DB defaults alone. |
| **Steps** | 1. POST analyze with custom URLs (even invalid host) in body. 2. Check agent logs / Playwright attempt. |
| **Expected** | Agent prompt contains exact URLs from request body. Does not substitute `experiments.variant_a_url` when body omits them (422 instead). |
| **Priority** | P0 |
| **Depends on** | FR-12 |

---

### TC-07: Structured error on agent failure

| Field | Value |
|-------|--------|
| **Objective** | FR-05 errors display in UI, not stack traces. |
| **Steps** | 1. Simulate failure (invalid OpenAI key, or mock AGENT_TOOL_LIMIT). 2. Run analyze from UI. |
| **Expected** | Drawer shows `⚠` error with human-readable message. No raw Python traceback in UI. Optional retry hint if `retryable: true`. |
| **Priority** | P1 |

---

### TC-08: Decision parity with chat path

| Field | Value |
|-------|--------|
| **Objective** | Analyze button produces same Decision shape as chat analysis. |
| **Steps** | 1. Run analyze via button. 2. Note fields: decision, p_value, uplift, inferred_metric, reasoning. 3. Clear chat, run via chat with URLs. |
| **Expected** | Same JSON fields rendered in Decision card. Executive summary (FR-09) appears if shipped. |
| **Priority** | P1 |

---

### TC-09: Invalid URL format — client hint

| Field | Value |
|-------|--------|
| **Objective** | Malformed URLs caught before or at API. |
| **Steps** | Enter `not-a-url` in Variant A field. Attempt analyze. |
| **Expected** | Inline validation message or 422 VALIDATION_ERROR. No hung browser inspection. |
| **Priority** | P2 |

---

### TC-10: Build and smoke curl

| Field | Value |
|-------|--------|
| **Objective** | Regression check. |
| **Steps** | 1. `cd packages/dashboard && npm run build`. 2. `curl -X POST .../analyze` with valid URLs. |
| **Expected** | Build exit 0. Curl returns 200 Decision JSON. |
| **Priority** | P0 |
