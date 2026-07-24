export default function MockPaymentForm() {
  return (
    <div className="mock-payment-form">
      <label className="form-field">
        <span>Email</span>
        <input type="email" value="demo@shopmock.com" readOnly />
      </label>
      <label className="form-field">
        <span>Card number</span>
        <input type="text" value="4242 4242 4242 4242" readOnly />
      </label>
      <div className="form-row">
        <label className="form-field">
          <span>Expiry</span>
          <input type="text" value="12 / 28" readOnly />
        </label>
        <label className="form-field">
          <span>CVC</span>
          <input type="text" value="123" readOnly />
        </label>
      </div>
    </div>
  );
}
