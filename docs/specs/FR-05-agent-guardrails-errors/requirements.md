# FR-05: Agent Guardrails & Graceful Error Handling

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P0 |
| Problem statement | Production maturity; reliable copilot under failure |
| Depends on | — |
| Blocks | FR-04, FR-06 |

## Main branch context (partial)

| Item | Status on main |
|------|----------------|
| Topic scope guardrail (decline off-topic) | ✅ In `_system_prompt()` |
| Read-only SQL role | ✅ `agent_readonly` |
| Playwright fallback when MCP down | ✅ Chat-only inference path |
| Per-session thread isolation | ✅ `{exp_id}:{session_id}` |
| Recursion limit | ⚠️ Hardcoded `recursion_limit=25` in `chat_turn` / `analyze_experiment` |
| Tool call budget | ❌ Not implemented |
| Structured `AgentError` / warning shape | ❌ Routes raise raw 500 with `str(err)` |
| `clear_chat_threads` on demo reset | ✅ `POST /demo/clear-chat` |

FR-05 completes what the prompt-only guardrail cannot: budgets, HTTP error contract, dashboard warnings.

## Summary

Central guardrail layer for all agent invocations (`chat_turn`, `analyze_experiment`). Enforces tool-call and recursion limits, catches failures, returns user-safe messages and structured error codes.

## Goals

- Prevent runaway agent loops (cost + latency).
- Never return raw Python exceptions to dashboard.
- Partial success when possible (reply without decision).

## Non-goals

- Distributed rate limiting across replicas.
- Billing / token accounting.

## Configuration

Add to `app/config.py`:

```python
AGENT_MAX_TOOL_CALLS = int(os.getenv("AGENT_MAX_TOOL_CALLS", "12"))
AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "25"))  # match current main default
AGENT_LLM_TIMEOUT_SEC = int(os.getenv("AGENT_LLM_TIMEOUT_SEC", "120"))
```

## Components

### `app/agent/guardrails.py`

| Export | Responsibility |
|--------|----------------|
| `AgentError` | Base exception with `code`, `message`, `retryable` |
| `ToolCallBudget` | Wraps tools; increments counter; raises on exceed |
| `wrap_tools(tools, budget)` | Returns wrapped tool list |
| `run_agent_safe(agent, input, config)` | invoke + catch GraphRecursionError, timeouts |
| `user_message_for(code)` | Static map to PM-friendly copy |

### Tool call budget

- Each tool invocation increments counter (including sub-agent internal tools if nested budget enabled).
- On limit: raise `AgentError(code="AGENT_TOOL_LIMIT", retryable=True)`.

### Recursion limit

- Pass `recursion_limit=AGENT_RECURSION_LIMIT` in LangGraph config.
- Catch `GraphRecursionError` → `AgentError(code="AGENT_RECURSION_LIMIT", retryable=True)`.

## User-facing messages

| code | Message |
|------|---------|
| `AGENT_TOOL_LIMIT` | "This analysis needed too many steps. Try asking a simpler question, or use Analyze once." |
| `AGENT_RECURSION_LIMIT` | "I hit my thinking limit for this turn. Please try again or narrow your question." |
| `AGENT_NO_DECISION` | "I couldn't produce a final recommendation. Check pre-flight status and try Analyze again." |
| `LLM_UNAVAILABLE` | "Copilot is temporarily unavailable. Live metrics in the drawer are still updating." |
| `INTERNAL_ERROR` | "Something unexpected happened. Your experiment data is safe — please retry." |

## Chat response shape

**Success**

```json
{ "reply": "…", "decision": { … } | null, "meta": { "toolCallsUsed": 8 } }
```

**Soft failure (chat still 200)**

```json
{
  "reply": "I couldn't finish the full analysis…",
  "decision": null,
  "warning": { "code": "AGENT_TOOL_LIMIT", "message": "…", "retryable": true }
}
```

**Hard failure (analyze endpoint → 429/503)**

```json
{ "error": { "code": "AGENT_NO_DECISION", "message": "…", "retryable": true } }
```

## Route layer

`chat.py` / `analyze.py`:

- Catch `AgentError` → map to HTTP + body per [00-engineering-standards.md](../00-engineering-standards.md).
- Log full exception server-side only.

## Dashboard

`api.js`: parse `error` and `warning` objects.

`ChatPanel.jsx`:

- Show `warning.message` as amber banner.
- Retry button when `retryable: true`.

## Acceptance criteria

- [ ] Agent stopped after 12 tool calls with user message, not 500 stack trace.
- [ ] Recursion limit produces `AGENT_RECURSION_LIMIT`.
- [ ] `analyze` without `submit_decision` returns `AGENT_NO_DECISION`, not generic 500.
- [ ] Logs include experiment_id and tool call count.

## Open questions

- [ ] Separate budgets for chat vs analyze (analyze may need higher limit)?
- [ ] Return partial metrics in `AGENT_NO_DECISION` response?
