const STEPS = [
  { id: 'cart', label: 'Cart' },
  { id: 'checkout', label: 'Checkout' },
  { id: 'done', label: 'Confirmation' },
];

export default function CheckoutSteps({ active }) {
  const activeIdx = STEPS.findIndex((s) => s.id === active);

  return (
    <nav className="checkout-steps" aria-label="Checkout progress">
      {STEPS.map((step, idx) => (
        <span key={step.id} className="checkout-step-wrap">
          {idx > 0 && <span className="checkout-step-sep">→</span>}
          <span
            className={`checkout-step ${idx <= activeIdx ? 'checkout-step-active' : ''} ${
              idx === activeIdx ? 'checkout-step-current' : ''
            }`}
          >
            {step.label}
          </span>
        </span>
      ))}
    </nav>
  );
}
