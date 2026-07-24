"""Agent eval dashboard — separate from /experiments routes."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ..metrics.eval_telemetry import aggregate_dashboard, log_event
from ..schemas_evals import EvalDashboardOut, EvalEventIn

router = APIRouter(prefix="/agent/evals", tags=["agent-evals"])


@router.get("/dashboard", response_model=EvalDashboardOut)
def eval_dashboard():
    return aggregate_dashboard()


@router.post("/events", status_code=201)
def record_eval_event(body: EvalEventIn):
    allowed_client = {
        "creation_started",
        "creation_completed",
        "config_rejected",
        "recommendation_applied",
    }
    if body.eventType not in allowed_client:
        return JSONResponse(
            status_code=422,
            content={"error": {"message": f"Unsupported client event: {body.eventType}"}},
        )

    payload = dict(body.payload)
    if body.durationMs is not None:
        payload.setdefault("durationMs", body.durationMs)

    log_event(
        body.experimentId,
        body.eventType,
        payload,
        session_id=body.sessionId,
        duration_ms=body.durationMs,
    )
    return {"ok": True}
