"""Deterministic SDUI block assembly from WidgetPlan + trusted data sources."""

from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import ValidationError

from .schema import (
    DECISION_TYPES,
    DATA_VIZ_TYPES,
    ActionButton,
    ActionsBlock,
    AlertBlock,
    BarChartBlock,
    BlockType,
    BlockUnion,
    ChartSeries,
    DecisionCardBlock,
    FunnelChartBlock,
    FunnelStep,
    MarkdownBlock,
    MetricGridBlock,
    MetricItem,
    TableBlock,
    VariantSeries,
    WidgetPlan,
    block_to_dict,
)

logger = logging.getLogger(__name__)

_ALL_EVENTS_CHART = re.compile(
    r"\b(all\s+(of\s+)?them|all events|each event|every event|all event|"
    r"single bar|one bar chart|event counts?|click data)\b",
    re.I,
)

ANALYSIS_BLOCK_ORDER: list[BlockType] = [
    "alert",
    "markdown",
    "metric_grid",
    "bar_chart",
    "funnel_chart",
    "table",
    "decision_card",
    "actions",
]


def _humanize_metric(name: str | None) -> str:
    if not name:
        return "the primary success metric"
    return name.replace("_", " ")


def _signed_pct(uplift: float) -> str:
    pct = uplift * 100
    sign = "+" if uplift >= 0 else ""
    return f"{sign}{pct:.1f}%"


def _executive_bullets(decision: dict) -> list[str]:
    metric = _humanize_metric(decision.get("inferred_metric"))
    uplift = float(decision.get("uplift") or 0)
    p_value = float(decision.get("p_value") or 1)
    sample = decision.get("sample_size") or {}
    a_n = sample.get("A")
    b_n = sample.get("B")

    bullet1 = f"Variant B drove {_signed_pct(uplift)} relative uplift in {metric}."
    if p_value < 0.05 and a_n is not None and b_n is not None:
        bullet2 = (
            f"Result is statistically significant (p = {p_value:.4f}) "
            f"with {a_n} users in Variant A and {b_n} in Variant B."
        )
    elif p_value < 0.05:
        bullet2 = f"Result is statistically significant (p = {p_value:.4f})."
    else:
        bullet2 = (
            f"Result is not yet statistically significant (p = {p_value:.4f}); "
            "continue collecting data before acting."
        )

    recs = {
        "Scale": "Recommendation: Scale — roll out Variant B to all traffic.",
        "Rollback": "Recommendation: Rollback — revert to Variant A.",
        "Continue": "Recommendation: Continue — keep the experiment running.",
        "Stop": "Recommendation: Stop — no meaningful difference detected.",
    }
    bullet3 = recs.get(decision.get("decision"), recs["Stop"])
    return [bullet1, bullet2, bullet3]


def _metric_tone(label: str, value: str) -> str:
    if "uplift" in label.lower() and value.startswith("+"):
        return "positive"
    if "uplift" in label.lower() and value.startswith("-"):
        return "negative"
    return "neutral"


def _metrics_from_decision(decision: dict) -> list[MetricItem]:
    sample = decision.get("sample_size") or {}
    uplift_str = _signed_pct(float(decision.get("uplift") or 0))
    return [
        MetricItem(
            label="p-value",
            value=f"{float(decision.get('p_value', 0)):.4f}",
            tone="positive" if float(decision.get("p_value", 1)) < 0.05 else "neutral",
        ),
        MetricItem(
            label="Relative uplift",
            value=uplift_str,
            tone=_metric_tone("uplift", uplift_str),
        ),
        MetricItem(
            label="Sample (A / B)",
            value=f"{sample.get('A', '—')} / {sample.get('B', '—')}",
            tone="neutral",
        ),
        MetricItem(
            label="Verdict",
            value=str(decision.get("decision", "—")),
            tone="positive" if decision.get("decision") == "Scale" else "neutral",
        ),
    ]


def _wants_grouped_events_chart(user_message: str) -> bool:
    return bool(_ALL_EVENTS_CHART.search(user_message or ""))


def _grouped_events_bar_chart(event_matrix: dict) -> BarChartBlock | None:
    events = event_matrix.get("eventNames") or []
    rows_data = event_matrix.get("rows") or []
    if not events or len(rows_data) < 2:
        return None

    grouped: list[VariantSeries] = []
    for row in rows_data:
        vid = row.get("variant_id", "?")
        counts = row.get("counts") or {}
        grouped.append(
            VariantSeries(
                name=vid,
                values=[float(counts.get(e, 0)) for e in events],
            )
        )

    return BarChartBlock(
        id="events-grouped-chart",
        title="Event counts by variant",
        y_label="Count",
        mode="grouped",
        categories=[e.replace("_", " ") for e in events],
        grouped_series=grouped,
    )


def _bar_chart_from_matrix(event_matrix: dict, *, grouped: bool = False) -> BarChartBlock | None:
    if grouped:
        return _grouped_events_bar_chart(event_matrix)
    rows = event_matrix.get("rows") or []
    conv_event = event_matrix.get("conversionEvent")
    if not conv_event or len(rows) < 2:
        return None
    series = []
    for row in rows:
        exposures = (row.get("counts") or {}).get("page_view", 0)
        conv = (row.get("counts") or {}).get(conv_event, 0)
        rate = (conv / exposures) if exposures else 0
        series.append(ChartSeries(name=row.get("variant_id", "?"), value=round(rate, 4)))
    return BarChartBlock(
        id="matrix-bar-chart",
        title=f"{conv_event.replace('_', ' ')} rate by variant",
        y_label="Conversion rate",
        mode="simple",
        series=series,
    )


