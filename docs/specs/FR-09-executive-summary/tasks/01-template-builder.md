# Task 01: Template builder utility

## Location

- `packages/dashboard/src/lib/executiveSummary.js` (new)

## Dependencies

- Existing `Decision` shape returned by copilot-backend (`decision`, `confidence`, `p_value`, `uplift`, `sample_size`, `inferred_metric`, `reasoning`, `sql_used`, `rule_rationale`)
- None (pure function, no API changes)

## What to build

Export `buildExecutiveSummary(decision)` that returns an array of exactly **three** plain-English strings (bullet body text only — no leading `•`).

The function must be deterministic: same `Decision` input → same bullets every time.

## Design spec

### Input guards

- If `decision` is null/undefined, return `[]`.
- If `inferred_metric` is missing, use `"the primary success metric"` as fallback label.
- If `sample_size.A` or `sample_size.B` is missing, omit per-variant counts from bullet 2 or say `"insufficient sample data"`.

### Bullet templates

**Bullet 1 — What changed and by how much**

```
Variant B drove {signedPct(uplift)} relative uplift in {humanizeMetric(inferred_metric)}.
```

- `signedPct`: `(uplift >= 0 ? '+' : '') + (uplift * 100).toFixed(1) + '%'`
- `humanizeMetric`: replace `_` with spaces (e.g. `checkout_completed` → `checkout completed`)

Optional enhancement: if experiment variant names are ever passed, prefer `"Variant B's checkout CTA"` style — v1 may use generic "Variant B".

**Bullet 2 — Statistical confidence**

If `p_value < 0.05`:

```
Result is statistically significant (p = {p_value.toFixed(4)}) with {sample_size.A} users in Variant A and {sample_size.B} in Variant B.
```

Else:

```
Result is not yet statistically significant (p = {p_value.toFixed(4)}); continue collecting data before acting.
```

**Bullet 3 — Recommendation**

Map `decision.decision` to plain English:

| Verdict | Text |
|---------|------|
| `Scale` | `Recommendation: Scale — roll out Variant B to all traffic.` |
| `Rollback` | `Recommendation: Rollback — revert to Variant A.` |
| `Continue` | `Recommendation: Continue — keep the experiment running.` |
| `Stop` | `Recommendation: Stop — no meaningful difference detected.` |

### Exclusions

- **Never** include `sql_used`, `rule_rationale`, or raw SQL fragments.
- **Never** call an LLM.

### Exports

```js
export function buildExecutiveSummary(decision) { /* returns string[] */ }
export function humanizeMetric(name) { /* helper, exported for tests */ }
```

## Done when

- [ ] `buildExecutiveSummary(mockDecision)` returns 3 strings for a typical Scale decision.
- [ ] Non-significant decisions produce the "not yet statistically significant" bullet 2.
- [ ] No SQL substrings appear in output for decisions that include `sql_used`.
- [ ] Unit-testable without React (pure JS module).
