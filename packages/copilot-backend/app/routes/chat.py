from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from ..agent.graph import chat_turn
from ..agent.guardrails import AgentError, http_status_for, user_message_for
from ..db import engine
from ..schemas import ChatIn
from ..sdui.pipeline import assemble_chat_blocks
from ..sdui.schema import SDUI_VERSION
from ..services.chat_stream import stream_chat_sse

router = APIRouter()

_SOFT_FAIL_CODES = frozenset(
    {"AGENT_TOOL_LIMIT", "AGENT_RECURSION_LIMIT", "AGENT_NO_DECISION"}
)


async def _attach_blocks(exp: dict, payload: dict, *, message: str) -> dict:
    with engine.begin() as conn:
        blocks = await assemble_chat_blocks(
            conn,
            exp,
            message=message,
            reply=payload.get("reply", ""),
            decision=payload.get("decision"),
            warning=payload.get("warning"),
            tool_calls_used=(payload.get("meta") or {}).get("toolCallsUsed", 0),
        )
    meta = payload.get("meta") or {}
    meta["sduiVersion"] = SDUI_VERSION
    payload["blocks"] = blocks
    payload["meta"] = meta
    return payload


@router.post("/experiments/{experiment_id}/chat")
async def chat(experiment_id: str, body: ChatIn):
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

    try:
        result = await chat_turn(exp_dict, body.message, session_id=body.sessionId)
    except AgentError as err:
        if err.code in _SOFT_FAIL_CODES:
            print(
                f"WARN experiment_id={experiment_id} code={err.code} "
                f"tool_calls={err.details.get('toolCallsUsed', 0)}"
            )
            return await _attach_blocks(
                exp_dict,
                {
                    "reply": user_message_for(err.code),
                    "decision": None,
                    "warning": {
                        "code": err.code,
                        "message": err.message,
                        "retryable": err.retryable,
                    },
                    "meta": {"toolCallsUsed": err.details.get("toolCallsUsed", 0)},
                },
                message=body.message,
            )
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

    if result.get("decision"):
        decision = result["decision"]
        print(
            f"[chat] {experiment_id} -> {decision['decision']} "
            f"(metric: {decision.get('inferred_metric')})"
        )

    return await _attach_blocks(
        exp_dict,
        {
            "reply": result["reply"],
            "decision": result.get("decision"),
            "meta": {"toolCallsUsed": result.get("tool_calls_used", 0)},
        },
        message=body.message,
    )


@router.post("/experiments/{experiment_id}/chat/stream")
async def chat_stream(experiment_id: str, body: ChatIn):
    if not body.sessionId:
        raise HTTPException(
            status_code=422,
            detail={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "sessionId is required for streaming chat",
                    "retryable": False,
                }
            },
        )

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

    return StreamingResponse(
        stream_chat_sse(dict(exp), body.message, body.sessionId),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
