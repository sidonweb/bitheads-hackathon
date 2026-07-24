import OrderSummary from './OrderSummary.jsx';
import CheckoutSteps from './CheckoutSteps.jsx';
import VariantBadge from './VariantBadge.jsx';

const FREE_SHIPPING_THRESHOLD = 50;

export default function Cart({
  cart,
  total,
  variant,
  onRemoveItem,
  onCheckout,
  onContinueShopping,
  showShippingNudge = false,
}) {
  const remaining = Math.max(0, FREE_SHIPPING_THRESHOLD - total);
  const progress = Math.min(100, (total / FREE_SHIPPING_THRESHOLD) * 100);
  return (
    <div className="cart-page-wrap">
      <div className="page-top-row">
        <CheckoutSteps active="cart" />
        <VariantBadge variant={variant} />
      </div>

      <div className="cart-page">
        <div className="cart-main">
          <div className="page-heading-row">
            <h2>Cart</h2>
            <button type="button" className="btn btn-link" onClick={onContinueShopping}>
              Continue shopping
            </button>
          </div>

          {showShippingNudge && cart.length > 0 && remaining > 0 && (
            <div className="shipping-nudge">
              <p className="shipping-nudge-text">
                Add <strong>${remaining.toFixed(2)}</strong> more for free shipping
              </p>
              <div className="shipping-progress" aria-hidden="true">
                <div className="shipping-progress-fill" style={{ width: `${progress}%` }} />
              </div>
            </div>
          )}

          {showShippingNudge && cart.length > 0 && remaining === 0 && (
            <p className="shipping-nudge-unlocked">You unlocked free shipping!</p>
          )}

          {cart.length === 0 ? (
            <p className="muted empty-cart">Your cart is empty.</p>
          ) : (
            <ul className="cart-items">
              {cart.map((item, idx) => (
                <li key={`${item.id}-${idx}`} className="cart-item">
                  <img src={item.image} alt={item.name} className="cart-item-thumb" />
                  <div className="cart-item-info">
                    <span className="cart-item-name">{item.name}</span>
                    <span className="cart-item-category">{item.category}</span>
                  </div>
                  <span className="cart-item-price">${item.price.toFixed(2)}</span>
                  <button
                    type="button"
                    className="cart-item-remove"
                    onClick={() => onRemoveItem(idx)}
                    aria-label={`Remove ${item.name}`}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <OrderSummary
          cart={cart}
          total={total}
          actionLabel={cart.length > 0 ? 'Proceed to checkout' : undefined}
          actionClassName={showShippingNudge && cart.length > 0 ? 'btn-hero' : undefined}
          onAction={cart.length > 0 ? onCheckout : undefined}
        />
      </div>
    </div>
  );
}
