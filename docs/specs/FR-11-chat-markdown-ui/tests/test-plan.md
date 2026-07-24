# FR-11: Formatted Chat UI — Test Plan

Minimum 8 detailed test cases for markdown rendering and XSS safety.

## Prerequisites

- Dashboard running (`npm run dev` in `packages/dashboard` or docker compose)
- Copilot-backend reachable for live agent replies (optional for mocked tests)

---

### TC-01: Bold and italic render correctly

| Field | Value |
|-------|--------|
| **Objective** | Inline markdown formatting displays properly. |
| **Steps** | 1. Mock assistant message or trigger agent reply containing `**bold**` and `*italic*`. 2. View chat bubble. |
| **Expected** | Visual bold and italic text. Raw `**` and `*` characters not visible. |
| **Priority** | P0 |

---

### TC-02: Unordered list renders

| Field | Value |
|-------|--------|
| **Objective** | Bullet lists formatted. |
| **Steps** | Display assistant text: `- Item one\n- Item two\n- Item three` |
| **Expected** | HTML `<ul>` with three `<li>` elements. Indentation and bullets per CSS task 04. |
| **Priority** | P0 |

---

### TC-03: Ordered list renders

| Field | Value |
|-------|--------|
| **Objective** | Numbered lists work. |
| **Steps** | Assistant text: `1. First\n2. Second\n3. Third` |
| **Expected** | Ordered list with correct numbering. |
| **Priority** | P1 |

---

### TC-04: Fenced code block styling

| Field | Value |
|-------|--------|
| **Objective** | Code blocks use monospace and background. |
| **Steps** | Assistant text with GFM fence:\n\n\`\`\`sql\nSELECT 1;\n\`\`\` |
| **Expected** | `<pre><code>` block with monospace font and background per styles. SQL visible, not executed. |
| **Priority** | P0 |

---

### TC-05: Inline code styling

| Field | Value |
|-------|--------|
| **Objective** | Backtick code distinct from body text. |
| **Steps** | Assistant text: `Use event \`checkout_completed\` for conversions.` |
| **Expected** | `checkout_completed` in styled inline `<code>`, not a code block. |
| **Priority** | P0 |

---

### TC-06: User bubble — no markdown injection

| Field | Value |
|-------|--------|
| **Objective** | PM input stays plain text. |
| **Steps** | 1. Send user message: `**I am not bold**` and `<script>alert(1)</script>`. 2. Inspect user bubble DOM. |
| **Expected** | Literal asterisks and angle brackets shown. No `<strong>`, no script execution, no HTML parsing. |
| **Priority** | P0 |

---

### TC-07: XSS — script tag in assistant output

| Field | Value |
|-------|--------|
| **Objective** | Sanitizer blocks script injection from model. |
| **Steps** | Render assistant message (mock): `<script>alert('xss')</script>Summary here.` |
| **Expected** | No alert dialog. Script tag stripped or escaped; "Summary here." still visible. |
| **Priority** | P0 |

---

### TC-08: XSS — javascript: link

| Field | Value |
|-------|--------|
| **Objective** | Dangerous link protocols blocked. |
| **Steps** | Render: `[click me](javascript:alert(1))` |
| **Expected** | Link removed or href sanitized; click does not execute JS. |
| **Priority** | P0 |

---

### TC-09: External link opens new tab safely

| Field | Value |
|-------|--------|
| **Objective** | Valid https links work with security attrs. |
| **Steps** | Render: `See [variant A](http://localhost:5173/?variant=A).` Click link. |
| **Expected** | New tab opens. `<a>` has `target="_blank"` and `rel="noopener noreferrer"`. |
| **Priority** | P1 |

---

### TC-10: GFM table renders readably

| Field | Value |
|-------|--------|
| **Objective** | Tables supported via remark-gfm. |
| **Steps** | Assistant text with markdown table (header + 2 rows). |
| **Expected** | `<table>` with borders/spacing per CSS. Readable in chat width; horizontal scroll if needed. |
| **Priority** | P2 |

---

### TC-11: Error assistant messages stay plain

| Field | Value |
|-------|--------|
| **Objective** | Error path not markdown-rendered. |
| **Steps** | Force chat API failure (stop backend). Send message. |
| **Expected** | Red/error assistant bubble with plain `Something went wrong: …` — no partial markdown parse. |
| **Priority** | P1 |

---

### TC-12: Build passes with new deps

| Field | Value |
|-------|--------|
| **Objective** | Production build includes markdown stack. |
| **Steps** | `cd packages/dashboard && npm run build` |
| **Expected** | Exit code 0. Bundle size increase acceptable for hackathon. |
| **Priority** | P0 |
