# FR-02 Test Plan: Metric & Configuration Recommendations

## Test strategy

| Layer | Approach |
|-------|----------|
| Unit | Event allowlist validation, heuristic fallback, alternatives filtering |
| API | curl against recommend-config + PATCH primaryMetric |
| UI | Manual dashboard ConfigRecommendationPanel flows |
| Integration | Hypothesis → recommend → accept → GET experiment shows metric |
| Regression | Analyze agent `inferred_metric` still independent at analysis time |

**Prerequisites:** Seeded `exp_1` with events in `universal_events`; Docker stack running.

## Manual test cases

| ID | Title | Steps | Expected |
|----|-------|-------|----------|
| FR02-M01 | Happy path recommendations | 1. Ensure events exist (seed or simulate)<br>2. POST recommend-config with hypothesis + URLs | 200; `primaryMetric.eventName` ∈ `availableEvents`; rationale non-empty |
| FR02-M02 | Accept primary metric | 1. FR02-M01 in UI<br>2. Click Accept metric | PATCH succeeds; GET shows `primary_metric=checkout_completed` |
| FR02-M03 | Events from DB only | Inspect `availableEvents` vs DB `DISTINCT event_name` | Exact match; no invented events |
| FR02-M04 | Zero events warning | 1. Truncate events for experiment<br>2. Recommend | 200 with `warning`; heuristic metric; UI amber banner |
| FR02-M05 | LLM invalid pick fallback | Mock LLM returning `fake_event` | Service adjusts to heuristic; rationale notes adjustment |
| FR02-M06 | URL fallback from experiment row | 1. Save URLs on experiment<br>2. POST recommend-config without URLs in body | Uses stored URLs in LLM prompt (verify via logs) |
| FR02-M07 | Alternatives validity | Check `alternatives` array | Every item ∈ `availableEvents`; excludes primary |
| FR02-M08 | Feature flag narrative | Read `featureFlag.summary` | Descriptive text; no SDK integration artifacts |
| FR02-M09 | Audience note display | View audience section | Shows "not enforced" note; no storefront behavior change |
| FR02-M10 | Metrics panel after accept | 1. Accept checkout_completed<br>2. View Metrics card | Conversions counted using accepted metric |

## Failure / edge cases

| Case | Trigger | Expected |
|------|---------|----------|
| DB down | Stop postgres | 502 `UPSTREAM_ERROR` |
| Invalid URL in request | `variantAUrl: "not-a-url"` | 422 `VALIDATION_ERROR` |
| Empty hypothesis | No hypothesis in body or DB | Still returns recommendations (degraded rationale) |
| Single event only (`page_view`) | Minimal data | Recommends page_view with warning about conversion tracking |
| LLM timeout | >30s | 503 `LLM_UNAVAILABLE` |
| Double accept | Click Accept twice | Idempotent PATCH; no error |
| Re-recommend after accept | Get recommendations again | New rationale; current metric badge still shown |

## Integration tests (recommended)

```python
def test_recommend_config_allowlist(client, seeded_exp):
    resp = client.post("/experiments/exp_1/recommend-config", json={...})
    data = resp.json()
    assert data["primaryMetric"]["eventName"] in data["availableEvents"]

def test_heuristic_fallback_when_llm_invalid(mock_llm_invalid):
    ...
```

## Regression checks

- [ ] `POST /experiments/exp_1/analyze` still infers metric independently when `primary_metric` NULL
- [ ] Setting `primary_metric` does not break GET experiment summary SQL
- [ ] Event matrix on dashboard still renders
- [ ] No CORS errors from new endpoints
- [ ] copilot-backend imports cleanly after new service module
