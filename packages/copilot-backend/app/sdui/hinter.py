"""SDUI hinter — picks widget types wisely, never every response."""

from __future__ import annotations

import asyncio
import logging
import re

from ..agent.graph import _build_llm
from .schema import BlockType, WidgetPlan

logger = logging.getLogger(__name__)

HINTER_TIMEOUT_SECONDS = 8

_SYSTEM_PROMPT = """You are an SDUI widget planner for an A/B experiment copilot chat UI.

Your job: decide IF and WHICH structured UI widgets should accompany the assistant's text reply.

CRITICAL — use widgets WISELY, NOT on every response:
- Default should_render=false for most turns.
- Plain conversation, URL prompts, scope refusals, capabilities questions → NO widgets.
- Only suggest widgets when they clearly add value (data viz request, post-analysis summary).

Allowed block_types (pick 0–4 when should_render=true):
- bar_chart, funnel_chart, table — need experiment event data in DB
- metric_grid, decision_card, actions — ONLY when a final decision exists
- alert — only for warnings (usually server adds this, skip unless user asks about errors)
- markdown — skip (prose is streamed as text)

Rules:
- Never suggest decision_card, metric_grid, or actions unless has_decision=true.
- Never suggest bar_chart, funnel_chart, or table unless has_events=true.
- User asking for graph/chart/breakdown/table/visualize → suggest relevant DATA viz types only.
- After full analysis with decision → suggest metric_grid, decision_card, actions only (no charts/tables unless the user asked for viz).
- Prefer 1–3 widgets, not the full stack every time."""

_ALL_EVENTS_CHART = re.compile(
    r"\b(all\s+(of\s+)?them|all events|each event|every event|single bar|one bar chart)\b",
    re.I,
)
_VIZ_KEYWORDS = re.compile(
    r"\b(graph|chart|visuali[sz]e|breakdown|table|funnel|plot|metrics?\s+chart|bar chart)\b",
    re.I,
)
_ANALYSIS_KEYWORDS = re.compile(
    r"\b(analy[sz]e|compare|recommend|verdict|scale|rollback|decision)\b",
    re.I,
)
_OFF_TOPIC = re.compile(
    r"\b(capabilit(y|ies)|who are you|what can you do|hello|hi there)\b",
    re.I,
)


def _heuristic_plan(
    message: str,
    *,
    has_decision: bool,
    has_events: bool,
) -> WidgetPlan:
    text = message.strip()
    if not text or _OFF_TOPIC.search(text):
        return WidgetPlan(should_render=False, rationale="off-topic or greeting")

    if has_decision and _ANALYSIS_KEYWORDS.search(text):
        return WidgetPlan(
            should_render=True,
            block_types=["metric_grid", "decision_card", "actions"],
            rationale="heuristic post-analysis",
        )

    if has_events and _VIZ_KEYWORDS.search(text):
        types: list[BlockType] = []
        if "funnel" in text.lower():
            types.append("funnel_chart")
        if re.search(r"\b(table|breakdown)\b", text, re.I) and not _ALL_EVENTS_CHART.search(text):
            types.append("table")
        if re.search(r"\b(graph|chart|visuali[sz]e|plot|bar)\b", text, re.I):
            types.append("bar_chart")
        if not types:
            types = ["bar_chart"] if _ALL_EVENTS_CHART.search(text) else ["table"]
        return WidgetPlan(should_render=True, block_types=types, rationale="heuristic data viz")

    return WidgetPlan(should_render=False, rationale="heuristic text-only")


async def hint_widgets(
    message: str,
    *,
    has_decision: bool,
    has_events: bool,
    tool_calls_used: int = 0,
) -> WidgetPlan:
    """Return widget plan for this chat turn. Falls back to heuristic if LLM fails."""

    if not has_decision and not _VIZ_KEYWORDS.search(message):
        return WidgetPlan(should_render=False, rationale="no decision and no explicit viz request")

    if tool_calls_used == 0 and not has_decision:
        return _heuristic_plan(message, has_decision=has_decision, has_events=has_events)

    user_prompt = (
        f"User message: {message}\n"
        f"has_decision: {has_decision}\n"
        f"has_events: {has_events}\n"
        f"tool_calls_used: {tool_calls_used}\n"
        "Return should_render, block_types, rationale."
    )

    llm = _build_llm().with_structured_output(WidgetPlan)
    try:
        result = await asyncio.wait_for(
            llm.ainvoke(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ]
            ),
            timeout=HINTER_TIMEOUT_SECONDS,
        )
        if isinstance(result, WidgetPlan):
            plan = result
        else:
            plan = WidgetPlan.model_validate(result)
    except Exception as err:  # noqa: BLE001
        logger.warning("SDUI hinter LLM failed, using heuristic: %s", type(err).__name__)
        plan = _heuristic_plan(message, has_decision=has_decision, has_events=has_events)

    if plan.should_render:
        logger.info(
            "SDUI hinter plan types=%s rationale=%s",
            plan.block_types,
            plan.rationale[:80],
        )
    return plan
