# Task 04: Styles and typography

## Location

- `packages/dashboard/src/styles.css` (modify — append near existing `.decision-card` block ~line 964)

## Dependencies

- Task 02: `ExecutiveSummary.jsx` class names
- Existing design tokens: `.field-label`, `.decision-card`, light theme palette

## What to build

CSS for `.executive-summary` that matches dashboard typography — readable, scannable, distinct from technical stats below.

## Design spec

### Classes

```css
.executive-summary { ... }
.executive-summary-title { ... }
.executive-summary-list { ... }
.executive-summary-list li { ... }
```

### Visual guidelines

- **Title:** Same weight as `.field-label` but slightly larger (e.g. `0.75rem` uppercase tracking or `0.875rem` semibold — match dashboard section headers).
- **List:** `margin: 0.75rem 0 1rem; padding-left: 1.25rem;` — standard disc bullets.
- **List items:** `line-height: 1.5; color: var(--text-primary)` or equivalent token; `margin-bottom: 0.35rem`.
- **Separator:** Optional subtle bottom border (`1px solid #e2e8f0`) between summary and verdict badge.
- **Background:** Optional very light tint (`#f8fafc`) with `border-radius: 8px` and `padding: 0.75rem 1rem` to visually group the three bullets.

### Responsive

- Bullets wrap on narrow viewports; no horizontal scroll.
- Do not use fixed widths.

### Dark/light

- Follow existing `.decision-card` light theme only (no new theme system).

## Done when

- [ ] Executive summary is visually distinct from `.stat-row` and `.reasoning`.
- [ ] Three bullets are easy to select/copy as a block.
- [ ] Styles do not break existing decision card layout.
- [ ] `npm run build` in `packages/dashboard` succeeds.
