# FR-06: Streaming Chat Responses

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P1 |
| Problem statement | Reduces analysis time UX; transparency during monitoring/analysis |
| Depends on | FR-05 |
| Blocks | — |

## Summary

Add SSE endpoint for chat that streams LLM tokens and tool lifecycle events to the dashboard. Non-streaming `/chat` remains as fallback.

## Goals

- PM sees progress during long analyses (browser + SQL steps).
- Perceived latency reduction via token streaming.

## Non-goals

- Streaming on `/analyze` in v1.5 (optional follow-up).
- WebSocket infrastructure.

## API design

### `POST /experiments/{id}/chat/stream`

**Request:** same body as `/chat`:

```json
{ "message": "…", "sessionId": "…" }
```

`sessionId` is **required** for correct thread isolation (matches main `ChatIn.sessionId`).

**Response:** `text/event-stream`

Events (SSE `event:` + `data:` JSON):

| event | data |
|-------|------|
| `token` | `{ "content": "partial text" }` |
| `tool_start` | `{ "name": "ask_data_analyst", "label": "Querying experiment data" }` |
| `tool_end` | `{ "name": "ask_data_analyst", "ok": true }` |
| `warning` | `{ "code", "message", "retryable" }` |
| `decision` | `{ …Decision object… }` |
| `done` | `{ "toolCallsUsed": 8 }` |
| `error` | `{ "code", "message", "retryable" }` |

Terminal event always sent (`done` or `error`).

## Implementation notes

- Use LangGraph `astream_events` (v2) filtered for `on_chat_model_stream`, `on_tool_start`, `on_tool_end`.
- Map tool names to human labels in `app/agent/stream_labels.py`.
- Wrap stream in try/finally; emit `error` event on `AgentError`.
- FastAPI: `StreamingResponse(event_generator(), media_type="text/event-stream")`.
- Disable nginx buffering in prod docs (`X-Accel-Buffering: no`) — note for deployment.

## UI

- `ChatPanel`: fetch stream reader; append tokens to assistant bubble.
- Show step indicator from `tool_start` / `tool_end`.
- On `error`, stop stream and show banner.
- Fallback: if stream endpoint fails, retry non-streaming `/chat`.

## Guardrails

- Stream timeout: same as `AGENT_LLM_TIMEOUT_SEC`.
- Client disconnect → cancel agent task (best-effort).

## Acceptance criteria

- [ ] First token within 5s for typical analysis prompt.
- [ ] Tool steps visible before final decision.
- [ ] Stream ends with `done` or `error` always.
- [ ] Non-streaming endpoint still works unchanged.

## Open questions

- [ ] Stream only assistant tokens or also tool JSON snippets?
- [ ] One stream per experiment concurrency policy?
