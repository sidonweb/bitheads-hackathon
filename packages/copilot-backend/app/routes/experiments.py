from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..schemas import ExperimentIn, ExperimentPatch

router = APIRouter()


# POST /experiments — create (or upsert) an experiment.
@router.post("/experiments", status_code=201)
def create_experiment(x: ExperimentIn):
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    INSERT INTO experiments
                      (id, name, hypothesis, primary_metric, variant_a_name, variant_b_name,
                       variant_a_url, variant_b_url, traffic_split)
                    VALUES (:id, :name, :hyp, :metric, :va, :vb, :vaurl, :vburl, :split)
                    ON CONFLICT (id) DO UPDATE SET
                      name = EXCLUDED.name,
                      hypothesis = EXCLUDED.hypothesis,
                      primary_metric = EXCLUDED.primary_metric,
                      variant_a_name = EXCLUDED.variant_a_name,
                      variant_b_name = EXCLUDED.variant_b_name,
                      variant_a_url = EXCLUDED.variant_a_url,
                      variant_b_url = EXCLUDED.variant_b_url,
                      traffic_split = EXCLUDED.traffic_split
                    """
                ),
                {
                    "id": x.id,
                    "name": x.name,
                    "hyp": x.hypothesis,
                    "metric": x.primaryMetric,
                    "va": x.variantAName,
                    "vb": x.variantBName,
                    "vaurl": x.variantAUrl,
                    "vburl": x.variantBUrl,
                    "split": x.trafficSplit,
                },
            )
        return {"ok": True, "id": x.id}
    except Exception as err:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(err))


# GET /experiments/:id — config + live per-variant summary.
# primary_metric may be NULL (not yet inferred); fall back to counting all
# non-exposure events as "conversions" so the dashboard still shows funnel data.
@router.get("/experiments/{experiment_id}")
def get_experiment(experiment_id: str):
    with engine.begin() as conn:
        exp = conn.execute(
            text("SELECT * FROM experiments WHERE id = :id"), {"id": experiment_id}
        ).mappings().first()
        if exp is None:
            raise HTTPException(status_code=404, detail="not found")

        metric = exp["primary_metric"]
        if metric:
            summary = conn.execute(
                text(
                    """
                    SELECT variant_id,
                           COUNT(*) FILTER (WHERE event_name = 'page_view') AS exposures,
                           COUNT(*) FILTER (WHERE event_name = :metric)     AS conversions
                      FROM universal_events
                     WHERE experiment_id = :id
                     GROUP BY variant_id
                    """
                ),
                {"id": experiment_id, "metric": metric},
            ).mappings().all()
        else:
            summary = conn.execute(
                text(
                    """
                    SELECT variant_id,
                           COUNT(*) FILTER (WHERE event_name = 'page_view')  AS exposures,
                           COUNT(*) FILTER (WHERE event_name <> 'page_view') AS conversions
                      FROM universal_events
                     WHERE experiment_id = :id
                     GROUP BY variant_id
                    """
                ),
                {"id": experiment_id},
            ).mappings().all()

    return {"experiment": dict(exp), "summary": [dict(r) for r in summary]}


# PATCH /experiments/:id — update traffic allocation / status / variant URLs.
@router.patch("/experiments/{experiment_id}")
def patch_experiment(experiment_id: str, patch: ExperimentPatch):
    sets, params = [], {"id": experiment_id}
    if patch.trafficSplit is not None:
        sets.append("traffic_split = :split")
        params["split"] = patch.trafficSplit
    if patch.status is not None:
        sets.append("status = :status")
        params["status"] = patch.status
    if patch.variantAUrl is not None:
        sets.append("variant_a_url = :vaurl")
        params["vaurl"] = patch.variantAUrl
    if patch.variantBUrl is not None:
        sets.append("variant_b_url = :vburl")
        params["vburl"] = patch.variantBUrl
    if not sets:
        raise HTTPException(status_code=400, detail="nothing to update")

    with engine.begin() as conn:
        row = conn.execute(
            text(f"UPDATE experiments SET {', '.join(sets)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"experiment": dict(row)}
