import { computeTax, computeTotal } from '../lib/pricing.js';

function groupCartItems(cart) {
  const groups = [];
  cart.forEach((item, idx) => {
    const existing = groups.find((g) => g.item.id === item.id);
    if (existing) {
      existing.qty += 1;
      existing.indices.push(idx);
    } else {
      groups.push({ item, qty: 1, indices: [idx] });
    }
  });
  return groups;
}

export default function OrderConfirmation({ cart, total, variant, onShopAgain }) {
  const tax = computeTax(total);
  const orderTotal = computeTotal(total);
  const grouped = groupCartItems(cart);

  return (
    <div className="order-confirmation-page">
      <div className="order-confirmation">
        <div className="success-icon-ring" aria-hidden="true">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <circle cx="28" cy="28" r="27" stroke="#16a34a" strokeWidth="2" />
            <path
              d="M17 28l8 8 14-16"
              stroke="#16a34a"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <h2>Order Placed!</h2>
        <p className="confirmation-message">
          Thank you for your purchase. We&apos;ve sent a confirmation email to your inbox.
        </p>
        <p className="event-pill">
          A checkout_completed event was sent for Variant {variant}
        </p>

        <div className="confirmation-recap">
          <h3>Order Summary</h3>
          {grouped.map(({ item, qty }) => (
            <div key={item.id} className="confirmation-line">
              <img src={item.image} alt={item.name} className="confirmation-thumb" />
              <div className="confirmation-line-info">
                <span className="confirmation-line-name">{item.name}</span>
                <span className="confirmation-line-qty">Qty: {qty}</span>
              </div>
              <span className="confirmation-line-price">${(item.price * qty).toFixed(2)}</span>
            </div>
          ))}
          <div className="summary-lines">
            <div className="summary-row">
              <span>Subtotal</span>
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
        </div>

        <button type="button" className="btn btn-primary btn-block" onClick={onShopAgain}>
          Shop again
        </button>
      </div>
    </div>
  );
}
