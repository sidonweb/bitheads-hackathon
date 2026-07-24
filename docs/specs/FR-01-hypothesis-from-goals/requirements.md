# FR-01: Hypothesis from Business Goals


| Field             | Value                                                   |
| ----------------- | ------------------------------------------------------- |
| Status            | Draft                                                   |
| Priority          | P0                                                      |
| Problem statement | Generates experiment hypotheses based on business goals |
| Depends on        | —                                                       |
| Blocks            | FR-02, FR-03                                            |


## Main branch context

`experiments.hypothesis` exists and is shown in the agent system prompt, but there is **no generate-hypothesis API**. Variant URLs on the experiment row are **optional** (`variantAUrl` / `variantBUrl` nullable in `ExperimentIn`) — the agent expects URLs in chat. FR-01 does not need to generate URLs unless product wants them saved for preflight/analyze (see G6/G7).

## Summary

PM enters a business goal (e.g. "Increase checkout conversion"). The copilot generates a structured experiment proposal: hypothesis, experiment name, and optional variant descriptions. PM can edit and save to the existing `experiments` table.

## Goals

- Reduce experiment creation time.
- Produce PM-readable hypothesis text, not jargon.
- Persist via existing `POST /experiments` or new dedicated endpoint.



## Non-goals

- Multi-step wizard for full experiment lifecycle.
- Auto-generating variant UI code.
- Audience or traffic split recommendations (see FR-02).



## User stories

1. As a PM, I enter a business goal and receive a draft hypothesis I can accept or edit.
2. As a PM, I see the generated hypothesis saved on the experiment record.
3. As a PM, if generation fails, I get a clear message and can type hypothesis manually.



## API design



### `POST /experiments/{id}/generate-hypothesis`

**Request**

```json
{
  "businessGoal": "Increase checkout conversion on mobile",
  "context": "We changed the checkout CTA on variant B"
}
```

**Response 200**

```json
{
  "hypothesis": "Variant B's redesigned checkout CTA increases checkout_completed conversion vs Variant A on mobile.",
  "suggestedName": "Checkout CTA Redesign — Mobile",
  "suggestedVariantBName": "Redesigned CTA",
  "suggestedVariantAName": "Original CTA",
  "confidence": "medium"
}
```

**Errors**


| code               | When                          |
| ------------------ | ----------------------------- |
| `VALIDATION_ERROR` | Empty goal, goal > 2000 chars |
| `LLM_UNAVAILABLE`  | LLM timeout or auth failure   |
| `NOT_FOUND`        | experiment_id missing         |




## Implementation notes

- New module: `app/services/hypothesis.py` — single function `generate_hypothesis(goal, context, exp)`.
- LLM call with structured output (Pydantic parse or JSON mode); **no DB writes inside LLM call**.
- Separate `PATCH` or reuse `POST /experiments` upsert for save (explicit user action "Accept").
- Prompt must not invent metrics or results — only hypothesis framing.



## UI (dashboard)

- Panel in Experiment drawer or modal: textarea "Business goal", button "Generate hypothesis".
- Shows draft in editable field; "Accept & save" commits to backend.
- Loading + error states per [00-engineering-standards.md](../00-engineering-standards.md).



## Guardrails

- Max input length: 2000 characters.
- Rate limit: 10 generations / experiment / hour (in-memory OK for hackathon).
- LLM timeout: 30s.



## Acceptance criteria

- [ ] Given goal "increase checkout conversion", returns non-empty hypothesis mentioning conversion.
- [ ] Empty goal returns 422 with clear message.
- [ ] LLM failure returns 503; UI shows fallback "Enter hypothesis manually".
- [ ] Accepted hypothesis persisted and visible on experiment reload.
- [ ] No stack trace in API response body.



## Open questions

- [ ] Generate into new experiment id vs only update existing `exp_1`?
- [ ] Single LLM provider only or reuse `_build_llm()` from graph?