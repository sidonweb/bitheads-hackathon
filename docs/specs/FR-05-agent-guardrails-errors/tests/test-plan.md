# FR-05 Test Plan: Agent Guardrails & Graceful Error Handling

| Spec | [../index.md](../index.md) |
| Environment | `docker compose up -d --build`; dashboard at `:5174` |

---

## Test cases

### TC-01: Tool call budget stops agent at 12

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set `AGENT_MAX_TOOL_CALLS=3` in copilot-backend env | Restart service |
| 2 | Chat: complex multi-step analysis with URLs | Agent stops by 4th tool call |
| 3 | Inspect response | `warning.code=AGENT_TOOL_LIMIT`, HTTP 200 on chat |
| 4 | Inspect body | No Python traceback in `reply` or `detail` |

---

### TC-02: Chat tool limit is soft failure (200)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger AGENT_TOOL_LIMIT via chat | HTTP 200 |
| 2 | Verify JSON | `decision: null`, `warning.retryable: true`, non-empty `reply` |

---

### TC-03: Analyze tool limit is hard failure (429)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set low tool limit | — |
| 2 | POST `/experiments/exp_1/analyze` with valid URLs | HTTP 429 |
| 3 | Body | `{ "error": { "code": "AGENT_TOOL_LIMIT", ... } }` |

---

### TC-04: Recursion limit maps to AGENT_RECURSION_LIMIT

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set `AGENT_RECURSION_LIMIT=5` | Restart |
| 2 | Chat: request deep iterative analysis | — |
| 3 | Response | `warning.code=AGENT_RECURSION_LIMIT` or 429 on analyze |
| 4 | Message | Matches `user_message_for("AGENT_RECURSION_LIMIT")` |

---

### TC-05: Analyze without submit_decision → AGENT_NO_DECISION

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock or prompt-inject agent that skips `submit_decision` | — |
| 2 | POST analyze | HTTP 502 |
| 3 | Body | `error.code=AGENT_NO_DECISION`, `retryable: true` |
| 4 | Not | Generic 500 with `agent did not submit a decision` raw string |

---

### TC-06: LLM unavailable → 503

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set invalid `OPENAI_API_KEY` or unreachable `OPENAI_BASE_URL` | — |
| 2 | POST chat | HTTP 503 |
| 3 | Body | `error.code=LLM_UNAVAILABLE` |
| 4 | Message | Mentions copilot unavailable; metrics still work (manual check drawer) |

---

### TC-07: Internal error sanitized

| Step | Action | Expected |
|------|--------|----------|
| 1 | Induce unexpected exception in agent path (dev-only hook) | — |
| 2 | Client response | `error.code=INTERNAL_ERROR`, generic safe message |
| 3 | Server logs | Full traceback + correlation id at ERROR |

---

### TC-08: meta.toolCallsUsed on success

| Step | Action | Expected |
|------|--------|----------|
| 1 | Successful chat analysis | — |
| 2 | Response | `meta.toolCallsUsed` integer ≥ 1 |
| 3 | Server logs | Same count logged with experiment_id |

---

### TC-09: Dashboard amber warning banner

| Step | Action | Expected |
|------|--------|----------|
| 1 | Trigger tool limit via chat in UI | Amber banner visible |
| 2 | Banner text | Matches `warning.message` from API |
| 3 | Chat history | Assistant reply still visible below banner |

---

### TC-10: Dashboard retry button

| Step | Action | Expected |
|------|--------|----------|
| 1 | Get `warning.retryable=true` | Retry button shown |
| 2 | Click Retry | Re-sends last user message |
| 3 | Get `retryable=false` error | No retry button |

---

### TC-11: api.js parseAgentError normalization

| Step | Action | Expected |
|------|--------|----------|
| 1 | Mock 502 with `{ detail: { error: { code, message } } }` | parseAgentError returns code |
| 2 | Mock legacy `{ detail: "string" }` | Falls back to INTERNAL_ERROR message |

---

### TC-12: Config defaults preserve current recursion behavior

| Step | Action | Expected |
|------|--------|----------|
| 1 | Unset env overrides | Defaults used |
| 2 | Normal analyze on exp_1 | Completes successfully (recursion 25) |
| 3 | Verify config | `AGENT_RECURSION_LIMIT=25`, `AGENT_MAX_TOOL_CALLS=12` |

---

## Manual smoke script

```bash
# Happy path
curl -s -X POST localhost:3001/experiments/exp_1/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze with URLs http://host:5173/?variant=A and http://host:5173/?variant=B"}' | jq .

# Low budget (after env change + restart)
# Expect warning or error JSON, never raw stack trace
```

## Sign-off

| Role | Name | Date | Pass/Fail |
|------|------|------|-----------|
| Dev | | | |
| QA | | | |
