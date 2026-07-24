import { API_BASE, EXPERIMENT_ID, parseApiError } from '../api.js';

export async function generateHypothesis(id, { businessGoal, context = '' }) {
  const res = await fetch(`${API_BASE}/experiments/${id}/generate-hypothesis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ businessGoal, context }),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function saveHypothesis(id, { hypothesis, name, variantAName, variantBName }) {
  const body = {};
  if (hypothesis != null) body.hypothesis = hypothesis;
  if (name != null) body.name = name;
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

export async function recommendConfig(id, { hypothesis = '', variantAUrl, variantBUrl } = {}) {
  const res = await fetch(`${API_BASE}/experiments/${id}/recommend-config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hypothesis, variantAUrl, variantBUrl }),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function savePrimaryMetric(id, primaryMetric, audienceNote = null) {
  const body = { primaryMetric };
  if (audienceNote != null) body.audienceNote = audienceNote;
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export async function getPreflight(id = EXPERIMENT_ID, { variantAUrl, variantBUrl } = {}) {
  const params = new URLSearchParams();
  if (variantAUrl) params.set('variantAUrl', variantAUrl);
  if (variantBUrl) params.set('variantBUrl', variantBUrl);
  const qs = params.toString();
  const url = `${API_BASE}/experiments/${id}/preflight${qs ? `?${qs}` : ''}`;

  const res = await fetch(url);
  if (!res.ok) throw await parseApiError(res);
  return res.json();
}

export function isPreflightReady(result) {
  return result?.ready === true;
}
