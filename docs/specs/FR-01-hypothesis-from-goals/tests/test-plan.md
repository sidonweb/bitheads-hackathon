# FR-01 Test Plan: Hypothesis from Business Goals

## Test strategy

| Layer | Approach |
|-------|----------|
| Unit | Test rate limiter, input validation, LLM output parsing (mock LLM) |
| API | Manual + curl/httpie against `copilot-backend:3001` |
| UI | Manual dashboard flows in Experiment drawer |
| Integration | End-to-end: generate → edit → save → reload GET experiment |
| Regression | Existing analyze/chat/chat panel unaffected |

**Environment:** Docker stack up, seeded `exp_1`, valid `OPENAI_API_KEY` in `packages/copilot-backend/.env`.

## Manual test cases

| ID | Title | Steps | Expected |
|----|-------|-------|----------|
| FR01-M01 | Happy path generation | 1. Open dashboard drawer<br>2. Enter goal "Increase checkout conversion"<br>3. Click Generate hypothesis | Draft hypothesis returned; mentions conversion; suggested name populated |
| FR01-M02 | Accept and save | 1. After FR01-M01, edit hypothesis slightly<br>2. Click Accept & save<br>3. Close drawer, reopen | Saved hypothesis matches edits; GET `/experiments/exp_1` shows updated `hypothesis` |
| FR01-M03 | Empty goal validation | 1. Leave goal blank<br>2. Click Generate | Client prevents call OR server returns 422 `VALIDATION_ERROR`; no crash |
| FR01-M04 | Goal length limit | 1. Paste 2001-char goal<br>2. Generate | 422 with clear message; char counter shows limit |
| FR01-M05 | LLM unavailable | 1. Set invalid API key or mock 503<br>2. Generate | 503 `LLM_UNAVAILABLE`; UI shows "Enter hypothesis manually"; manual textarea still works |
| FR01-M06 | Manual hypothesis save | 1. Skip generate<br>2. Type hypothesis manually<br>3. Accept & save | PATCH succeeds; hypothesis persisted |
| FR01-M07 | Rate limit | 1. Call generate 11 times within 1 hour for same experiment | 11th request returns 429; UI shows rate limit message |
| FR01-M08 | Experiment not found | `curl -X POST localhost:3001/experiments/missing/generate-hypothesis -d '{"businessGoal":"test"}'` | 404 `NOT_FOUND`; structured error body |
| FR01-M09 | Context field optional | 1. Enter goal + context "Variant B has new CTA"<br>2. Generate | Response hypothesis reflects context nuance |
| FR01-M10 | Page reload persistence | 1. Save hypothesis<br>2. Hard refresh browser | Hypothesis panel pre-fills from server data |

## Failure / edge cases

| Case | Trigger | Expected behavior |
|------|---------|-------------------|
| LLM returns malformed JSON | Mock parser failure | 502/500 safe message; no stack trace in response |
| LLM inventing metrics | Inspect generated text | Hypothesis must not contain p-values, sample sizes, or fabricated event names |
| Concurrent generate + save | Double-click Generate | Button disabled while `generating`; no duplicate in-flight requests |
| PATCH with empty hypothesis | Save with cleared field | 422 or client validation prevents empty hypothesis save |
| Network timeout | Slow LLM (>30s) | 503 after timeout; UI recoverable |
| Special characters in goal | Emoji, quotes, newlines | Properly escaped in JSON; no XSS in dashboard render |

## Integration tests (recommended)

```python
# packages/copilot-backend/tests/test_hypothesis_route.py (future)
async def test_generate_hypothesis_returns_draft(client, mock_llm): ...
async def test_empty_goal_422(client): ...
async def test_rate_limit_429(client): ...
```

If no test runner yet, document curl scripts:

```bash
# Happy path
curl -s -X POST localhost:3001/experiments/exp_1/generate-hypothesis \
  -H 'Content-Type: application/json' \
  -d '{"businessGoal":"Increase checkout conversion"}' | jq .

# Validation
curl -s -o /dev/null -w '%{http_code}' -X POST localhost:3001/experiments/exp_1/generate-hypothesis \
  -H 'Content-Type: application/json' \
  -d '{"businessGoal":""}'
# expect 422
```

## Regression checks

- [ ] `POST /experiments/exp_1/analyze` still works after hypothesis save
- [ ] Chat panel unaffected; no new errors in browser console on dashboard load
- [ ] Existing traffic split slider still functions in drawer
- [ ] `GET /experiments/exp_1` response shape unchanged (new hypothesis value only)
- [ ] `npm run build` (dashboard) and copilot-backend startup logs clean
