# Task 05: API Client — Recommend Config

## Location

- **Package:** `packages/dashboard`
- **Files to create/modify:**
  - `src/api.js` — add `recommendConfig`, `savePrimaryMetric`

## Dependencies

- Task 03 (backend routes)
- FR-01 Task 05 (`parseApiError` — reuse)

## What to build

### `recommendConfig`

```javascript
export async function recommendConfig(id, { hypothesis = '', variantAUrl, variantBUrl } = {}) {
  const res = await fetch(`${API_BASE}/experiments/${id}/recommend-config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hypothesis, variantAUrl, variantBUrl }),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}
```

### `savePrimaryMetric`

```javascript
export async function savePrimaryMetric(id, primaryMetric, audienceNote = null) {
  const body = { primaryMetric };
  if (audienceNote != null) body.audienceNote = audienceNote;
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}
```

Alternative: extend `saveHypothesis` into generic `patchExperiment(id, partial)` — only if it reduces duplication without scope creep.

## Design spec

### Client usage in ConfigRecommendationPanel

```javascript
const data = await recommendConfig(experimentId, {
  hypothesis: experiment.hypothesis,
  variantAUrl,
  variantBUrl,
});
setRecommendation(data);
setSelectedMetric(data.primaryMetric.eventName);
```

### Error mapping

| Code | UI |
|------|-----|
| `LLM_UNAVAILABLE` | "Recommendations unavailable — select metric manually from list" |
| `UPSTREAM_ERROR` | "Cannot load event data" |
| `NOT_FOUND` | Drawer-level error |

## Done when

- [ ] Both functions exported from `api.js`
- [ ] Uses shared `parseApiError`
- [ ] camelCase request/response keys
- [ ] Dashboard build passes
