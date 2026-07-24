# FR-06: Streaming Chat — Test Plan

Manual tests unless noted. Run stack: `docker compose up -d --build`, dashboard at `localhost:5174`, seed data reset per CLAUDE.md.

## Prerequisites

- `OPENAI_API_KEY` set in `packages/copilot-backend/.env`
- FR-05 guardrails merged (structured errors) — or verify graceful degradation with current 500 shape
- Browser DevTools → Network tab filtered to `chat/stream`

---

## Happy path

### T1 — First token within 5 seconds

**Steps:** Open dashboard, new session, send "Analyze the experiment and recommend a decision."

**Expected:** Assistant bubble shows text within 5s; Network shows `chat/stream` with `text/event-stream` type.

**Pass:** First `token` event observed ≤ 5s from send.

---

### T2 — Tool steps visible before decision

**Steps:** Same as T1; watch step indicator during analysis.

**Expected:** At least one `tool_start` / `tool_end` pair (e.g. "Querying experiment data") appears before the Scale/Continue decision card.

**Pass:** Step labels visible; decision card renders after tool steps complete.

---

### T3 — Stream terminates with `done`

**Steps:** Complete T1; inspect last SSE events in Network → EventStream preview or `curl -N`.

**Expected:** Final events include `event: done` with `toolCallsUsed` integer.

**Pass:** No hanging connection; composer re-enabled.

---

### T4 — Decision payload matches non-streaming

**Steps:** Send same prompt on stream path; note decision. New session, send same prompt via direct `curl` to `POST /chat`.

**Expected:** Same `decision`, `p_value`, `inferred_metric` (within same data snapshot).

**Pass:** Verdict and stats match.

---

### T5 — Token accumulation in UI

**Steps:** During stream, observe assistant bubble text growing incrementally.

**Expected:** Text updates without full-page flash; scroll follows bottom.

**Pass:** Smooth append behavior; final text coherent.

---

## Failure & edge cases

### T6 — Stream endpoint unavailable → fallback

**Steps:** Temporarily comment out stream route or point `chatStream` to wrong URL; send analysis prompt.

**Expected:** UI falls back to `POST /chat`; full reply appears after wait; no permanent error state.

**Pass:** User receives complete answer; console may log fallback once.

---

### T7 — Missing sessionId rejected

**Steps:** `curl -N -X POST localhost:3001/experiments/exp_1/chat/stream -H 'Content-Type: application/json' -d '{"message":"hi"}'`

**Expected:** HTTP 422 JSON error, no SSE body.

**Pass:** Structured validation error; dashboard always sends sessionId in normal use.

---

### T8 — Agent tool limit (FR-05)

**Steps:** Set `AGENT_MAX_TOOL_CALLS=1` (when FR-05 lands) or simulate via mock; run analysis.

**Expected:** Stream emits `warning` or terminal `error` with code `AGENT_TOOL_LIMIT`; partial assistant text may exist; banner shown.

**Pass:** No raw stack trace; `busy` clears; retryable hint if applicable.

---

### T9 — Client abort (new message while streaming)

**Steps:** Send long analysis prompt; before completion, send a second short message ("What is variant A?").

**Expected:** First stream aborted; second request proceeds independently; no merged text in one bubble.

**Pass:** Two distinct assistant responses; no duplicate decision cards from aborted stream.

---

### T10 — Experiment not found

**Steps:** `curl -N -X POST localhost:3001/experiments/missing/chat/stream -H 'Content-Type: application/json' -d '{"message":"hi","sessionId":"s1"}'`

**Expected:** HTTP 404 JSON, not event stream.

**Pass:** Correct status before stream opens.

---

### T11 — Session thread isolation

**Steps:** Session A: start analysis. Switch to Session B mid-stream; send different message.

**Expected:** Session B gets its own stream; Session A state preserved in sidebar (may show partial or error on return).

**Pass:** No cross-session message contamination.

---

### T12 — Non-streaming `/chat` unchanged

**Steps:** `curl -X POST localhost:3001/experiments/exp_1/chat -H 'Content-Type: application/json' -d '{"message":"hello","sessionId":"s_test"}'`

**Expected:** `{ "reply": "...", "decision": null | object }` JSON; no regression.

**Pass:** Same response shape as before FR-06.

---

## Build & deploy checks

### T13 — Dashboard build

**Steps:** `cd packages/dashboard && npm run build`

**Expected:** Exit 0.

---

### T14 — Nginx buffering (documentation)

**Steps:** Verify response includes `X-Accel-Buffering: no` on stream route.

**Expected:** Tokens not batch-delivered only at end behind reverse proxy.

**Pass:** Header present in FastAPI response.

---

## Sign-off checklist

- [ ] T1–T5 happy path
- [ ] T6–T12 edge cases
- [ ] T13 build
- [ ] Acceptance criteria in FR-06 index marked complete
