"""Reset DB and seed experiment metadata (no event rows — use simulate_traffic for metrics)."""

from sqlalchemy import text

from .scenarios import (
    DEFAULT_VARIATION,
    SCENARIOS,
    SCENARIO_IDS,
    VARIATION_PRESETS,
    experiment_id_for_variation,
    variation_urls,
)


def reset_and_seed(
    conn,
    scenario_id: str,
    ecom_web_url: str,
    *,
    variation_id: str = DEFAULT_VARIATION,
    rng_seed: int = 42,
) -> dict:
    del rng_seed  # kept for API compatibility
    if scenario_id not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario_id}. Choose from {SCENARIO_IDS}")
    if variation_id not in VARIATION_PRESETS:
        raise ValueError(f"unknown variation: {variation_id}")

    cfg = SCENARIOS[scenario_id]
    preset = VARIATION_PRESETS[variation_id]
    exp_id = experiment_id_for_variation(variation_id)
    va_url, vb_url = variation_urls(ecom_web_url, variation_id)

    conn.execute(
        text("DELETE FROM universal_events WHERE experiment_id = :id"),
        {"id": exp_id},
    )
    conn.execute(
        text("DELETE FROM experiments WHERE id = :id"),
        {"id": exp_id},
    )

    conn.execute(
        text(
            """
            INSERT INTO experiments
              (id, name, hypothesis, primary_metric,
               variant_a_name, variant_b_name, variant_a_url, variant_b_url,
               traffic_split, status)
            VALUES
              (:id, :name, :hyp, NULL, :va, :vb, :vaurl, :vburl, 50, 'running')
            """
        ),
        {
            "id": exp_id,
            "name": preset["name"],
            "hyp": preset["hypothesis"],
            "va": preset["variant_a_name"],
            "vb": preset["variant_b_name"],
            "vaurl": va_url,
            "vburl": vb_url,
        },
    )

    return {
        "ok": True,
        "scenario": scenario_id,
        "label": cfg["label"],
        "expectedVerdict": cfg["expected_verdict"],
        "eventsInserted": 0,
        "summary": [],
        "experimentId": exp_id,
        "variation": variation_id,
        "variantAUrl": va_url,
        "variantBUrl": vb_url,
    }
