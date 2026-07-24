# Task 05: Route Error Wrapping (`chat.py`, `analyze.py`)

## Location

| Action | Path |
|--------|------|
| Edit | `packages/copilot-backend/app/routes/chat.py` |
| Edit | `packages/copilot-backend/app/routes/analyze.py` |
| Edit | `packages/copilot-backend/app/schemas.py` — response models |

## Dependencies

- Task 04 (`run_agent_safe`, `AgentError`)
- Task 02 (`http_status_for`, error body shape)

## What to build

Replace bare `except Exception → HTTPException(500, str(err))` with structured handling.

### `chat.py`

```python
from ..agent.guardrails import AgentError, http_status_for

try:
    result = await chat_turn(...)
except AgentError as err:
    if err.code in ("AGENT_TOOL_LIMIT", "AGENT_RECURSION_LIMIT", "AGENT_NO_DECISION"):
        return {
            "reply": user_message_for(err.code),
            "decision": None,
            "warning": {
                "code": err.code,
                "message": err.message,
                "retryable": err.retryable,
            },
        }
    raise HTTPException(
        status_code=http_status_for(err.code),
        detail={"error": {"code": err.code, "message": err.message, "retryable": err.retryable}},
    )
```

Prefer returning 200 with `warning` for recoverable agent limits in **chat** (partial success).

Also handle soft failures returned inline from `chat_turn` (no exception).

Success response adds `meta.toolCallsUsed`.

### `analyze.py`

Analyze is **hard failure** for agent errors:

```python
except AgentError as err:
    raise HTTPException(
        status_code=http_status_for(err.code),
        detail={"error": {"code": err.code, "message": err.message, "retryable": err.retryable, "details": err.details}},
    )
```

No decision without `submit_decision` → 502 `AGENT_NO_DECISION`.

### `schemas.py` additions

```python
class ChatMeta(BaseModel):
    toolCallsUsed: int = 0

class ChatOut(BaseModel):
    reply: str
    decision: Optional[Decision] = None
    warning: Optional[AgentWarning] = None
    meta: Optional[ChatMeta] = None
```

## Design spec

### HTTP status mapping (wire test)

| Scenario | Endpoint | HTTP | Body key |
|----------|----------|------|----------|
| Tool limit | chat | 200 | `warning.code=AGENT_TOOL_LIMIT` |
| Tool limit | analyze | 429 | `error.code=AGENT_TOOL_LIMIT` |
| Recursion limit | chat | 200 | `warning` |
| No decision | analyze | 502 | `error.code=AGENT_NO_DECISION` |
| LLM down | both | 503 | `error.code=LLM_UNAVAILABLE` |
| Unknown bug | both | 500 | `error.code=INTERNAL_ERROR` |

### Response wireframe — chat warning

```
┌─────────────────────────────────────────┐
│ ChatPanel                               │
│ ┌─────────────────────────────────────┐ │
│ │ ⚠ This analysis needed too many     │ │
│ │   steps. Try a simpler question.    │ │
│ │                        [Retry]      │ │
│ └─────────────────────────────────────┘ │
│ Assistant: I couldn't finish the full…  │
└─────────────────────────────────────────┘
```

## Done when

- [ ] No route returns `detail=str(python_exception)` to client
- [ ] Chat returns `warning` object on tool/recursion limit (200)
- [ ] Analyze returns structured `error` JSON with correct HTTP status
- [ ] 404 unchanged for missing experiment
- [ ] Server logs full exception; client sees safe message only
