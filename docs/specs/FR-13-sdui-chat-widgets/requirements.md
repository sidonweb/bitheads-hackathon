# FR-13: Server-Driven UI (SDUI) for Chat Widgets

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P1 |
| Problem statement | Chat is text-only; PMs need charts, metric cards, and rich widgets inline |
| Depends on | FR-06 (streaming), FR-11 (markdown) |
| Blocks | — |

## Summary

Introduce a **block-based SDUI protocol** between copilot-backend and dashboard. The server sends typed UI blocks (charts, tables, metric grids, action buttons) alongside markdown text. The client renders blocks from a **versioned allowlist registry** — no arbitrary HTML/JS from server.

## Goals

- Rich inline visuals: variant comparison charts, funnel, metric grids, decision cards.
- Server controls *what* to show; client controls *how* (design system, a11y).
- Works with non-streaming `/chat` and streaming `/chat/stream`.
- Backward compatible: `reply` string still works when `blocks` is empty.

## Non-goals

- Full arbitrary layout engine (no flexbox JSON from LLM).
- Client-side chart generation from raw SQL (server sends chart-ready data).
- SDUI for ecom storefront.
- Replacing Experiment drawer panels in v1 (chat-only first).

## Block types (v1)

| Type | Purpose |
|------|---------|
| `markdown` | Prose (replaces raw `reply` long-term) |
| `metric_grid` | 2–4 stat tiles (p-value, uplift, sample) |
| `bar_chart` | Variant A vs B comparison |
| `funnel_chart` | Event funnel per variant |
| `table` | Event matrix / SQL preview rows |
| `decision_card` | Verdict badge + exec summary + apply CTA |
| `alert` | Info / warning / error strip |
| `actions` | Inline buttons (Apply Scale, Re-run analyze) |

## API shape (target)

```json
{
  "reply": "Variant B is ahead on checkout_completed…",
  "blocks": [
    { "type": "markdown", "id": "b1", "content": "…" },
    { "type": "metric_grid", "id": "b2", "metrics": […] },
    { "type": "bar_chart", "id": "b3", "title": "Conversion rate", "series": […] },
    { "type": "decision_card", "id": "b4", "decision": { … } }
  ],
  "decision": null,
  "meta": { "sduiVersion": "1.0", "toolCallsUsed": 8 }
}
```

Streaming: new SSE event `block` with partial block payloads; terminal `done` unchanged.

## Security

- Block `type` must be in server + client allowlist.
- No `html`, `script`, or `iframe` block types.
- Chart data: numbers + labels only; max 50 data points.
- Actions: server sends `actionId` from enum; client maps to known handlers.

## Acceptance criteria

- [ ] Analysis turn renders at least one chart + metric grid in chat without custom frontend code per response.
- [ ] Unknown block type → graceful fallback message, chat does not crash.
- [ ] Streaming analysis emits `block` events before `done`.
- [ ] Plain-text-only responses still render (blocks optional).

## Open questions

- [ ] Migrate existing `Decision.jsx` fully into SDUI or keep dual path during transition?
- [ ] Chart library: Recharts vs lightweight custom SVG?
- [ ] Who builds blocks: deterministic Python after `submit_decision`, or LLM-assisted layout?
