# FR-03: Pre-Flight Validation

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P0 |
| Problem statement | Suggests configurations and validates setup before launch; detects config issues |
| Depends on | — |
| Blocks | — |

## Main branch context

On `main`, the **analysis agent does not read variant URLs from the experiment row** — the PM pastes them in chat. Preflight must still validate URLs, so checks C1/C2 use URLs from (in order):

1. Optional query/body params on the preflight request (recommended for demo)
2. `experiments.variant_a_url` / `variant_b_url` if stored
3. **Warn** (not fail) if no URLs anywhere: "Paste variant URLs in chat or save them on the experiment before launch."

URL reachability should test the same deep link the agent uses: append `screen=checkout` when the URL has no `screen` param (matches `_deep_link_checkout` in `graph.py`).

## Summary

Deterministic pre-launch checklist run on demand or before "Analyze". Returns pass/warn/fail per check with human-readable messages. No LLM required for core checks.

## Goals

- Catch misconfiguration before analysis wastes agent tool budget.
- Surface overlapping-experiment risk (best-effort with current schema).

## Non-goals

- Blocking experiment start in API (advisory only in v1.5).
- Full multi-experiment overlap engine.

## Checks

| ID | Check | Pass | Warn | Fail |
|----|-------|------|------|------|
| C1 | Variant A URL reachable | 2xx/3xx | timeout slow | unreachable |
| C2 | Variant B URL reachable | same | same | same |
| C1b | URLs provided | at least one source | neither chat nor DB URLs | — (warn only) |
| C3 | Events exist for experiment | count > 0 | count < 100 total | count = 0 |
| C4 | Exposures (`page_view`) per variant | both ≥ 1 | one variant 0 | both 0 |
| C5 | Traffic split | sum logic 100% | split 0 or 100 on one side only | invalid int |
| C6 | Hypothesis non-empty | present | — | empty |
| C7 | Sample size guidance | both variants ≥ 300 exposures | 50–299 | < 50 |
| C8 | Overlap (best-effort) | no user in 2+ running exps | — | users in 2+ exps |

C8 SQL (when multiple experiments exist):

```sql
SELECT user_id, COUNT(DISTINCT experiment_id) AS n
FROM universal_events
GROUP BY user_id
HAVING COUNT(DISTINCT experiment_id) > 1
LIMIT 5;
```

With only `exp_1`, C8 always passes with note "single experiment in system".

## API design

### `GET /experiments/{id}/preflight`

Optional query params (override stored URLs):

```
?variantAUrl=http://localhost:5173/?variant=A&variantBUrl=http://localhost:5173/?variant=B
```

**Response 200**

```json
{
  "ready": false,
  "score": "4/8",
  "checks": [
    {
      "id": "C1",
      "name": "Variant A URL reachable",
      "status": "pass",
      "message": "HTTP 200 in 120ms"
    }
  ],
  "evaluatedAt": "2026-07-24T20:00:00Z"
}
```

`ready: true` when no `fail` statuses (warns allowed).

## Implementation notes

- Service: `app/services/preflight.py` — pure functions, unit-testable.
- URL checks: `httpx` HEAD/GET with 5s timeout.
- Cache results 60s per experiment id (avoid hammering storefront).

## UI

- Card in Experiment drawer: checklist with icons.
- "Re-run checks" button.
- Link failed checks to remediation hint.

## Error handling

- URL check failure for one variant → that check `fail`, others still run.
- DB unavailable → 503 `UPSTREAM_ERROR`, message "Cannot reach experiment data."

## Acceptance criteria

- [ ] All 8 checks returned in stable order.
- [ ] Unreachable URL produces `fail` with URL in message.
- [ ] Zero events produces C3 `fail`.
- [ ] Response time < 10s p95 with URL checks.

## Open questions

- [ ] Run preflight automatically before `/analyze`?
- [ ] Store last preflight result on experiment row?
- [ ] Resolve G6 in [REFINEMENT.md](./REFINEMENT.md): body vs DB URLs for C1/C2?
