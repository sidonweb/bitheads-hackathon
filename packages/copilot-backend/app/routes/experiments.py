from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from ..db import engine
from ..schemas import ExperimentIn, ExperimentPatch
from ..metrics.event_matrix import build_event_matrix
from ..metrics.eval_telemetry import log_event

router = APIRouter()


# GET /experiments — list all experiments (id + name for dashboard picker).
@router.get("/experiments")
def list_experiments():
    with engine.begin() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id, name, hypothesis, variant_a_name, variant_b_name,
                       variant_a_url, variant_b_url, traffic_split, status
                  FROM experiments
                 ORDER BY id
                """
            )
        ).mappings().all()
    return {"experiments": [dict(r) for r in rows]}


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

        event_matrix = build_event_matrix(conn, experiment_id, exp["primary_metric"])

    return {
        "experiment": dict(exp),
        "summary": [dict(r) for r in summary],
        "eventMatrix": event_matrix,
    }


# DELETE /experiments/:id — remove experiment and its events.
@router.delete("/experiments/{experiment_id}")
def delete_experiment(experiment_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM universal_events WHERE experiment_id = :id"),
            {"id": experiment_id},
        )
        result = conn.execute(
            text("DELETE FROM experiments WHERE id = :id RETURNING id"),
            {"id": experiment_id},
        ).first()
    if result is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"ok": True, "id": experiment_id}


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
    if patch.name is not None:
        sets.append("name = :name")
        params["name"] = patch.name
    if patch.hypothesis is not None:
        sets.append("hypothesis = :hyp")
        params["hyp"] = patch.hypothesis
    if patch.variantAName is not None:
        sets.append("variant_a_name = :van")
        params["van"] = patch.variantAName
    if patch.variantBName is not None:
        sets.append("variant_b_name = :vbn")
        params["vbn"] = patch.variantBName
    if patch.primaryMetric is not None:
        sets.append("primary_metric = :metric")
        params["metric"] = patch.primaryMetric
    if not sets:
        raise HTTPException(status_code=400, detail="nothing to update")

    with engine.begin() as conn:
        row = conn.execute(
            text(f"UPDATE experiments SET {', '.join(sets)} WHERE id = :id RETURNING *"),
            params,
        ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="not found")

    if patch.primaryMetric is not None:
        log_event(
            experiment_id,
            "config_accepted",
            {"primaryMetric": patch.primaryMetric},
        )

    if patch.trafficSplit is not None and patch.trafficSplit in (0, 100):
        log_event(
            experiment_id,
            "recommendation_applied",
            {
                "trafficSplit": patch.trafficSplit,
                "decision": "Scale" if patch.trafficSplit == 100 else "Rollback",
            },
        )

    return {"experiment": dict(row)}
