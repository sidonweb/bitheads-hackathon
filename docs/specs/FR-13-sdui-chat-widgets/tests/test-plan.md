# FR-13 Test Plan

## Manual — block rendering

| ID | Steps | Expected |
|----|-------|----------|
| T1 | Complete analysis in chat | ≥1 chart + metric grid visible inline |
| T2 | Response with only `reply`, no blocks | Markdown renders as today |
| T3 | Inject unknown block type in mock | "Unsupported widget" fallback |
| T4 | Scale decision | `actions` block shows Apply Scale |
| T5 | Continue decision | Apply button absent/disabled |

## Manual — streaming

| ID | Steps | Expected |
|----|-------|----------|
| T6 | Stream analysis | `markdown` tokens first, `block` events before `done` |
| T7 | Chart block arrives mid-stream | Chart mounts without flicker |

## API

| ID | Steps | Expected |
|----|-------|----------|
| T8 | GET chat response JSON | `blocks` array validates against schema |
| T9 | Block with 51 chart points | Server truncates or rejects |

## Regression

| ID | Steps | Expected |
|----|-------|----------|
| T10 | Legacy `decision` field still sent | Old Decision card works until migration complete |
| T11 | FR-11 markdown in markdown block | Bold/lists render |

## Security

| ID | Steps | Expected |
|----|-------|----------|
| T12 | Malicious `actionId` not in enum | Button not rendered |
| T13 | markdown block with `<script>` | Sanitized via rehype-sanitize |
