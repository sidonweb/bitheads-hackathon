import OrderSummary from '../components/OrderSummary.jsx';
import CheckoutSteps from '../components/CheckoutSteps.jsx';
import MockPaymentForm from '../components/MockPaymentForm.jsx';
import VariantBadge from '../components/VariantBadge.jsx';

// Variant B (treatment): prominent CTA, urgency copy, trust cue.
export default function CheckoutB({ cart, total, variant, onComplete }) {
  return (
    <div className="checkout-page-wrap">
      <div className="page-top-row">
        <CheckoutSteps active="checkout" />
        <VariantBadge variant={variant} />
      </div>
      <div className="checkout-page">
        <div className="checkout-main">
          <div className="checkout-panel checkout-b">
            <h2>You&apos;re almost there!</h2>
            <p className="urgent">
              Complete your order in the next 10 minutes to lock in this price.
            </p>
            <MockPaymentForm />
            <button type="button" className="btn btn-hero" onClick={onComplete}>
              Buy Now — Fast &amp; Secure Checkout
            </button>
            <p className="trust">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
              </svg>
              Secure payment · Free returns
            </p>
          </div>
        </div>
        <OrderSummary cart={cart} total={total} />
      </div>
    </div>
  );
}
