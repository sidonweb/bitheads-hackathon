"""CLI traffic simulator — flag assignment + event replay."""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import EXPERIMENT_ID  # noqa: E402
from app.db import engine  # noqa: E402
from app.demo.simulate import simulate_traffic  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description="Simulate storefront traffic via flag + events")
    parser.add_argument("--users", type=int, default=500, help="synthetic users (1-10000)")
    parser.add_argument("--conv-a", type=float, default=0.158, help="variant A conversion rate 0-1")
    parser.add_argument("--conv-b", type=float, default=0.18, help="variant B conversion rate 0-1")
    parser.add_argument("--experiment-id", default=EXPERIMENT_ID)
    args = parser.parse_args()

    with engine.begin() as conn:
        result = simulate_traffic(
            conn,
            experiment_id=args.experiment_id,
            users=args.users,
            conv_a=args.conv_a,
            conv_b=args.conv_b,
        )

    print(f"Simulated {result['usersSimulated']} users, {result['eventsInserted']} events")
    for row in result["summary"]:
        exp = row["exposures"]
        conv = row["conversions"]
        rate = (conv / exp * 100) if exp else 0
        print(f"  {row['variant_id']}: {conv}/{exp} = {rate:.1f}%")


if __name__ == "__main__":
    main()
