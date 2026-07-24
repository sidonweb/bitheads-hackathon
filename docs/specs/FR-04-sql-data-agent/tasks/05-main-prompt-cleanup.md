# Task 05: Main Agent Prompt Cleanup (Remove Hardcoded Schema)

## Location

| Action | Path |
|--------|------|
| Edit | `packages/copilot-backend/app/agent/graph.py` — `_system_prompt()` |
| Remove | Hardcoded references in module docstring (lines 8–9 mention `universal_events` toolkit) |

## Dependencies

- Task 04 (`ask_data_analyst` available)
- Task 06 should follow immediately after (remove toolkit from `build_agent`)

## What to build

Rewrite `_system_prompt(exp, has_browser)` to remove all schema-specific guidance.

### Remove entirely

From current `graph.py` `_system_prompt()` (~lines 224–252):

- `Event data lives in universal_events(experiment_id, user_id, ...)`
- `Exposures are rows where event_name = 'page_view'`
- Candidate event examples: `'add_to_cart', 'checkout_started', 'checkout_completed'`
- Step 3: `SELECT DISTINCT event_name FROM universal_events WHERE experiment_id = ...`
- Step 4: Full example `SELECT variant_id, COUNT(*) FILTER (WHERE event_name = 'page_view') ...` template
- Any instruction to "Run a SQL query" directly

### Replace with

```
Event data: use ask_data_analyst to discover schema and fetch aggregates for experiment `{exp['id']}`.
Never write SQL yourself — delegate all database questions to ask_data_analyst.

Workflow (when PM asks for analysis):
1. GET URLS: ...
2. INSPECT: ...
3. INFER: From page diff + ask_data_analyst (list events for this experiment), choose ONE success metric from events that actually exist. State why.
4. DATA: ask_data_analyst for per-variant exposure and conversion counts using your inferred metric.
5. STATS: run_statistics ...
6. DECIDE: submit_decision ... include sql_used from ask_data_analyst response
```

Keep unchanged: scope guardrail, URL-from-chat rules (FR-12), `run_statistics` / `submit_decision` determinism boundary.

## Design spec

### Before vs after prompt structure

```
┌──────────────────────────────────────────────────────────────┐
│ BEFORE (_system_prompt)                                      │
├──────────────────────────────────────────────────────────────┤
│ • universal_events column list                               │
│ • page_view = exposure                                       │
│ • Example FILTER SQL (copy-paste template)                   │
│ • Step: SELECT DISTINCT event_name FROM universal_events     │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│ AFTER                                                        │
├──────────────────────────────────────────────────────────────┤
│ • "Use ask_data_analyst for all data questions"              │
│ • experiment id only hard identifier in prompt               │
│ • No table names, column names, or event name examples       │
└──────────────────────────────────────────────────────────────┘
```

### Grep acceptance (run after change)

```bash
rg -n "universal_events|page_view|checkout_completed|FILTER \(WHERE" \
  packages/copilot-backend/app/agent/graph.py
```

Expected: **zero matches** in `_system_prompt` body (imports/docstring cleanup optional).

## Done when

- [ ] `_system_prompt()` contains no table names, column lists, or example SQL
- [ ] No hardcoded event names in main agent prompt
- [ ] Workflow steps reference `ask_data_analyst` for steps 3–4
- [ ] Scope guardrail and stats/decision determinism language preserved
- [ ] Grep audit passes for forbidden strings in prompt function
