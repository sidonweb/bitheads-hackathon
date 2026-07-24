-- Shared schema for the split-backend architecture.
-- ecom-backend owns writes to universal_events; copilot-backend owns experiments
-- CRUD; the agent reads everything through a SELECT-only role.

-- Roles ---------------------------------------------------------------------
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ecom_role') THEN
    CREATE ROLE ecom_role LOGIN PASSWORD 'ecom_pw';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'copilot_role') THEN
    CREATE ROLE copilot_role LOGIN PASSWORD 'copilot_pw';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'agent_readonly') THEN
    CREATE ROLE agent_readonly LOGIN PASSWORD 'agent_pw';
  END IF;
END
$$;

-- Tables --------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS experiments (
  id             TEXT PRIMARY KEY,
  name           TEXT NOT NULL,
  hypothesis     TEXT NOT NULL DEFAULT '',
  primary_metric TEXT,                       -- nullable: inferred by the agent at analyze time
  variant_a_name TEXT NOT NULL DEFAULT 'Control',
  variant_b_name TEXT NOT NULL DEFAULT 'Treatment',
  variant_a_url  TEXT,                        -- page the agent inspects for variant A
  variant_b_url  TEXT,                        -- page the agent inspects for variant B
  traffic_split  INT  NOT NULL DEFAULT 50 CHECK (traffic_split BETWEEN 0 AND 100),
  status         TEXT NOT NULL DEFAULT 'running',
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS universal_events (
  id            BIGSERIAL PRIMARY KEY,
  experiment_id TEXT        NOT NULL,
  user_id       TEXT        NOT NULL,
  variant_id    TEXT        NOT NULL,
  event_name    TEXT        NOT NULL,
  metric_value  NUMERIC     NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_lookup
  ON universal_events (experiment_id, variant_id, event_name);

-- Backfill URL columns if the tables predate this migration.
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS variant_a_url TEXT;
ALTER TABLE experiments ADD COLUMN IF NOT EXISTS variant_b_url TEXT;
ALTER TABLE experiments ALTER COLUMN primary_metric DROP NOT NULL;

-- Grants --------------------------------------------------------------------
-- ecom_role: writes events, reads experiments (for the flag endpoint).
GRANT SELECT, INSERT ON universal_events TO ecom_role;
GRANT USAGE, SELECT ON SEQUENCE universal_events_id_seq TO ecom_role;
GRANT SELECT ON experiments TO ecom_role;

-- copilot_role: owns experiment CRUD, and reads events to show dashboard metrics
-- (read-only on events — it never writes telemetry).
GRANT SELECT, INSERT, UPDATE ON experiments TO copilot_role;
GRANT SELECT ON universal_events TO copilot_role;

-- agent_readonly: SELECT only on both tables — the guardrail at the DB layer.
GRANT SELECT ON universal_events TO agent_readonly;
GRANT SELECT ON experiments TO agent_readonly;
ALTER ROLE agent_readonly SET statement_timeout = '5s';
