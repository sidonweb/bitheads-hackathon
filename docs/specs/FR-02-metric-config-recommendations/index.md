# FR-02: Metric & Configuration Recommendations

## Feature metadata

| Field | Value |
|-------|--------|
| **ID** | FR-02 |
| **Short name** | metric-config-recommendations |
| **Priority** | P0 |
| **Status** | Draft |
| **Depends on** | [FR-01](../FR-01-hypothesis-from-goals/index.md) (optional), [FR-04](../FR-04-sql-data-agent/requirements.md) (optional) |
| **Blocks** | — |
| **Source requirement** | [FR-02-metric-config-recommendations.md](requirements.md) |

## Summary

After hypothesis generation (or on demand), copilot suggests a primary success metric (constrained to events in `universal_events`), a feature-flag narrative describing variant treatment mapping, and an audience suggestion stored as metadata. PM confirms before saving `primary_metric` to the experiment row.

## Goals

- Give PM a concrete measurement plan before launch.
- Metric suggestions constrained to events that **exist** in `universal_events` for the experiment.
- Rationale ties metric choice to hypothesis and variant URL differences.

## Non-goals

- LaunchDarkly / Split.io integration.
- Enforcing audience rules in ecom storefront.
- Auto-setting `primary_metric` without PM confirmation.
- Duplicating full analyze workflow (agent already infers metric at analysis time).

## Task index

| # | Task | Package | Description |
|---|------|---------|-------------|
| 01 | [Schemas](./tasks/01-schemas-recommend-config.md) | copilot-backend | Request/response models, PATCH for primary_metric |
| 02 | [Config recommendation service](./tasks/02-config-recommendation-service.md) | copilot-backend | SQL event discovery + LLM selection + validation |
| 03 | [Recommend-config route](./tasks/03-recommend-config-route.md) | copilot-backend | `POST /experiments/{id}/recommend-config` |
| 04 | [Dashboard config panel](./tasks/04-dashboard-config-panel.md) | dashboard | Metric recommendation UI with accept flow |
| 05 | [API client](./tasks/05-api-client-recommend-config.md) | dashboard | `api.js` helpers |

## Acceptance criteria

- [ ] Returns only `eventName` values present in `universal_events` for experiment.
- [ ] If no conversion events exist, returns warning + suggests collecting data first.
- [ ] LLM output validated against allowlist; invalid pick falls back to heuristic (`checkout_completed` if present).
- [ ] PM can accept metric and save via PATCH `primary_metric` on existing experiment API.
- [ ] `alternatives` list contains only valid event names.
- [ ] Feature flag summary is descriptive text, not SDK integration.
- [ ] No stack trace in API responses.

## Related FRs

| FR | Relationship |
|----|--------------|
| [FR-01](../FR-01-hypothesis-from-goals/index.md) | Optional input: saved hypothesis feeds recommend-config request |
| [FR-03](../FR-03-preflight-validation/index.md) | Preflight C3/C4 validate events/exposures after metric chosen |
| [FR-04](../FR-04-sql-data-agent/requirements.md) | Optional: could reuse SQL sub-agent for event discovery |
| [FR-07](../FR-07-apply-recommendation/requirements.md) | Apply recommendation UX may overlap — FR-02 focuses on pre-launch config |

## Open questions (from source)

- Combine with FR-01 in single "Create experiment" API call? **Spec decision:** separate endpoints; UI may chain calls.
- Use SQL sub-agent (FR-04) vs direct SQL in service? **Spec decision:** direct SQL in service for v1 (deterministic, faster).
