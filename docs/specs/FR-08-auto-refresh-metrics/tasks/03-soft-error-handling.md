# Task 03: Soft Error Handling on Poll Failure

## Location

- `packages/dashboard/src/App.jsx` — extend `load()` catch path
- `packages/dashboard/src/components/SimulationMetricsPanel.jsx` — inline warning banner
- Consider splitting global `error` from metrics-specific `metricsError` if experiment drawer errors should remain global

## Dependencies

- Existing `load()` with `.catch((e) => setError(e.message))` *(current behavior blanks trust — extend)*
- Shipped `eventMatrix` / `exp` state *(preserve on failure)*

## What to build

1. **Extend** `load()`: on fetch failure, do **not** clear `exp`, `eventMatrix`, or `split`.
2. Set `metricsRefreshError` state (string or null) instead of global fatal error for poll failures.
3. Show amber inline banner in metrics panel:
   > Could not refresh metrics. Showing last loaded data.
4. Clear `metricsRefreshError` on next successful `load()`.
5. **404 experiment:** stop polling (clear interval or set `pollStopped`), set global error — this is the one case where stale data is misleading.
6. Distinguish initial load failure (no data yet) vs refresh failure (keep stale) — empty state OK on first load only.

## Design spec

### Error banner (metrics panel only)

```
┌─────────────────────────────────────────────────┐
│ ⚠ Could not refresh metrics. Showing last data. │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  event matrix table (unchanged stale data)      │
└─────────────────────────────────────────────────┘
```

- Amber background `#fef3c7` / border `#f59e0b` (match dashboard warning tokens if defined)
- Does not block manual ↻ retry

### 404 handling

Stop auto-refresh; show experiment missing message at app level; do not loop 404 every 30s.

## Done when

- [ ] Simulated network drop during poll keeps event matrix visible
- [ ] Amber banner appears on refresh failure; clears on successful ↻
- [ ] Initial page load failure still shows appropriate empty/error (no fake stale)
- [ ] 404 stops interval polling
- [ ] Decision/simulate `load()` calls benefit from same soft-error behavior
