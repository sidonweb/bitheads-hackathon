from fastapi import APIRouter, HTTPException, Query

from ..config import DEMO_MODE
from ..agent.graph import clear_chat_threads

router = APIRouter()


@router.post("/demo/clear-chat")
def clear_chat(experimentId: str = Query("exp_1")):
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="demo mode disabled")
    clear_chat_threads(experimentId)
    return {"ok": True, "experimentId": experimentId}
