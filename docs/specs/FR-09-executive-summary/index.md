# FR-09: Executive Summary — Spec Index

| Field | Value |
|-------|--------|
| Source FR | [FR-09-executive-summary.md](requirements.md) |
| Priority | P2 |
| Depends on | Existing `Decision` object (from chat or `/analyze`) |
| Blocks | — |

## Problem

PMs need a business-friendly, copy-paste-ready summary when a decision is shown. Raw stats (`p_value`, `inferred_metric`, SQL) belong in the technical sections, not in Slack/email drafts.

## Solution (v1)

Template-driven **Executive Summary** — three bullet points derived from `Decision` fields. No extra LLM call in v1 (Option A from FR).

## Scope

| In scope | Out of scope |
|----------|--------------|
| `ExecutiveSummary.jsx` component | PDF export |
| Render inside `Decision.jsx` above verdict stats | Email sending |
| Plain-English bullets: metric, uplift, significance, recommendation | Raw SQL in summary |
| Visible whenever Decision card is shown | LLM polish (Option B — defer) |

## Example output

```
Executive Summary
• Variant B's checkout CTA drove +14.0% relative uplift in checkout_completed.
• Result is statistically significant (p = 0.0030) with 5,000 users per variant.
• Recommendation: Scale — roll out Variant B to all traffic.
```

## Tasks

| # | Task | File |
|---|------|------|
| 1 | Template builder utility | [tasks/01-template-builder.md](./tasks/01-template-builder.md) |
| 2 | ExecutiveSummary component | [tasks/02-executive-summary-component.md](./tasks/02-executive-summary-component.md) |
| 3 | Integrate into Decision card | [tasks/03-integrate-decision-card.md](./tasks/03-integrate-decision-card.md) |
| 4 | Styles and typography | [tasks/04-styles.md](./tasks/04-styles.md) |

## Test plan

[tests/test-plan.md](./tests/test-plan.md) — minimum 8 manual/automated cases.

## Acceptance criteria (from FR)

- [ ] Summary visible whenever Decision card shown.
- [ ] Contains verdict, metric name, uplift, significance in plain English.
- [ ] No raw SQL in executive summary (SQL stays in `ReasoningExpander`).

## Open questions

- Template-only v1 is decided; revisit LLM polish only if templates prove insufficient for edge verdicts.
- Whether to also render markdown in executive summary bullets (coordinate with FR-11 if yes).
