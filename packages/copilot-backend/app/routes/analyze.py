import time

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from ..agent.graph import analyze_experiment
from ..agent.guardrails import AgentError, http_status_for
from ..db import engine
from ..metrics.eval_telemetry import build_analysis_eval_payload, log_event
from ..schemas_agent import AnalyzeIn, ChatMeta
from ..sdui.pipeline import assemble_analyze_blocks
from ..sdui.schema import SDUI_VERSION

router = APIRouter()


@router.post("/experiments/{experiment_id}/analyze")
async def analyze(experiment_id: str, body: AnalyzeIn):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
    if exp is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "experiment not found",
                    "retryable": False,
                }
            },
        )

    exp_dict = dict(exp)

    started = time.perf_counter()
    try:
        decision = await analyze_experiment(
            exp_dict,
            variant_a_url=body.variantAUrl,
            variant_b_url=body.variantBUrl,
        )
    except AgentError as err:
        raise HTTPException(
            status_code=http_status_for(err.code),
            detail={
                "error": {
                    "code": err.code,
                    "message": err.message,
                    "retryable": err.retryable,
                    "details": err.details,
                }
            },
        ) from err
    duration_ms = int((time.perf_counter() - started) * 1000)

    print(
        f"[analyze] {experiment_id} -> {decision['decision']} "
        f"(metric: {decision.get('inferred_metric')}, sql: {decision['sql_used']})"
    )

    eval_payload = build_analysis_eval_payload(
        decision,
        duration_ms,
        experiment_id=experiment_id,
    )
    log_event(
        experiment_id,
        "analysis_completed",
        eval_payload,
        duration_ms=duration_ms,
    )

    reply = decision.get("reasoning") or "Analysis complete."
    with engine.begin() as conn:
        blocks = await assemble_analyze_blocks(
            conn, exp_dict, reply=reply, decision=decision
        )

    return {
        "decision": decision,
        "reply": reply,
        "blocks": blocks,
        "meta": ChatMeta(sduiVersion=SDUI_VERSION).model_dump(),
    }
