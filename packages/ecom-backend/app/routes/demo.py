from fastapi import APIRouter, HTTPException, Query

from ..config import DEMO_MODE, ECOM_WEB_URL
from ..db import admin_engine
from ..demo.scenarios import DEFAULT_VARIATION, SCENARIO_IDS, experiment_id_for_variation
from ..demo.seed_lib import reset_and_seed
from ..demo.simulate import simulate_traffic

router = APIRouter()


def _require_demo_mode():
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="demo mode disabled")


@router.post("/demo/reset")
def demo_reset(
    scenario: str = Query("scale"),
    variation: str = Query(DEFAULT_VARIATION),
):
    _require_demo_mode()
    if scenario not in SCENARIO_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"unknown scenario; choose from {SCENARIO_IDS}",
        )
    try:
        with admin_engine.begin() as conn:
            result = reset_and_seed(conn, scenario, ECOM_WEB_URL, variation_id=variation)
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err
    return result


@router.post("/demo/simulate")
def demo_simulate(
    users: int = Query(500, ge=1, le=10_000),
    convA: float = Query(0.158, ge=0.0, le=1.0),
    convB: float = Query(0.18, ge=0.0, le=1.0),
    experimentId: str | None = Query(None),
    variation: str = Query(DEFAULT_VARIATION),
):
    _require_demo_mode()
    resolved_id = experimentId or experiment_id_for_variation(variation)
    try:
        with admin_engine.begin() as conn:
            result = simulate_traffic(
                conn,
                experiment_id=resolved_id,
                users=users,
                conv_a=convA,
                conv_b=convB,
                variation_id=variation,
            )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err)) from err
    return result
