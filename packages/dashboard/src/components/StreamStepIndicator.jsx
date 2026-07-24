export default function StreamStepIndicator({ label }) {
  if (!label) return null;

  return (
    <div className="stream-status" aria-live="polite" aria-label="Analysis progress">
      <span className="stream-status-dot" aria-hidden="true" />
      <span className="stream-status-label">{label}</span>
      <span className="stream-status-cursor" aria-hidden="true" />
    </div>
  );
}
