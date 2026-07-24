# FR-12: Dynamic Variant URLs (User Input Only)

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P0 |
| Problem statement | Variant URLs must come from PM input — never hardcoded or assumed |
| Depends on | — |
| Blocks | FR-03, FR-10 |
| Conflicts with main | `_deep_link_checkout()` auto-appends `?screen=checkout`; remove or make user-driven |

## Summary

All variant URLs are **dynamic**. The agent gets them only from what the PM types in chat (or explicit API body on `/analyze`). No defaults in system prompt, config, or code paths.

## Rules

| Do | Don't |
|----|-------|
| Parse URLs from user messages in the conversation | Hardcode `localhost:5173`, `?variant=A`, demo URLs in prompt |
| Ask PM for both URLs if either is missing | Read URLs from `experiments.variant_*_url` unless PM also pasted them |
| Pass user-provided URLs verbatim to `inspect_variant_pages` | Auto-append query params (`screen=checkout`) without user saying where to inspect |
| Store URLs only if PM explicitly saves them (optional UX) | Assume checkout page is always the diff surface |

## Agent prompt changes (`graph.py`)

- Remove any example URLs from `_system_prompt()`.
- Workflow step 1: "Extract both variant URLs from the PM's messages in this thread."
- If missing → ask once; do not call browser or SQL analysis tools until both exist.
- Optional: lightweight URL extractor helper (regex/http) on latest user message — not hardcoded paths.

## `/analyze` (FR-10)

- Require `{ variantAUrl, variantBUrl }` in request body **or** fail with clear error.
- Do not inject DB-stored URLs silently.

## Preflight (FR-03)

- C1/C2 use URLs from request query/body only (same as user-supplied).
- Warn if URLs not provided — do not substitute demo URLs.

## Acceptance criteria

- [ ] Fresh chat with no URLs → agent asks PM; no browser call.
- [ ] Grep codebase: no `localhost:5173` or `variant=A` in agent prompts.
- [ ] User-provided URL is passed to Playwright unchanged (unless PM asks to add params).
- [ ] `/analyze` without URLs returns 422, not a hung agent turn.

## Open questions

- [ ] Should UI offer optional URL fields in experiment drawer (still user-entered, not hardcoded)?
