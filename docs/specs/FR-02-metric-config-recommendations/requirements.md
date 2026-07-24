# FR-02: Metric & Configuration Recommendations

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P0 |
| Problem statement | Recommends feature flags, target audiences, and success metrics |
| Depends on | FR-01 (optional), FR-04 (optional) |
| Blocks | — |

## Main branch context

The chat agent **already infers** `inferred_metric` at analysis time (DISTINCT events + page diff) and returns it on the Decision object. FR-02 is a **separate, explicit recommend-config API** for pre-launch setup — it should not duplicate the full analyze workflow. URLs may come from request body (aligned with chat-driven URL model on main); stored `variant_*_url` columns remain optional.

## Summary

After hypothesis generation (or on demand), copilot suggests:

- **Primary success metric** (event_name from DB)
- **Feature flag narrative** (which variant treatment maps to which flag — descriptive, not a real flag SDK)
- **Audience suggestion** (stored as metadata; not enforced in v1.5)

## Goals

- Give PM a concrete measurement plan before launch.
- Metric suggestions constrained to events that **exist** in `universal_events`.

## Non-goals

- LaunchDarkly / Split.io integration.
- Enforcing audience rules in ecom storefront.
- Auto-setting `primary_metric` without PM confirmation.

## User stories

1. As a PM, I see a recommended primary metric with rationale tied to variant differences.
2. As a PM, I can accept the metric and save it to `experiments.primary_metric`.
3. As a PM, I see why a metric was ruled out (e.g. event not in data).

## API design

### `POST /experiments/{id}/recommend-config`

**Request**

```json
{
  "hypothesis": "…",
  "variantAUrl": "http://localhost:5173/?variant=A",
  "variantBUrl": "http://localhost:5173/?variant=B"
}
```

**Response 200**

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
  "availableEvents": ["page_view", "add_to_cart", "checkout_started", "checkout_completed"]
}
```

## Implementation notes

- Service: `app/services/config_recommendation.py`.
- Step 1 (deterministic): query `DISTINCT event_name` for experiment_id.
- Step 2 (LLM): choose metric from list only; pass variant URLs + hypothesis.
- Validate LLM output: `primaryMetric.eventName` MUST be in `availableEvents` else fallback to heuristic (prefer `checkout_completed` if present).

## Data model (optional extension)

```sql
-- v1.5 optional: JSON column on experiments
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS audience_note TEXT;
```

Or store audience in hypothesis metadata JSON — decision at implementation time.

## Guardrails

- Never recommend events not in DB.
- LLM output validated against allowlist before returning.

## Acceptance criteria

- [ ] Returns only event names present in `universal_events` for experiment.
- [ ] If no conversion events exist, returns warning + suggests collecting data first.
- [ ] PM can PATCH `primary_metric` via existing experiment API after accept.

## Open questions

- [ ] Combine with FR-01 in single "Create experiment" API call?
- [ ] Use SQL sub-agent (FR-04) for event discovery vs direct SQL in service?
