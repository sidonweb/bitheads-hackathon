"""Reset DB and seed a demo scenario profile."""

import random
from sqlalchemy import text

from .scenarios import (
    EXPERIMENT_ID,
    EXPOSURE,
    METRIC,
    SCENARIOS,
    SCENARIO_IDS,
    variant_urls,
)


def _build_event_rows(scenario_id: str, rng: random.Random) -> list[tuple]:
    cfg = SCENARIOS[scenario_id]
    rows = []
    for variant in ("A", "B"):
        rate = cfg["rates"][variant]
        for i in range(cfg["users_per_variant"]):
            uid = f"u_{variant}_{i}"
            rows.append((EXPERIMENT_ID, uid, variant, EXPOSURE, 0))
            if rng.random() < rate:
                rows.append((EXPERIMENT_ID, uid, variant, METRIC, 1))
    return rows


def _summary(conn, experiment_id: str = EXPERIMENT_ID) -> list[dict]:
    result = conn.execute(
        text(
            """
            SELECT variant_id,
                   COUNT(*) FILTER (WHERE event_name = :exposure) AS exposures,
                   COUNT(*) FILTER (WHERE event_name = :metric) AS conversions
              FROM universal_events
             WHERE experiment_id = :id
             GROUP BY variant_id
             ORDER BY variant_id
            """
        ),
        {"id": experiment_id, "exposure": EXPOSURE, "metric": METRIC},
    ).mappings().all()
    return [dict(r) for r in result]


def reset_and_seed(conn, scenario_id: str, ecom_web_url: str, rng_seed: int = 42) -> dict:
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario_id}. Choose from {SCENARIO_IDS}")

    cfg = SCENARIOS[scenario_id]
    va_url, vb_url = variant_urls(ecom_web_url)
    rng = random.Random(rng_seed)

    conn.execute(text("TRUNCATE universal_events RESTART IDENTITY"))
    conn.execute(text("DELETE FROM experiments"))

    conn.execute(
        text(
            """
            INSERT INTO experiments
              (id, name, hypothesis, primary_metric,
               variant_a_name, variant_b_name, variant_a_url, variant_b_url,
               traffic_split, status)
            VALUES
              (:id, :name, :hyp, NULL, :va, :vb, :vaurl, :vburl, :split, 'running')
            """
        ),
        {
            "id": EXPERIMENT_ID,
            "name": cfg["name"],
            "hyp": cfg["hypothesis"],
            "va": cfg["variant_a_name"],
            "vb": cfg["variant_b_name"],
            "vaurl": va_url,
            "vburl": vb_url,
            "split": cfg["traffic_split"],
        },
    )

    rows = _build_event_rows(scenario_id, rng)
    if rows:
        conn.execute(
            text(
                """
                INSERT INTO universal_events
                  (experiment_id, user_id, variant_id, event_name, metric_value)
                VALUES (:eid, :uid, :vid, :ename, :mval)
                """
            ),
            [
                {
                    "eid": eid,
                    "uid": uid,
                    "vid": vid,
                    "ename": ename,
                    "mval": mval,
                }
                for eid, uid, vid, ename, mval in rows
            ],
        )

    summary = _summary(conn)
    return {
        "ok": True,
        "scenario": scenario_id,
        "label": cfg["label"],
        "expectedVerdict": cfg["expected_verdict"],
        "eventsInserted": len(rows),
        "summary": summary,
        "experimentId": EXPERIMENT_ID,
    }
