# Task 03: PATCH Wiring + Success Feedback

## Location

- `packages/dashboard/src/App.jsx` — `handleApplyDecision`, `split` state sync
- `packages/dashboard/src/api.js` — existing `setTrafficSplit()`
- `packages/dashboard/src/components/ChatPanel.jsx` — wire handlers to `Decision`
- `packages/dashboard/src/components/ExperimentDrawer.jsx` — receives updated `split` prop

## Dependencies

- Task 02 (confirm triggers PATCH)
- Existing `onSplitCommit` / `setTrafficSplit(EXPERIMENT_ID, value)`

## What to build

1. Implement `handleApplyDecision(decision)` in App:
   - Scale → `setTrafficSplit(id, 100)`
   - Rollback → `setTrafficSplit(id, 0)`
2. On success:
   - `setSplit(100 | 0)`
   - Toast: "Variant B is now at 100% traffic." / "Reverted to 100% Variant A."
   - Mark decision apply state `applied`
   - Optional: call `load()` to refresh experiment summary
3. On failure:
   - Parse error from `setTrafficSplit` (improve message in `api.js` if body has `error.message`)
   - Set apply state `error` with message on Decision card
   - Do not update slider on failure
4. Experiment drawer traffic slider reflects new split immediately without reopen.

## Design spec

### Success toast

Transient banner top-right or above chat (match existing error strip pattern if any):

```
✓ Variant B is now at 100% traffic.
```

Auto-dismiss after 4s; dismissible.

### Error on card

```
┌─────────────────────────────────────────────┐
│ [ Apply Scale — roll out Variant B ]        │
│ ⚠ Could not update traffic. Try again.      │
└─────────────────────────────────────────────┘
```

### State sync

```
PATCH success → split state → ExperimentDrawer slider → flag API (ecom-backend) on next user assignment
```

No second PATCH from drawer unless user manually adjusts slider afterward.

## Done when

- [ ] Confirming Scale sets traffic to 100; drawer slider shows 100
- [ ] Confirming Rollback sets traffic to 0; drawer slider shows 0
- [ ] Success toast appears and auto-dismisses
- [ ] Simulated PATCH failure (stop copilot-backend) shows inline error, slider unchanged
- [ ] `npm run build` passes
