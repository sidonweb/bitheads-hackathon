# Task 05: Wire decision state + error display

## Location

- `packages/dashboard/src/App.jsx` (modify)
- `packages/dashboard/src/components/ExperimentDrawer.jsx` (modify — error prop already exists)
- `packages/dashboard/src/components/ChatPanel.jsx` (verify — no changes expected)

## Dependencies

- Task 04: analyze button handler
- Existing `onDecision` in `App.jsx` (line ~143)
- FR-05 error envelope from backend

## What to build

Connect analyze success to global decision state and display FR-05-compatible errors in the drawer (and optionally a toast).

## Design spec

### Success wiring

`App.jsx` already has:

```js
const onDecision = (d) => { setDecision(d); ... };
```

Pass `onDecision` to `ExperimentDrawer` (or call from analyze handler in App):

- On analyze success → `onDecision(decision)` — Decision card renders in `ChatPanel` scroll area.
- Optionally scroll chat to decision (`ChatPanel` already scrolls on `decision` change via `useEffect`).

### Error display

Use existing `error` / `setError` pattern in drawer:

```jsx
{error && <p className="error drawer-error">⚠ {error}</p>}
```

Map error codes to friendly copy when helpful:

| Code | UI message hint |
|------|-----------------|
| `VALIDATION_ERROR` | Fix URL fields |
| `AGENT_TOOL_LIMIT` | Try again; agent hit tool budget |
| `AGENT_NO_DECISION` | Analysis incomplete — retry |
| `LLM_UNAVAILABLE` | Copilot temporarily unavailable |

Show `retryable: true` errors with suggestion "Try again" in message.

### Chat vs analyze independence

- Analyze errors do **not** add assistant error bubbles to chat (drawer-only unless product decides otherwise).
- Chat `busy` and analyze `analyzeBusy` may be separate flags to allow chat during analyze (optional) — default: share busy to avoid concurrent agent runs.

### Preflight (optional, non-blocking)

If FR-03 preflight endpoint exists:

- Before analyze, optionally `GET /preflight?variantAUrl=…` — warn in drawer if soft fails; do not block unless G3 decides block.

## Done when

- [ ] Successful analyze populates Decision card identical to chat-triggered decision.
- [ ] 422 missing URLs shows clear message in drawer, not console-only.
- [ ] Agent limit / 502 errors show user-friendly text per FR-05.
- [ ] `onDecision` not called on failure; previous decision cleared or preserved (product choice: **preserve** previous decision on failure).
