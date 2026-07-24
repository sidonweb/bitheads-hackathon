#!/usr/bin/env bash
set -euo pipefail

echo "Waiting for Postgres..."
python - <<'PY'
import time, psycopg, os
url = os.environ.get("ADMIN_DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/copilot")
for attempt in range(30):
    try:
        with psycopg.connect(url, connect_timeout=3):
            print("Postgres is ready.")
            break
    except Exception as e:
        print(f"  not ready ({attempt+1}/30): {e}")
        time.sleep(2)
else:
    raise SystemExit("Postgres did not become ready in time")
PY

echo "Running migrations..."
python scripts/migrate.py

if [ "${SEED_ON_START:-true}" = "true" ]; then
  echo "Seeding demo data (idempotent-ish; safe on a fresh volume)..."
  python scripts/seed.py || echo "seed skipped/failed (continuing)"
fi

echo "Starting ecom-backend on :${PORT:-3002}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-3002}"
