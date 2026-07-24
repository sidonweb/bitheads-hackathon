import OrderSummary from '../components/OrderSummary.jsx';
import CheckoutSteps from '../components/CheckoutSteps.jsx';
import MockPaymentForm from '../components/MockPaymentForm.jsx';
import VariantBadge from '../components/VariantBadge.jsx';

// Variant A (control): understated CTA, standard layout.
export default function CheckoutA({ cart, total, variant, onComplete }) {
  return (
    <div className="checkout-page-wrap">
      <div className="page-top-row">
        <CheckoutSteps active="checkout" />
        <VariantBadge variant={variant} />
      </div>
      <div className="checkout-page">
        <div className="checkout-main">
          <div className="checkout-panel checkout-a">
            <h2>Checkout</h2>
            <p className="muted">Review your order and place it below.</p>
            <MockPaymentForm />
            <button type="button" className="btn btn-plain" onClick={onComplete}>
              Place Order
            </button>
          </div>
        </div>
        <OrderSummary cart={cart} total={total} />
      </div>
    </div>
  );
}
