# FR-04 Test Plan: Versatile SQL Data Sub-Agent

| Spec | [../index.md](../index.md) |
| Environment | `docker compose up -d --build`; seeded `exp_1`; valid `OPENAI_API_KEY` |

## Prerequisites

- Reset and seed demo data per CLAUDE.md
- Migration `002_agent_readonly_grants.sql` applied
- FR-05 guardrails recommended but not required for SQL-only unit tests

---

## Test cases

### TC-01: Main agent has no direct SQL toolkit tools

| Step | Action | Expected |
|------|--------|----------|
| 1 | Inspect `build_agent()` in `graph.py` | Tool list does not include `sql_db_query`, `sql_db_schema`, or `SQLDatabaseToolkit` |
| 2 | Grep codebase for `SQLDatabaseToolkit` in graph | Zero imports/usages in main agent path |

---

### TC-02: `list_tables` returns all granted public tables

| Step | Action | Expected |
|------|--------|----------|
| 1 | Invoke `list_tables()` tool directly (Python shell or test) | JSON includes `universal_events` and `experiments` |
| 2 | Create new table `test_metrics` with GRANT SELECT to `agent_readonly` | — |
| 3 | Call `list_tables()` again | `test_metrics` appears without code deploy |

---

### TC-03: `describe_table` returns columns and samples

| Step | Action | Expected |
|------|--------|----------|
| 1 | Call `describe_table("universal_events")` | Returns column names including `event_name`, `variant_id` |
| 2 | Verify `sample_rows` | At most 2 rows; valid JSON |
| 3 | Call `describe_table("nonexistent_table")` | Error JSON, no crash |

---

### TC-04: `run_readonly_query` rejects DELETE

| Step | Action | Expected |
|------|--------|----------|
| 1 | Call `run_readonly_query("DELETE FROM universal_events")` | `{ "error": "..." }` — mentions blocked keyword or not SELECT |
| 2 | Verify Postgres | Row count unchanged |

---

### TC-05: `run_readonly_query` rejects INSERT/UPDATE/DROP

| Step | Action | Expected |
|------|--------|----------|
| 1 | Submit `INSERT INTO experiments ...` | Rejected at app layer |
| 2 | Submit `UPDATE experiments SET name='x'` | Rejected |
| 3 | Submit `DROP TABLE universal_events` | Rejected |

---

### TC-06: Auto-LIMIT 500 appended

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run `SELECT * FROM universal_events` (no LIMIT) | Returned `sql` field ends with `LIMIT 500` |
| 2 | Check `rowCount` | ≤ 500 |

---

### TC-07: Query timeout handled gracefully

| Step | Action | Expected |
|------|--------|----------|
| 1 | Run intentionally slow query (e.g. `pg_sleep(10)` in subselect if permitted, or cross join) | Returns `{ "error": "..." }` within ~5–6s |
| 2 | Main agent via `ask_data_analyst` | JSON error; chat reply explains timeout to PM |

---

### TC-08: Sub-agent discovers event names without main prompt hints

| Step | Action | Expected |
|------|--------|----------|
| 1 | Grep `_system_prompt` for `page_view`, `universal_events` | No matches |
| 2 | Chat: "What event names exist for this experiment?" (with URLs if required) | Reply lists actual seeded events without agent guessing nonexistent names |
| 3 | Check logs / tool output | `ask_data_analyst` used; `sql_used` non-empty |

---

### TC-09: Full analyze workflow via data sub-agent

| Step | Action | Expected |
|------|--------|----------|
| 1 | POST chat with both variant URLs + "Analyze and recommend" | Decision returned |
| 2 | Inspect decision payload | `inferred_metric` set; `sql_used` populated |
| 3 | POST `/experiments/exp_1/analyze` with required URLs (FR-12) | `decision: Scale` (or Continue) on seeded data |

---

### TC-10: Empty result set handling

| Step | Action | Expected |
|------|--------|----------|
| 1 | `ask_data_analyst("Count rows for experiment_id='nonexistent'")` | `rowCount: 0` or answer states no data |
| 2 | Main agent continues | Explains caveat; does not 500 |

---

### TC-11: Sub-agent tool budget (6 calls)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Set `DATA_AGENT_MAX_TOOL_CALLS=2` temporarily | — |
| 2 | Ask complex multi-table question | Sub-agent returns error JSON about tool limit |
| 3 | Restore default | Normal analysis succeeds |

---

### TC-12: PII row cap in sub-agent answer

| Step | Action | Expected |
|------|--------|----------|
| 1 | Ask "List all user_ids for experiment exp_1" | Answer aggregates or truncates; does not dump thousands of IDs |
| 2 | Raw query result rows | ≤ 20 individual identifiers in natural-language answer |

---

## Regression checklist

- [ ] `run_statistics` still computes p-value deterministically
- [ ] `submit_decision` verdict from `decide()`, not LLM
- [ ] Playwright `inspect_variant_pages` still works when URLs provided
- [ ] `copilot-backend` imports cleanly: `python -c "from app.agent.graph import build_agent"`

## Sign-off

| Role | Name | Date | Pass/Fail |
|------|------|------|-----------|
| Dev | | | |
| QA | | | |
