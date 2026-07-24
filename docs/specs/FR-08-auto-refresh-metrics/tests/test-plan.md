# FR-08: Auto-Refresh Metrics — Test Plan

Manual tests. **Extend** existing behavior — verify baseline (30s poll, manual ↻) still works after changes.

Baseline reference: `packages/dashboard/src/App.jsx` lines ~83–102, `SimulationMetricsPanel.jsx`.

---

## Already shipped (regression)

### T1 — 30s auto-poll still works

**Steps:** Mount dashboard with metrics expanded; note event counts; wait 35s without interaction; optionally simulate traffic.

**Expected:** `GET /experiments/exp_1` fires ~every 30s; matrix updates if backend data changed.

**Pass:** Single poll loop in Network tab; no duplicate intervals.

---

### T2 — Manual refresh unchanged

**Steps:** Click ↻ Refresh in metrics panel.

**Expected:** Immediate `GET`; `refreshing` shows "Refreshing…"; data updates.

**Pass:** Same behavior as pre-FR-08 polish.

---

### T3 — Refresh after decision/simulate

**Steps:** Run chat analysis or demo simulate.

**Expected:** `load()` called from `onDecision` / `onSimulateComplete`; metrics update.

**Pass:** No regression in App.jsx callbacks.

---

## New polish (FR-08 remaining)

### T4 — Last updated timestamp appears

**Steps:** Load dashboard; expand metrics panel.

**Expected:** "Last updated just now" or "Ns ago" visible in header after first fetch.

**Pass:** Timestamp present; updates after poll and manual refresh.

---

### T5 — Relative time ticks locally

**Steps:** Wait 10s without new fetch.

**Expected:** Display changes from "just now" → "10s ago" without extra API calls.

**Pass:** 1s local tick only.

---

### T6 — Pause stops auto-poll

**Steps:** Turn auto-refresh off; wait 60s.

**Expected:** No periodic GET requests; last updated time stops advancing unless manual refresh.

**Pass:** Interval gated; only one timer registered.

---

### T7 — Manual refresh works while paused

**Steps:** Pause auto-refresh; click ↻.

**Expected:** Fetch runs; matrix and "Last updated" update.

**Pass:** Manual path independent of pause flag.

---

### T8 — Pause preference persists

**Steps:** Pause auto-refresh; hard reload page.

**Expected:** Still paused after reload.

**Pass:** `localStorage` key read on init.

---

### T9 — Failed poll keeps stale data

**Steps:** Load metrics successfully; stop copilot-backend; wait for auto-poll or click ↻.

**Expected:** Event matrix remains visible with previous numbers; amber banner "Could not refresh metrics…"

**Pass:** `eventMatrix` not nulled; no full-page error replacing metrics.

---

### T10 — Successful refresh clears metrics error

**Steps:** After T9, restart copilot-backend; click ↻.

**Expected:** Banner clears; fresh data loads; timestamp updates.

**Pass:** `metricsRefreshError` reset on success.

---

### T11 — Initial load failure (no stale)

**Steps:** Start dashboard with copilot-backend down (fresh session).

**Expected:** Empty/error state appropriate — no fake "stale" banner with empty table.

**Pass:** Distinguish first load vs refresh failure.

---

### T12 — 404 stops polling

**Steps:** Point `VITE_EXPERIMENT_ID` to nonexistent id or mock 404.

**Expected:** Polling stops; experiment missing message; no 404 every 30s.

**Pass:** Interval cleared or gated permanently.

---

### T13 — Refresh pulse on success

**Steps:** Observe header on successful ↻ with motion enabled.

**Expected:** Subtle pulse on timestamp or icon (~600ms).

**Pass:** Pulse on success only.

---

### T14 — Reduced motion

**Steps:** Enable OS "reduce motion"; trigger refresh.

**Expected:** Timestamp updates; no pulse animation.

**Pass:** `prefers-reduced-motion` respected.

---

### T15 — Optional env interval (Task 05)

**Steps:** Set `VITE_METRICS_POLL_MS=10000`; rebuild dashboard; open with auto-refresh on.

**Expected:** GET ~every 10s; UI may show "every 10s".

**Pass:** Clamped env works; invalid values fall back to 30s.

---

## Sign-off checklist

- [ ] T1–T3 regression (shipped behavior intact)
- [ ] T4–T8 last updated + pause
- [ ] T9–T12 error handling
- [ ] T13–T14 pulse
- [ ] T15 env (if Task 05 implemented)
- [ ] FR-08 acceptance criteria complete
