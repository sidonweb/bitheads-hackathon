# Task 05: API Client — Preflight

## Location

- **Package:** `packages/dashboard`
- **Files to create/modify:**
  - `src/api.js` — add `getPreflight`

## Dependencies

- Task 03 (GET endpoint)
- FR-01 Task 05 (`parseApiError`)

## What to build

### `getPreflight`

```javascript
export async function getPreflight(id, { variantAUrl, variantBUrl } = {}) {
  const params = new URLSearchParams();
  if (variantAUrl) params.set('variantAUrl', variantAUrl);
  if (variantBUrl) params.set('variantBUrl', variantBUrl);
  const qs = params.toString();
  const url = `${API_BASE}/experiments/${id}/preflight${qs ? `?${qs}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}
```

### Optional: `formatPreflightScore(result)`

UI helper (can live in component instead):

```javascript
export function isPreflightReady(result) {
  return result?.ready === true;
}
```

## Design spec

### Query string encoding

URLs must be fully encoded by `URLSearchParams`:

```javascript
// variantAUrl=http://localhost:5173/?variant=A
// Encoded correctly for query string
```

### Error mapping

| Code | UI |
|------|-----|
| `UPSTREAM_ERROR` | "Cannot load preflight checks — database unavailable" |
| `NOT_FOUND` | "Experiment not found" |

### Caching note

Server caches 60s — client may also debounce Re-run clicks (disable button for 2s) to avoid double-fetch UX issues.

## Done when

- [ ] `getPreflight` exported from `api.js`
- [ ] Query params correctly appended
- [ ] Uses `parseApiError` for failures
- [ ] Dashboard build passes
- [ ] Manual test: returns checks array with id, name, status, message
