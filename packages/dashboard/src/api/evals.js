import { API_BASE, EXPERIMENT_ID, parseApiError } from '../api.js';

export async function getEvalDashboard() {
  const res = await fetch(`${API_BASE}/agent/evals/dashboard`);
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function logEvalEvent({
  eventType,
  experimentId = EXPERIMENT_ID,
  sessionId = null,
  durationMs = null,
  payload = {},
}) {
  const res = await fetch(`${API_BASE}/agent/evals/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      experimentId,
      eventType,
      sessionId,
      durationMs,
      payload,
    }),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}
