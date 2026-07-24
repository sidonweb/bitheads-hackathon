"""Deterministic demo seed — experiment metadata only (metrics via simulate_traffic)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ECOM_WEB_URL, SEED_PROFILE  # noqa: E402
from app.db import admin_engine  # noqa: E402
from app.demo.seed_lib import reset_and_seed  # noqa: E402


def main():
    profile = os.getenv("SEED_PROFILE", SEED_PROFILE)
    with admin_engine.begin() as conn:
        result = reset_and_seed(conn, profile, ECOM_WEB_URL)

    print(f"Seeded scenario={result['scenario']} ({result['label']})")
    print(f"  Events: {result['eventsInserted']} (use simulate_traffic to populate metrics)")


if __name__ == "__main__":
    main()
