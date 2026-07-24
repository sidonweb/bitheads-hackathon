# Task 02: API client — analyze with URLs + error parse

## Location

- `packages/dashboard/src/api.js` (modify `analyze` function)

## Dependencies

- Task 01: backend accepts `{ variantAUrl, variantBUrl }`
- [00-engineering-standards.md](../../00-engineering-standards.md) — normalized error parsing (align with FR-05 if `parseApiError` helper exists)

## What to build

Update `analyze()` to accept variant URLs, POST them in the request body, and throw a structured error object (or Error with `.code` / `.message`) consumable by UI.

## Design spec

### Function signature

```js
export async function analyze({ variantAUrl, variantBUrl, id = EXPERIMENT_ID } = {})
```

- Both URLs required at call site; validate client-side before fetch:
  - If either missing → throw `Error('Both variant URLs are required')` immediately.

### Request

```js
const res = await fetch(`${API_BASE}/experiments/${id}/analyze`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ variantAUrl, variantBUrl }),
});
```

### Error parsing

On `!res.ok`:

1. Parse JSON body.
2. Prefer `body.error.message` (FR-05 shape).
3. Fallback: `body.detail` or `'analysis failed'`.
4. Attach `code: body.error?.code` and `retryable: body.error?.retryable` on thrown error if useful for UI.

Example:

```js
const err = new Error(message);
err.code = body.error?.code;
err.retryable = body.error?.retryable ?? false;
throw err;
```

### Success

Return parsed JSON `Decision` object unchanged.

### Backward compatibility

Remove or update any call sites that invoked `analyze()` with no args — they must pass URLs after this change.

## Done when

- [ ] `analyze({ variantAUrl, variantBUrl })` succeeds against running stack.
- [ ] Missing URL throws before network call.
- [ ] 422 from backend surfaces human-readable message in thrown Error.
- [ ] No silent fallback to empty POST body.
