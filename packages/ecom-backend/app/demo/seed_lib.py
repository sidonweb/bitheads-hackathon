"""Reset DB and seed experiment metadata (no event rows — use simulate_traffic for metrics)."""

from sqlalchemy import text

from .scenarios import (
    EXPERIMENT_ID,
    SCENARIOS,
    SCENARIO_IDS,
    variant_urls,
)


def reset_and_seed(conn, scenario_id: str, ecom_web_url: str, rng_seed: int = 42) -> dict:
    del rng_seed  # kept for API compatibility
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario_id}. Choose from {SCENARIO_IDS}")

    cfg = SCENARIOS[scenario_id]
    va_url, vb_url = variant_urls(ecom_web_url)

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

    return {
        "ok": True,
        "scenario": scenario_id,
        "label": cfg["label"],
        "expectedVerdict": cfg["expected_verdict"],
        "eventsInserted": 0,
        "summary": [],
        "experimentId": EXPERIMENT_ID,
    }
