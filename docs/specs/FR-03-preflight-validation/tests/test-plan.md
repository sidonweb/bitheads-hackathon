# FR-03 Test Plan: Pre-Flight Validation

## Test strategy

| Layer | Approach |
|-------|----------|
| Unit | Each check function with mocked DB rows and httpx responses |
| API | curl GET preflight with/without URL query params |
| UI | PreflightCard manual checklist verification |
| Integration | Fix failing checks → re-run → ready becomes true |
| Performance | Measure p95 latency with both URL checks |

**Environment:** Docker stack; seeded `exp_1`; storefront reachable at configured URLs.

## Manual test cases

| ID | Title | Steps | Expected |
|----|-------|-------|----------|
| FR03-M01 | All checks returned | `curl GET /experiments/exp_1/preflight?variantAUrl=...&variantBUrl=...` | 200; 8 checks in order C1b,C1,C2,C3,C4,C5,C6,C7,C8 |
| FR03-M02 | Ready on healthy setup | Run preflight with seeded data + valid URLs + hypothesis saved | `ready: true`; no fail statuses |
| FR03-M03 | Unreachable URL fail | 1. Stop ecom frontend OR use bad URL<br>2. Run preflight | C1 or C2 `fail`; message includes URL; `ready: false` |
| FR03-M04 | Zero events fail | 1. Truncate universal_events for exp_1<br>2. Preflight | C3 `fail`; other checks still present |
| FR03-M05 | Missing URLs warn | GET preflight without query params and no URLs in DB | C1b `warn`; C1/C2 `warn` "URL not provided" |
| FR03-M06 | Query param URL override | Store wrong URL in DB; pass correct URL in query | C1/C2 use query URLs (reachable) |
| FR03-M07 | Empty hypothesis fail | Clear hypothesis on experiment; preflight | C6 `fail` |
| FR03-M08 | Sample size warn/fail | 1. Simulate 60 users<br>2. Preflight | C7 `warn` or `fail` with exposure counts in message |
| FR03-M09 | Cache 60s | 1. Run preflight twice within 60s<br>2. Compare evaluatedAt | Same timestamp (cached) OR within cache policy |
| FR03-M10 | DB unavailable | Stop postgres; GET preflight | 503 `UPSTREAM_ERROR`; UI shows actionable message |
| FR03-M11 | Deep link checkout | Mock httpx to capture requested URL | Request URL includes `screen=checkout` when not present |
| FR03-M12 | UI re-run | 1. Open drawer<br>2. Click Re-run checks | Loading spinner; checklist updates |

## Failure / edge cases

| Case | Trigger | Expected |
|------|---------|----------|
| One URL check fails | A reachable, B not | C1 pass, C2 fail; others still evaluated |
| Traffic split 0 | PATCH split=0 | C5 warn about one-sided traffic |
| Traffic split invalid | DB corruption / bad value | C5 fail |
| Single variant exposures | All users on A | C4 warn "variant B has 0 page_views" |
| Multiple experiments overlap | Seed second experiment sharing users | C8 fail with user_ids (if test data supports) |
| Slow URL (>3s) | Throttle network | C1/C2 warn with slow message |
| Invalid experiment id | GET /experiments/bad/preflight | 404 NOT_FOUND |
| Special chars in URL query | Encoded URL params | No 400; correct fetch |

## Integration tests (recommended)

```python
@pytest.mark.asyncio
async def test_preflight_all_checks_present(client):
    r = client.get("/experiments/exp_1/preflight", params={...})
    ids = [c["id"] for c in r.json()["checks"]]
    assert ids == ["C1b", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"]

def test_c3_fail_zero_events(client, empty_events):
    ...
```

### curl scripts

```bash
# Full preflight
curl -s "localhost:3001/experiments/exp_1/preflight?variantAUrl=http://localhost:5173/?variant=A&variantBUrl=http://localhost:5173/?variant=B" | jq .

# Score + ready
curl -s "localhost:3001/experiments/exp_1/preflight" | jq '{ready, score}'
```

## Regression checks

- [ ] `/analyze` still works when preflight `ready: false` (advisory only)
- [ ] No new LLM calls from preflight endpoint
- [ ] Agent `_deep_link_checkout` behavior unchanged (shared util matches)
- [ ] GET experiment response unchanged
- [ ] Preflight completes in < 10s p95 with live storefront
- [ ] copilot-backend startup unaffected
