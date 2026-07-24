# Task 05: XSS and link safety verification

## Location

- `packages/dashboard/src/components/FormattedMessage.jsx` (verify config)
- Manual QA / optional: `packages/dashboard/src/components/__tests__/FormattedMessage.test.jsx` (if test harness added)

## Dependencies

- Task 02: rehype-sanitize configured
- Task 03: ChatPanel integration

## What to build

Confirm sanitize defaults block XSS vectors and external links behave safely. Document any custom sanitize schema overrides if needed.

## Design spec

### Sanitize defaults

Use `rehype-sanitize` default schema — do **not** allow `raw` HTML unless explicitly extending schema with care.

Forbidden in output DOM:

- `<script>` tags
- Event handlers (`onclick`, `onerror`)
- `javascript:` hrefs
- `<iframe>`, `<object>`, `<embed>`

### Link policy

All rendered `<a>` tags:

```jsx
target="_blank"
rel="noopener noreferrer"
```

Optional: prepend visual icon for external links (non-goal for v1).

### Manual test payloads

Inject via mocked assistant message or dev-only chat override:

1. `<script>alert('xss')</script>Hello`
2. `[click](javascript:alert(1))`
3. `<img src=x onerror=alert(1)>`
4. Normal `[docs](https://example.com)`

Expected: (1)(2)(3) do not execute JS; (4) opens new tab safely.

### User message isolation

Confirm PM sending `<script>alert(1)</script>` in user bubble renders as literal text (text node), not HTML.

### Future FR-06 streaming

Document: incremental markdown parse must still pass through same sanitize pipeline on each update.

## Done when

- [ ] Manual XSS payloads produce no alert dialogs.
- [ ] View-source / DevTools shows no `<script>` in assistant message DOM.
- [ ] External https links open in new tab with noopener.
- [ ] Security checklist item signed off in PR description.
