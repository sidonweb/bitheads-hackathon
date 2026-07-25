const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3001';
const ECOM_API_BASE = import.meta.env.VITE_ECOM_API_BASE || 'http://localhost:3002';
export const EXPERIMENT_ID = import.meta.env.VITE_EXPERIMENT_ID || 'exp_checkout_cta';
export { VARIATION_IDS, VARIATION_CATALOG, buildVariationUrls, experimentIdForVariation } from './lib/variationCatalog.js';
export { API_BASE, ECOM_API_BASE };
export { DEMO_MODE } from './lib/demoSim.js';

export async function parseApiError(res) {
  const body = await res.json().catch(() => ({}));
  if (body?.error?.message) {
    const err = new Error(body.error.message);
    err.code = body.error.code;
    err.retryable = body.error.retryable ?? false;
    err.details = body.error.details ?? {};
    return err;
  }
  return new Error(body.detail || body.error || `Request failed (${res.status})`);
}

export async function getExperiment(id = EXPERIMENT_ID) {
  const res = await fetch(`${API_BASE}/experiments/${id}`);
  if (!res.ok) {
    const err = await parseApiError(res);
    if (res.status === 404) err.message = 'Experiment not found.';
    throw err;
  }
  return res.json();
}

export async function listExperiments() {
  const res = await fetch(`${API_BASE}/experiments`);
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function setTrafficSplit(id, trafficSplit) {
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ trafficSplit }),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function patchExperiment(
  { variantAUrl, variantBUrl, name, hypothesis, variantAName, variantBName } = {},
  id = EXPERIMENT_ID,
) {
  const body = {};
  if (variantAUrl != null) body.variantAUrl = variantAUrl;
  if (variantBUrl != null) body.variantBUrl = variantBUrl;
  if (name != null) body.name = name;
  if (hypothesis != null) body.hypothesis = hypothesis;
  if (variantAName != null) body.variantAName = variantAName;
  if (variantBName != null) body.variantBName = variantBName;
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function demoReset(scenario, id = EXPERIMENT_ID, variation = null) {
  const params = new URLSearchParams({ scenario });
  if (variation) params.set('variation', variation);
  const res = await fetch(`${ECOM_API_BASE}/demo/reset?${params}`, { method: 'POST' });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || 'demo reset failed');
  }
  const data = await res.json();
  await clearChat(id);
  return data;
}

export async function demoSimulate({ users, convA, convB, id = EXPERIMENT_ID, variation = null }) {
  const params = new URLSearchParams({
    users: String(users),
    convA: String(convA),
    convB: String(convB),
    experimentId: id,
  });
  if (variation) params.set('variation', variation);
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

export async function analyze({ variantAUrl, variantBUrl, id = EXPERIMENT_ID } = {}) {
  if (!variantAUrl?.trim() || !variantBUrl?.trim()) {
    throw new Error('Both variant URLs are required');
  }
  const res = await fetch(`${API_BASE}/experiments/${id}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      variantAUrl: variantAUrl.trim(),
      variantBUrl: variantBUrl.trim(),
    }),
  });
  if (!res.ok) throw await parseApiError(res);
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
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

function parseSSEBuffer(buffer) {
  const events = [];
  let remainder = buffer.replace(/\r\n/g, '\n');

  while (true) {
    const idx = remainder.indexOf('\n\n');
    if (idx === -1) break;

    const block = remainder.slice(0, idx);
    remainder = remainder.slice(idx + 2);

    let event = 'message';
    const dataLines = [];

    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) {
        event = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        dataLines.push(line.slice(5).trimStart());
      }
    }

    if (dataLines.length) {
      const raw = dataLines.join('\n');
      try {
        events.push({ event, data: JSON.parse(raw) });
      } catch {
        events.push({ event, data: raw });
      }
    }
  }

  return { events, remainder };
}

// SSE stream for a chat turn. Calls onEvent({ event, data }) per frame.
// Throws on HTTP / content-type errors before the stream body is consumed.
export async function chatStream(message, sessionId, onEvent, signal, id = EXPERIMENT_ID) {
  const res = await fetch(`${API_BASE}/experiments/${id}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({ message, sessionId }),
    signal,
  });

  if (!res.ok) {
    throw await parseApiError(res);
  }

  const contentType = res.headers.get('content-type') || '';
  if (!contentType.includes('text/event-stream')) {
    throw new Error('Stream endpoint returned an unexpected response type');
  }

  if (!res.body) {
    throw new Error('Stream response has no body');
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const { events, remainder } = parseSSEBuffer(buffer);
      buffer = remainder;

      for (const frame of events) {
        onEvent(frame);
      }
    }

    if (buffer.trim()) {
      const { events } = parseSSEBuffer(`${buffer}\n\n`);
      for (const frame of events) {
        onEvent(frame);
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// A fresh, unique session id — used by "New Test" to start a clean conversation.
export function newSessionId() {
  return `s_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}
