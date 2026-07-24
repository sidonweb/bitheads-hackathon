# Task 01: Backend — analyze request body + validation

## Location

- `packages/copilot-backend/app/schemas.py` (modify or create `AnalyzeRequest` model)
- `packages/copilot-backend/app/routes/analyze.py` (modify)
- `packages/copilot-backend/app/agent/graph.py` (modify `analyze_experiment`)

## Dependencies

- **[FR-12](../../FR-12-dynamic-variant-urls/requirements.md)** — URLs must come from request body, not DB silent injection (G7)
- [00-engineering-standards.md](../../00-engineering-standards.md) — error envelope

## What to build

Extend `POST /experiments/{id}/analyze` to require `variantAUrl` and `variantBUrl` in the JSON body. Return `422 VALIDATION_ERROR` when either is missing or invalid. Pass URLs into the agent prompt for the one-shot analyze turn.

## Design spec

### Request model

```python
class AnalyzeRequest(BaseModel):
    variant_a_url: str = Field(..., alias="variantAUrl", min_length=1)
    variant_b_url: str = Field(..., alias="variantBUrl", min_length=1)
```

- Use Pydantic validation: non-empty strings, basic URL format (http/https).
- FastAPI route signature: `async def analyze(experiment_id: str, body: AnalyzeRequest)`

### Error response (422)

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Both variantAUrl and variantBUrl are required to run analysis.",
    "retryable": false,
    "details": { "missing": ["variantAUrl"] }
  }
}
```

### Agent prompt injection

Update `analyze_experiment(exp, variant_a_url, variant_b_url)`:

```python
user_message = (
    f"Analyze this experiment now and submit a decision.\n"
    f"Variant A URL: {variant_a_url}\n"
    f"Variant B URL: {variant_b_url}"
)
```

- Pass URLs **verbatim** — do not append query params (FR-12: remove `_deep_link_checkout` auto-append on analyze path).
- Do **not** read `exp['variant_a_url']` / `exp['variant_b_url']` as fallback.

### Success path

Unchanged: return `Decision` dict on 200.

### Logging

Log at INFO: `experiment_id`, both URLs (host only if PII concern), verdict.

## Done when

- [ ] `curl -X POST localhost:3001/experiments/exp_1/analyze` with no body → 422 with structured error.
- [ ] `curl` with both URLs → 200 Decision (agent uses provided URLs).
- [ ] Grep confirms analyze path does not silently inject DB URLs.
- [ ] FR-05 error shape used for validation failures (not raw FastAPI `detail` string only).
