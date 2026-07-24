"""Reset + re-seed a demo scenario in one command."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ECOM_WEB_URL, SEED_PROFILE  # noqa: E402
from app.db import admin_engine  # noqa: E402
from app.demo.scenarios import SCENARIO_IDS  # noqa: E402
from app.demo.seed_lib import reset_and_seed  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Reset demo DB and seed a scenario profile")
    parser.add_argument(
        "--scenario",
        default=SEED_PROFILE,
        choices=SCENARIO_IDS,
        help=f"scenario profile (default: {SEED_PROFILE})",
    )
    args = parser.parse_args()

    with admin_engine.begin() as conn:
        result = reset_and_seed(conn, args.scenario, ECOM_WEB_URL)

    print(f"Demo reset complete: scenario={result['scenario']} ({result['label']})")
    if result["expectedVerdict"]:
        print(f"  Expected verdict: {result['expectedVerdict']}")
    print(f"  Events inserted: {result['eventsInserted']}")
    for row in result["summary"]:
        exp = row["exposures"]
        conv = row["conversions"]
        rate = (conv / exp * 100) if exp else 0
        print(f"  {row['variant_id']}: {conv}/{exp} = {rate:.1f}%")


if __name__ == "__main__":
    main()
