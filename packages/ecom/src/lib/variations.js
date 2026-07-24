export const DEFAULT_VARIATION = 'checkout-cta';

export const VARIATION_IDS = [
  'checkout-cta',
  'plp-social-proof',
  'pdp-sticky-cta',
  'cart-shipping-nudge',
];

export const VARIATIONS = {
  'checkout-cta': { id: 'checkout-cta', label: 'Checkout CTA', surface: 'checkout' },
  'plp-social-proof': { id: 'plp-social-proof', label: 'PLP Social Proof', surface: 'listing' },
  'pdp-sticky-cta': { id: 'pdp-sticky-cta', label: 'PDP Sticky CTA', surface: 'detail' },
  'cart-shipping-nudge': { id: 'cart-shipping-nudge', label: 'Cart Shipping Nudge', surface: 'cart' },
};

export function variationOverride() {
  const v = new URLSearchParams(window.location.search).get('variation');
  return VARIATION_IDS.includes(v) ? v : null;
}

export function resolveVariation() {
  return variationOverride() || DEFAULT_VARIATION;
}
