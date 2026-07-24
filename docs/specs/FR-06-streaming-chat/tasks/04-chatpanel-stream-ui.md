# Task 04: ChatPanel Stream Consumer

## Location

- `packages/dashboard/src/api.js` — `chatStream(message, sessionId, onEvent, signal)`
- `packages/dashboard/src/components/ChatPanel.jsx` — primary consumer
- `packages/dashboard/src/components/StreamStepIndicator.jsx` — new component
- `packages/dashboard/src/styles` or co-located CSS for step indicator

## Dependencies

- Task 01–03 (working SSE endpoint)
- Existing message state in `App.jsx` / `ChatPanel` props

## What to build

1. Add `chatStream()` using `fetch` + `ReadableStream` reader (not EventSource — POST body required).
2. Parse SSE frames (`event:` + `data:` lines); call `onEvent({ event, data })` per frame.
3. In `ChatPanel.send()`:
   - Prefer `chatStream` over `chat()`
   - Maintain `streamingText` on the in-flight assistant message
   - Append `token.content` to assistant bubble in real time
4. Replace static "Analyzing variants…" busy state with `StreamStepIndicator`:
   - Active step from latest `tool_start` without matching `tool_end`
   - Completed steps show checkmark
5. On `decision` event: call `onDecision(data)`; render `Decision` card as today.
6. On `done`: finalize message text, clear step state, set `busy = false`.
7. On `warning`: show inline amber banner above composer (non-blocking).

## Design spec

### Streaming message lifecycle

```
User sends → user bubble appears immediately
           → empty assistant bubble created
           → tokens append character-by-character (or chunk-by-chunk)
           → step indicator updates during tools
           → decision card appended when event arrives
           → stream closes
```

### Visual states

| State | UI |
|-------|-----|
| Waiting for first token | Subtle typing dots inside assistant bubble |
| Streaming | Growing text, cursor optional |
| Tool running | Step row with animated dot + label |
| Tool done | Step row with green check |
| Warning | Amber strip: "Analysis partially completed — …" |

### Accessibility

- Step indicator uses `aria-live="polite"` for active step changes
- Send button disabled while `busy`; textarea disabled during stream

## Done when

- [ ] PM sees first assistant text within 5s on "Analyze the experiment…" prompt
- [ ] Tool steps visible before decision card renders
- [ ] Decision card identical to non-streaming path
- [ ] Multiple messages in one session stream independently without text bleed
- [ ] `npm run build` in `packages/dashboard` passes
