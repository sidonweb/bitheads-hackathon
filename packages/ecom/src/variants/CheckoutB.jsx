// Variant B (treatment): prominent CTA, urgency copy, trust cue.
export default function CheckoutB({ total, onComplete }) {
  return (
    <div className="checkout checkout-b">
      <h2>You're almost there!</h2>
      <p className="urgent">Complete your order in the next 10 minutes to lock in this price.</p>
      <div className="order-total">Total: ${total.toFixed(2)}</div>
      <button className="btn btn-hero" onClick={onComplete}>
        Buy Now — Fast &amp; Secure Checkout
      </button>
      <p className="trust">🔒 Secure payment · Free returns</p>
    </div>
  );
}
