# Task 04: Run full analysis button + loading UX

## Location

- `packages/dashboard/src/components/ExperimentDrawer.jsx` (modify) **or**
- `packages/dashboard/src/App.jsx` (header toolbar — choose one primary placement)

Recommended: **Experiment drawer** — groups URLs + analyze action.

## Dependencies

- Task 02: `analyze()` API client
- Task 03: URL fields populated
- FR-05: structured errors (for display in task 05)

## What to build

Primary action button **"Run full analysis"** that triggers the full agent workflow without posting a chat message.

## Design spec

### Button behavior

| State | Label | Enabled |
|-------|-------|---------|
| Idle | `Run full analysis` | Both URLs valid, not busy |
| In flight | `Analyzing…` + spinner | Disabled |
| After success | `Run full analysis` | Re-enabled |

- Use existing `.btn` / `.btn-secondary` or primary variant consistent with drawer actions.
- Place below URL inputs in drawer section "Analysis".

### Click handler

```js
setAnalyzeBusy(true);
setError('');
try {
  const decision = await analyze({ variantAUrl, variantBUrl });
  onDecision(decision);
} catch (e) {
  setError(e.message); // or structured banner
} finally {
  setAnalyzeBusy(false);
}
```

### Double-click prevention

- `disabled={analyzeBusy || !urlsValid || simBusy || resetBusy}` on button.
- Ignore clicks while `analyzeBusy === true` (guard at start of handler).

### Loading indicator

- Inline spinner on button text **or** reuse chat "Analyzing variants…" pattern in a drawer status line.
- Do not block entire dashboard — only disable analyze button and optionally chat composer if shared busy flag.

### Separation from chat

- **Do not** append a user message to chat history.
- **Do not** call `chat()` API.
- Decision appears in existing Decision card slot in `ChatPanel` via `onDecision` callback (same as chat path).

## Done when

- [ ] Clicking button runs `/analyze` and shows Decision card without new chat turn.
- [ ] Button disabled while request in flight; second click ignored.
- [ ] Spinner/label indicates progress during 10–60s agent run.
- [ ] Works with URLs typed in drawer (demo: `http://localhost:5173/?variant=A` and `?variant=B`).
