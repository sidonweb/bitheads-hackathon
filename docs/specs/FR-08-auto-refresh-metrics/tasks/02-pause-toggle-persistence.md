# Task 02: Pause Toggle + localStorage Persistence

## Location

- `packages/dashboard/src/App.jsx` — extend existing `setInterval` effect
- `packages/dashboard/src/components/SimulationMetricsPanel.jsx` — toggle UI in header
- `packages/dashboard/src/lib/metricsPrefs.js` (new) — `readAutoRefresh()`, `saveAutoRefresh(bool)`

## Dependencies

- Task 01 (header space for toggle)
- Existing interval: `useEffect(() => { const id = setInterval(() => { load(); }, 30_000); ... }, [load])`

## What to build

1. Add state `autoRefreshEnabled` defaulting from `localStorage` key `copilot_metrics_auto_refresh_v1` (default `true`).
2. **Extend** interval effect: only call `load()` on tick when `autoRefreshEnabled`.
3. Add toggle in metrics panel header: **"Auto-refresh on"** / **"Auto-refresh off"** (switch or pill button).
4. On toggle: update state + `localStorage`; do not cancel manual ↻ refresh.
5. When paused, show subtle hint: "Auto-refresh paused · manual refresh still available."

## Design spec

### Toggle control

```
[ Auto-refresh ●——○ ]   Last updated 22s ago
        on

[ Auto-refresh ○——● ]   Last updated 22s ago (paused)
        off
```

- Persist across page reloads
- Pausing clears only automatic ticks — initial `load()` on mount still runs

### Interval behavior (extend, not replace)

```javascript
// Pseudocode — modify existing effect
setInterval(() => {
  if (autoRefreshEnabled) load();
}, METRICS_POLL_INTERVAL_MS);
```

**Do not** register a second `setInterval`.

## Done when

- [ ] Toggle visible in expanded metrics panel
- [ ] Paused state stops 30s polls (verify via Network tab — no periodic GET)
- [ ] Manual ↻ still calls `load()` when paused
- [ ] Preference survives browser refresh
- [ ] Resuming auto-refresh restores interval without page reload
