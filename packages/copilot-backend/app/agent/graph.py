"""Async LangGraph agent that analyzes one A/B experiment via conversation.

The agent no longer receives a hardcoded metric. Instead it:
  1. INSPECTS the two variant URLs using Playwright MCP browser tools (open page,
     read text/DOM) — plus whatever the PM says in chat.
  2. INFERS which event_name(s) define success from the page diff + conversation,
     and states that measurement plan explicitly.
  3. QUERIES universal_events (read-only SQL toolkit) to aggregate per variant.
  4. Runs the deterministic z-test (run_statistics) and submits a verdict
     (submit_decision) whose decision is derived by fixed rules.

Determinism boundary is unchanged: the LLM picks what to measure and writes the
prose, but never computes the numbers or the verdict.

Guardrails: the SQL toolkit uses a SELECT-only DB role (agent_readonly). If
Playwright is unavailable, the agent falls back to inferring from chat alone so
the demo still completes.
"""

import json
from urllib.parse import urlsplit, urlunsplit

from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase
from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ..config import (
    AGENT_DATABASE_URL,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    PLAYWRIGHT_MCP_URL,
    PLAYWRIGHT_LOCALHOST_ALIAS,
    USE_PLAYWRIGHT,
    XAI_API_KEY,
    XAI_MODEL,
)
from .statistics import run_statistics as _run_stats, decide


def _build_llm():
    if LLM_PROVIDER == "xai":
        from langchain_xai import ChatXAI

        return ChatXAI(model=XAI_MODEL, api_key=XAI_API_KEY, temperature=0)

    from langchain_openai import ChatOpenAI

    kwargs = {"model": OPENAI_MODEL,
              "api_key": OPENAI_API_KEY, "temperature": 0}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


def _build_sql_db() -> SQLDatabase:
    uri = AGENT_DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")
    return SQLDatabase.from_uri(
        uri,
        include_tables=["universal_events", "experiments"],
        sample_rows_in_table_info=2,
    )


def _browser_url(url: str | None) -> str:
    """Convert host-local URLs into addresses reachable from the MCP container."""
    if not url or not PLAYWRIGHT_LOCALHOST_ALIAS:
        return url or ""

    parts = urlsplit(url)
    if parts.hostname not in {"localhost", "127.0.0.1"}:
        return url

    netloc = PLAYWRIGHT_LOCALHOST_ALIAS
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


# --- Playwright MCP -----------------------------------------------------------
# The raw @playwright/mcp tools each open a FRESH, isolated browser session per
# call, so a `navigate` in one call and a `snapshot` in the next don't share a
# page (the second sees about:blank). To read a page reliably we must keep both
# calls inside ONE persistent MCP session. Rather than expose 24 low-level tools
# and hope the model threads a session through them, we expose a single
# high-level tool that navigates + snapshots each variant URL within one session.

_mcp_client = None  # cached MultiServerMCPClient (created once, in the loop)
_playwright_ok: bool | None = None  # None=unknown, True/False after first probe


async def _get_mcp_client():
    global _mcp_client
    if _mcp_client is None:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        _mcp_client = MultiServerMCPClient(
            {
                "playwright": {
                    "transport": "streamable_http",
                    "url": PLAYWRIGHT_MCP_URL,
                }
            }
        )
    return _mcp_client


async def _snapshot_url(session_tools: dict, url: str) -> str:
    """navigate → snapshot within a single (already-open) session."""
    await session_tools["browser_navigate"].ainvoke({"url": url})
    snap = await session_tools["browser_snapshot"].ainvoke({})
    return str(snap)


async def _inspect_pages(url_a: str, url_b: str) -> str:
    """Open both variant URLs in ONE persistent Playwright session and return
    their accessibility snapshots so the agent can diff what actually changed."""
    from langchain_mcp_adapters.tools import load_mcp_tools

    client = await _get_mcp_client()
    async with client.session("playwright") as session:
        tools = {t.name: t for t in await load_mcp_tools(session)}
        snap_a = await _snapshot_url(tools, url_a) if url_a else "(no url for A)"
        snap_b = await _snapshot_url(tools, url_b) if url_b else "(no url for B)"
    return (
        f"=== VARIANT A PAGE ({url_a}) ===\n{snap_a}\n\n"
        f"=== VARIANT B PAGE ({url_b}) ===\n{snap_b}"
    )


