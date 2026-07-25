// Points at ecom-backend (owns events + flag). Empty string = same-origin + Vite proxy (Docker/Playwright).
export const API_BASE =
  import.meta.env.VITE_API_BASE !== undefined
    ? import.meta.env.VITE_API_BASE
    : 'http://localhost:3002';

const VARIATION_EXPERIMENT_IDS = {
  'checkout-cta': 'exp_checkout_cta',
  'plp-social-proof': 'exp_plp_social_proof',
  'pdp-sticky-cta': 'exp_pdp_sticky_cta',
  'cart-shipping-nudge': 'exp_cart_shipping_nudge',
};

export function experimentIdForVariation(variationId) {
  return VARIATION_EXPERIMENT_IDS[variationId] || 'exp_checkout_cta';
}

// Legacy default — used when no variation context is available.
export const EXPERIMENT_ID = import.meta.env.VITE_EXPERIMENT_ID || 'exp_checkout_cta';

// Optional ?variant=A|B URL override so each variant is directly viewable
// (and so the agent's Playwright browser can open a specific variant).
export function variantOverride() {
  const v = new URLSearchParams(window.location.search).get('variant');
  return v === 'A' || v === 'B' ? v : null;
}
