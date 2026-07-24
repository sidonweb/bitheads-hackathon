# FR-11: Formatted Chat UI (Markdown Rendering)

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P1 |
| Problem statement | Copilot replies should look professional, not raw markdown |
| Depends on | — |
| Blocks | FR-06 (streaming should render formatted output too) |

## Summary

Assistant messages in `ChatPanel` currently render as plain text (`{m.text}`), so `**bold**`, lists, and code blocks show literally. Render markdown safely with readable typography.

## Goals

- Headings, bold/italic, bullet/numbered lists, inline code, code blocks render correctly.
- Links open in new tab with `rel="noopener"`.
- Tables (if agent uses them) render readably.

## Non-goals

- Full Notion-style editor for user input.
- HTML passthrough from model (sanitize only).
- Syntax highlighting for every language (optional nice-to-have).

## UI

- New component: `FormattedMessage.jsx` (or extend `ChatPanel`).
- Use `react-markdown` + `remark-gfm`; sanitize with `rehype-sanitize` (no raw HTML).
- Style via existing CSS tokens (`.assistant-text` variants for `h3`, `ul`, `code`, `pre`).

## Acceptance criteria

- [ ] `**bold**` and `- list item` render formatted, not raw characters.
- [ ] Code blocks use monospace + background; inline code styled.
- [ ] User bubbles stay plain text (no markdown injection risk from PM).
- [ ] XSS: `<script>` in model output does not execute.

## Open questions

- [ ] Also render markdown in `Decision.reasoning` / FR-09 executive summary?
