# Task 04: Refresh Pulse Indicator

## Location

- `packages/dashboard/src/components/SimulationMetricsPanel.jsx` — header animation
- `packages/dashboard/src/App.jsx` — pass `justRefreshed` pulse flag or derive from `refreshing` → false edge

## Dependencies

- Task 01 (`lastRefreshedAt`)
- Existing `refreshing` prop *(already wired from App.jsx)*

## What to build

1. **Extend** panel header: when `refreshing` transitions `true → false` on success, trigger a 600ms subtle pulse on timestamp or ↻ icon.
2. Implementation options (pick one):
   - CSS class `sim-metrics-pulse` toggled for 600ms after successful refresh
   - Brief opacity flash on "Last updated" text
3. Do not pulse on failed refresh.
4. Respect `prefers-reduced-motion`: skip animation, instant timestamp update only.

## Design spec

### Animation

- Scale or opacity pulse on "Last updated just now" text
- Duration ≤ 600ms, ease-out
- No layout shift (no table reflow)

### Collapsed panel

Skip pulse when panel collapsed — optional dot badge on "Metrics" chevron if low effort.

## Done when

- [ ] Successful manual refresh triggers visible pulse
- [ ] Successful 30s auto-refresh triggers same pulse
- [ ] Failed refresh does not pulse
- [ ] `prefers-reduced-motion: reduce` disables animation
- [ ] No new network requests from animation logic
