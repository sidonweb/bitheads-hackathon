# FR-01: Hypothesis from Business Goals

## Feature metadata

| Field | Value |
|-------|--------|
| **ID** | FR-01 |
| **Short name** | hypothesis-from-goals |
| **Priority** | P0 |
| **Status** | Draft |
| **Depends on** | — |
| **Blocks** | [FR-02](../FR-02-metric-config-recommendations/index.md), [FR-03](../FR-03-preflight-validation/index.md) |
| **Source requirement** | [FR-01-hypothesis-from-goals.md](requirements.md) |

## Summary

PM enters a business goal (e.g. "Increase checkout conversion"). The copilot generates a structured experiment proposal: hypothesis, experiment name, and optional variant descriptions. PM can edit and save to the existing `experiments` table via explicit "Accept & save" action.

## Goals

- Reduce experiment creation time.
- Produce PM-readable hypothesis text, not jargon.
- Persist via existing `POST /experiments` upsert or `PATCH /experiments/{id}` for save (explicit user action).

## Non-goals

- Multi-step wizard for full experiment lifecycle.
- Auto-generating variant UI code.
- Audience or traffic split recommendations (see [FR-02](../FR-02-metric-config-recommendations/index.md)).
- Auto-generating variant URLs unless product decides to save them for preflight/analyze (out of scope for v1).

## Task index

| # | Task | Package | Description |
|---|------|---------|-------------|
| 01 | [Schemas & error helpers](./tasks/01-schemas-and-errors.md) | copilot-backend | Pydantic models, structured error responses |
| 02 | [Hypothesis service](./tasks/02-hypothesis-service.md) | copilot-backend | LLM-backed `generate_hypothesis()` with guardrails |
| 03 | [Generate-hypothesis route](./tasks/03-generate-hypothesis-route.md) | copilot-backend | `POST /experiments/{id}/generate-hypothesis` |
| 04 | [Dashboard hypothesis panel](./tasks/04-dashboard-hypothesis-panel.md) | dashboard | UI in Experiment drawer for goal → draft → save |
| 05 | [API client](./tasks/05-api-client-hypothesis.md) | dashboard | `api.js` helpers + error normalization |

## Acceptance criteria

- [ ] Given goal "increase checkout conversion", returns non-empty hypothesis mentioning conversion.
- [ ] Empty goal returns 422 with `VALIDATION_ERROR` and clear message.
- [ ] Goal > 2000 chars returns 422 with `VALIDATION_ERROR`.
- [ ] LLM failure returns 503 with `LLM_UNAVAILABLE`; UI shows fallback "Enter hypothesis manually".
- [ ] Accepted hypothesis persisted via `POST /experiments` or `PATCH` and visible on experiment reload.
- [ ] Rate limit: 10 generations / experiment / hour returns 429.
- [ ] No stack trace in API response body (per [00-engineering-standards.md](../00-engineering-standards.md)).
- [ ] LLM prompt does not invent metrics or results — only hypothesis framing.

## Related FRs

| FR | Relationship |
|----|--------------|
| [FR-02](../FR-02-metric-config-recommendations/index.md) | Optional downstream: metric recommendations can use saved hypothesis |
| [FR-03](../FR-03-preflight-validation/index.md) | Check C6 validates hypothesis is non-empty before launch |
| [FR-10](../FR-10-one-click-analyze/requirements.md) | One-click analyze may consume hypothesis from experiment row |

## Open questions (from source)

- Generate into new experiment id vs only update existing `exp_1`? **Spec decision:** operate on existing experiment id from route; PM creates experiment first or uses seeded `exp_1`.
- Single LLM provider only or reuse `_build_llm()` from graph? **Spec decision:** reuse `_build_llm()` for provider consistency.
