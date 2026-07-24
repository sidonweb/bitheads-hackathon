"""Lifecycle endpoints for FR-01, FR-02, and FR-03."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..db import engine
from ..schemas_lifecycle import (
    GenerateHypothesisIn,
    GenerateHypothesisOut,
    LifecycleError,
    PreflightResult,
    RecommendConfigIn,
    RecommendConfigOut,
    api_error,
)
from ..services.config_recommendation import recommend_config
from ..services.hypothesis import (
    HYPOTHESIS_RATE_LIMIT,
    HYPOTHESIS_RATE_WINDOW_SECONDS,
    generate_hypothesis,
    hypothesis_rate_limiter,
)
from ..services.preflight import run_preflight
from ..metrics.eval_telemetry import log_event

router = APIRouter()
logger = logging.getLogger(__name__)


def _error_response(exc: LifecycleError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": exc.error})


def _load_experiment(experiment_id: str) -> dict | None:
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"),
            {"id": experiment_id},
        ).mappings().first()
    return dict(row) if row else None


@router.post(
    "/experiments/{experiment_id}/generate-hypothesis",
    response_model=GenerateHypothesisOut,
    responses={
        404: {"description": "Experiment not found"},
        422: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
        503: {"description": "LLM unavailable"},
    },
)
async def generate_hypothesis_route(
    experiment_id: str,
    body: GenerateHypothesisIn,
) -> GenerateHypothesisOut | JSONResponse:
    request_id = str(uuid.uuid4())
    logger.info("generate-hypothesis start request_id=%s experiment_id=%s", request_id, experiment_id)

    experiment = _load_experiment(experiment_id)
    if experiment is None:
        return JSONResponse(
            status_code=404,
            content={"error": api_error("NOT_FOUND", f"Experiment {experiment_id} not found.")},
        )

    business_goal = body.businessGoal.strip()
    if not business_goal:
        return JSONResponse(
            status_code=422,
            content={
                "error": api_error(
                    "VALIDATION_ERROR",
                    "Business goal is required.",
                    details={"field": "businessGoal"},
                )
            },
        )

    rate_key = f"hypothesis:{experiment_id}"
    if not hypothesis_rate_limiter.check(
        rate_key,
        HYPOTHESIS_RATE_LIMIT,
        HYPOTHESIS_RATE_WINDOW_SECONDS,
    ):
        logger.warning(
            "Hypothesis rate limit request_id=%s experiment_id=%s",
            request_id,
            experiment_id,
        )
        return JSONResponse(
            status_code=429,
            content={
                "error": api_error(
                    "AGENT_TOOL_LIMIT",
                    "Too many hypothesis generations. Try again in an hour.",
                    retryable=True,
                )
            },
        )

    try:
        result = await generate_hypothesis(
            business_goal=business_goal,
            context=body.context,
            experiment=experiment,
        )
    except LifecycleError as err:
        logger.warning(
            "generate-hypothesis failed request_id=%s code=%s",
            request_id,
            err.error["code"],
        )
        return _error_response(err)

    hypothesis_rate_limiter.record(rate_key)
    return result


def _log_config_recommended(experiment_id: str, result) -> None:
    metric = ""
    if result.primaryMetric:
        metric = result.primaryMetric.eventName or ""
    log_event(
        experiment_id,
        "config_recommended",
        {
            "recommendedMetric": metric,
            "availableEvents": result.availableEvents or [],
        },
    )


@router.post(
    "/experiments/{experiment_id}/recommend-config",
    response_model=RecommendConfigOut,
    responses={
        404: {"description": "Experiment not found"},
        422: {"description": "Validation error"},
        502: {"description": "Upstream error"},
        503: {"description": "LLM unavailable"},
    },
)
async def recommend_config_route(
    experiment_id: str,
    body: RecommendConfigIn,
) -> RecommendConfigOut | JSONResponse:
    request_id = str(uuid.uuid4())
    logger.info("recommend-config start request_id=%s experiment_id=%s", request_id, experiment_id)

    experiment = _load_experiment(experiment_id)
    if experiment is None:
        return JSONResponse(
            status_code=404,
            content={"error": api_error("NOT_FOUND", f"Experiment {experiment_id} not found.")},
        )

    variant_a_url = body.variantAUrl or experiment.get("variant_a_url")
    variant_b_url = body.variantBUrl or experiment.get("variant_b_url")
    hypothesis = body.hypothesis or experiment.get("hypothesis") or ""

    try:
        with engine.begin() as conn:
            result = await recommend_config(
                experiment_id=experiment_id,
                hypothesis=hypothesis,
                variant_a_url=variant_a_url,
                variant_b_url=variant_b_url,
                experiment=experiment,
                conn=conn,
            )
    except LifecycleError as err:
        return _error_response(err)
    except SQLAlchemyError as err:
        logger.error(
            "recommend-config db error request_id=%s error=%s",
            request_id,
            type(err).__name__,
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": api_error(
                    "UPSTREAM_ERROR",
                    "Cannot reach experiment data.",
                    retryable=True,
                )
            },
        )

    _log_config_recommended(experiment_id, result)
    return result


@router.get(
    "/experiments/{experiment_id}/preflight",
    response_model=PreflightResult,
    responses={
        404: {"description": "Experiment not found"},
        503: {"description": "Upstream error"},
    },
)
async def preflight_route(
    experiment_id: str,
    variantAUrl: str | None = Query(default=None),
    variantBUrl: str | None = Query(default=None),
) -> PreflightResult | JSONResponse:
    request_id = str(uuid.uuid4())
    logger.info("preflight start request_id=%s experiment_id=%s", request_id, experiment_id)

    experiment = _load_experiment(experiment_id)
    if experiment is None:
        return JSONResponse(
            status_code=404,
            content={"error": api_error("NOT_FOUND", f"Experiment {experiment_id} not found.")},
        )

    try:
        with engine.begin() as conn:
            result = await run_preflight(
                experiment_id=experiment_id,
                experiment=experiment,
                variant_a_url=variantAUrl,
                variant_b_url=variantBUrl,
                conn=conn,
            )
    except SQLAlchemyError as err:
        logger.error(
            "preflight db error request_id=%s error=%s",
            request_id,
            type(err).__name__,
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": api_error(
                    "UPSTREAM_ERROR",
                    "Cannot reach experiment data.",
                    retryable=True,
                )
            },
        )
    except Exception as err:  # noqa: BLE001
        logger.error(
            "preflight unexpected error request_id=%s error=%s",
            request_id,
            type(err).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": api_error(
                    "INTERNAL_ERROR",
                    "Preflight validation failed unexpectedly.",
                )
            },
        )

    return result
