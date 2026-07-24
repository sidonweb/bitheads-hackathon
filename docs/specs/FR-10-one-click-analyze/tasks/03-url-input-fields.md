# Task 03: URL input fields in experiment drawer

## Location

- `packages/dashboard/src/components/ExperimentDrawer.jsx` (modify)
- `packages/dashboard/src/App.jsx` (modify — lift URL state or pass callbacks)
- `packages/dashboard/src/styles.css` (minor — reuse `.drawer-input`)

## Dependencies

- **[FR-12](../../FR-12-dynamic-variant-urls/requirements.md)** — URLs are user-entered, not hardcoded defaults
- Task 02: analyze API expects URLs from UI

## What to build

Add two text inputs in the experiment drawer for Variant A and Variant B URLs. Persist in component state (and optionally `localStorage` for demo convenience). Expose values to parent for the analyze button.

## Design spec

### UI section (new drawer section above or below Traffic allocation)

```
Variant URLs
Provide both URLs before running full analysis.

Variant A URL  [ input type="url" ]
Variant B URL  [ input type="url" ]
```

- Placeholder examples may show format hints (`https://…/?variant=A`) but **must not** auto-fill on mount with hardcoded localhost URLs.
- Optional: pre-fill from `experiment.variant_a_url` / `variant_b_url` **only if** PM previously saved them via PATCH — label as "Saved URLs" and still editable.

### State lifting

Option A (preferred): Lift `variantAUrl`, `variantBUrl` to `App.jsx` alongside `split`, pass to `ExperimentDrawer` and analyze button host.

Option B: Keep in drawer, expose via `onUrlsChange` callback.

### Validation (client)

- Trim whitespace.
- Basic check: starts with `http://` or `https://`.
- Show inline hint if invalid format (non-blocking until analyze click).

### Props changes

```jsx
ExperimentDrawer({
  ...
  variantAUrl,
  variantBUrl,
  onVariantAUrlChange,
  onVariantBUrlChange,
})
```

## Done when

- [ ] PM can type/paste both URLs in drawer.
- [ ] URLs survive drawer close/reopen (session state minimum).
- [ ] No hardcoded `localhost:5173` injected on page load without user action.
- [ ] Empty URL fields disable "Run full analysis" button (task 04).
