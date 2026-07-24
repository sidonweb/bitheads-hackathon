# FR-12: Dynamic Variant URLs (User Input Only) — Implementation Spec

| Field | Value |
|-------|--------|
| Requirement | [FR-12-dynamic-variant-urls.md](requirements.md) |
| Status | Spec ready |
| Priority | P0 |
| Depends on | — |
| Blocks | FR-03, FR-10 |

## Problem

Variant URLs must come **only** from PM input (chat or explicit API body). Today:

- `_deep_link_checkout()` auto-appends `?screen=checkout` in `graph.py`
- System prompt may contain implicit assumptions about where variants differ
- `/analyze` does not require URLs in request body — may rely on DB or hung agent
- DB-stored `variant_a_url` / `variant_b_url` must not silently substitute for user input

## Solution

1. Remove `_deep_link_checkout` — pass PM URLs verbatim to Playwright (after localhost alias rewrite only)
2. Main agent workflow: extract URLs from conversation; ask once if missing; block tools until both exist
3. `/analyze` requires `{ variantAUrl, variantBUrl }` in body or returns 422
4. Optional URL extractor helper for latest user message

## Rules summary

| Do | Don't |
|----|-------|
| Parse URLs from user messages | Hardcode `localhost:5173`, `?variant=A` in prompts |
| Ask PM for both URLs if missing | Read URLs from `experiments.variant_*_url` for agent/browser |
| Pass user URLs verbatim to `inspect_variant_pages` | Auto-append `screen=checkout` |
| 422 when analyze body lacks URLs | Run browser/SQL until URLs provided |

## Task index

| # | Task | File |
|---|------|------|
| 1 | Remove `_deep_link_checkout` | [tasks/01-remove-deep-link-checkout.md](./tasks/01-remove-deep-link-checkout.md) |
| 2 | URL extractor helper | [tasks/02-url-extractor-helper.md](./tasks/02-url-extractor-helper.md) |
| 3 | Agent prompt URL workflow | [tasks/03-agent-prompt-url-workflow.md](./tasks/03-agent-prompt-url-workflow.md) |
| 4 | Analyze request body URLs | [tasks/04-analyze-body-urls.md](./tasks/04-analyze-body-urls.md) |
| 5 | Prompt/code audit — no hardcoded URLs | [tasks/05-no-hardcoded-urls-audit.md](./tasks/05-no-hardcoded-urls-audit.md) |
| 6 | Dashboard analyze URL passthrough | [tasks/06-dashboard-analyze-urls.md](./tasks/06-dashboard-analyze-urls.md) |

## Acceptance criteria

- [ ] Fresh chat with no URLs → agent asks PM; no browser call
- [ ] Grep: no `localhost:5173` or `variant=A` in agent prompts
- [ ] User-provided URL passed to Playwright unchanged (except localhost alias)
- [ ] `/analyze` without URLs returns 422, not hung agent

## Testing

See [tests/test-plan.md](./tests/test-plan.md).
