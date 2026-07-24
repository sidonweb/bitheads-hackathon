# Task 04: Markdown typography styles

## Location

- `packages/dashboard/src/styles.css` (modify — extend `.assistant-text` section)

## Dependencies

- Task 02–03: FormattedMessage integrated in ChatPanel

## What to build

CSS rules so rendered markdown matches dashboard visual language — readable hierarchy without overwhelming the chat layout.

## Design spec

### Selector scope

Nest under `.assistant-text` to avoid affecting user bubbles or decision card:

```css
.assistant-text h1, .assistant-text h2, .assistant-text h3 { ... }
.assistant-text p { ... }
.assistant-text ul, .assistant-text ol { ... }
.assistant-text li { ... }
.assistant-text code { ... }
.assistant-text pre { ... }
.assistant-text pre code { ... }
.assistant-text table { ... }
.assistant-text a { ... }
```

### Typography guidelines

| Element | Style |
|---------|--------|
| `h3` | `font-size: 1rem; font-weight: 600; margin: 0.75rem 0 0.35rem;` |
| `p` | `margin: 0.35rem 0; line-height: 1.55;` |
| `ul`, `ol` | `margin: 0.35rem 0 0.5rem; padding-left: 1.25rem;` |
| `li` | `margin-bottom: 0.25rem;` |
| Inline `code` | Monospace, `background: #f1f5f9`, `padding: 0.1em 0.35em`, `border-radius: 4px`, `font-size: 0.9em` |
| `pre` | `background: #f8fafc`, `border: 1px solid #e2e8f0`, `border-radius: 8px`, `padding: 0.75rem`, `overflow-x: auto` |
| `pre code` | No extra background; inherit monospace |
| `table` | Full width, collapsed borders, small font for GFM tables |
| `a` | Link color matching dashboard accent; underline on hover |

### First-child margin

Reset top margin on first element inside `.assistant-text` to align with bubble padding.

### Compatibility

- Must not break `.assistant-text.thinking` typing dots layout.
- Tables wider than chat column scroll horizontally inside `pre`-style overflow.

## Done when

- [ ] Bulleted lists are visually indented with disc markers.
- [ ] Code blocks distinguishable from inline code.
- [ ] Headings smaller than welcome `h1` — chat hierarchy clear.
- [ ] No global `p` or `code` styles leak to user bubbles.