def _funnel_from_matrix(event_matrix: dict, variant_id: str = "B") -> FunnelChartBlock | None:
    rows = event_matrix.get("rows") or []
    row = next((r for r in rows if r.get("variant_id") == variant_id), None)
    if not row:
        return None
    events = event_matrix.get("eventNames") or []
    counts = row.get("counts") or {}
    steps = [FunnelStep(label=e.replace("_", " "), count=counts.get(e, 0)) for e in events]
    if not any(s.count for s in steps):
        return None
    return FunnelChartBlock(
        id=f"funnel-{variant_id.lower()}",
        title=f"Variant {variant_id} funnel",
        steps=steps,
    )


def _table_from_matrix(event_matrix: dict) -> TableBlock | None:
    events = event_matrix.get("eventNames") or []
    rows_data = event_matrix.get("rows") or []
    if not events or not rows_data:
        return None
    columns = ["Variant", *events, "Conv. rate"]
    table_rows = []
    for row in rows_data:
        counts = row.get("counts") or {}
        rate = row.get("conversionRate")
        rate_str = f"{rate * 100:.1f}%" if rate is not None else "—"
        table_rows.append(
            [row.get("variant_id", "?"), *[counts.get(e, 0) for e in events], rate_str]
        )
    return TableBlock(
        id="event-matrix",
        title="Event breakdown by variant",
        columns=columns,
        rows=table_rows,
    )


def _actions_from_decision(decision: dict) -> ActionsBlock | None:
    verdict = decision.get("decision")
    if verdict == "Scale":
        return ActionsBlock(
            id="analysis-actions",
            buttons=[
                ActionButton(
                    action_id="apply_scale",
                    label="Apply Scale — roll out Variant B",
                    variant="primary",
                    disabled=False,
                )
            ],
        )
    if verdict == "Rollback":
        return ActionsBlock(
            id="analysis-actions",
            buttons=[
                ActionButton(
                    action_id="apply_rollback",
                    label="Apply Rollback — revert to Variant A",
                    variant="destructive",
                    disabled=False,
                )
            ],
        )
    return None


def _filter_plan_types(
    plan: WidgetPlan,
    *,
    decision: dict | None,
    event_matrix: dict | None,
) -> list[BlockType]:
    if not plan.should_render:
        return []

    allowed: list[BlockType] = []
    for block_type in plan.block_types:
        if block_type in DECISION_TYPES and not decision:
            continue
        if block_type in DATA_VIZ_TYPES and not event_matrix:
            continue
        if block_type not in allowed:
            allowed.append(block_type)
    return allowed


def _build_single_block(
    block_type: BlockType,
    *,
    reply: str,
    decision: dict | None,
    event_matrix: dict | None,
    warning: dict | None,
    include_markdown: bool,
    user_message: str = "",
) -> BlockUnion | None:
    if block_type == "alert" and warning:
        return AlertBlock(
            id="chat-warning",
            tone="warning",
            message=warning.get("message", "Partial analysis completed."),
        )
    if block_type == "markdown" and include_markdown and reply.strip():
        return MarkdownBlock(id="assistant-markdown", content=reply.strip())
    if block_type == "metric_grid" and decision:
        metrics = _metrics_from_decision(decision)
        return MetricGridBlock(
            id="analysis-metrics",
            columns=min(4, len(metrics)),
            metrics=metrics,
        )
    if block_type == "bar_chart" and event_matrix:
        grouped = _wants_grouped_events_chart(user_message)
        return _bar_chart_from_matrix(event_matrix, grouped=grouped)
    if block_type == "funnel_chart" and event_matrix:
        return _funnel_from_matrix(event_matrix, "B")
    if block_type == "table" and event_matrix:
        return _table_from_matrix(event_matrix)
    if block_type == "decision_card" and decision:
        return DecisionCardBlock(
            id="analysis-decision",
            decision=decision,
            bullets=_executive_bullets(decision),
        )
    if block_type == "actions" and decision:
        return _actions_from_decision(decision)
    return None


def build_blocks_for_plan(
    plan: WidgetPlan,
    *,
    reply: str = "",
    decision: dict | None = None,
    event_matrix: dict | None = None,
    warning: dict | None = None,
    include_markdown: bool = False,
    user_message: str = "",
) -> list[dict]:
    """Build validated blocks for the hinter plan. Returns JSON-ready dicts."""
    if not plan.should_render:
        return []

    types = _filter_plan_types(plan, decision=decision, event_matrix=event_matrix)
    ordered = [t for t in ANALYSIS_BLOCK_ORDER if t in types]

    blocks: list[dict] = []
    for block_type in ordered:
        try:
            block = _build_single_block(
                block_type,
                reply=reply,
                decision=decision,
                event_matrix=event_matrix,
                warning=warning,
                include_markdown=include_markdown,
                user_message=user_message,
            )
            if block is not None:
                blocks.append(block_to_dict(block))
        except ValidationError as err:
            logger.warning("SDUI block validation failed type=%s: %s", block_type, err)
    return blocks


def full_analysis_plan() -> WidgetPlan:
    return WidgetPlan(
        should_render=True,
        block_types=["metric_grid", "decision_card", "actions"],
        rationale="analysis verdict without redundant charts",
    )
