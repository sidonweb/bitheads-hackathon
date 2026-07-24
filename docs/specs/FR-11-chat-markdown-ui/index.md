# FR-11: Formatted Chat UI (Markdown Rendering) — Spec Index

| Field | Value |
|-------|--------|
| Source FR | [FR-11-chat-markdown-ui.md](requirements.md) |
| Priority | P1 |
| Depends on | — |
| Blocks | [FR-06](../FR-06-streaming-chat/requirements.md) (streaming must render formatted output too) |

## Problem

Assistant messages in `ChatPanel` render as plain text (`{m.text}`), so markdown from the agent (`**bold**`, lists, code blocks) appears literally and looks unprofessional.

## Solution

New `FormattedMessage.jsx` using **`react-markdown`** + **`remark-gfm`** with **`rehype-sanitize`** (no raw HTML passthrough). User bubbles remain plain text.

## Scope

| In scope | Out of scope |
|----------|--------------|
| Headings, bold/italic, lists, inline code, code blocks, tables | Full Notion-style editor for user input |
| Links open in new tab with `rel="noopener noreferrer"` | HTML passthrough from model |
| XSS prevention via sanitize | Syntax highlighting for every language (nice-to-have) |
| CSS tokens under `.assistant-text` | Markdown in user bubbles |

## Dependencies (npm)

```json
{
  "react-markdown": "^9.x",
  "remark-gfm": "^4.x",
  "rehype-sanitize": "^6.x"
}
```

## Tasks

| # | Task | File |
|---|------|------|
| 1 | Install markdown dependencies | [tasks/01-install-deps.md](./tasks/01-install-deps.md) |
| 2 | FormattedMessage component | [tasks/02-formatted-message-component.md](./tasks/02-formatted-message-component.md) |
| 3 | Integrate into ChatPanel | [tasks/03-integrate-chat-panel.md](./tasks/03-integrate-chat-panel.md) |
| 4 | Markdown typography styles | [tasks/04-markdown-styles.md](./tasks/04-markdown-styles.md) |
| 5 | XSS and link safety verification | [tasks/05-xss-link-safety.md](./tasks/05-xss-link-safety.md) |

## Test plan

[tests/test-plan.md](./tests/test-plan.md) — minimum 8 manual/automated cases.

## Acceptance criteria (from FR)

- [ ] `**bold**` and `- list item` render formatted, not raw characters.
- [ ] Code blocks use monospace + background; inline code styled.
- [ ] User bubbles stay plain text (no markdown injection risk from PM).
- [ ] XSS: `<script>` in model output does not execute.

## Open questions

- Also render markdown in `Decision.reasoning` / FR-09 executive summary? Defer unless PM feedback requests it; keep FR-11 scoped to chat assistant turns.
