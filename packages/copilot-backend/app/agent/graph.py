"""Async LangGraph agent that analyzes one A/B experiment via conversation.

The agent:
  1. INSPECTS the two variant URLs using Playwright MCP browser tools (open page,
     read text/DOM) — plus whatever the PM says in chat.
  2. INFERS which event_name(s) define success from the page diff + conversation,
     and states that measurement plan explicitly.
  3. Delegates data questions to ask_data_analyst (read-only data sub-agent).
  4. Runs the deterministic z-test (run_statistics) and submits a verdict
     (submit_decision) whose decision is derived by fixed rules.

Determinism boundary is unchanged: the LLM picks what to measure and writes the
prose, but never computes the numbers or the verdict.

Guardrails: the data sub-agent uses a SELECT-only DB role (agent_readonly). If
Playwright is unavailable, the agent falls back to inferring from chat alone so
the demo still completes.
"""

import asyncio
import json
import re
from collections.abc import AsyncIterator
from urllib.parse import urlsplit, urlunsplit

from langchain_core.tools import tool
from langgraph.errors import GraphRecursionError
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ..config import (
    AGENT_LLM_TIMEOUT_SEC,
    AGENT_MAX_TOOL_CALLS,
    AGENT_RECURSION_LIMIT,
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    PLAYWRIGHT_LOCALHOST_ALIAS,
    PLAYWRIGHT_MCP_URL,
    USE_PLAYWRIGHT,
    XAI_API_KEY,
    XAI_MODEL,
)
from .data_agent import make_ask_data_analyst_tool
from .guardrails import (
    AgentError,
    ToolCallBudget,
    ToolFailureTracker,
    run_agent_safe,
    user_message_for,
    wrap_tools,
)
from .statistics import run_statistics as _run_stats, decide
from .stream_labels import label_for_tool


def _build_llm():
    if LLM_PROVIDER == "xai":
        from langchain_xai import ChatXAI

        return ChatXAI(model=XAI_MODEL, api_key=XAI_API_KEY, temperature=0)

    from langchain_openai import ChatOpenAI

    kwargs = {"model": OPENAI_MODEL, "api_key": OPENAI_API_KEY, "temperature": 0}
    if OPENAI_BASE_URL:
        kwargs["base_url"] = OPENAI_BASE_URL
    return ChatOpenAI(**kwargs)


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
_mcp_client = None
_playwright_ok: bool | None = None


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
    await session_tools["browser_navigate"].ainvoke({"url": url})
    snap = await session_tools["browser_snapshot"].ainvoke({})
    return str(snap)


async def _inspect_pages(url_a: str, url_b: str) -> str:
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
    global _playwright_ok
    if _playwright_ok is not None:
        return _playwright_ok
    if not USE_PLAYWRIGHT:
        _playwright_ok = False
        return False
    try:
        client = await _get_mcp_client()
        tools = await client.get_tools()
        _playwright_ok = any(t.name == "browser_navigate" for t in tools)
        print(
            f"[agent] Playwright MCP ready ({len(tools)} tools); "
            f"browser inspection {'ENABLED' if _playwright_ok else 'DISABLED'}."
        )
    except Exception as err:  # noqa: BLE001
        print(f"[agent] Playwright MCP unavailable, chat-only inference: {err}")
        _playwright_ok = False
    return _playwright_ok


async def _load_playwright_tools():
    return await _probe_playwright()


def make_inspect_tool():
    @tool
    async def inspect_variant_pages(variant_a_url: str, variant_b_url: str) -> str:
        """Open BOTH variant URLs in a real browser and return their rendered
        content so you can see exactly what differs between them (the UI change).
        You MUST pass both URLs — get them from the PM in the chat. If you do not
        have both, ask the PM for them instead of calling this tool."""
        if not variant_a_url or not variant_b_url:
            return (
                "Missing a URL. Ask the PM to provide BOTH the variant A and "
                "variant B URLs before calling this tool."
            )
        url_a = _browser_url(variant_a_url)
        url_b = _browser_url(variant_b_url)
        try:
            return await _inspect_pages(url_a, url_b)
        except Exception as err:  # noqa: BLE001
            return f"(browser inspection failed: {err}; ask the PM to describe the change)"

    return inspect_variant_pages


