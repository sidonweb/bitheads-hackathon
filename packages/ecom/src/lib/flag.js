import { API_BASE, EXPERIMENT_ID, variantOverride } from '../config.js';
import { getUserId } from './user.js';

// Resolve this session's variant. A ?variant=A|B URL param wins (so each variant
// is directly viewable); otherwise the platform assigns one by hashing userId.
export async function fetchVariant(experimentId = EXPERIMENT_ID) {
  const override = variantOverride();
  if (override) {
    return { experimentId, variantId: override, trafficSplit: null, forced: true };
  }
  const userId = getUserId();
  const res = await fetch(
    `${API_BASE}/experiments/${experimentId}/flag?userId=${encodeURIComponent(userId)}`,
  );
  if (!res.ok) throw new Error(`flag fetch failed: ${res.status}`);
  return res.json(); // { experimentId, variantId, trafficSplit }
}
