import { computeTax, computeTotal } from '../lib/pricing.js';

export default function OrderSummary({
  cart,
  total,
  actionLabel,
  onAction,
  children,
}) {
  const tax = computeTax(total);
  const orderTotal = computeTotal(total);

  return (
    <aside className="order-summary">
      <h3>Order Summary</h3>
      <div className="summary-lines">
        <div className="summary-row">
          <span>Subtotal ({cart.length} {cart.length === 1 ? 'item' : 'items'})</span>
          <span>${total.toFixed(2)}</span>
        </div>
        <div className="summary-row">
          <span>Shipping</span>
          <span className="summary-free">Free</span>
        </div>
        <div className="summary-row">
          <span>Tax</span>
          <span>${tax.toFixed(2)}</span>
        </div>
        <div className="summary-row summary-total">
          <span>Total</span>
          <span>${orderTotal.toFixed(2)}</span>
        </div>
      </div>
      {children}
      {actionLabel && onAction && (
        <button type="button" className="btn btn-primary btn-block" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </aside>
  );
}
