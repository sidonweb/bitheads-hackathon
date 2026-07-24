from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from ..db import engine
from ..flag import assign_variant

router = APIRouter()


# GET /experiments/:id/flag?userId=... — client reads its variant assignment.
# ecom-backend owns this because it drives which variant the storefront renders.
@router.get("/experiments/{experiment_id}/flag")
def get_flag(experiment_id: str, userId: str = Query(...)):
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT traffic_split FROM experiments WHERE id = :id"),
            {"id": experiment_id},
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="experiment not found")
    variant = assign_variant(experiment_id, userId, row["traffic_split"])
    return {"experimentId": experiment_id, "variantId": variant, "trafficSplit": row["traffic_split"]}
