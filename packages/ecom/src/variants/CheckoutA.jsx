// Variant A (control): understated CTA, standard layout.
export default function CheckoutA({ total, onComplete }) {
  return (
    <div className="checkout">
      <h2>Checkout</h2>
      <p className="muted">Review your order and place it below.</p>
      <div className="order-total">Total: ${total.toFixed(2)}</div>
      <button className="btn btn-plain" onClick={onComplete}>
        Place Order
      </button>
    </div>
  );
}