def _system_prompt(exp: dict, has_browser: bool) -> str:
    inspect = (
        "2. INSPECT: Once you have BOTH URLs, call `inspect_variant_pages(variant_a_url, "
        "variant_b_url)` with the two URLs the PM gave you. Pass them verbatim — do not "
        "modify query parameters. It opens both pages in a real browser and returns their "
        "rendered content. Read both snapshots and note what actually differs between A and B."
        if has_browser
        else "2. INSPECT: Browser tools are unavailable. Ask the PM to describe what "
        "differs between the two versions, and rely on that description."
    )
    return f"""You are an A/B-testing analyst assistant working WITH a product manager in a chat.

SCOPE — READ FIRST. You ONLY help with this: analyzing A/B experiments (comparing two
versions of a page/feature), inferring the success metric, querying the experiment's
event data, running the statistical test, and giving a Scale/Continue/Stop/Rollback
recommendation — plus directly related discussion.

ON-TOPIC (always help): analyze/compare variants, visualize or chart experiment metrics,
graph the A/B data, explain results for THIS experiment, questions about the workflow.

OFF-TOPIC (decline briefly): general capabilities, unrelated trivia, coding help on
other products, personal questions. Use the one-line steer-back ONLY for off-topic asks.

If the PM asks to analyze, compare, chart, or graph experiment data but has NOT pasted
both variant URLs yet, ask them once for both links — do NOT treat that as off-topic.

The chat UI renders bar charts, funnels, and tables automatically from stored telemetry.
Do not draw ASCII charts in prose. For visualization-only requests (chart/graph/breakdown
with no analysis or verdict), reply in 1–2 short sentences — do NOT call ask_data_analyst;
the UI builds charts from the event matrix server-side.

NEVER paste SQL in your reply. All database access goes through ask_data_analyst only.

TOOL ERROR RECOVERY — mandatory self-check loop
When ANY tool returns an error, failure text, or empty/useless result:
1. STOP — do not immediately call another tool or repeat the same call.
2. Ask yourself: "Am I doing something wrong?" Assume the failure is caused by bad
   inputs or a wrong approach until you have verified otherwise.
3. Verify ALL inputs you passed before the failed call:
   - experiment_id is exactly `{exp['id']}` in every data question
   - variant URLs from experiment context or the PM's chat (never invented)
   - data questions reference event_name (NOT event_type) and variant_id IN ('A','B')
   - run_statistics uses integer success/total counts from ask_data_analyst — never guessed
   - inspect_variant_pages gets two full http(s) URLs unchanged from the PM
4. Fix the root cause, then retry that tool AT MOST ONCE with corrected inputs.
5. If the same tool fails twice in one turn: stop retrying, tell the PM plainly what
   blocked you. Do not burn the tool budget on repeated identical mistakes.
The tool output will include a TOOL ERROR — SELF-CHECK LOOP block when this happens.
Follow it exactly before any retry.

Experiment context:
- id: {exp['id']}
- name: {exp['name']}
- hypothesis: {exp.get('hypothesis') or '(none provided)'}
- variant A inspect URL: {exp.get('variant_a_url') or '(not set — ask PM)'}
- variant B inspect URL: {exp.get('variant_b_url') or '(not set — ask PM)'}

Each experiment tests ONE funnel stage. Storefront inspect URLs use `?variation=…&variant=A|B`
(and optional `?screen=` deep links) — never experiment ids in the URL. Control = variant A,
treatment = variant B. The success metric is NOT pre-configured — infer it from the page diff
+ event data. Common metrics: add_to_cart, checkout_started, checkout_completed (always verify
via ask_data_analyst that the event exists before using it).

Event data: use ask_data_analyst to discover schema and fetch aggregates for experiment
`{exp['id']}`. Never write SQL yourself — delegate all database questions to ask_data_analyst.

When the PM asks you to analyze / compare / recommend / chart / graph / visualize,
follow this workflow:
1. GET URLS: Use variant_a_url and variant_b_url from the experiment context above when
   set. Otherwise extract BOTH variant URLs from the PM's messages in this thread.
   - Pass URLs verbatim to inspect_variant_pages — do NOT modify query parameters.
   - If you do NOT have both URLs, ask the PM once to paste both links and STOP.
     Do not call inspect_variant_pages, ask_data_analyst, run_statistics, or
     submit_decision until both URLs are available.
{inspect}
3. INFER: From the page diff + ask_data_analyst (list events for this experiment),
   choose ONE success metric from events that actually exist. State why. Exposure is
   usually page_view; conversion may be add_to_cart, checkout_started, or checkout_completed.
4. DATA: Call ask_data_analyst for per-variant exposure and conversion counts using
   your inferred metric.
5. STATS: Call run_statistics with control = variant A, treatment = variant B
   (success = conversions, total = exposures).
6. DECIDE: Call submit_decision with those statistics, a plain-English reasoning
   paragraph that names your inferred metric, and the sql_used from ask_data_analyst.

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


_checkpointer = MemorySaver()


async def build_agent(exp: dict, budget: ToolCallBudget):
    """Build the agent for one experiment. Returns (agent, capture, has_browser)."""
    capture: dict = {"decision": None}

    llm = _build_llm()
    has_browser = await _probe_playwright()
    tools = [
        run_statistics,
        make_decision_tool(capture),
        make_ask_data_analyst_tool(),
    ]
    if has_browser:
        tools.append(make_inspect_tool())

    tools = wrap_tools(
        tools,
        budget,
        experiment_id=exp["id"],
        failure_tracker=ToolFailureTracker(max_retries_per_tool=1),
    )

    agent = create_react_agent(
        llm,
        tools,
        prompt=_system_prompt(exp, has_browser=has_browser),
        checkpointer=_checkpointer,
    )
    return agent, capture, has_browser


_SKIP_STREAM_TOOLS = frozenset({"", "RunnableSequence", "RunnableLambda"})

_SQL_FRAGMENT = re.compile(
    r"^\s*(SELECT|FROM|WHERE|GROUP\s+BY|COUNT\s*\(|FILTER\s*\(|;"
    r"|variant_id|event_name|event_type|universal_events|experiment_id\s*=)",
    re.I,
)


def _looks_like_sql_fragment(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if _SQL_FRAGMENT.search(stripped):
        return True
    upper = stripped.upper()
    return "FROM UNIVERSAL_EVENTS" in upper or upper.startswith("SELECT ")


def _chunk_text(content) -> str:
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                parts.append(block.get("text", ""))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _should_stream_tool(name: str | None) -> bool:
    return bool(name) and name not in _SKIP_STREAM_TOOLS


def _tool_output_ok(output) -> bool:
    text = output if isinstance(output, str) else str(output)
    lowered = text.lower()
    if lowered.startswith("(browser inspection failed"):
        return False
    if '"error"' in lowered and '"error": null' not in lowered:
        try:
            payload = json.loads(text)
            if isinstance(payload, dict) and payload.get("error"):
                return False
        except json.JSONDecodeError:
            if "error" in lowered[:120]:
                return False
    return True


async def chat_turn_stream(
    exp: dict,
    message: str,
    session_id: str,
) -> AsyncIterator[dict]:
    """Stream one conversational turn as typed dict events for SSE mapping."""
    budget = ToolCallBudget(AGENT_MAX_TOOL_CALLS)
    agent, capture, _ = await build_agent(exp, budget)
    thread_id = f"{exp['id']}:{session_id}"
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": AGENT_RECURSION_LIMIT,
    }
    seen_tool_end_runs: set[str] = set()

    try:
        stream = agent.astream_events(
            {"messages": [("user", message)]},
            config=config,
            version="v2",
        )
        deadline = asyncio.get_running_loop().time() + AGENT_LLM_TIMEOUT_SEC

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise asyncio.TimeoutError()

            try:
                event = await asyncio.wait_for(stream.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break

            kind = event.get("event")
            if kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                content = _chunk_text(getattr(chunk, "content", None))
                if content and not _looks_like_sql_fragment(content):
                    yield {"type": "token", "content": content}
            elif kind == "on_tool_start":
                name = event.get("name") or ""
                if not _should_stream_tool(name):
                    continue
                yield {
                    "type": "tool_start",
                    "name": name,
                    "label": label_for_tool(name),
                }
            elif kind == "on_tool_end":
                run_id = event.get("run_id") or ""
                if run_id in seen_tool_end_runs:
                    continue
                seen_tool_end_runs.add(run_id)
                name = event.get("name") or ""
                if not _should_stream_tool(name):
                    continue
                output = event.get("data", {}).get("output", "")
                yield {
                    "type": "tool_end",
                    "name": name,
                    "ok": _tool_output_ok(output),
                }
    except AgentError:
        raise
    except asyncio.TimeoutError as err:
        raise AgentError(
            code="LLM_UNAVAILABLE",
            message=user_message_for("LLM_UNAVAILABLE"),
            retryable=True,
            details={"toolCallsUsed": budget.count},
        ) from err
    except GraphRecursionError as err:
        raise AgentError(
            code="AGENT_RECURSION_LIMIT",
            message=user_message_for("AGENT_RECURSION_LIMIT"),
            retryable=True,
            details={"toolCallsUsed": budget.count},
        ) from err
    except Exception as err:  # noqa: BLE001
        raise AgentError(
            code="INTERNAL_ERROR",
            message=user_message_for("INTERNAL_ERROR"),
            retryable=False,
            details={"toolCallsUsed": budget.count},
        ) from err

    decision = capture.get("decision")
    if decision:
        yield {"type": "decision", "decision": decision}

    verdict = decision.get("decision") if decision else None
    print(
        f"INFO experiment_id={exp['id']} tool_calls={budget.count} "
        f"verdict={verdict or 'none'} (stream)"
    )
    yield {"type": "done", "toolCallsUsed": budget.count}


async def chat_turn(exp: dict, message: str, session_id: str | None = None) -> dict:
    """One conversational turn. Returns {reply, decision?, tool_calls_used}."""
    budget = ToolCallBudget(AGENT_MAX_TOOL_CALLS)
    agent, capture, _ = await build_agent(exp, budget)
    thread_id = f"{exp['id']}:{session_id}" if session_id else f"{exp['id']}:default"
    return await run_agent_safe(
        agent,
        {"messages": [("user", message)]},
        {"configurable": {"thread_id": thread_id}},
        budget,
        capture,
        expect_decision=False,
        experiment_id=exp["id"],
    )


async def analyze_experiment(
    exp: dict,
    *,
    variant_a_url: str,
    variant_b_url: str,
) -> dict:
    """One-shot analysis. URLs are injected from the API body, not experiment config."""
    message = (
        f"Variant A URL: {variant_a_url}\n"
        f"Variant B URL: {variant_b_url}\n"
        "Analyze this experiment now and submit a decision."
    )
    budget = ToolCallBudget(AGENT_MAX_TOOL_CALLS)
    agent, capture, _ = await build_agent(exp, budget)
    result = await run_agent_safe(
        agent,
        {"messages": [("user", message)]},
        {"configurable": {"thread_id": f"{exp['id']}:analyze"}},
        budget,
        capture,
        expect_decision=True,
        experiment_id=exp["id"],
    )
    return result["decision"]


def clear_chat_threads(experiment_id: str) -> None:
    """Drop in-memory chat history for an experiment (demo reset)."""
    for thread_id in (experiment_id, f"{experiment_id}:analyze"):
        try:
            _checkpointer.delete_thread(thread_id)
        except AttributeError:
            store = getattr(_checkpointer, "storage", None)
            if isinstance(store, dict):
                store.pop(thread_id, None)
        except Exception:  # noqa: BLE001
            pass
