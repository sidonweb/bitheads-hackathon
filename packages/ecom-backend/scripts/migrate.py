"""Apply .sql migrations as the admin/superuser (creates roles + grants)."""
import glob
import os
import sys
import psycopg

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.config import ADMIN_DATABASE_URL  # noqa: E402

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "migrations")


def main():
    files = sorted(glob.glob(os.path.join(HERE, "*.sql")))
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as conn:
        for path in files:
            print(f"Applying {os.path.basename(path)}...")
            with open(path, "r", encoding="utf-8") as f:
                conn.execute(f.read())
    print(f"Done. Applied {len(files)} migration(s).")


if __name__ == "__main__":
    main()
