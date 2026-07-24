# FR-10: One-Click Analyze

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P2 |
| Problem statement | Reduction in experiment analysis time |
| Depends on | FR-05, G7 in [REFINEMENT.md](./REFINEMENT.md), existing POST `/analyze` |
| Blocks | — |

## Main branch context (gap)

`analyze_experiment()` sends only: *"Analyze this experiment now and submit a decision."* — **no variant URLs**. On main, the agent is instructed to stop and ask the PM for URLs if missing. One-click analyze will fail or stall unless:

- **Option A:** Inject URLs from `experiments.variant_a_url` / `variant_b_url` into the analyze prompt when present
- **Option B:** Accept `{ variantAUrl, variantBUrl }` on `POST /analyze` body
- **Option C:** UI requires URLs saved on experiment before enabling the button

Resolve via G7 before shipping FR-10 UI.

## Summary

Expose existing `/analyze` endpoint in dashboard UI — button triggers full agent workflow without typing in chat.

## Goals

- Faster demo path for judges.
- Clear separation: chat = discussion; Analyze = full workflow.

## Non-goals

- Replacing chat analysis.

## UI

- Button in Experiment drawer or header: "Run full analysis".
- Disabled while busy; shows spinner.
- On success: populate Decision card (same as chat decision).
- On failure: show structured error from FR-05.

## API

Existing (extend per G7):

```
POST /experiments/{id}/analyze → Decision
```

Optional request body:

```json
{
  "variantAUrl": "http://localhost:5173/?variant=A",
  "variantBUrl": "http://localhost:5173/?variant=B"
}
```

Optional pre-hook: call FR-03 preflight first; warn if not ready (non-blocking).

## Acceptance criteria

- [ ] Button triggers analyze and shows Decision without chat message.
- [ ] Errors show user-friendly code/message.
- [ ] Double-click prevented while in flight.

## Open questions

- [ ] Block analyze if preflight fails hard?
