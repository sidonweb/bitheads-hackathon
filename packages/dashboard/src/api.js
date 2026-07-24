const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';
export const EXPERIMENT_ID = import.meta.env.VITE_EXPERIMENT_ID || 'exp_1';

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
