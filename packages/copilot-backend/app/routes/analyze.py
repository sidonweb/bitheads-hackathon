from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..agent.graph import analyze_experiment

router = APIRouter()


# POST /experiments/:id/analyze — run the agent's full workflow, return the decision.
@router.post("/experiments/{experiment_id}/analyze")
async def analyze(experiment_id: str):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
    if exp is None:
        raise HTTPException(status_code=404, detail="experiment not found")

    try:
        decision = await analyze_experiment(dict(exp))
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err))

    print(f"[analyze] {experiment_id} -> {decision['decision']} "
          f"(metric: {decision.get('inferred_metric')}, sql: {decision['sql_used']})")
    return decision
