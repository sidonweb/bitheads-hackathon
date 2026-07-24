# Task 01: Apply Button on Decision Card

## Location

- `packages/dashboard/src/components/Decision.jsx`
- `packages/dashboard/src/components/ChatPanel.jsx` — pass new props through

## Dependencies

- Existing `Decision` component and verdict badge styles
- Decision object shape from analyze/chat (`decision.decision` ∈ Scale | Rollback | Continue | Stop)

## What to build

1. Add optional props to `Decision`: `onApply`, `applyState` (`idle` | `loading` | `applied` | `error`), `experimentStatus`.
2. Render primary CTA only when `decision.decision === 'Scale'` or `'Rollback'`:
   - Scale: **"Apply Scale — roll out Variant B"** (green outline or solid)
   - Rollback: **"Apply Rollback — revert to Variant A"** (red outline)
3. Hide button entirely for Continue / Stop (or show disabled with tooltip — see Task 04).
4. Wire `onClick` → parent opens confirmation modal (Task 02), not PATCH directly.

## Design spec

### Decision card footer (Scale)

```
┌─────────────────────────────────────────────┐
│ SCALE                          92.0% conf   │
│ Roll Variant B out to everyone.             │
│ … stats … reasoning …                       │
├─────────────────────────────────────────────┤
│  [ Apply Scale — roll out Variant B ]       │  ← full-width on mobile
└─────────────────────────────────────────────┘
```

### Rollback variant

Same layout; button copy and color use destructive palette (`#dc2626` border/text).

### Applied state

After successful apply, button becomes **"Applied ✓"** disabled for this decision instance (until new decision arrives).

## Done when

- [ ] Scale and Rollback cards show apply button with correct copy
- [ ] Continue and Stop cards show no apply button (or disabled per Task 04)
- [ ] Button does not call API directly — delegates to parent modal flow
- [ ] Visual style matches existing dashboard buttons (`btn`, `btn-primary`)
