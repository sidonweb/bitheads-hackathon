# Task 02: LangGraph astream_events Integration

## Location

- `packages/copilot-backend/app/agent/graph.py` — new `chat_turn_stream()` async generator
- `packages/copilot-backend/app/services/chat_stream.py` — delegates to agent stream

## Dependencies

- Task 01 (route shell exists)
- Existing `chat_turn()` logic (thread id, tools, checkpointer)
- LangGraph `astream_events` v2 API

## What to build

1. Add `async def chat_turn_stream(exp, message, session_id) -> AsyncIterator[StreamEvent]` (internal typed dict or dataclass).
2. Reuse the same graph, tools, and `thread_id = f"{exp['id']}:{session_id}"` as `chat_turn`.
3. Call `graph.astream_events(input, config, version="v2")` and filter:
   - `on_chat_model_stream` → emit `{ type: "token", content }` from chunk text
   - `on_tool_start` → emit `{ type: "tool_start", name, label }` (label from Task 03)
   - `on_tool_end` → emit `{ type: "tool_end", name, ok }` (ok = no error in output)
4. After stream completes, read final state for `decision` (same path as `submit_decision` capture).
5. Emit `{ type: "decision", ... }` if present, then `{ type: "done", toolCallsUsed }`.
6. Respect `AGENT_LLM_TIMEOUT_SEC` via `asyncio.wait_for` around the stream loop.

## Design spec

### Event filtering rules

| LangGraph event | Map to | Skip when |
|-----------------|--------|-----------|
| `on_chat_model_stream` | `token` | Empty content string |
| `on_tool_start` | `tool_start` | Internal/no-op tools |
| `on_tool_end` | `tool_end` | Duplicate end for same run id |

**Do not** stream raw tool arguments or SQL result JSON to the client in v1.5 — labels only.

### Thread isolation

Same session rules as non-streaming chat:

```
thread_id = f"{experiment_id}:{sessionId}"
```

Switching sessions in the sidebar must not leak prior stream state.

### Determinism boundary

The stream may narrate progress, but **decision numbers and verdict** still come from `run_statistics` + `submit_decision` — never from LLM token text.

## Done when

- [ ] `chat_turn_stream` yields token events during a full analysis prompt
- [ ] Tool start/end events fire for SQL and browser tools
- [ ] Final `decision` object matches non-streaming `/chat` output for same prompt
- [ ] Timeout raises `AgentError` with `LLM_UNAVAILABLE`
- [ ] Unit smoke: import `chat_turn_stream` without circular imports
