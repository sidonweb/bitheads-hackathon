"""Truncate telemetry + experiments so the demo can be re-run clean."""
import os
import sys
import psycopg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ADMIN_DATABASE_URL  # noqa: E402


def main():
    # Runs as admin: TRUNCATE/DELETE are privileged; app_role deliberately lacks them.
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as conn:
        conn.execute("TRUNCATE universal_events RESTART IDENTITY")
        conn.execute("DELETE FROM experiments")
    print("Reset complete: universal_events + experiments cleared.")


if __name__ == "__main__":
    main()
