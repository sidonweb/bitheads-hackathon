# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Universal A/B Testing & Decision Platform ("AI Experiment Copilot"). A mock e-commerce app streams generic telemetry into a single Postgres table; a conversational LangGraph agent inspects the two variant pages with a real browser, **infers** the success metric, writes SQL to aggregate the events, runs a real statistical test, and returns a **Scale / Continue / Stop / Rollback** verdict to a PM dashboard. Built for a hackathon golden-path demo (one experiment, `exp_1`, seeded so Variant B clearly wins).

The distinguishing design points:
- **Metric is inferred, not configured.** `primary_metric` is NULL in the DB. The agent discovers the real event names via SQL, then picks the success metric from the variant page diff + the PM's chat — never from hardcoded config.
- **Two separate backends** share one Postgres via distinct DB roles.
- **The agent uses Playwright (via MCP)** to open the actual variant URLs, with an automatic fallback to chat-only inference if the browser is unavailable.

## Layout

Six services. Backends + Playwright are Python/Node in Docker; the two React frontends are containerized as static nginx builds.

| Package | Role | Port |
|---------|------|------|
| `packages/ecom-backend` | FastAPI. **Owns the schema + events.** Ingestion (`/events`), variant flag, runs migrations + seed. | 3002 |
| `packages/copilot-backend` | FastAPI. Experiments CRUD, the LangGraph agent, `/chat`, `/analyze`. | 3001 |
| `packages/ecom` | React storefront (test subject). Renders `?variant=A\|B`. | 5173 |
| `packages/dashboard` | React PM dashboard: chat panel + decision/metrics cards. | 5174 |
| `packages/playwright-mcp` | Custom image: Playwright MCP browser-tool server. | 8931 |
| (postgres) | Shared instance. | 5432 |

## Running

```bash
docker compose up -d --build    # drop --build if no code change
```
`docker-compose.yml` supplies `OPENAI_API_KEY` to copilot-backend via `env_file: packages/copilot-backend/.env`, so no shell-sourcing is needed. If `/analyze` or `/chat` 500s with "Missing credentials", the key is missing from that `.env`.

**Startup order matters and is wired via `depends_on`:** ecom-backend runs migrations + seed (it owns the schema); copilot-backend waits for the `experiments` table to appear before starting; the copilot warms its Playwright browser tools once at FastAPI startup (look for `Loaded 24 Playwright browser tools` in its logs).

**Frontends:** built into the images; open `localhost:5174` (dashboard) and `localhost:5173/?variant=A` / `?variant=B` (storefront). For host dev instead, `cd packages/ecom && npm run dev`.

**Reset demo data** (the Postgres volume persists across runs, so re-seeding STACKS — always reset first for clean numbers):
```bash
docker compose exec -T ecom-backend python -c "import psycopg; from app.config import ADMIN_DATABASE_URL; c=psycopg.connect(ADMIN_DATABASE_URL, autocommit=True); c.execute('TRUNCATE universal_events RESTART IDENTITY'); c.execute('DELETE FROM experiments'); print('reset OK')"
docker compose exec -T ecom-backend python scripts/seed.py
```
Reset/seed run against **ecom-backend** (it owns the schema) and use the admin connection — the app roles deliberately lack TRUNCATE/DELETE. `docker compose down -v` wipes the volume for a fully fresh start.

**Smoke-test the agent:** `curl -s -X POST localhost:3001/experiments/exp_1/analyze`

## Architecture

**Universal telemetry, single table.** Everything flows through `universal_events(experiment_id, user_id, variant_id, event_name, metric_value, created_at)`. No per-client integrations — any client POSTs the same generic event shape. `experiments` holds config including `variant_a_url` / `variant_b_url` (the pages the agent inspects) and a nullable `primary_metric`. Schema + roles live in **`packages/ecom-backend/migrations/001_init.sql`** (ecom-backend owns the schema; copilot-backend never migrates).

**Backend split — who owns what:**
- **ecom-backend** writes events, serves the flag, owns migrations/seed. Runs as `ecom_role`.
- **copilot-backend** owns experiments (`copilot_role`, which also has SELECT on events to render dashboard metrics) and runs the agent's read-only SQL as `agent_readonly`.

