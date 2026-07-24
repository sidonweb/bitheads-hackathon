# FR-04: Versatile SQL Data Sub-Agent

| Field | Value |
|-------|--------|
| Status | Draft |
| Priority | P0 |
| Problem statement | Intelligent querying; supports metric inference and analysis |
| Depends on | FR-05 |
| Blocks | FR-02 (optional integration) |

## Main branch context

Main agent still attaches **`SQLDatabaseToolkit` directly** with `include_tables=["universal_events", "experiments"]`. System prompt includes a **hardcoded example aggregation SQL** and step "SELECT DISTINCT event_name …". FR-04 replaces this with dynamic schema discovery via sub-agent.

Browser side on main: single tool `inspect_variant_pages` (not 24 MCP tools). Sub-agent work is independent of browser tools.

## Summary

Replace hardcoded `include_tables=["universal_events", "experiments"]` on the main agent with a **dedicated data sub-agent** exposed as a single tool: `ask_data_analyst(question)`.

The sub-agent discovers schema dynamically, reads metadata, executes read-only SQL, and returns structured answers.

## Goals

- **Fully dynamic** — discovers schema at runtime; not biased to `universal_events`, `checkout_completed`, or this hackathon's ecom schema.
- Main agent prompt must **not** contain table names, column names, example SQL, or event-name lists.
- Clear separation: main agent = orchestration; data agent = SQL.
- Production guardrails on every query.

## Non-goals

- Write/DDL/DML queries.
- Cross-database federation (MySQL, BigQuery).
- Arbitrary connection strings from user input.

## Architecture

```
Main Analyst Agent
  tools: [inspect_variant_pages?, run_statistics, submit_decision, ask_data_analyst]

Data Sub-Agent (internal, not user-facing)
  tools: [list_tables, describe_table, run_readonly_query]
```

## Sub-agent tools

### `list_tables(schema='public')`

Returns table names the `agent_readonly` role can read.

### `describe_table(table_name)`

Returns columns (from `information_schema`), row count estimate, 2 sample rows.

### `run_readonly_query(sql)`

- Reject if SQL contains (case-insensitive): `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`.
- Must start with `SELECT` (after strip).
- Append `LIMIT 500` if no limit present.
- Execute with existing 5s statement timeout.
- Return `{ columns, rows, rowCount, sql }` or `{ error, sql }`.

## Main agent tool

### `ask_data_analyst(question: str) -> str`

Spawns sub-agent with max **6 tool calls** (nested budget inside FR-05 global budget).

Returns JSON string:

```json
{
  "answer": "Variant B has 900 conversions vs 790 for A on checkout_completed.",
  "sql_used": ["SELECT …"],
  "tables_used": ["universal_events"]
}
```

## DB permissions

Migration addition (if needed):

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA public TO agent_readonly;
-- information_schema is readable by default for column metadata
```

## Prompt constraints (sub-agent)

- Always `list_tables` → `describe_table` before querying unknown tables.
- Scope queries using **only** identifiers passed in the question (e.g. experiment id from main agent) — no baked-in table/column assumptions.
- Never hardcode event names (`page_view`, `checkout_completed`, etc.) in sub-agent system prompt.
- Never expose raw PII lists > 20 rows to main agent.

## Main agent prompt cleanup (with FR-04)

Remove from `_system_prompt()` today:

- Hardcoded `universal_events(...)` column list as the only schema hint
- Example `SELECT … FILTER (WHERE event_name = 'page_view')` SQL
- Step "SELECT DISTINCT event_name …" with fixed table name

Replace with: "Use `ask_data_analyst` to discover schema and fetch aggregates for experiment `{id}`."

## Error handling

| Failure | Sub-agent returns | Main agent behavior |
|---------|-------------------|---------------------|
| Query timeout | error message | Explain to PM; suggest narrower question |
| Invalid SQL | validation error | Retry once with describe_table |
| Empty result | answer with rowCount 0 | Continue analysis with caveat |

## Acceptance criteria

- [ ] Main agent no longer has direct SQLDatabaseToolkit tools attached.
- [ ] Sub-agent can answer "what event names exist?" without hardcoded schema in main prompt.
- [ ] `run_readonly_query("DELETE …")` rejected at app layer.
- [ ] Adding a new table to DB (with GRANT) works without code change to table list.

## Open questions

- [x] ~~Keep experiment-specific SQL examples in main prompt?~~ **No — fully dynamic (team decision).**
- [ ] Cache `list_tables` / `describe_table` for 5 minutes?
