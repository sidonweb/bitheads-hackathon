# Task 02: SDUI Builders (Deterministic)

## Location

- `packages/copilot-backend/app/sdui/builders.py` (NEW)
- Called from `graph.py` after `submit_decision` or from `routes/chat.py` post-process

## Design

**LLM does NOT invent block layout.** Python assembles blocks from structured data:

| Input | Blocks produced |
|-------|-----------------|
| `Decision` dict | `metric_grid`, `bar_chart`, `decision_card`, `actions` |
| `eventMatrix` from DB | `table`, optional `funnel_chart` per variant |
| Agent `reply` string | `markdown` |
| `AgentWarning` | `alert` |

## Builder API

```python
def build_analysis_blocks(
    *,
    reply: str,
    decision: dict | None,
    event_matrix: dict | None,
    experiment: dict,
) -> list[Block]:
    blocks = [MarkdownBlock(content=reply)]
    if decision:
        blocks.append(metric_grid_from_decision(decision))
        blocks.append(bar_chart_from_decision(decision))
        blocks.append(decision_card_block(decision))
        blocks.append(actions_from_decision(decision))
    if event_matrix:
        blocks.append(table_from_event_matrix(event_matrix))
    return blocks
```

## Chart data rules

- Bar chart: conversion rate = conversions / exposures per variant (from decision sample + inferred metric, or event matrix).
- Funnel: ordered steps from `eventMatrix.eventNames` funnel order when present.
- Cap at 50 points; round rates to 4 decimals.

## Done when

- [ ] Same analysis always produces same block structure (deterministic)
- [ ] Blocks include no PII beyond aggregated counts
- [ ] Unit-testable without LLM
