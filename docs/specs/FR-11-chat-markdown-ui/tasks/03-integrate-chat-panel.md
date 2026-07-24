# Task 03: Integrate into ChatPanel

## Location

- `packages/dashboard/src/components/ChatPanel.jsx` (modify)

## Dependencies

- Task 02: `FormattedMessage.jsx`
- Existing message model: `{ role, text, error? }`

## What to build

Replace plain-text assistant rendering with `FormattedMessage` for assistant turns only. Keep user bubbles as plain text.

## Design spec

### Change

**Before** (line ~91):

```jsx
<div className="assistant-text">{m.text}</div>
```

**After**:

```jsx
<FormattedMessage text={m.text} className="assistant-text" />
```

### Scope of markdown rendering

| Role | Renderer |
|------|----------|
| `user` | Plain text in `.user-bubble` — **no markdown** |
| `assistant` | `FormattedMessage` |
| `assistant` + `error: true` | Plain text (errors are system strings, not markdown) |

### Thinking / loading state

Keep typing indicator as plain HTML — do not run markdown on "Analyzing variants…".

### Decision card

`Decision` component unchanged in this task — rendered separately below messages.

### Streaming note (FR-06)

Structure `FormattedMessage` so `text` prop can update incrementally later — no internal state that blocks prop updates.

## Done when

- [ ] Agent reply with `**bold**` and `- list` renders formatted in chat.
- [ ] User messages with `**not bold**` stay literal.
- [ ] Error assistant bubbles (`Something went wrong: …`) remain plain text.
- [ ] Chat scroll behavior unchanged after long formatted replies.
