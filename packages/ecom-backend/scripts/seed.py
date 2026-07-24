"""Deterministic seed: ~5000 users/variant where B clearly beats A at p<0.05,
so the demo reliably lands on "Scale".

  A (control):   15.8% conversion
  B (treatment): 18.0% conversion

primary_metric is left NULL on purpose — the agent must INFER the success metric
from the variant page diff + chat, not read it from config.

Runs as admin because it writes both experiments and events (roles are split:
ecom_role can't insert experiments, copilot_role can't insert events).
"""
import os
import random
import sys
import psycopg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ADMIN_DATABASE_URL  # noqa: E402

EXPERIMENT_ID = "exp_1"
USERS_PER_VARIANT = 5000
RATES = {"A": 0.158, "B": 0.18}
METRIC = "checkout_completed"

# Where the storefront is reachable. Inside compose the Playwright container
# reaches ecom-web by service name; override with ECOM_WEB_URL for local runs.
ECOM_WEB_URL = os.getenv("ECOM_WEB_URL", "http://ecom-web")
VARIANT_A_URL = f"{ECOM_WEB_URL}/?variant=A"
VARIANT_B_URL = f"{ECOM_WEB_URL}/?variant=B"


def build_rows():
    rng = random.Random(42)  # fixed seed -> identical dataset every run
    rows = []
    for variant in ("A", "B"):
        for i in range(USERS_PER_VARIANT):
            uid = f"u_{variant}_{i}"
            rows.append((EXPERIMENT_ID, uid, variant, "page_view", 0))
            if rng.random() < RATES[variant]:
                rows.append((EXPERIMENT_ID, uid, variant, METRIC, 1))
    return rows


def main():
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as conn:
        conn.execute("DELETE FROM universal_events WHERE experiment_id = %s", (EXPERIMENT_ID,))
        conn.execute(
            """
            INSERT INTO experiments
              (id, name, hypothesis, primary_metric,
               variant_a_name, variant_b_name, variant_a_url, variant_b_url,
               traffic_split, status)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, 'running')
            ON CONFLICT (id) DO UPDATE SET
              hypothesis = EXCLUDED.hypothesis,
              variant_a_url = EXCLUDED.variant_a_url,
              variant_b_url = EXCLUDED.variant_b_url,
              primary_metric = NULL
            """,
            (
                EXPERIMENT_ID,
                "Checkout CTA Redesign",
                "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
                "Original CTA",
                "Redesigned CTA",
                VARIANT_A_URL,
                VARIANT_B_URL,
                50,
            ),
        )

        rows = build_rows()
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO universal_events
                  (experiment_id, user_id, variant_id, event_name, metric_value)
                VALUES (%s, %s, %s, %s, %s)
                """,
                rows,
            )

        summary = conn.execute(
            """
            SELECT variant_id,
                   COUNT(*) FILTER (WHERE event_name = 'page_view') AS exposures,
                   COUNT(*) FILTER (WHERE event_name = %s)          AS conversions
              FROM universal_events WHERE experiment_id = %s
             GROUP BY variant_id ORDER BY variant_id
            """,
            (METRIC, EXPERIMENT_ID),
        ).fetchall()

    print(f"Seeded {len(rows)} events for {EXPERIMENT_ID} (primary_metric=NULL, inferred by agent):")
    print(f"  A url: {VARIANT_A_URL}")
    print(f"  B url: {VARIANT_B_URL}")
    for variant_id, exposures, conversions in summary:
        rate = (conversions / exposures * 100) if exposures else 0
        print(f"  {variant_id}: {conversions}/{exposures} = {rate:.1f}%")


if __name__ == "__main__":
    main()
