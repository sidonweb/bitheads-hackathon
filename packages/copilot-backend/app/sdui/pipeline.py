"""Assemble SDUI blocks for a chat/analyze response."""

from __future__ import annotations

import re
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection

from ..metrics.event_matrix import build_event_matrix
from .builders import build_blocks_for_plan, full_analysis_plan
from .hinter import hint_widgets
from .schema import WidgetPlan

_VIZ_ONLY = re.compile(
    r"\b(graph|chart|visuali[sz]e|bar chart|funnel|table|plot|show me|see all)\b",
    re.I,
)
_ANALYSIS_ONLY = re.compile(
    r"\b(analy[sz]e|compare|recommend|verdict|scale|rollback|decision|significant|p-value)\b",
    re.I,
)

def _experiment_has_events(conn: Connection, experiment_id: str) -> bool:
    count = conn.execute(
        text("SELECT COUNT(*) FROM universal_events WHERE experiment_id = :id"),
        {"id": experiment_id},
    ).scalar()
    return bool(count and count > 0)


def is_viz_only_message(message: str) -> bool:
    """True when the user only wants charts/tables, not a full analysis workflow."""
    text = message.strip()
    if not text:
        return False
    return bool(_VIZ_ONLY.search(text)) and not _ANALYSIS_ONLY.search(text)


async def assemble_chat_blocks(
    conn: Connection,
    exp: dict,
    *,
    message: str,
    reply: str,
    decision: dict | None,
    warning: dict | None,
    tool_calls_used: int,
    include_markdown: bool = False,
    plan_override: WidgetPlan | None = None,
) -> list[dict]:
    has_events = _experiment_has_events(conn, exp["id"])
    plan = plan_override or await hint_widgets(
        message,
        has_decision=decision is not None,
        has_events=has_events,
        tool_calls_used=tool_calls_used,
    )

    needs_matrix = any(t in plan.block_types for t in ("bar_chart", "funnel_chart", "table"))
    event_matrix = None
    if plan.should_render and (needs_matrix or decision):
        event_matrix = build_event_matrix(conn, exp["id"], exp.get("primary_metric"))

    return build_blocks_for_plan(
        plan,
        reply=reply,
        decision=decision,
        event_matrix=event_matrix,
        warning=warning,
        include_markdown=include_markdown,
        user_message=message,
    )


async def assemble_analyze_blocks(
    conn: Connection,
    exp: dict,
    *,
    reply: str,
    decision: dict,
) -> list[dict]:
    event_matrix = build_event_matrix(conn, exp["id"], exp.get("primary_metric"))
    return build_blocks_for_plan(
        full_analysis_plan(),
        reply=reply,
        decision=decision,
        event_matrix=event_matrix,
    )
