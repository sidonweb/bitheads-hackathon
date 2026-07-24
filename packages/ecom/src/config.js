// Points at ecom-backend (owns events + flag).
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:3002';
export const EXPERIMENT_ID = import.meta.env.VITE_EXPERIMENT_ID || 'exp_1';

// Optional ?variant=A|B URL override so each variant is directly viewable
// (and so the agent's Playwright browser can open a specific variant).
export function variantOverride() {
  const v = new URLSearchParams(window.location.search).get('variant');
  return v === 'A' || v === 'B' ? v : null;
}
