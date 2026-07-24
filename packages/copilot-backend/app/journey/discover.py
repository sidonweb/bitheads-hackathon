"""Playwright MCP journey discovery — walk the storefront once and capture event names."""

import json
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from langchain_core.tools import tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from ..agent.graph import _browser_url, _build_llm, _load_playwright_tools
from .recipe import save_recipe

_discover_checkpointer = MemorySaver()


def _store_url(exp: dict, has_browser: bool) -> str:
    """Base storefront URL without ?variant= override, reachable from MCP browser."""
    raw = exp.get("variant_a_url") or exp.get("variant_b_url") or ""
    if not raw:
        return ""
    parts = urlsplit(raw)
    q = parse_qs(parts.query, keep_blank_values=True)
    q.pop("variant", None)
    query = urlencode({k: v[0] for k, v in q.items()}, doseq=False)
    cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
    return _browser_url(cleaned) if has_browser else cleaned


def _discovery_prompt(exp: dict, store_url: str, has_browser: bool) -> str:
    if not has_browser:
        return (
            "Browser tools are unavailable. Call submit_journey_recipe with the default "
            "ecommerce funnel: exposure page_view, funnel add_to_cart, checkout_started, "
            "checkout_completed, conversion checkout_completed."
        )
    return f"""You are discovering the telemetry funnel for experiment {exp['id']}.

Store URL (use this in the browser): {store_url}

Follow these steps exactly:
1. Navigate to the store URL.
2. Use browser_evaluate to run: localStorage.setItem('copilot_uid', 'discover_probe_1')
3. Reload/navigate to the store URL again so the flag API assigns a variant.
4. Walk the purchase funnel using browser_snapshot and browser_click:
   - Open a product from the grid
   - Add to cart
   - Proceed to checkout
   - Place order / complete checkout
5. Call browser_network_requests and find every POST request to a path containing "/events".
   Read the JSON body of each and extract eventName values in chronological order.
6. Call submit_journey_recipe with:
   - exposure_event: the first event (usually page_view on load)
   - conversion_event: the final success event (usually checkout_completed)
   - funnel_events: all distinct event names in order observed during a full conversion path
   - store_url: "{store_url}"

If the network capture is empty, use the standard ecommerce names:
page_view, add_to_cart, checkout_started, checkout_completed.

You MUST finish by calling submit_journey_recipe. Do not analyze statistics."""


def make_recipe_tool(experiment_id: str, capture: dict):
    @tool
    def submit_journey_recipe(
        exposure_event: str,
        conversion_event: str,
        funnel_events: list[str],
        store_url: str = "",
    ) -> str:
        """Submit the discovered journey recipe after walking the funnel."""
        funnel = list(dict.fromkeys(funnel_events))
        on_convert = [e for e in funnel if e != exposure_event]
        recipe = save_recipe(
            experiment_id,
            {
                "exposureEvent": exposure_event,
                "conversionEvent": conversion_event,
                "funnelEvents": funnel,
                "funnelOnConvert": on_convert,
                "discoveredVia": "playwright-mcp",
                "storeUrl": store_url,
            },
        )
        capture["recipe"] = recipe
        return json.dumps(recipe)

    return submit_journey_recipe


async def discover_journey(exp: dict) -> dict:
    """Run Playwright discovery once; returns {{reply, recipe?}}."""
    capture: dict = {"recipe": None}
    llm = _build_llm()
    browser_tools = await _load_playwright_tools()
    has_browser = bool(browser_tools)
    store_url = _store_url(exp, has_browser)

    tools = [*browser_tools, make_recipe_tool(exp["id"], capture)]
    agent = create_react_agent(
        llm,
        tools,
        prompt=_discovery_prompt(exp, store_url, has_browser),
        checkpointer=_discover_checkpointer,
    )

    result = await agent.ainvoke(
        {"messages": [("user", "Discover the experiment funnel and submit the journey recipe.")]},
        config={
            "configurable": {"thread_id": f"{exp['id']}:discover"},
            "recursion_limit": 35,
        },
    )
    reply = result["messages"][-1].content

    if capture["recipe"] is None:
        recipe = save_recipe(
            exp["id"],
            {
                "exposureEvent": "page_view",
                "conversionEvent": "checkout_completed",
                "funnelEvents": [
                    "page_view",
                    "add_to_cart",
                    "checkout_started",
                    "checkout_completed",
                ],
                "funnelOnConvert": ["add_to_cart", "checkout_started", "checkout_completed"],
                "discoveredVia": "fallback-default",
                "storeUrl": store_url,
            },
        )
        capture["recipe"] = recipe
        reply = (
            f"{reply}\n\n(No recipe submitted by agent — saved default ecommerce funnel.)"
        )

    return {"reply": reply, "recipe": capture["recipe"]}
