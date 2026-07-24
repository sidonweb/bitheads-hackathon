# Task 03: Tool Label Mapping

## Location

- `packages/copilot-backend/app/agent/stream_labels.py` — new module

## Dependencies

- Task 02 (tool_start events need labels)
- Tool names registered in `packages/copilot-backend/app/agent/graph.py`

## What to build

1. Create `TOOL_LABELS: dict[str, str]` mapping internal tool names to PM-friendly strings.
2. Export `label_for_tool(name: str) -> str` — returns mapped label or a title-cased fallback.
3. Wire into `chat_turn_stream` so every `tool_start` includes `"label"`.

## Design spec

### Label table (initial)

| Tool name | Label shown in UI |
|-----------|-------------------|
| `sql_db_query` | Querying experiment data |
| `sql_db_schema` | Inspecting data schema |
| `sql_db_list_tables` | Listing available tables |
| `run_statistics` | Running statistical test |
| `submit_decision` | Applying decision rules |
| Browser tools (`browser_*`) | Inspecting variant page |
| Unknown | Inspecting variant page (browser) or Running analysis step (other) |

### UI presentation

Step indicator appears **below** the streaming assistant bubble:

```
┌─────────────────────────────────────┐
│ Variant B shows a stronger CTA…     │  ← streaming tokens
└─────────────────────────────────────┘
  ◉ Querying experiment data            ← pulsing dot while tool active
  ✓ Inspecting variant page             ← check when tool_end ok
```

Labels are short (≤ 40 chars), present tense, no internal tool names.

## Done when

- [ ] `stream_labels.py` exists with mappings for all agent tools in `graph.py`
- [ ] `label_for_tool("sql_db_query")` returns `"Querying experiment data"`
- [ ] Unknown tools get a sensible fallback (never expose raw snake_case to PM)
- [ ] Labels appear in SSE `tool_start` payloads in manual test