async def _probe_playwright() -> bool:
    """One-time connectivity check at startup. Caches whether the browser path is
    usable so the agent falls back to chat-only inference cleanly if not."""
    global _playwright_ok
    if _playwright_ok is not None:
        return _playwright_ok
    if not USE_PLAYWRIGHT:
        _playwright_ok = False
        return False
    try:
        client = await _get_mcp_client()
        tools = await client.get_tools()  # verifies the server is reachable
        _playwright_ok = any(t.name == "browser_navigate" for t in tools)
        print(f"[agent] Playwright MCP ready ({len(tools)} tools); "
              f"browser inspection {'ENABLED' if _playwright_ok else 'DISABLED'}.")
    except Exception as err:  # noqa: BLE001
        print(f"[agent] Playwright MCP unavailable, chat-only inference: {err}")
        _playwright_ok = False
    return _playwright_ok


# Kept for the startup warm-up hook in main.py.
async def _load_playwright_tools():
    return await _probe_playwright()


def _deep_link_checkout(url: str) -> str:
    """Append screen=checkout so the storefront jumps straight to the checkout
    page — that's where the A/B variants actually differ (the CTA). The landing
    page is near-identical between variants, so inspecting it tells us nothing."""
    if not url:
        return url
    parts = urlsplit(url)
    query = parts.query + ("&" if parts.query else "") + "screen=checkout"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))


def make_inspect_tool():
    """A single tool that opens both variant pages in one session and returns
    their snapshots. The PM provides the two URLs in chat — they are NOT read
    from config. Far more reliable for the model than 24 low-level calls."""

    @tool
    async def inspect_variant_pages(variant_a_url: str, variant_b_url: str) -> str:
        """Open BOTH variant URLs in a real browser and return their rendered
        content so you can see exactly what differs between them (the UI change).
        You MUST pass both URLs — get them from the PM in the chat. If you do not
        have both, ask the PM for them instead of calling this tool."""
        if not variant_a_url or not variant_b_url:
            return ("Missing a URL. Ask the PM to provide BOTH the variant A and "
                    "variant B URLs before calling this tool.")
        url_a = _deep_link_checkout(_browser_url(variant_a_url))
        url_b = _deep_link_checkout(_browser_url(variant_b_url))
        try:
            return await _inspect_pages(url_a, url_b)
        except Exception as err:  # noqa: BLE001
            return f"(browser inspection failed: {err}; ask the PM to describe the change)"

    return inspect_variant_pages


def _system_prompt(exp: dict, has_browser: bool) -> str:
    inspect = (
        "2. INSPECT: Once you have BOTH URLs, call `inspect_variant_pages(variant_a_url, "
        "variant_b_url)` with the two URLs the PM gave you. It opens both pages in a real "
        "browser and returns their rendered content. Read both snapshots and note what "
        "actually differs between A and B (the UI change)."
        if has_browser
        else "2. INSPECT: Browser tools are unavailable. Ask the PM to describe what "
        "differs between the two versions, and rely on that description."
    )
    return f"""You are an A/B-testing analyst assistant working WITH a product manager in a chat.

SCOPE — READ FIRST. You ONLY help with this: analyzing A/B experiments (comparing two
versions of a page/feature), inferring the success metric, querying the experiment's
event data, running the statistical test, and giving a Scale/Continue/Stop/Rollback
recommendation — plus directly related discussion. If the PM asks about anything else
(general knowledge, coding help, trivia, other products, personal questions, etc.),
politely decline in one sentence and steer them back, e.g. "I can only help analyze
this A/B experiment — want me to compare your two variants?" Do NOT answer off-topic
questions and do NOT use your tools for them.

Experiment context:
- id: {exp['id']}
- name: {exp['name']}
- hypothesis: {exp.get('hypothesis') or '(none provided)'}

The two variant URLs are NOT stored — the PM provides them in the chat. The success
metric is also NOT given — you must infer it.

Event data lives in universal_events(experiment_id, user_id, variant_id, event_name, metric_value, created_at).
Exposures are rows where event_name = 'page_view'. Other event_names are candidate
conversion signals (e.g. 'add_to_cart', 'checkout_started', 'checkout_completed').

When the PM asks you to analyze / compare / recommend, follow this workflow:
1. GET URLS: You need the URL of BOTH versions (variant A and variant B). Look for them
   in the conversation. If you do NOT have both, ASK the PM to paste both URLs and STOP
   there — do not guess, do not proceed, do not call any tool until you have both.
{inspect}
3. INFER: Run a SQL query to list the DISTINCT event_names that actually exist for this
   experiment (SELECT DISTINCT event_name FROM universal_events WHERE experiment_id =
   '{exp['id']}'). You may ONLY choose a metric from that list — never guess an event name
   that isn't present. From the page differences AND the available events, decide which
   single event_name best represents the success metric, and briefly say why. State it
   plainly, e.g. "Measuring checkout_completed / page_view conversion."
4. QUERY: Run ONE aggregation, scoped to experiment_id = '{exp['id']}', returning per
   variant_id the exposure count (page_view) and the conversion count (your inferred
   event_name). Do NOT filter event_name in the WHERE clause — you need BOTH event types
   in the same query. Use conditional aggregation, exactly like:
     SELECT variant_id,
            COUNT(*) FILTER (WHERE event_name = 'page_view') AS exposures,
            COUNT(*) FILTER (WHERE event_name = '<inferred_metric>') AS conversions
       FROM universal_events
      WHERE experiment_id = '{exp['id']}'
      GROUP BY variant_id;
5. STATS: Call run_statistics with control = variant A, treatment = variant B
   (success = conversions, total = exposures).
6. DECIDE: Call submit_decision with those statistics, a plain-English reasoning
   paragraph that names your inferred metric, and the exact SQL you ran.

For ordinary on-topic chat turns (questions about the experiment, discussion), reply
conversationally — only run the full workflow when the PM asks for analysis or a
recommendation. NEVER compute statistics yourself; always use run_statistics. Always
finish an analysis with submit_decision."""


