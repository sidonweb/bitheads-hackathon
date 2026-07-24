# Task 05: Optional Poll Interval Env

## Location

- `packages/dashboard/src/App.jsx` — replace hardcoded `30_000` with configurable constant
- `packages/dashboard/.env.example` — document `VITE_METRICS_POLL_MS`
- `docker-compose.yml` or dashboard Dockerfile build args *(optional, demo only)*

## Dependencies

- Existing single `setInterval` in App.jsx *(extend constant, not loop)*

## What to build

1. **Extend** top of App.jsx:
   ```javascript
   const METRICS_POLL_INTERVAL_MS =
     Number(import.meta.env.VITE_METRICS_POLL_MS) || 30_000;
   ```
2. Use `METRICS_POLL_INTERVAL_MS` in the existing interval effect.
3. Validate: if env is NaN or < 5000, fall back to 30_000 (prevent accidental hammering).
4. Optional UI transparency: show "(every 30s)" next to auto-refresh label when expanded.
5. Document in `.env.example`; default behavior unchanged when env unset.

## Design spec

### Demo transparency (optional)

```
Auto-refresh on (every 30s)    Last updated 4s ago
```

When `VITE_METRICS_POLL_MS=10000`, label shows "every 10s".

### Guardrails

| Env value | Effective interval |
|-----------|-------------------|
| unset | 30_000 ms |
| `10000` | 10_000 ms |
| `1000` | 30_000 ms (clamp — min 5s) |
| `abc` | 30_000 ms |

## Done when

- [ ] Default poll remains 30s with no env set
- [ ] `VITE_METRICS_POLL_MS=15000` changes interval (verify in Network)
- [ ] Invalid values clamp safely
- [ ] `.env.example` documents variable
- [ ] Still only one `setInterval` in App.jsx
