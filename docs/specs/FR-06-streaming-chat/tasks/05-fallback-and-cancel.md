# Task 05: Fallback + Client Disconnect Handling

## Location

- `packages/dashboard/src/api.js` — fallback logic in `chatStream` / wrapper
- `packages/dashboard/src/components/ChatPanel.jsx` — `AbortController` on unmount / new send
- `packages/copilot-backend/app/services/chat_stream.py` — cancel on disconnect
- `docs/` or deployment notes — nginx buffering header

## Dependencies

- Task 04 (stream UI wired)
- Existing non-streaming `chat()` in `api.js`

## What to build

1. **Fallback:** If stream request fails before first byte (network, 404, 500, wrong content-type), automatically retry once via `chat()` and show full reply.
2. **Mid-stream failure:** On terminal `error` event, show error banner with `message` and `retryable` hint; do not fallback (partial text may exist).
3. **Abort:** Pass `AbortSignal` from `ChatPanel`; abort prior stream when user sends a new message or navigates away.
4. **Server cancel:** On client disconnect, cancel the agent asyncio task (best-effort — log at WARN if cancel fails).
5. Document `X-Accel-Buffering: no` for nginx in copilot-backend or dashboard deploy notes.

## Design spec

### Fallback decision tree

```
POST /chat/stream
├─ HTTP error before body → fallback to POST /chat
├─ Stream starts → no fallback
│   ├─ event: error (terminal) → show banner, keep partial text
│   └─ event: done → success
└─ Connection dropped → show "Connection lost" if no terminal event
```

### Error banner (client)

```
┌──────────────────────────────────────────────────┐
│ ⚠ Could not complete streaming analysis.         │
│   Tool limit reached. Try a shorter question.    │
│   [ Retry ]  (only if retryable)                 │
└──────────────────────────────────────────────────┘
```

### Disconnect (server)

When `request.is_disconnected()` or generator `CancelledError`:

- Stop consuming `astream_events`
- Log: `WARN stream cancelled experiment_id=… session_id=…`
- Do not emit further events

## Done when

- [ ] Stopping copilot-backend mid-stream does not hang the dashboard (timeout + error UI)
- [ ] Disabling stream route (404) triggers silent fallback to `/chat` with full reply
- [ ] Sending a second message while first stream runs aborts the first request
- [ ] Terminal `error` always clears `busy` state and re-enables composer
- [ ] Non-streaming `/chat` still works when called directly
