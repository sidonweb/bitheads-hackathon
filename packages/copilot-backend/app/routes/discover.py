from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from ..db import engine
from ..journey.discover import discover_journey
from ..journey.recipe import get_recipe_or_default, load_recipe

router = APIRouter()


@router.post("/experiments/{experiment_id}/discover-journey")
async def discover(experiment_id: str):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
    if exp is None:
        raise HTTPException(status_code=404, detail="not found")

    try:
        result = await discover_journey(dict(exp))
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err

    print(f"[discover] {experiment_id} -> {result['recipe'].get('funnelEvents')}")
    return result


@router.get("/experiments/{experiment_id}/journey-recipe")
def get_journey_recipe(experiment_id: str):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT id FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
    if exp is None:
        raise HTTPException(status_code=404, detail="not found")

    stored = load_recipe(experiment_id)
    recipe = get_recipe_or_default(experiment_id)
    return {"recipe": recipe, "discovered": stored is not None}
