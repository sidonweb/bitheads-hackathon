export const TAX_RATE = 0.0825;

export function computeTax(subtotal) {
  return Math.round(subtotal * TAX_RATE * 100) / 100;
}

export function computeTotal(subtotal) {
  return Math.round((subtotal + computeTax(subtotal)) * 100) / 100;
}
