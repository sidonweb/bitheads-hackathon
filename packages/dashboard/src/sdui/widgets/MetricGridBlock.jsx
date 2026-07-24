const TONE_CLASS = {
  positive: 'tone-positive',
  negative: 'tone-negative',
  neutral: 'tone-neutral',
};

export default function MetricGridBlock({ metrics = [], columns = 4 }) {
  if (!metrics.length) return null;
  return (
    <div
      className="sdui-metric-grid"
      style={{ gridTemplateColumns: `repeat(${Math.min(columns, metrics.length)}, 1fr)` }}
    >
      {metrics.map((metric) => (
        <div
          key={metric.label}
          className={`sdui-metric ${TONE_CLASS[metric.tone] || TONE_CLASS.neutral}`}
        >
          <div className="sdui-metric-label">{metric.label}</div>
          <div className="sdui-metric-value">{metric.value}</div>
        </div>
      ))}
    </div>
  );
}
