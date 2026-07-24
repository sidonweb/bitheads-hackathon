# Task 01: Last Updated Timestamp

## Location

- `packages/dashboard/src/App.jsx` — add `lastRefreshedAt` state; set on successful `load()`
- `packages/dashboard/src/components/SimulationMetricsPanel.jsx` — display in header
- Optional: `packages/dashboard/src/lib/formatRelativeTime.js` (new small helper)

## Dependencies

- Existing `load()` callback and `refreshing` flag *(already on main)*
- **Extend only** — do not create new fetch logic

## What to build

1. Add `const [lastRefreshedAt, setLastRefreshedAt] = useState(null)`.
2. In `load()` `.then()` success path (after `setExp` / `setEventMatrix`), call `setLastRefreshedAt(Date.now())`.
3. Pass `lastRefreshedAt` prop to `SimulationMetricsPanel`.
4. Render in expanded panel header: **"Last updated 12s ago"** — update every second via lightweight `setInterval` in panel or parent (clear on unmount).
5. Initial mount: after first successful load, show timestamp (not "Never" if data loaded).

## Design spec

### Header layout (extend existing)

```
Simulation metrics                    [↻ Refresh]
Dynamic event breakdown…              Last updated 8s ago
```

- Relative time: `just now` → `Ns ago` → `Nm ago` (cap at 59m, then clock time for demo)
- Muted text (`sim-metrics-sub` or new `sim-metrics-meta` class)
- Timestamp ticks on 1s interval without triggering new API calls

### Collapsed panel

Optional one-line in collapsed chevron tooltip: "Metrics · updated 5s ago" — nice-to-have, not blocking.

## Done when

- [ ] Successful `load()` updates `lastRefreshedAt`
- [ ] Visible "Last updated Xs ago" in expanded metrics header
- [ ] Counter increments every second locally
- [ ] Manual refresh and 30s poll both update timestamp
- [ ] No second poll loop introduced
