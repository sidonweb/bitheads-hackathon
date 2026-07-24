# Task 04: Guardrails + Disabled States

## Location

- `packages/dashboard/src/components/Decision.jsx`
- `packages/dashboard/src/App.jsx` — pass `experiment.status`, optional preflight flag

## Dependencies

- Task 01–03 (apply flow complete)
- Experiment object: `status`, `traffic_split`

## What to build

1. **Continue / Stop:** No apply button; optional muted line: "No traffic change recommended."
2. **Already applied:** If current `traffic_split` matches target (Scale + split=100, Rollback + split=0), show "Traffic already matches recommendation" and disable button.
3. **Experiment not running:** If `experiment.status !== 'running'`, disable apply with tooltip: "Experiment is not running."
4. **Loading:** Disable apply button while modal PATCH in flight.
5. **Optional (FR-03 link):** If preflight critical fails exposed on experiment, disable with link "Fix preflight issues first."

## Design spec

### Disabled tooltip examples

| Condition | Tooltip |
|-----------|---------|
| Continue verdict | "Continue means keep the test running — no apply action." |
| Stop verdict | "Stop means no traffic change." |
| status ≠ running | "Start or resume the experiment to apply traffic changes." |
| split already 100 (Scale) | "Variant B is already at 100% traffic." |

### Visual treatment

Disabled button: `opacity: 0.5`, `cursor: not-allowed`, `title` or visible helper text below button.

Do **not** auto-apply on Scale decision arrival — always require explicit click + confirm.

## Done when

- [ ] Continue/Stop never show enabled apply button
- [ ] Apply disabled when traffic already matches recommendation
- [ ] Non-running experiment blocks apply with clear message
- [ ] No silent PATCH on decision render
- [ ] Manual test: Scale → Apply → second Apply on same card stays disabled/applied
