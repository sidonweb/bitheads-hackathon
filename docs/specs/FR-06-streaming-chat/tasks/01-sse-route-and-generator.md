# Task 01: SSE Route + Event Generator

## Location

- `packages/copilot-backend/app/routes/chat.py` — register new route
- `packages/copilot-backend/app/services/chat_stream.py` — new module (async generator)
- `packages/copilot-backend/app/main.py` — ensure router includes stream route

## Dependencies

- FR-05: `AgentError` with `{ code, message, retryable }` shape
- Existing `ChatIn` schema (`packages/copilot-backend/app/schemas.py`)
- `config.AGENT_LLM_TIMEOUT_SEC` for stream timeout

## What to build

1. Add `POST /experiments/{experiment_id}/chat/stream` alongside existing `/chat`.
2. Validate experiment exists (404 if missing); validate `sessionId` is present (422 if missing).
3. Implement `async def event_generator(...)` that yields SSE frames:
   ```
   event: token
   data: {"content":"..."}

   ```
4. Wrap generator in `try/finally`; on any `AgentError`, emit `error` event before closing.
5. Return `StreamingResponse(event_generator(), media_type="text/event-stream", headers={...})`.
6. Set response headers: `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`.

## Design spec

### PM-visible behavior

The dashboard opens a long-lived HTTP connection when the PM sends a chat message. Tokens appear in the assistant bubble as they arrive — no change to the send button UX beyond faster feedback.

### Server contract

```
POST /experiments/exp_1/chat/stream
Content-Type: application/json

{ "message": "Analyze and recommend", "sessionId": "s_abc123" }

→ 200 text/event-stream
→ sequence: token* → tool_start/tool_end* → [warning?] → [decision?] → done | error
```

### Error mapping

| Condition | SSE `error.code` | HTTP |
|-----------|------------------|------|
| Experiment not found | (no stream — 404 JSON) | 404 |
| Missing sessionId | (no stream — 422 JSON) | 422 |
| Agent timeout | `LLM_UNAVAILABLE` | 200 stream + terminal `error` |
| Tool limit (FR-05) | `AGENT_TOOL_LIMIT` | 200 stream + terminal `error` |

## Done when

- [ ] Route registered and returns `text/event-stream` for valid requests
- [ ] Missing `sessionId` returns 422 with structured error (not a stream)
- [ ] Generator always emits terminal `done` or `error` event
- [ ] `curl -N` against the endpoint shows incremental SSE frames during analysis
- [ ] Existing `POST /chat` behavior is untouched
