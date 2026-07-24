#!/usr/bin/env bash
set -euo pipefail

# copilot-backend does NOT own the schema — ecom-backend runs migrations + seed.
# Wait until the experiments table exists (and is reachable via copilot_role).
echo "Waiting for schema (experiments table) to be ready..."
python - <<'PY'
import time, os, psycopg
url = os.environ["DATABASE_URL"]
for attempt in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            conn.execute("SELECT 1 FROM experiments LIMIT 1")
            print("Schema is ready.")
            break
    except Exception as e:
        print(f"  waiting ({attempt+1}/60): {e}")
        time.sleep(2)
else:
    raise SystemExit("experiments table did not appear in time")
PY

echo "Starting copilot-backend on :${PORT:-3001}..."
if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-3001}" --reload --reload-dir app
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-3001}"
