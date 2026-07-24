"""Deterministic demo seed — delegates to scenario profiles in app.demo."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ECOM_WEB_URL, SEED_PROFILE  # noqa: E402
from app.db import admin_engine  # noqa: E402
from app.demo.seed_lib import reset_and_seed  # noqa: E402


def main():
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as conn:
        conn.execute(
            "DELETE FROM universal_events WHERE experiment_id = %s", (EXPERIMENT_ID,))
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
    profile = os.getenv("SEED_PROFILE", SEED_PROFILE)
    with admin_engine.begin() as conn:
        result = reset_and_seed(conn, profile, ECOM_WEB_URL)

    print(f"Seeded scenario={result['scenario']} ({result['label']})")
    print(f"  Events: {result['eventsInserted']}")
    if result["expectedVerdict"]:
        print(f"  Expected verdict: {result['expectedVerdict']}")
    for row in result["summary"]:
        exp = row["exposures"]
        conv = row["conversions"]
        rate = (conv / exp * 100) if exp else 0
        print(f"  {row['variant_id']}: {conv}/{exp} = {rate:.1f}%")


if __name__ == "__main__":
    main()
