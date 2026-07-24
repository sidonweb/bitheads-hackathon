# Task 02: Confirmation Modal

## Location

- `packages/dashboard/src/components/ApplyDecisionModal.jsx` — new
- `packages/dashboard/src/App.jsx` or `ChatPanel.jsx` — modal open state

## Dependencies

- Task 01 (apply button triggers open)
- Experiment context: variant names if available (`variant_a_name`, `variant_b_name`)

## What to build

1. Create controlled modal: `open`, `decision`, `onConfirm`, `onCancel`, `loading`.
2. Scale confirmation copy:
   > **Send 100% traffic to Variant B?**
   > This will stop splitting traffic and show Variant B to all new users. Continue?
3. Rollback confirmation copy:
   > **Revert to 100% Variant A?**
   > This will stop the test and route all traffic to the control. Continue?
4. Actions: **Cancel** (secondary) | **Apply** (primary/destructive for Rollback).
5. Trap focus; close on Escape unless `loading`.
6. Block double-submit while PATCH in flight.

## Design spec

### Modal layout

```
        ┌─────────────────────────────────┐
        │  Send 100% traffic to Variant B? │
        │                                  │
        │  This will stop splitting traffic│
        │  and show Variant B to all new   │
        │  users.                          │
        │                                  │
        │     [ Cancel ]    [ Apply ]      │
        └─────────────────────────────────┘
```

- Overlay: semi-transparent backdrop (`rgba(0,0,0,0.4)`)
- Max width ~420px, centered
- Use existing modal patterns from `SessionModals.jsx` for consistency

### Accessibility

- `role="dialog"`, `aria-modal="true"`, `aria-labelledby` on title
- Initial focus on Cancel; Apply confirms on Enter only when focused

## Done when

- [ ] Clicking Apply on Decision card opens modal with decision-specific copy
- [ ] Cancel closes without API call
- [ ] Confirm invokes `onConfirm` callback once
- [ ] Modal cannot be dismissed by backdrop click while `loading`
- [ ] Keyboard Escape closes when idle
