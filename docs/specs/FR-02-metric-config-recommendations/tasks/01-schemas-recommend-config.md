# Task 01: Schemas — Recommend Config

## Location

- **Package:** `packages/copilot-backend`
- **Files to create/modify:**
  - `app/schemas.py` — add recommend-config models
  - `app/schemas.py` — extend `ExperimentPatch` with `primaryMetric`

## Dependencies

- FR-01 Task 01 (`app/errors.py` error helpers) — reuse if already created
- Existing `ExperimentPatch` in `schemas.py`

## What to build

### Request model

```python
class RecommendConfigIn(BaseModel):
    hypothesis: str = ""
    variantAUrl: Optional[str] = None
    variantBUrl: Optional[str] = None
```

URLs optional — fall back to experiment row values in route handler.

### Response models

```python
class PrimaryMetricRecommendation(BaseModel):
    eventName: str
    rationale: str
    alternatives: list[str] = []

class FeatureFlagRecommendation(BaseModel):
    summary: str
    suggestedTrafficSplit: int = 50

class AudienceRecommendation(BaseModel):
    suggestion: str
    note: str = "Audience targeting not enforced in v1.5; stored for documentation."

class RecommendConfigOut(BaseModel):
    primaryMetric: PrimaryMetricRecommendation
    featureFlag: FeatureFlagRecommendation
    audience: AudienceRecommendation
    availableEvents: list[str]
    warning: Optional[str] = None  # e.g. insufficient events
```

### Extend `ExperimentPatch`

```python
primaryMetric: Optional[str] = None
audienceNote: Optional[str] = None  # if audience_note column added
```

### Optional DB migration (document in Task 02)

```sql
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS audience_note TEXT;
```

Decision: store audience in `audience_note` column OR skip persistence in v1 (display only). Spec recommends column add in ecom-backend migration if persisting.

## Design spec

### Response example

```json
{
  "primaryMetric": {
    "eventName": "checkout_completed",
    "rationale": "Variant diff is checkout CTA; checkout_completed best captures goal.",
    "alternatives": ["checkout_started", "add_to_cart"]
  },
  "featureFlag": {
    "summary": "Treat variant B checkout hero CTA as the treatment flag.",
    "suggestedTrafficSplit": 50
  },
  "audience": {
    "suggestion": "All users",
    "note": "Audience targeting not enforced in v1.5; stored for documentation."
  },
  "availableEvents": ["page_view", "add_to_cart", "checkout_started", "checkout_completed"],
  "warning": null
}
```

### Validation rules

| Field | Rule |
|-------|------|
| `hypothesis` | max 4000 chars |
| `variantAUrl` / `variantBUrl` | valid URL format if provided |
| Response `primaryMetric.eventName` | MUST ∈ `availableEvents` (enforced in service) |

## Done when

- [ ] All Pydantic models defined in `schemas.py`
- [ ] `ExperimentPatch.primaryMetric` mapped in route PATCH handler
- [ ] Optional `audienceNote` patch field documented
- [ ] Models use camelCase aliases for JSON serialization consistency with frontends
- [ ] Import smoke test passes
