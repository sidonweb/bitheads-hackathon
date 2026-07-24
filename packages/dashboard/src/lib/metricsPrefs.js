const AUTO_REFRESH_KEY = 'copilot_metrics_auto_refresh_v1';

export function readAutoRefresh() {
  try {
    const raw = localStorage.getItem(AUTO_REFRESH_KEY);
    if (raw === 'false') return false;
    if (raw === 'true') return true;
  } catch {
    // ignore
  }
  return true;
}

export function saveAutoRefresh(enabled) {
  try {
    localStorage.setItem(AUTO_REFRESH_KEY, enabled ? 'true' : 'false');
  } catch {
    // ignore
  }
}
