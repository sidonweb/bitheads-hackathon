export default function StreamStepIndicator({ steps }) {
  if (!steps?.length) return null;

  return (
    <div className="stream-steps" aria-live="polite" aria-label="Analysis progress">
      {steps.map((step) => (
        <div
          key={step.id}
          className={`stream-step stream-step-${step.status}`}
        >
          <span className="stream-step-icon" aria-hidden="true">
            {step.status === 'done' && '✓'}
            {step.status === 'error' && '✕'}
            {step.status === 'active' && <span className="stream-step-dot" />}
          </span>
          <span className="stream-step-label">{step.label}</span>
        </div>
      ))}
    </div>
  );
}
