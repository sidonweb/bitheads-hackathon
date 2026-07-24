"""Metric and configuration recommendations for FR-02."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import text

from ..agent.graph import _build_llm
from ..schemas_lifecycle import (
    AudienceRecommendation,
    FeatureFlagRecommendation,
    LifecycleError,
    PrimaryMetricRecommendation,
    RecommendConfigLLMOut,
    RecommendConfigOut,
)

logger = logging.getLogger(__name__)

RECOMMEND_TIMEOUT_SECONDS = 30

_CONVERSION_PRIORITY = [
    "checkout_completed",
    "checkout_started",
    "add_to_cart",
    "page_view",
]

_SYSTEM_PROMPT = """You recommend A/B experiment configuration for a PM.
Pick the primary metric event name ONLY from the allowed list provided.
Do NOT recommend events outside the allowlist.
page_view counts exposures, not conversions.
Return descriptive feature-flag narrative text only — no SDK keys."""


def heuristic_primary_metric(events: list[str]) -> str:
    for event in _CONVERSION_PRIORITY:
        if event in events:
            return event
    return events[0] if events else "page_view"


def _discover_events(conn, experiment_id: str) -> list[str]:
    rows = conn.execute(
        text(
            """
            SELECT DISTINCT event_name
              FROM universal_events
             WHERE experiment_id = :id
             ORDER BY event_name
            """
        ),
        {"id": experiment_id},
    ).scalars().all()
    return list(rows)


def _build_user_prompt(
    *,
    hypothesis: str,
    variant_a_url: str | None,
    variant_b_url: str | None,
    available_events: list[str],
    traffic_split: int,
) -> str:
    return (
        f"ALLOWED primary metric event names (pick exactly one): {available_events}\n"
        f"Hypothesis: {hypothesis or '(none)'}\n"
        f"Variant A URL: {variant_a_url or '(none)'}\n"
        f"Variant B URL: {variant_b_url or '(none)'}\n"
        f"Current traffic split: {traffic_split}\n\n"
        "Return JSON with primaryMetric, featureFlag, and audience.\n"
        "page_view counts exposures, not conversions."
    )


def _empty_events_response(available_events: list[str]) -> RecommendConfigOut:
    metric_name = heuristic_primary_metric(available_events)
    return RecommendConfigOut(
        primaryMetric=PrimaryMetricRecommendation(
            eventName=metric_name,
            rationale=(
                "No telemetry collected yet. "
                f"Defaulting to {metric_name} once events arrive."
            ),
            alternatives=[],
        ),
        featureFlag=FeatureFlagRecommendation(
            summary="Configure a 50/50 split between control (A) and treatment (B) once URLs are live.",
            suggestedTrafficSplit=50,
        ),
        audience=AudienceRecommendation(
            suggestion="All users",
        ),
        availableEvents=available_events,
        warning="No events collected yet. Run traffic simulation or wait for live data.",
    )


def _apply_allowlist_guard(
    primary: PrimaryMetricRecommendation,
    available_events: list[str],
) -> PrimaryMetricRecommendation:
    if primary.eventName not in available_events:
        fallback = heuristic_primary_metric(available_events)
        logger.warning(
            "LLM metric pick %r not in allowlist; using %r",
            primary.eventName,
            fallback,
        )
        rationale = primary.rationale + " (Adjusted: LLM pick was not in available events.)"
        primary = PrimaryMetricRecommendation(
            eventName=fallback,
            rationale=rationale,
            alternatives=primary.alternatives,
        )

    filtered_alts = [e for e in primary.alternatives if e in available_events and e != primary.eventName]
    return PrimaryMetricRecommendation(
        eventName=primary.eventName,
        rationale=primary.rationale,
        alternatives=filtered_alts,
    )


async def recommend_config(
    *,
    experiment_id: str,
    hypothesis: str,
    variant_a_url: str | None,
    variant_b_url: str | None,
    experiment: dict[str, Any],
    conn,
) -> RecommendConfigOut:
    """Recommend primary metric, feature-flag narrative, and audience without DB writes."""
    started = time.monotonic()

    try:
        available_events = _discover_events(conn, experiment_id)
    except Exception as err:  # noqa: BLE001
        logger.error("Event discovery failed experiment_id=%s error=%s", experiment_id, type(err).__name__)
        raise LifecycleError(
            502,
            "UPSTREAM_ERROR",
            "Cannot reach experiment data.",
            retryable=True,
        ) from err

    if not available_events:
        logger.warning("Zero events for experiment_id=%s", experiment_id)
        return _empty_events_response(available_events)

    traffic_split = experiment.get("traffic_split")
    if traffic_split is None:
        traffic_split = 50

    llm = _build_llm().with_structured_output(RecommendConfigLLMOut)
    prompt = _build_user_prompt(
        hypothesis=hypothesis,
        variant_a_url=variant_a_url,
        variant_b_url=variant_b_url,
        available_events=available_events,
        traffic_split=int(traffic_split),
    )

    try:
        llm_result = await asyncio.wait_for(
            llm.ainvoke(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            ),
            timeout=RECOMMEND_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as err:
        raise LifecycleError(
            503,
            "LLM_UNAVAILABLE",
            "Configuration recommendations are temporarily unavailable.",
            retryable=True,
        ) from err
    except Exception as err:  # noqa: BLE001
        logger.error(
            "Recommend-config LLM failure experiment_id=%s error=%s",
            experiment_id,
            type(err).__name__,
        )
        raise LifecycleError(
            503,
            "LLM_UNAVAILABLE",
            "Configuration recommendations are temporarily unavailable.",
            retryable=True,
        ) from err

    if not isinstance(llm_result, RecommendConfigLLMOut):
        llm_result = RecommendConfigLLMOut.model_validate(llm_result)

    primary = _apply_allowlist_guard(llm_result.primaryMetric, available_events)
    feature_flag = llm_result.featureFlag
    if feature_flag.suggestedTrafficSplit is None:
        feature_flag = FeatureFlagRecommendation(
            summary=feature_flag.summary,
            suggestedTrafficSplit=int(traffic_split),
        )

    latency_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "Config recommended experiment_id=%s events=%d metric=%s latency_ms=%d",
        experiment_id,
        len(available_events),
        primary.eventName,
        latency_ms,
    )

    return RecommendConfigOut(
        primaryMetric=primary,
        featureFlag=feature_flag,
        audience=llm_result.audience,
        availableEvents=available_events,
        warning=None,
    )
