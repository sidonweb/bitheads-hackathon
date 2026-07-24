# FR-09: Executive Summary — Test Plan

Minimum 8 detailed test cases. Run against seeded demo (`exp_1`) after stack is up (`docker compose up -d`).

## Prerequisites

- Dashboard at `http://localhost:5174`
- Copilot-backend at `http://localhost:3001`
- Seeded experiment with data that yields a Scale decision (reset + seed per CLAUDE.md)

---

### TC-01: Summary visible on chat-triggered decision

| Field | Value |
|-------|--------|
| **Objective** | Verify executive summary appears whenever Decision card is shown via chat. |
| **Steps** | 1. Open dashboard. 2. Send chat: "Analyze this experiment and submit a decision" (with variant URLs if FR-12 requires). 3. Wait for Decision card. |
| **Expected** | "Executive Summary" heading visible above verdict badge. Exactly 3 bullet points present. |
| **Priority** | P0 |

---

### TC-02: Bullet 1 contains metric and uplift

| Field | Value |
|-------|--------|
| **Objective** | First bullet describes uplift and metric in plain English. |
| **Steps** | Complete TC-01. Read bullet 1. |
| **Expected** | Contains humanized metric name (e.g. "checkout completed" not only `checkout_completed`). Contains signed percentage uplift (e.g. "+2.2%" or similar). References Variant B. |
| **Priority** | P0 |

---

### TC-03: Bullet 2 reflects statistical significance

| Field | Value |
|-------|--------|
| **Objective** | Second bullet states significance correctly for seeded data. |
| **Steps** | Complete TC-01 with default seed (B wins, p < 0.05). |
| **Expected** | Text includes "statistically significant" and a p-value formatted to 4 decimals. Includes sample sizes for A and B (e.g. 5000 / 5000). |
| **Priority** | P0 |

---

### TC-04: Bullet 3 matches verdict

| Field | Value |
|-------|--------|
| **Objective** | Recommendation bullet aligns with verdict badge. |
| **Steps** | Complete TC-01. Compare bullet 3 to verdict badge label. |
| **Expected** | For Scale seed: bullet says "Recommendation: Scale" and badge shows "SCALE". Wording matches mapping table in task 01. |
| **Priority** | P0 |

---

### TC-05: No SQL in executive summary

| Field | Value |
|-------|--------|
| **Objective** | SQL remains in ReasoningExpander only. |
| **Steps** | Complete TC-01. Expand "Show SQL & decision rule" (ReasoningExpander). Compare to executive summary text. |
| **Expected** | Executive summary contains no `SELECT`, `FROM`, `universal_events`, or `sql_used` content. SQL visible only in expander. |
| **Priority** | P0 |

---

### TC-06: Non-significant decision wording

| Field | Value |
|-------|--------|
| **Objective** | Template handles Continue/insufficient significance. |
| **Steps** | 1. Reset demo to low-traffic or equal-conversion scenario (via Experiment drawer simulate/reset). 2. Trigger analysis. 3. If decision is Continue or non-significant p ≥ 0.05, inspect bullet 2. |
| **Expected** | Bullet 2 says "not yet statistically significant" (or equivalent) instead of claiming significance. No false "statistically significant" claim when p ≥ 0.05. |
| **Priority** | P1 |

---

### TC-07: Missing inferred_metric fallback

| Field | Value |
|-------|--------|
| **Objective** | Summary degrades gracefully without inferred metric. |
| **Steps** | 1. Mock or intercept a Decision JSON with `inferred_metric: null` (devtools override or unit test `buildExecutiveSummary`). 2. Render Decision card. |
| **Expected** | Bullet 1 uses fallback phrase "primary success metric" (or similar). Component does not crash. Still 3 bullets. |
| **Priority** | P1 |

---

### TC-08: Copy-paste friendly for Slack/email

| Field | Value |
|-------|--------|
| **Objective** | PM can copy summary for external comms. |
| **Steps** | Select all text in executive summary list. Paste into plain-text editor. |
| **Expected** | Three readable sentences/lines without broken HTML tags or duplicate verdict badges. No markdown artifacts unless FR-11 extended here. |
| **Priority** | P2 |

---

### TC-09: Summary on one-click analyze path (FR-10 integration)

| Field | Value |
|-------|--------|
| **Objective** | Executive summary also appears when decision comes from `/analyze` button, not chat. |
| **Steps** | 1. Use "Run full analysis" button (FR-10). 2. Wait for Decision card. |
| **Expected** | Same Executive Summary block as chat path. No duplicate summary blocks. |
| **Priority** | P1 |
| **Depends on** | FR-10 shipped |

---

### TC-10: Build passes

| Field | Value |
|-------|--------|
| **Objective** | No regressions in dashboard build. |
| **Steps** | `cd packages/dashboard && npm run build` |
| **Expected** | Exit code 0. No unused import warnings for ExecutiveSummary. |
| **Priority** | P0 |
