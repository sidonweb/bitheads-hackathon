from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..schemas import ChatIn
from ..agent.graph import chat_turn
from ..journey.discover import discover_journey

router = APIRouter()


def _is_discover_request(message: str) -> bool:
    m = message.lower()
    return "discover" in m and ("funnel" in m or "journey" in m)


# POST /experiments/:id/chat — one conversational turn with the copilot.
# History persists per experiment (LangGraph checkpointer keyed by experiment id),
# so the PM can discuss the A/B differences, then ask for a recommendation.
# When the agent completes an analysis, `decision` is populated alongside the reply.
@router.post("/experiments/{experiment_id}/chat")
async def chat(experiment_id: str, body: ChatIn):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
    if exp is None:
        raise HTTPException(status_code=404, detail="experiment not found")

    try:
        if _is_discover_request(body.message):
            result = await discover_journey(dict(exp))
        else:
            result = await chat_turn(dict(exp), body.message)
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err

    if result.get("decision"):
        d = result["decision"]
        print(f"[chat] {experiment_id} -> {d['decision']} (metric: {d.get('inferred_metric')})")
    if result.get("recipe"):
        print(f"[chat] {experiment_id} journey discovered: {result['recipe'].get('funnelEvents')}")
    return result
