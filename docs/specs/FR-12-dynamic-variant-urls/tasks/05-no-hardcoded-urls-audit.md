# Task 05: No Hardcoded URLs — Code & Prompt Audit

## Location

| Action | Path |
|--------|------|
| Audit | `packages/copilot-backend/app/agent/graph.py` |
| Audit | `packages/copilot-backend/app/**/*.py` |
| Audit | `packages/copilot-backend/app/routes/*.py` |
| Exclude | Seed scripts, ecom frontend demo defaults (out of agent path) |

## Dependencies

- Tasks 01, 03, 04 complete

## What to build

Run and fix violations from acceptance grep:

```bash
rg -n "localhost:5173|variant=A|variant=B|screen=checkout" \
  packages/copilot-backend/app/agent/
```

### Allowed exceptions

| Location | Why |
|----------|-----|
| `_browser_url()` | Rewrites localhost for Docker — not a default URL |
| Tests/fixtures | If added later, not in agent prompts |
| Comments referencing FR-12 removal | Documentation only |

### Forbidden in agent path

- System prompt example URLs
- Default URL constants used when PM omits input
- Reading `exp["variant_a_url"]` in `build_agent` or `_system_prompt`
- Injecting demo URLs in `analyze_experiment` fallback

### experiments table

URLs may still exist in DB for **display** or future FR-03 preflight — agent must ignore them unless PM also pasted them in chat.

Document in code comment near `build_agent`:

```python
# FR-12: variant URLs for browser/SQL workflow come from chat or /analyze body only.
# exp["variant_a_url"] is NOT passed to the agent automatically.
```

## Design spec

### Audit checklist

| Check | Pass criteria |
|-------|---------------|
| `_system_prompt` grep | No localhost, no variant= query examples |
| `analyze.py` | No DB URL fallback |
| `chat_turn` | No silent URL injection from experiment row |
| `inspect_variant_pages` | Verbatim PM URLs only |
| Seed / ecom packages | Out of scope for agent grep |

### Report template (attach to PR)

```markdown
## FR-12 URL audit
- [ ] copilot-backend/app/agent: clean
- [ ] copilot-backend/app/routes: clean
- Violations fixed: (list files)
```

## Done when

- [ ] Grep on `packages/copilot-backend/app/agent/` returns zero forbidden patterns in prompts
- [ ] No code path passes DB-stored URLs to agent without user message/body
- [ ] Audit documented in task PR or spec folder
- [ ] CLAUDE.md smoke-test curl updated to include analyze body URLs
