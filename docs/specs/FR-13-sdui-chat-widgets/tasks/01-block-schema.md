# Task 01: Block Schema & Versioning

## Location

- `packages/copilot-backend/app/sdui/schema.py` (NEW)
- `packages/copilot-backend/app/sdui/__init__.py` (NEW)
- `packages/copilot-backend/app/schemas_agent.py` — extend `ChatOut`

## Block envelope

Every block:

```python
class BlockBase(BaseModel):
    type: Literal["markdown", "metric_grid", "bar_chart", ...]
    id: str  # uuid or stable slug, e.g. "analysis-metrics"
    version: str = "1.0"
```

## Example definitions

### `markdown`

```json
{ "type": "markdown", "id": "b1", "content": "**Variant B** leads on checkout_completed." }
```

### `metric_grid`

```json
{
  "type": "metric_grid",
  "id": "b2",
  "columns": 3,
  "metrics": [
    { "label": "p-value", "value": "0.003", "tone": "positive" },
    { "label": "Uplift", "value": "+14.2%", "tone": "positive" },
    { "label": "Sample A / B", "value": "2,400 / 2,380", "tone": "neutral" }
  ]
}
```

### `bar_chart`

```json
{
  "type": "bar_chart",
  "id": "b3",
  "title": "Conversion rate by variant",
  "yLabel": "Rate",
  "series": [
    { "name": "A", "value": 0.108 },
    { "name": "B", "value": 0.123 }
  ]
}
```

### `funnel_chart`

```json
{
  "type": "funnel_chart",
  "id": "b4",
  "title": "Variant B funnel",
  "steps": [
    { "label": "page_view", "count": 106 },
    { "label": "add_to_cart", "count": 19 },
    { "label": "checkout_completed", "count": 19 }
  ]
}
```

### `decision_card`

Wraps existing Decision object + executive summary bullets (server-built).

### `actions`

```json
{
  "type": "actions",
  "id": "b5",
  "buttons": [
    { "actionId": "apply_scale", "label": "Apply Scale", "variant": "primary", "disabled": false }
  ]
}
```

**Allowed `actionId`:** `apply_scale`, `apply_rollback`, `rerun_analyze`, `open_preflight` — client maps to handlers.

## ChatOut extension

```python
class ChatOut(BaseModel):
    reply: str  # keep for backward compat + LLM fallback
    blocks: list[BlockUnion] = []
    decision: Optional[dict] = None  # deprecated path — migrate to decision_card block
    meta: ChatMeta  # add sduiVersion: "1.0"
```

## Done when

- [ ] Pydantic validates all v1 block types
- [ ] Unknown type rejected at build time (server), ignored at render time (client)
- [ ] JSON schema exported for dashboard TypeScript types (optional JSDoc)
