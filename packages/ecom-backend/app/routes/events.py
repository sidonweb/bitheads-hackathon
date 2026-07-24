from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..schemas import EventIn, BulkEventsIn

router = APIRouter()


# POST /events — ingest a single telemetry event. Fast, fire-and-forget.
@router.post("/events", status_code=202)
def ingest_event(e: EventIn):
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO universal_events
                      (experiment_id, user_id, variant_id, event_name, metric_value, created_at)
                    VALUES
                      (:eid, :uid, :vid, :ename, :mval, COALESCE(CAST(:ts AS timestamptz), now()))
                    """
                ),
                {
                    "eid": e.experimentId,
                    "uid": e.userId,
                    "vid": e.variantId,
                    "ename": e.eventName,
                    "mval": e.metricValue,
                    "ts": e.timestamp,
                },
            )
        return {"ok": True}
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err))


# POST /events/bulk — array insert for seeding / simulation.
@router.post("/events/bulk", status_code=202)
def ingest_bulk(payload: BulkEventsIn):
    rows = [
        {
            "eid": e.experimentId,
            "uid": e.userId,
            "vid": e.variantId,
            "ename": e.eventName,
            "mval": e.metricValue,
        }
        for e in payload.events
    ]
    if not rows:
        raise HTTPException(status_code=400, detail="no events")
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO universal_events
                      (experiment_id, user_id, variant_id, event_name, metric_value)
                    VALUES (:eid, :uid, :vid, :ename, :mval)
                    """
                ),
                rows,
            )
        return {"ok": True, "inserted": len(rows)}
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err))
