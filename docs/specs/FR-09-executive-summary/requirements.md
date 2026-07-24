# FR-09: Executive Summary Card

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P2 |
| Problem statement | Automatically summarizes results in business-friendly language |
| Depends on | Existing Decision object |
| Blocks | — |

## Summary

Structured non-technical summary rendered above or inside Decision card: 3 bullets PM can paste into Slack/email.

## Goals

- Satisfy "business-friendly language" eval explicitly in UI.
- No extra LLM call if decision.reasoning already sufficient — may derive by template.

## Non-goals

- PDF export.
- Email sending.

## UI content

```
Executive Summary
• Variant B's checkout CTA drove +14% relative uplift in checkout_completed.
• Result is statistically significant (p = 0.003) with 5,000 users per variant.
• Recommendation: Scale — roll out Variant B to all traffic.
```

## Implementation options

**Option A (preferred v1.5):** Template from decision fields (no LLM).

**Option B:** Second LLM call `summarize_for_executives(decision)` — higher cost, use only if template insufficient.

## Component

- `ExecutiveSummary.jsx` — props: `decision`.
- Render inside `Decision.jsx` or chat turn when decision present.

## Acceptance criteria

- [ ] Summary visible whenever Decision card shown.
- [ ] Contains verdict, metric name, uplift, significance in plain English.
- [ ] No raw SQL in executive summary (SQL stays in ReasoningExpander).

## Open questions

- [ ] Template-only vs LLM polish?
