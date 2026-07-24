# FR-07: Apply Recommendation — Test Plan

Manual tests. Stack running with seeded `exp_1` (Variant B wins on analyze → Scale).

---

## Happy path

### T1 — Scale shows apply button

**Steps:** Run analysis via chat or `curl -X POST localhost:3001/experiments/exp_1/analyze`. View Decision card in dashboard.

**Expected:** Verdict Scale; button "Apply Scale — roll out Variant B" visible.

**Pass:** Button present with correct label.

---

### T2 — Continue hides apply button

**Steps:** Use demo scenario or simulate data yielding Continue verdict (non-significant).

**Expected:** No apply button, or disabled with explanatory tooltip.

**Pass:** No way to PATCH traffic from Continue card.

---

### T3 — Confirmation modal gates action

**Steps:** Click Apply on Scale card.

**Expected:** Modal with 100% Variant B warning; traffic unchanged until Confirm.

**Pass:** Cancel closes modal with split unchanged; Confirm proceeds.

---

### T4 — Apply Scale sets traffic to 100

**Steps:** Confirm Scale apply with split initially 50.

**Expected:** PATCH succeeds; toast success; drawer slider at 100; `GET /experiments/exp_1` shows `traffic_split: 100`.

**Pass:** UI and API agree.

---

### T5 — Apply Rollback sets traffic to 0

**Steps:** Obtain Rollback decision (demo scenario or inverted simulate). Apply Rollback.

**Expected:** `traffic_split: 0`; toast mentions Variant A; slider at 0.

**Pass:** Matches behavior matrix.

---

### T6 — Drawer slider sync without reopen

**Steps:** Apply Scale with drawer closed. Open experiment drawer.

**Expected:** Slider already at 100; no stale 50 display.

**Pass:** `split` state propagated from App.

---

## Failure & edge cases

### T7 — PATCH failure surfaces message

**Steps:** Stop copilot-backend or block network; confirm Apply.

**Expected:** Inline error on Decision card; no toast success; slider unchanged.

**Pass:** User-visible error; no silent fail.

---

### T8 — Double-click / double confirm

**Steps:** Rapidly double-click Apply in modal.

**Expected:** Single PATCH request; button shows loading; no duplicate requests in Network tab.

**Pass:** Idempotent UI during loading.

---

### T9 — Already at target traffic

**Steps:** Manually set split to 100 in drawer; run Scale decision; view Apply button.

**Expected:** Button disabled or "already applied" with explanation.

**Pass:** No redundant PATCH on click.

---

### T10 — Experiment not running (if status field used)

**Steps:** Set experiment `status` to non-running via DB or PATCH if supported; view Scale decision.

**Expected:** Apply disabled with tooltip.

**Pass:** Guardrail prevents PATCH.

---

### T11 — Rollback button destructive styling

**Steps:** View Rollback decision card.

**Expected:** Apply button uses destructive color; modal warns about reverting to Variant A.

**Pass:** Visual distinction from Scale.

---

### T12 — Applied state persists for session

**Steps:** Apply Scale successfully; scroll chat; return to same decision card.

**Expected:** "Applied ✓" or disabled applied state until new analysis replaces decision.

**Pass:** No second accidental apply.

---

## Regression

### T13 — Manual slider still works

**Steps:** After Apply, open drawer and manually set split to 50.

**Expected:** PATCH from drawer still works independently of apply feature.

**Pass:** No conflict with `onSplitCommit`.

---

## Sign-off checklist

- [ ] T1–T6 happy path
- [ ] T7–T12 edge cases
- [ ] T13 regression
- [ ] FR-07 acceptance criteria complete
