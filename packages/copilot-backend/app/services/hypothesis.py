"""LLM-backed hypothesis generation for FR-01."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

from ..agent.graph import _build_llm
from ..schemas_lifecycle import GenerateHypothesisOut, LifecycleError

logger = logging.getLogger(__name__)

HYPOTHESIS_TIMEOUT_SECONDS = 30
HYPOTHESIS_RATE_LIMIT = 10
HYPOTHESIS_RATE_WINDOW_SECONDS = 3600


class InMemoryRateLimiter:
    """Sliding-window rate limiter keyed by arbitrary string."""

    def __init__(self) -> None:
        self._events: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        cutoff = now - window_seconds
        events = [ts for ts in self._events.get(key, []) if ts > cutoff]
        self._events[key] = events
        return len(events) < limit

    def record(self, key: str) -> None:
        self._events[key].append(time.monotonic())


hypothesis_rate_limiter = InMemoryRateLimiter()

_SYSTEM_PROMPT = """You help PMs draft A/B test hypotheses. Output structured JSON only.
Never invent metrics, sample sizes, expected lift, p-values, or event names.
Hypothesis must be one clear sentence comparing Variant B (treatment) to Variant A (control).
suggestedName must be at most 80 characters and human-readable.
Variant names are descriptive labels, not code identifiers."""


def _build_user_prompt(
    *,
    business_goal: str,
    context: str,
    experiment: dict[str, Any],
) -> str:
    name = experiment.get("name") or ""
    hypothesis = experiment.get("hypothesis") or ""
    return (
        f"Business goal: {business_goal}\n"
        f"Additional context: {context or '(none)'}\n"
        f"Current experiment name: {name or '(none)'}\n"
        f"Current hypothesis (if any): {hypothesis or '(none)'}\n\n"
        "Generate a testable hypothesis comparing Variant B (treatment) to Variant A (control)."
    )


async def generate_hypothesis(
    *,
    business_goal: str,
    context: str,
    experiment: dict[str, Any],
) -> GenerateHypothesisOut:
    """Generate a draft hypothesis without persisting to the database."""
    started = time.monotonic()
    experiment_id = experiment.get("id", "unknown")

    llm = _build_llm().with_structured_output(GenerateHypothesisOut)
    prompt = _build_user_prompt(
        business_goal=business_goal,
        context=context,
        experiment=experiment,
    )

    try:
        result = await asyncio.wait_for(
            llm.ainvoke(
                [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ]
            ),
            timeout=HYPOTHESIS_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as err:
        logger.warning(
            "Hypothesis LLM timeout experiment_id=%s goal_len=%d",
            experiment_id,
            len(business_goal),
        )
        raise LifecycleError(
            503,
            "LLM_UNAVAILABLE",
            "Hypothesis generation is temporarily unavailable. Enter your hypothesis manually.",
            retryable=True,
        ) from err
    except Exception as err:  # noqa: BLE001
        logger.error(
            "Hypothesis LLM failure experiment_id=%s error=%s",
            experiment_id,
            type(err).__name__,
        )
        raise LifecycleError(
            503,
            "LLM_UNAVAILABLE",
            "Hypothesis generation is temporarily unavailable. Enter your hypothesis manually.",
            retryable=True,
        ) from err

    if not isinstance(result, GenerateHypothesisOut):
        try:
            result = GenerateHypothesisOut.model_validate(result)
        except Exception as err:  # noqa: BLE001
            logger.error(
                "Hypothesis parse failure experiment_id=%s error=%s",
                experiment_id,
                type(err).__name__,
            )
            raise LifecycleError(
                500,
                "INTERNAL_ERROR",
                "Could not parse hypothesis response. Enter your hypothesis manually.",
            ) from err

    latency_ms = int((time.monotonic() - started) * 1000)
    logger.info(
        "Hypothesis generated experiment_id=%s goal_len=%d confidence=%s latency_ms=%d",
        experiment_id,
        len(business_goal),
        result.confidence,
        latency_ms,
    )
    return result
