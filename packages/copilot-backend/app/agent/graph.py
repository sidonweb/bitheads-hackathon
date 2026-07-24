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


# Browser tools are loaded ONCE (at startup) and cached. Reconnecting on every
# request breaks inside uvicorn's running event loop, and it's wasteful anyway.
_browser_tools: list | None = None


async def _load_playwright_tools():
    """Load browser tools from the Playwright MCP server, cached after first success.
    Returns [] on any failure so the agent still runs in chat-only inference mode."""
    global _browser_tools
    if _browser_tools is not None:
        return _browser_tools
    if not USE_PLAYWRIGHT:
        _browser_tools = []
        return _browser_tools
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        client = MultiServerMCPClient(
            {
                "playwright": {
                    "transport": "streamable_http",
                    "url": PLAYWRIGHT_MCP_URL,
                }
            }
        )
        _browser_tools = await client.get_tools()
        print(
            f"[agent] Loaded {len(_browser_tools)} Playwright browser tools.")
        return _browser_tools
    except Exception as err:  # noqa: BLE001
        print(
            f"[agent] Playwright MCP unavailable, chat-only inference: {err}")
        return []  # not cached — allow a later retry to succeed


def _system_prompt(exp: dict, has_browser: bool) -> str:
    variant_a_url = exp.get("variant_a_url") or ""
    variant_b_url = exp.get("variant_b_url") or ""
    browser_variant_a_url = _browser_url(variant_a_url) if has_browser else variant_a_url
    browser_variant_b_url = _browser_url(variant_b_url) if has_browser else variant_b_url

    inspect = (
        "1. INSPECT: Use the Playwright browser tools to open browser_variant_a_url "
        "and browser_variant_b_url. Read each page's visible text/DOM and note what "
        "actually differs between A and B."
        if has_browser
        else "1. INSPECT: Browser tools are unavailable. Rely on the PM's chat "
        "description of what differs between A and B."
    )
    return f"""You are an autonomous A/B-testing analyst working WITH a product manager in a chat.

Experiment:
- id: {exp['id']}
- name: {exp['name']}
- hypothesis: {exp.get('hypothesis') or '(none provided)'}
- variant A ({exp.get('variant_a_name')}): {variant_a_url or '(no url)'}
- variant B ({exp.get('variant_b_name')}): {variant_b_url or '(no url)'}
- browser_variant_a_url: {browser_variant_a_url or '(no url)'}
- browser_variant_b_url: {browser_variant_b_url or '(no url)'}

The success metric is NOT given to you — you must infer it.

Event data lives in universal_events(experiment_id, user_id, variant_id, event_name, metric_value, created_at).
Exposures are rows where event_name = 'page_view'. Other event_names are candidate
conversion signals (e.g. 'add_to_cart', 'checkout_started', 'checkout_completed').

When the PM asks you to analyze, follow this workflow:
{inspect}
2. INFER: First run a SQL query to list the DISTINCT event_names that actually exist
   for this experiment (SELECT DISTINCT event_name FROM universal_events WHERE
   experiment_id = '{exp['id']}'). You may ONLY choose a metric from that list — never
   guess an event name that isn't present. From the page differences, the conversation,
   AND the available events, decide which single event_name best represents the success
   metric, and briefly say why. State it plainly, e.g. "Measuring checkout_completed / page_view conversion."
3. QUERY: Use the SQL tools to run ONE aggregation, scoped to experiment_id = '{exp['id']}',
   returning per variant_id the exposure count (page_view) and the conversion count
   (your inferred event_name). Do NOT filter event_name in the WHERE clause — you need
   BOTH event types in the same query. Use conditional aggregation, exactly like:
     SELECT variant_id,
            COUNT(*) FILTER (WHERE event_name = 'page_view') AS exposures,
            COUNT(*) FILTER (WHERE event_name = '<inferred_metric>') AS conversions
       FROM universal_events
      WHERE experiment_id = '{exp['id']}'
      GROUP BY variant_id;
4. STATS: Call run_statistics with control = variant A, treatment = variant B
   (success = conversions, total = exposures).
5. DECIDE: Call submit_decision with those statistics, a plain-English reasoning
   paragraph that names your inferred metric, and the exact SQL you ran.

For ordinary chat turns (questions, discussion), just reply conversationally — only
run the full workflow when the PM asks for analysis or a recommendation. NEVER compute
statistics yourself; always use run_statistics. Always finish an analysis with submit_decision."""


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

    browser_tools = await _load_playwright_tools()
    tools = [*_sql_tools, *browser_tools,
             run_statistics, make_decision_tool(capture)]

    agent = create_react_agent(
        llm,
        tools,
        prompt=_system_prompt(exp, has_browser=bool(browser_tools)),
        checkpointer=_checkpointer,
    )
    return agent, capture, bool(browser_tools)


async def chat_turn(exp: dict, message: str) -> dict:
    """One conversational turn. Persists history per experiment via thread_id.
    Returns {reply, decision?}."""
    agent, capture, _ = await build_agent(exp)
    result = await agent.ainvoke(
        {"messages": [("user", message)]},
        config={"configurable": {
            "thread_id": exp["id"]}, "recursion_limit": 25},
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
