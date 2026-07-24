import ReasoningExpander from './ReasoningExpander.jsx';

const BADGE = {
  Scale: { color: '#16a34a', label: 'SCALE', hint: 'Roll Variant B out to everyone.' },
  Rollback: { color: '#dc2626', label: 'ROLLBACK', hint: 'Revert to Variant A.' },
  Continue: { color: '#d97706', label: 'CONTINUE', hint: 'Keep the test running.' },
  Stop: { color: '#64748b', label: 'STOP', hint: 'No meaningful difference.' },
};

const pct = (x) => `${(x * 100).toFixed(1)}%`;

export default function Decision({ decision }) {
  const b = BADGE[decision.decision] || BADGE.Stop;
  return (
    <div className="decision-card">
      <div className="verdict" style={{ background: b.color }}>
        <span className="verdict-label">{b.label}</span>
        <span className="verdict-conf">{pct(decision.confidence)} confidence</span>
      </div>
      <p className="verdict-hint">{b.hint}</p>

      {decision.inferred_metric && (
        <div className="inferred">
          <span className="field-label">Inferred metric</span>
          <code>{decision.inferred_metric}</code>
        </div>
      )}

      <div className="stat-row">
        <div className="stat"><div className="stat-k">p-value</div><div className="stat-v">{decision.p_value.toFixed(4)}</div></div>
        <div className="stat"><div className="stat-k">Relative uplift</div><div className="stat-v">{decision.uplift >= 0 ? '+' : ''}{pct(decision.uplift)}</div></div>
        <div className="stat"><div className="stat-k">Sample (A / B)</div><div className="stat-v">{decision.sample_size.A} / {decision.sample_size.B}</div></div>
      </div>

      <div className="reasoning">
        <div className="field-label">Copilot reasoning</div>
        <p>{decision.reasoning}</p>
      </div>

      <ReasoningExpander decision={decision} />
    </div>
  );
}
