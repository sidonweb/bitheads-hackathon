# Task 03: Integrate into Decision card

## Location

- `packages/dashboard/src/components/Decision.jsx` (modify)

## Dependencies

- Task 02: `ExecutiveSummary.jsx`
- Existing `Decision.jsx` layout and `ReasoningExpander.jsx`

## What to build

Mount `ExecutiveSummary` inside the decision card so it appears whenever the Decision card is shown (chat turn or future one-click analyze path).

## Design spec

### Placement

Insert **above** the colored verdict badge (`.verdict`), at the top of `.decision-card`:

```jsx
<div className="decision-card">
  <ExecutiveSummary decision={decision} />
  <div className="verdict" style={{ background: b.color }}>
    ...
```

Rationale: PM reads summary first, then sees the badge and detailed stats.

### Chat integration

No changes required in `ChatPanel.jsx` — it already renders `<Decision decision={decision} />` when a decision exists. Executive summary appears automatically.

### Content separation

| Section | Content |
|---------|---------|
| Executive Summary | 3 template bullets (plain English) |
| Verdict badge | Scale / Rollback / Continue / Stop |
| Stat row | p-value, uplift, sample sizes |
| Copilot reasoning | Full agent prose (`decision.reasoning`) |
| ReasoningExpander | SQL + rule rationale |

Ensure `decision.reasoning` and `ReasoningExpander` remain unchanged.

## Done when

- [ ] Opening dashboard after chat analysis shows Executive Summary above verdict.
- [ ] Decision card without `inferred_metric` still renders summary with fallback metric label.
- [ ] SQL visible only in `ReasoningExpander`, not in executive summary.
- [ ] No layout regression on mobile-width dashboard (summary wraps cleanly).
