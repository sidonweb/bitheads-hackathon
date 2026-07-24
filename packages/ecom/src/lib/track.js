import { API_BASE, EXPERIMENT_ID } from '../config.js';
import { getUserId } from './user.js';

// Fire-and-forget telemetry. Never blocks the UI; failures are swallowed.
export function track(eventName, variantId, metricValue = 0) {
  const payload = {
    userId: getUserId(),
    experimentId: EXPERIMENT_ID,
    variantId,
    eventName,
    metricValue,
    timestamp: new Date().toISOString(),
  };
  fetch(`${API_BASE}/events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    keepalive: true,
  }).catch(() => {});
}
