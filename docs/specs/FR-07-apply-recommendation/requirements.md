# FR-07: Apply Recommendation (Scale / Rollback)

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P1 |
| Problem statement | Recommends next best action — make it actionable |
| Depends on | Existing Decision + PATCH experiment |
| Blocks | — |

## Summary

When decision is **Scale** or **Rollback**, PM can apply it with one click by updating `traffic_split` via existing API. Includes confirmation modal and audit log entry.

## Goals

- Close the loop: recommendation → action.
- Demonstrate adoption of AI guidance (eval metric).

## Non-goals

- Auto-apply without user confirmation.
- Changing variant URLs or code deployment.

## Behavior

| Decision | Action on Apply |
|----------|-----------------|
| Scale | `traffic_split = 100` (100% to Variant B) |
| Rollback | `traffic_split = 0` (100% to Variant A) |
| Continue / Stop | No apply button (or disabled with tooltip) |

## API

Reuse `PATCH /experiments/{id}` with `{ "trafficSplit": 0 | 100 }`.

Optional audit:

### `POST /experiments/{id}/decisions/{decisionId}/apply`

If decision objects gain server-side ids later; for v1.5 client-side apply via PATCH is sufficient.

**Response**

```json
{
  "ok": true,
  "trafficSplit": 100,
  "message": "Variant B is now at 100% traffic."
}
```

## UI

- On `Decision` card: button "Apply Scale — roll out Variant B".
- Confirmation: "This will send 100% traffic to Variant B. Continue?"
- Success toast + drawer traffic slider updates.
- Error: show PATCH failure message.

## Guardrails

- Disable apply if experiment `status != 'running'` (optional warn).
- Disable if preflight has critical fails (optional link to FR-03).

## Acceptance criteria

- [ ] Scale decision shows apply button; Continue does not.
- [ ] Apply sets traffic to 100 and UI reflects change.
- [ ] PATCH failure shows user message, no silent fail.

## Open questions

- [ ] Record apply events in new `experiment_actions` table or log only?