def make_decision_tool(capture: dict):
    @tool
    def submit_decision(
        p_value: float,
        uplift: float,
        sample_size: dict,
        reasoning: str,
        inferred_metric: str = "",
        sql_used: str = "",
        confidence: float | None = None,
        control: str = "A",
        treatment: str = "B",
    ) -> str:
        """Submit the final analysis. Provide the inferred_metric (the event_name you
        chose as the success measure). The verdict (Scale/Continue/Stop/Rollback) is
        derived deterministically from the numbers by the decision rules."""
        ruled = decide(p_value, uplift, sample_size)
        decision = {
            "decision": ruled["decision"],
            "confidence": float(confidence if confidence is not None else max(0.0, 1 - p_value)),
            "p_value": float(p_value),
            "uplift": float(uplift),
            "sample_size": sample_size,
            "reasoning": reasoning,
            "inferred_metric": inferred_metric,
            "sql_used": sql_used,
            "control": control,
            "treatment": treatment,
            "rule_rationale": ruled["rationale"],
        }
        capture["decision"] = decision
        return json.dumps(decision)

    return submit_decision


@tool
def run_statistics(control: dict, treatment: dict) -> str:
    """Two-proportion z-test. control/treatment are {"success": int, "total": int}.
    Returns p_value, uplift (relative), confidence, significant, sample_size."""
    return json.dumps(_run_stats(control, treatment))


# Cache the read-only SQL toolkit + a shared checkpointer across turns.
_sql_tools = None
_checkpointer = MemorySaver()


async def build_agent(exp: dict):
    """Build the agent for one experiment. Returns (agent, capture, has_browser)."""
    global _sql_tools
    capture: dict = {"decision": None}

    llm = _build_llm()
    if _sql_tools is None:
        _sql_tools = SQLDatabaseToolkit(
            db=_build_sql_db(), llm=llm).get_tools()

    has_browser = await _probe_playwright()
    tools = [*_sql_tools, run_statistics, make_decision_tool(capture)]
    if has_browser:
        # One high-level browser tool (opens both pages in a persistent session)
        # instead of 24 low-level ones that can't share a page across calls.
        tools.append(make_inspect_tool())

    agent = create_react_agent(
        llm,
        tools,
        prompt=_system_prompt(exp, has_browser=has_browser),
        checkpointer=_checkpointer,
    )
    return agent, capture, has_browser


async def chat_turn(exp: dict, message: str, session_id: str | None = None) -> dict:
    """One conversational turn. Each session_id is an isolated conversation, so
    two different tests don't share history. Falls back to a per-experiment
    default thread when no session_id is given. Returns {reply, decision?}."""
    agent, capture, _ = await build_agent(exp)
    thread_id = f"{exp['id']}:{session_id}" if session_id else f"{exp['id']}:default"
    result = await agent.ainvoke(
        {"messages": [("user", message)]},
        config={"configurable": {
            "thread_id": thread_id}, "recursion_limit": 25},
    )
    reply = result["messages"][-1].content
    return {"reply": reply, "decision": capture["decision"]}


async def analyze_experiment(exp: dict) -> dict:
    """One-shot analysis (the /analyze endpoint). Instructs the agent to run the
    full workflow and return a decision."""
    agent, capture, _ = await build_agent(exp)
    await agent.ainvoke(
        {"messages": [
            ("user", "Analyze this experiment now and submit a decision.")]},
        config={"configurable": {
            "thread_id": f"{exp['id']}:analyze"}, "recursion_limit": 25},
    )
    if capture["decision"] is None:
        raise RuntimeError("agent did not submit a decision")
    return capture["decision"]
