const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';
const ECOM_API_BASE = import.meta.env.VITE_ECOM_API_BASE || 'http://localhost:3002';
export const EXPERIMENT_ID = import.meta.env.VITE_EXPERIMENT_ID || 'exp_1';
export { DEMO_MODE } from './lib/demoSim.js';

export async function getExperiment(id = EXPERIMENT_ID) {
  const res = await fetch(`${API_BASE}/experiments/${id}`);
  if (!res.ok) throw new Error('failed to load experiment');
  return res.json();
}

export async function setTrafficSplit(id, trafficSplit) {
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trafficSplit }),
  });
  if (!res.ok) throw new Error('failed to update split');
  return res.json();
}

export async function demoReset(scenario, id = EXPERIMENT_ID) {
  const params = new URLSearchParams({ scenario });
  const res = await fetch(`${ECOM_API_BASE}/demo/reset?${params}`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'demo reset failed');
  }
  const data = await res.json();
  await clearChat(id);
  return data;
}

export async function demoSimulate({ users, convA, convB, id = EXPERIMENT_ID }) {
  const params = new URLSearchParams({
    users: String(users),
    convA: String(convA),
    convB: String(convB),
    experimentId: id,
  });
  const res = await fetch(`${ECOM_API_BASE}/demo/simulate?${params}`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'simulate failed');
  }
  return res.json();
}

export async function clearChat(id = EXPERIMENT_ID) {
  const params = new URLSearchParams({ experimentId: id });
  const res = await fetch(`${API_BASE}/demo/clear-chat?${params}`, { method: 'POST' });
  if (res.status === 404) return null;
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'clear chat failed');
  }
  return res.json();
}

export async function analyze(id = EXPERIMENT_ID) {
  const res = await fetch(`${API_BASE}/experiments/${id}/analyze`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.error || 'analysis failed');
  }
  return res.json();
}

// One conversational turn with the copilot. sessionId isolates this test's
// history from other tests. Returns { reply, decision? }.
export async function chat(message, sessionId, id = EXPERIMENT_ID) {
  const res = await fetch(`${API_BASE}/experiments/${id}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, sessionId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.error || 'chat failed');
  }
  return res.json();
}

// A fresh, unique session id — used by "New Test" to start a clean conversation.
export function newSessionId() {
  return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}
