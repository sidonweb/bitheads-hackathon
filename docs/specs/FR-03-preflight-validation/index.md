# FR-03: Pre-Flight Validation

## Feature metadata

| Field | Value |
|-------|--------|
| **ID** | FR-03 |
| **Short name** | preflight-validation |
| **Priority** | P0 |
| **Status** | Draft |
| **Depends on** | — |
| **Blocks** | — |
| **Source requirement** | [FR-03-preflight-validation.md](requirements.md) |

## Summary

Deterministic pre-launch checklist run on demand (or optionally before Analyze). Returns pass/warn/fail per check with human-readable messages. No LLM required for core checks. Advisory only in v1.5 — does not block experiment start in API.

## Goals

- Catch misconfiguration before analysis wastes agent tool budget.
- Surface overlapping-experiment risk (best-effort with current schema).
- Validate variant URL reachability using same deep-link logic as the analysis agent.

## Non-goals

- Blocking experiment start in API (advisory only).
- Full multi-experiment overlap engine.
- LLM-based validation.
- Storing last preflight result on experiment row (open question — out of scope unless added later).

## Task index

| # | Task | Package | Description |
|---|------|---------|-------------|
| 01 | [Preflight service core](./tasks/01-preflight-service-core.md) | copilot-backend | Orchestrator, check model, caching |
| 02 | [URL and DB checks](./tasks/02-url-and-db-checks.md) | copilot-backend | C1–C8 individual check functions |
| 03 | [Preflight route](./tasks/03-preflight-route.md) | copilot-backend | `GET /experiments/{id}/preflight` |
| 04 | [Dashboard preflight card](./tasks/04-dashboard-preflight-card.md) | dashboard | Checklist UI with re-run |
| 05 | [API client](./tasks/05-api-client-preflight.md) | dashboard | `api.js` preflight helper |

## Checks reference

| ID | Check | Pass | Warn | Fail |
|----|-------|------|------|------|
| C1 | Variant A URL reachable | 2xx/3xx | slow timeout | unreachable |
| C2 | Variant B URL reachable | same | same | same |
| C1b | URLs provided | at least one source | neither param nor DB | — (warn only) |
| C3 | Events exist for experiment | count > 0 | count < 100 total | count = 0 |
| C4 | Exposures (`page_view`) per variant | both ≥ 1 | one variant 0 | both 0 |
| C5 | Traffic split | valid 0–100 | split 0 or 100 one-sided | invalid int |
| C6 | Hypothesis non-empty | present | — | empty |
| C7 | Sample size guidance | both ≥ 300 exposures | 50–299 | < 50 |
| C8 | Overlap (best-effort) | no user in 2+ exps | — | users in 2+ exps |

`ready: true` when no check has status `fail` (warns allowed).

## Acceptance criteria

- [ ] All checks returned in stable order (C1b, C1, C2, C3, C4, C5, C6, C7, C8).
- [ ] Unreachable URL produces `fail` with URL in message.
- [ ] Zero events produces C3 `fail`.
- [ ] Response time < 10s p95 with URL checks.
- [ ] DB unavailable → 503 `UPSTREAM_ERROR`.
- [ ] URL deep-link: append `screen=checkout` when no `screen` param (match `_deep_link_checkout`).
- [ ] Results cached 60s per experiment id.

## Related FRs

| FR | Relationship |
|----|--------------|
| [FR-01](../FR-01-hypothesis-from-goals/index.md) | C6 validates hypothesis from FR-01 save flow |
| [FR-02](../FR-02-metric-config-recommendations/index.md) | C3/C4 validate data after metric setup |
| [FR-10](../FR-10-one-click-analyze/requirements.md) | May auto-run preflight before analyze |
| [FR-12](../FR-12-dynamic-variant-urls/requirements.md) | URL source priority aligns with dynamic URLs |

## Open questions (from source)

- Run preflight automatically before `/analyze`? **Spec decision:** optional hook in FR-10; FR-03 delivers standalone GET endpoint.
- Store last preflight result on experiment row? **Spec decision:** no for v1.5.
- Body vs DB URLs for C1/C2? **Spec decision:** query params override DB (see Task 03).
