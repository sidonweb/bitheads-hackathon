# FR-08: Auto-Refresh Metrics

| Field | Value |
|-------|--------|
| Status | **Partial** |
| Priority | P1 |
| Problem statement | Continuously monitors experiment performance |
| Depends on | Existing GET `/experiments/{id}` |
| Blocks | — |

## Main branch context (already shipped)

| Item | Location | Status |
|------|----------|--------|
| 30s poll while dashboard mounted | `packages/dashboard/src/App.jsx` (`setInterval(..., 30_000)`) | ✅ Done |
| Manual refresh on metrics panel | `SimulationMetricsPanel` ↻ button | ✅ Done |
| Event matrix (variant × event counts) | `GET /experiments/{id}` → `eventMatrix`; `build_event_matrix()` | ✅ Done |
| Refresh after decision / simulate | `onDecision`, `onSimulateComplete` call `load()` | ✅ Done |

**Remaining work** is UX polish only — do not rebuild polling from scratch.

## Summary

Dashboard polls experiment data every N seconds while the copilot page is mounted. Shows last-updated timestamp and optional pause. **No raw event stream** (explicitly out of scope).

## Goals

- Metrics feel live without manual refresh.
- Low server load with sane interval.
- PM sees **when** data was last fetched (not yet on main).

## Non-goals

- WebSocket push from backend.
- CleverTap-style event feed.
- Alerting / anomaly detection (future).
- Replacing `SimulationMetricsPanel` / event matrix (already shipped).

## Configuration

```javascript
// dashboard — already in App.jsx
const METRICS_POLL_INTERVAL_MS = 30_000;
```

Optional env: `VITE_METRICS_POLL_MS` (not yet wired).

## UI (remaining polish)

- [ ] "Last updated Xs ago" in metrics panel header or experiment drawer
- [ ] Optional pause toggle "Auto-refresh on/off" (persist preference in localStorage)
- [ ] On fetch error: keep stale data + amber "Could not refresh metrics" (currently `setError` on load failure may blank loading state — soften)
- [ ] Subtle pulse or timestamp tick when refresh completes

## API

No new endpoint. Uses existing:

```
GET /experiments/{id} → { experiment, summary, eventMatrix }
```

## Implementation notes

- Extend existing `load()` / interval in `App.jsx` — do not add a second poll loop.
- Track `lastRefreshedAt` state on successful fetch.
- Debounce: skip if prior request in flight (`refreshing` flag already exists).

## Error handling

- Network error: do not wipe `eventMatrix` / `exp`; show inline warning.
- 404: stop polling, show experiment missing.

## Acceptance criteria

- [x] Summary/event matrix updates every 30s with app mounted (main).
- [x] Manual refresh works from metrics panel (main).
- [ ] "Last updated" visible and updates after each successful poll.
- [ ] Optional pause stops interval without breaking manual refresh.
- [ ] Failed poll does not crash UI or clear existing metrics.

## Open questions

- [ ] Poll only when metrics panel expanded vs always (current: always — keep?)
- [ ] Show poll interval in UI for demo transparency?
