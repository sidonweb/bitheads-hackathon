export const DEFAULT_VARIATION = 'checkout-cta';

export const VARIATION_IDS = [
  'checkout-cta',
  'plp-social-proof',
  'pdp-sticky-cta',
  'cart-shipping-nudge',
];

export const ECOM_WEB_BASE = import.meta.env.VITE_ECOM_WEB_URL || 'http://localhost:5173';

export const VARIATION_CATALOG = {
  'checkout-cta': {
    id: 'checkout-cta',
    experimentId: 'exp_checkout_cta',
    label: 'Checkout CTA Redesign',
    name: 'Checkout CTA Redesign',
    hypothesis: "Variant B's redesigned checkout CTA increases checkout conversion vs Variant A.",
    variantAName: 'Original CTA',
    variantBName: 'Redesigned CTA',
    defaultConvA: 15.8,
    defaultConvB: 18.0,
  },
  'plp-social-proof': {
    id: 'plp-social-proof',
    experimentId: 'exp_plp_social_proof',
    label: 'PLP Social Proof',
    name: 'PLP Social Proof',
    hypothesis: 'Showing star ratings and review counts on product cards increases add-to-cart rate.',
    variantAName: 'No Ratings',
    variantBName: 'Star Ratings',
    defaultConvA: 12.0,
    defaultConvB: 14.5,
  },
  'pdp-sticky-cta': {
    id: 'pdp-sticky-cta',
    experimentId: 'exp_pdp_sticky_cta',
    label: 'PDP Sticky CTA',
    name: 'PDP Sticky CTA',
    hypothesis: 'A sticky bottom add-to-cart bar on product detail increases add-to-cart rate.',
    variantAName: 'Inline CTA',
    variantBName: 'Sticky CTA Bar',
    defaultConvA: 14.0,
    defaultConvB: 16.5,
  },
  'cart-shipping-nudge': {
    id: 'cart-shipping-nudge',
    experimentId: 'exp_cart_shipping_nudge',
    label: 'Cart Free-Shipping Nudge',
    name: 'Cart Free-Shipping Nudge',
    hypothesis: 'A free-shipping progress bar nudges more users from cart into checkout.',
    variantAName: 'Standard Cart',
    variantBName: 'Shipping Nudge',
    defaultConvA: 22.0,
    defaultConvB: 19.5,
  },
};

export function experimentIdForVariation(variationId) {
  return VARIATION_CATALOG[variationId]?.experimentId || 'exp_checkout_cta';
}

const STORAGE_KEY = 'copilot_active_variation';

export function buildVariationUrls(variationId, base = ECOM_WEB_BASE) {
  const root = base.replace(/\/$/, '');
  const q = `variation=${variationId}`;
  if (variationId === 'checkout-cta') {
    return {
      variantAUrl: `${root}/?${q}&variant=A&screen=checkout`,
      variantBUrl: `${root}/?${q}&variant=B&screen=checkout`,
    };
  }
  if (variationId === 'plp-social-proof') {
    return {
      variantAUrl: `${root}/?${q}&variant=A`,
      variantBUrl: `${root}/?${q}&variant=B`,
    };
  }
  if (variationId === 'pdp-sticky-cta') {
    return {
      variantAUrl: `${root}/?${q}&variant=A&screen=detail&product=p1`,
      variantBUrl: `${root}/?${q}&variant=B&screen=detail&product=p1`,
    };
  }
  if (variationId === 'cart-shipping-nudge') {
    return {
      variantAUrl: `${root}/?${q}&variant=A&screen=cart&product=p8`,
      variantBUrl: `${root}/?${q}&variant=B&screen=cart&product=p8`,
    };
  }
  return buildVariationUrls(DEFAULT_VARIATION, base);
}

export function readActiveVariation(defaultId = DEFAULT_VARIATION) {
  const stored = localStorage.getItem(STORAGE_KEY);
  return VARIATION_IDS.includes(stored) ? stored : defaultId;
}

export function saveActiveVariation(id) {
  if (VARIATION_IDS.includes(id)) {
    localStorage.setItem(STORAGE_KEY, id);
  }
}
