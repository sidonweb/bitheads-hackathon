# FR-10: One-Click Analyze — Spec Index

| Field | Value |
|-------|--------|
| Source FR | [FR-10-one-click-analyze.md](requirements.md) |
| Priority | P2 |
| Depends on | [FR-05](../FR-05-agent-guardrails-errors/requirements.md) (structured errors), [FR-12](../FR-12-dynamic-variant-urls/requirements.md) (URLs in analyze body, G7) |
| Blocks | — |

## Problem

Judges and PMs must type in chat to trigger a full agent workflow. The backend already exposes `POST /experiments/{id}/analyze`, but the dashboard has no button and the endpoint does not yet accept required variant URLs per G7.

## Solution

Add a **Run full analysis** button in the dashboard that calls `/analyze` with user-supplied variant URLs, shows a loading state, and populates the same Decision card used by chat — without sending a chat message.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Dashboard button + spinner + disabled-while-busy | Replacing chat-based analysis |
| Extend `analyze()` in `api.js` with URL body | Silent injection of DB-stored URLs |
| Structured error display (FR-05 shape) | Hard-blocking on preflight (FR-03 warn-only unless G3 changes) |
| Double-click prevention | |

## API contract (target)

```
POST /experiments/{id}/analyze
Content-Type: application/json

{
  "variantAUrl": "https://example.com/?variant=A",
  "variantBUrl": "https://example.com/?variant=B"
}
```

| Case | HTTP | Response |
|------|------|----------|
| Success | 200 | `Decision` object |
| Missing URLs | 422 | `{ "error": { "code": "VALIDATION_ERROR", "message": "…", "retryable": false } }` |
| Agent failure | 429/502/503 | FR-05 error envelope |

**Important:** Per FR-12/G7, URLs must come from explicit user input (drawer fields or modal), not from `experiments.variant_*_url` unless the PM typed them there.

## Tasks

| # | Task | File |
|---|------|------|
| 1 | Backend: analyze request body + validation | [tasks/01-backend-analyze-body.md](./tasks/01-backend-analyze-body.md) |
| 2 | API client: analyze with URLs + error parse | [tasks/02-api-client-analyze.md](./tasks/02-api-client-analyze.md) |
| 3 | URL input fields in experiment drawer | [tasks/03-url-input-fields.md](./tasks/03-url-input-fields.md) |
| 4 | Run full analysis button + loading UX | [tasks/04-analyze-button-ui.md](./tasks/04-analyze-button-ui.md) |
| 5 | Wire decision state + error display | [tasks/05-wire-decision-and-errors.md](./tasks/05-wire-decision-and-errors.md) |

## Test plan

[tests/test-plan.md](./tests/test-plan.md) — minimum 8 manual/automated cases.

## Acceptance criteria (from FR)

- [ ] Button triggers analyze and shows Decision without chat message.
- [ ] Errors show user-friendly code/message.
- [ ] Double-click prevented while in flight.

## Implementation order

1. **FR-12** backend changes (required body, prompt injection of URLs into analyze message).
2. FR-10 UI tasks (can proceed in parallel once API contract is stable).