**The agent (`packages/copilot-backend/app/agent/graph.py`) is an async LangGraph `create_react_agent`** with a `MemorySaver` checkpointer (conversation persists per experiment via `thread_id`). Its tools:
1. **Playwright MCP browser tools** — loaded once at startup via `MultiServerMCPClient` and cached in `_browser_tools`. Reconnecting per-request breaks inside uvicorn's loop, so they are warmed in the FastAPI `lifespan` hook in `main.py`. On any failure the agent falls back to chat-only inference (`USE_PLAYWRIGHT`, graceful `[]`).
2. LangChain `SQLDatabaseToolkit` — inspect schema + run SELECTs (read-only role).
3. `run_statistics` — deterministic two-proportion z-test.
4. `submit_decision` — applies the verdict rules, captures the structured result (including the agent's `inferred_metric`).

**Agent workflow (metric inference is the core new behavior):** INSPECT the two variant URLs with the browser → discover the real `event_name`s via `SELECT DISTINCT` (never guess a name that isn't present) → INFER the success metric from the page diff + chat → QUERY per-variant exposures/conversions → run_statistics → submit_decision.

**Determinism boundary — do not violate this.** The LLM decides *what* to query and writes the prose, but it never computes the numbers or picks the verdict. The z-test math is `app/agent/statistics.py::run_statistics`; the verdict is derived by `statistics.py::decide` (rules: `p<0.05 & uplift>0 → Scale`; `p<0.05 & uplift<0 → Rollback`; insufficient sample or non-significant → `Continue`; else `Stop`). Letting the model return a decision or p-value directly is a regression — route it through these functions.

**Security guardrail is at the DB layer, not just in code.** `agent_readonly` (used by the SQL toolkit via `AGENT_DATABASE_URL`) has SELECT-only grants + a 5s `statement_timeout`. Even if the model emits a mutation, Postgres rejects it with "permission denied". Keep the agent on `agent_readonly`.

**LLM provider is switchable** via `LLM_PROVIDER` (`openai` default, or `xai`). `_build_llm()` in `graph.py` branches on it. Default `gpt-4o-mini`. `OPENAI_BASE_URL` points `ChatOpenAI` at an OpenAI-compatible gateway (e.g. OpenRouter). Note: an xAI key with no team credits returns `permission-denied` on every model — that's account-level, not a code issue.

**Playwright MCP image** (`packages/playwright-mcp/Dockerfile`): version pairing between `@playwright/mcp` and prebuilt Playwright base images is fragile (chrome vs chrome-for-testing vs chromium-NNNN). The working recipe is a `node` base + `@playwright/mcp` global + `playwright-mcp install-browser chrome-for-testing` at build time + launching with `--browser chromium --allowed-hosts '*'`. The `--allowed-hosts '*'` is required or the server 403s cross-container requests.

## API contracts (frontends depend on these — keep stable)

**ecom-backend (`:3002`):**
- `POST /events` — `{userId, experimentId, variantId, eventName, metricValue, timestamp?}`
- `POST /events/bulk` — `{events: [...]}`
- `GET /experiments/:id/flag?userId=` — `{experimentId, variantId, trafficSplit}`

**copilot-backend (`:3001`):**
- `POST /experiments` / `GET /experiments/:id` / `PATCH /experiments/:id` (fields incl. `variantAUrl`, `variantBUrl`; `primaryMetric` nullable)
- `POST /experiments/:id/analyze` — runs the full workflow, returns the Decision (`decision, confidence, p_value, uplift, sample_size, reasoning, inferred_metric, sql_used, rule_rationale`)
- `POST /experiments/:id/chat` — `{message}` → `{reply, decision?}`; `decision` populated when the agent completes an analysis

**Variant assignment** (`ecom-backend/app/flag.py`) is deterministic FNV-1a hashing of `experimentId:userId` → bucket 0–99; `< trafficSplit` → B, else A. The storefront honors a `?variant=A|B` URL override (so each variant is directly viewable and the agent's browser can open a specific one); otherwise it fetches from `GET /flag`, then fires funnel events (`page_view` → `add_to_cart` → `checkout_started` → `checkout_completed`).

Frontends target `VITE_API_BASE` (baked at image build): ecom → `:3002`, dashboard → `:3001`.

## Notes

- `.env` files are gitignored (only `.env.example` committed). `packages/copilot-backend/.env` holds the real `OPENAI_API_KEY`.
- Seed (`ecom-backend/scripts/seed.py`) uses fixed RNG seed 42: A ≈ 15.8%, B ≈ 18.0% over 5000 users each — engineered to yield a significant "Scale". It sets the variant URLs and leaves `primary_metric` NULL on purpose.
- gpt-4o-mini sometimes narrates SQL instead of calling the tool, or guesses non-existent event names — the prompt in `graph.py` explicitly counters both (forces `SELECT DISTINCT event_name` first, gives a `FILTER (WHERE ...)` query template). If you change the model, re-verify the agent actually calls tools rather than describing them.
- No automated test suite in the current tree; verify by running the stack and hitting the endpoints (the deterministic `statistics.py` functions are the safest thing to unit-test if you add tests).
