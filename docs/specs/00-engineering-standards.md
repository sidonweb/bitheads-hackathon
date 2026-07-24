# Engineering Standards (Cross-Cutting)

Applies to **all** feature requirements in this folder.

## Principles

1. **Separation of concerns** — UI, API routes, business logic, and agent orchestration live in distinct modules.
2. **Deterministic truth** — Statistics, verdicts, and validation rules are computed in Python, not by the LLM.
3. **Fail gracefully** — Never expose stack traces or raw exceptions to the user.
4. **Defense in depth** — Guardrails at DB role, tool layer, agent limits, and API validation.
5. **Observable** — Structured server logs; client receives actionable error codes/messages.
6. **Minimal scope** — Smallest change that satisfies the FR; no speculative abstractions.

## Error response contract (API)

All copilot-backend endpoints that can fail MUST return:

```json
{
  "error": {
    "code": "AGENT_TOOL_LIMIT",
    "message": "Human-readable message for the PM.",
    "retryable": true,
    "details": {}
  }
}
```

HTTP status mapping:

| Code | HTTP | retryable |
|------|------|-----------|
| `NOT_FOUND` | 404 | false |
| `VALIDATION_ERROR` | 422 | false |
| `AGENT_TOOL_LIMIT` | 429 | true |
| `AGENT_RECURSION_LIMIT` | 429 | true |
| `AGENT_NO_DECISION` | 502 | true |
| `LLM_UNAVAILABLE` | 503 | true |
| `UPSTREAM_ERROR` | 502 | true |
| `INTERNAL_ERROR` | 500 | false |

Chat endpoints MAY return partial success:

```json
{
  "reply": "I couldn't finish the full analysis, but here is what the metrics show…",
  "decision": null,
  "warning": { "code": "AGENT_TOOL_LIMIT", "message": "…" }
}
```

## Agent guardrails (global)

| Limit | Env var | Default (target) | On main today |
|-------|---------|------------------|---------------|
| Max tool calls per turn | `AGENT_MAX_TOOL_CALLS` | 12 | Not enforced |
| Max graph steps | `AGENT_RECURSION_LIMIT` | 25 | Hardcoded 25 in `graph.py` |
| Topic scope | system prompt | A/B analysis only | ✅ Implemented |
| SQL statement timeout | DB role | 5s | ✅ `agent_readonly` |
| LLM temperature | — | 0 | ✅ |
| Session threads | `sessionId` on chat | per session | ✅ `{exp_id}:{session_id}` |

Variant URLs for browser inspection: **from PM chat**, not experiment config. Preflight may use stored URLs or request params (see FR-03, G6).

## Logging

- Log at **INFO**: experiment id, verdict, inferred metric, tool call count.
- Log at **WARN**: limit reached, Playwright unavailable, partial analysis.
- Log at **ERROR**: unexpected exceptions with correlation id (request-level uuid).
- Never log API keys, full card data, or PII beyond `user_id` in debug.

## Security

- Agent DB connection: **SELECT only** (`agent_readonly` role).
- SQL sub-agent: reject non-SELECT statements at application layer before execution.
- No arbitrary URL fetch except variant URLs in pre-flight checks (stored or request-supplied) and Playwright inspection of PM-provided URLs in chat.
- CORS: current `*` acceptable for hackathon demo; document as non-production.

## Testing expectations (per FR)

Each feature SHOULD include at minimum:

- One happy-path manual test step in the FR acceptance criteria.
- One failure-path (limit hit, LLM down, empty data).
- Build passes (`npm run build`, copilot-backend imports cleanly).

## File layout conventions

```
packages/copilot-backend/app/
  agent/          # LangGraph agent, sub-agents, guardrails
  routes/         # FastAPI routers (thin — delegate to services)
  services/       # NEW: business logic (validation, hypothesis, etc.)
  schemas.py      # Pydantic request/response models

packages/dashboard/src/
  components/     # UI components per feature
  api.js          # API client with normalized error parsing
```

## Review checklist (before marking Approved)

- [ ] Non-goals explicitly listed
- [ ] API contract defined (request/response/errors)
- [ ] Failure modes documented
- [ ] No duplicate responsibility with another FR
- [ ] Acceptance criteria are testable
- [ ] Dependencies on other FRs noted
