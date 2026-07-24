# Task 02: ExecutiveSummary component

## Location

- `packages/dashboard/src/components/ExecutiveSummary.jsx` (new)

## Dependencies

- Task 01: `buildExecutiveSummary` from `../lib/executiveSummary.js`
- Existing `Decision` prop shape (same as `Decision.jsx`)

## What to build

A presentational React component that renders the executive summary block above the verdict badge inside the decision card.

## Design spec

### Props

```jsx
ExecutiveSummary({ decision })
```

- `decision`: required when rendered; parent (`Decision.jsx`) guards null.

### Markup

```jsx
<section className="executive-summary" aria-label="Executive summary">
  <h3 className="executive-summary-title">Executive Summary</h3>
  <ul className="executive-summary-list">
    {bullets.map((text, i) => (
      <li key={i}>{text}</li>
    ))}
  </ul>
</section>
```

- Call `buildExecutiveSummary(decision)` inside the component (or memoize with `useMemo` if decision object is stable).
- If builder returns empty array, render nothing (`return null`).

### Accessibility

- Use semantic `<section>` with `aria-label`.
- List items are plain text (no interactive elements in v1).

### Non-goals

- Do not render `decision.reasoning` here.
- Do not add copy-to-clipboard button in v1 (PM can select text manually).

## Done when

- [ ] Component renders 3 bullets for a mock Scale decision.
- [ ] Component returns `null` when `buildExecutiveSummary` returns `[]`.
- [ ] No imports from backend or API layer.
- [ ] Component exported as default from `ExecutiveSummary.jsx`.
