-- Agent eval telemetry for the /agent/evals dashboard (copilot-backend writes).

CREATE TABLE IF NOT EXISTS agent_eval_events (
  id            BIGSERIAL PRIMARY KEY,
  experiment_id TEXT NOT NULL,
  session_id    TEXT,
  event_type    TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}',
  duration_ms   INT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_agent_eval_events_type
  ON agent_eval_events (event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_eval_events_experiment
  ON agent_eval_events (experiment_id, created_at DESC);

CREATE TABLE IF NOT EXISTS agent_eval_baselines (
  key         TEXT PRIMARY KEY,
  value       NUMERIC NOT NULL,
  unit        TEXT NOT NULL,
  description TEXT
);

INSERT INTO agent_eval_baselines (key, value, unit, description) VALUES
  ('manual_creation_minutes', 45, 'minutes', 'Manual experiment setup baseline'),
  ('manual_analysis_minutes', 120, 'minutes', 'Manual analysis baseline')
ON CONFLICT (key) DO NOTHING;

GRANT SELECT, INSERT ON agent_eval_events TO copilot_role;
GRANT USAGE, SELECT ON SEQUENCE agent_eval_events_id_seq TO copilot_role;
GRANT SELECT ON agent_eval_baselines TO copilot_role;
