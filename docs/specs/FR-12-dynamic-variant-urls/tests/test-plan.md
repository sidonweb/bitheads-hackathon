# FR-12 Test Plan: Dynamic Variant URLs (User Input Only)

| Spec | [../index.md](../index.md) |
| Environment | `docker compose up -d --build`; dashboard `:5174`; ecom `:5173` |

---

## Test cases

### TC-01: Fresh chat without URLs — agent asks, no browser

| Step | Action | Expected |
|------|--------|----------|
| 1 | New session; clear chat | Empty thread |
| 2 | Send: "Analyze the experiment and recommend" | Reply asks for both variant URLs |
| 3 | Check copilot-backend logs | No Playwright navigate calls |
| 4 | Response time | Fast (no browser timeout wait) |

---

### TC-02: Agent proceeds after PM provides both URLs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Send URLs in one message: `A: http://localhost:5173/?variant=A B: http://localhost:5173/?variant=B` | — |
| 2 | Send: "Now analyze" | Agent calls `inspect_variant_pages` |
| 3 | Logs | Navigate to both URLs |

---

### TC-03: No `_deep_link_checkout` — URL passed verbatim

| Step | Action | Expected |
|------|--------|----------|
| 1 | PM provides `http://localhost:5173/?variant=A` (no screen=checkout) | — |
| 2 | Inspect tool runs | Playwright navigates exact URL (+ localhost alias only) |
| 3 | Grep logs/snapshot header | URL does NOT contain `screen=checkout` unless PM included it |

---

### TC-04: PM URL with custom query preserved

| Step | Action | Expected |
|------|--------|----------|
| 1 | PM provides `https://example.com/path?foo=bar&variant=A` | — |
| 2 | Inspect | Query string unchanged except localhost alias |

---

### TC-05: `/analyze` without body → 422

| Step | Action | Expected |
|------|--------|----------|
| 1 | `curl -X POST .../analyze` with no body | HTTP 422 |
| 2 | Response | Structured error; mentions required URLs |
| 3 | Duration | No LLM invocation (immediate) |

---

### TC-06: `/analyze` with one URL missing → 422

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST `{ "variantAUrl": "http://a.test" }` only | HTTP 422 |
| 2 | Agent | Not started |

---

### TC-07: `/analyze` with valid URLs → 200 decision

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST both demo URLs in JSON body | HTTP 200 |
| 2 | Body | Decision with `inferred_metric`, `sql_used` |
| 3 | DB URLs | Not used if different from body (verify by divergent test URL in body) |

---

### TC-08: Agent prompt grep — no hardcoded demo URLs

| Step | Action | Expected |
|------|--------|----------|
| 1 | `rg "localhost:5173|variant=A" packages/copilot-backend/app/agent/` | Zero matches in prompts/code defaults |
| 2 | `_system_prompt` review | No example URLs |

---

### TC-09: DB-stored URLs not auto-used in chat

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ensure `experiments.variant_a_url` set in DB (seed) | — |
| 2 | Fresh chat without PM pasting URLs | Agent still asks for URLs |
| 3 | Agent | Does not mention stored URL as source |

---

### TC-10: `inspect_variant_pages` early return without URLs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Force tool call with empty `variant_b_url` (dev test) | Tool returns "Missing a URL…" string |
| 2 | No exception | Graph continues |

---

### TC-11: Dashboard Analyze requires URLs

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click Analyze without entering URLs | Modal or error — not infinite loading |
| 2 | Enter both URLs and Analyze | Decision renders |
| 3 | Network tab | Request body includes `variantAUrl`, `variantBUrl` |

---

### TC-12: URL extractor helper unit behavior

| Step | Action | Expected |
|------|--------|----------|
| 1 | `extract_urls("See https://a.com and https://b.com/page")` | Two URLs in order |
| 2 | `extract_urls("hello")` | `[]` |
| 3 | No default localhost injected | — |

---

## Regression

- [ ] `_browser_url` still rewrites localhost for Docker Playwright
- [ ] Playwright fallback when MCP down still works (chat-only path)
- [ ] FR-04 `ask_data_analyst` not called before URLs provided (when analysis requested)

## Sign-off

| Role | Name | Date | Pass/Fail |
|------|------|------|-----------|
| Dev | | | |
| QA | | | |
