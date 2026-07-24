"""Simulate traffic via flag assignment + event ingestion (same path as live browsers)."""

import random
from sqlalchemy import text

from ..flag import assign_variant
from .scenarios import EXPERIMENT_ID, EXPOSURE, METRIC, FUNNEL_ON_CONVERT


def _metric_value(event_name: str, conversion_event: str) -> float:
    return 1.0 if event_name == conversion_event else 0.0


def simulate_traffic(
    conn,
    *,
    experiment_id: str = EXPERIMENT_ID,
    users: int,
    conv_a: float,
    conv_b: float,
    rng_seed: int | None = None,
) -> dict:
    if users < 1 or users > 10_000:
        raise ValueError("users must be between 1 and 10000")

    row = conn.execute(
        text("SELECT traffic_split FROM experiments WHERE id = :id"),
        {"id": experiment_id},
    ).mappings().first()
    if row is None:
        raise ValueError(f"experiment not found: {experiment_id}")

    traffic_split = row["traffic_split"]
    exposure_event = EXPOSURE
    funnel_on_convert = FUNNEL_ON_CONVERT
    conversion_event = METRIC

    conn.execute(
        text("DELETE FROM universal_events WHERE experiment_id = :id"),
        {"id": experiment_id},
    )

    rng = random.Random(rng_seed) if rng_seed is not None else random.Random()

    batch: list[dict] = []
    conversions = {"A": 0, "B": 0}
    exposures = {"A": 0, "B": 0}
    events_inserted = 0

    for i in range(users):
        user_id = f"sim_{i}"
        variant = assign_variant(experiment_id, user_id, traffic_split)
        rate = conv_a if variant == "A" else conv_b
        exposures[variant] += 1

        batch.append(
            {
                "eid": experiment_id,
                "uid": user_id,
                "vid": variant,
                "ename": exposure_event,
                "mval": 0,
            }
        )
        events_inserted += 1

        if rng.random() < rate:
            conversions[variant] += 1
            for event_name in funnel_on_convert:
                batch.append(
                    {
                        "eid": experiment_id,
                        "uid": user_id,
                        "vid": variant,
                        "ename": event_name,
                        "mval": _metric_value(event_name, conversion_event),
                    }
                )
                events_inserted += 1

        if len(batch) >= 2000:
            _insert_batch(conn, batch)
            batch = []

    if batch:
        _insert_batch(conn, batch)

    recipe = {
        "exposureEvent": exposure_event,
        "conversionEvent": conversion_event,
        "funnelOnConvert": funnel_on_convert,
    }

    return {
        "ok": True,
        "usersSimulated": users,
        "eventsInserted": events_inserted,
        "exposures": exposures,
        "conversions": conversions,
        "convA": conv_a,
        "convB": conv_b,
        "trafficSplit": traffic_split,
        "recipe": recipe,
        "summary": simulate_summary(conn, experiment_id),
    }


def _insert_batch(conn, batch: list[dict]) -> None:
    conn.execute(
        text(
            """
            INSERT INTO universal_events
              (experiment_id, user_id, variant_id, event_name, metric_value)
            VALUES (:eid, :uid, :vid, :ename, :mval)
            """
        ),
        batch,
    )


def simulate_summary(
    conn, experiment_id: str = EXPERIMENT_ID
) -> list[dict]:
    result = conn.execute(
        text(
            """
            SELECT variant_id,
                   COUNT(*) FILTER (WHERE event_name = :exposure) AS exposures,
                   COUNT(*) FILTER (WHERE event_name = :conversion) AS conversions
              FROM universal_events
             WHERE experiment_id = :id
             GROUP BY variant_id
             ORDER BY variant_id
            """
        ),
        {"id": experiment_id, "exposure": EXPOSURE, "conversion": METRIC},
    ).mappings().all()
    return [dict(r) for r in result]
