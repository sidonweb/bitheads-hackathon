import ReasoningExpander from './ReasoningExpander.jsx';
import ExecutiveSummary from './ExecutiveSummary.jsx';

const BADGE = {
  Scale: { color: '#16a34a', label: 'SCALE', hint: 'Roll Variant B out to everyone.' },
  Rollback: { color: '#dc2626', label: 'ROLLBACK', hint: 'Revert to Variant A.' },
  Continue: { color: '#d97706', label: 'CONTINUE', hint: 'Keep the test running.' },
  Stop: { color: '#64748b', label: 'STOP', hint: 'No meaningful difference.' },
};

const pct = (x) => `${(x * 100).toFixed(1)}%`;

function getApplyState(decision, applyState, trafficSplit, experimentStatus) {
  const verdict = decision?.decision;
  if (verdict !== 'Scale' && verdict !== 'Rollback') {
    return { show: false, disabled: true, label: null, hint: 'No traffic change recommended.' };
  }

  const targetSplit = verdict === 'Scale' ? 100 : 0;
  const alreadyApplied = trafficSplit === targetSplit;

  if (applyState === 'applied' || alreadyApplied) {
    return {
      show: true,
      disabled: true,
      label: alreadyApplied && applyState !== 'applied' ? 'Traffic already matches recommendation' : 'Applied ✓',
      hint: verdict === 'Scale'
        ? 'Variant B is already at 100% traffic.'
        : 'Variant A is already at 100% traffic.',
      variant: verdict === 'Rollback' ? 'destructive' : 'primary',
    };
  }

  if (experimentStatus && experimentStatus !== 'running') {
    return {
      show: true,
      disabled: true,
      label: verdict === 'Scale' ? 'Apply Scale — roll out Variant B' : 'Apply Rollback — revert to Variant A',
      hint: 'Start or resume the experiment to apply traffic changes.',
      variant: verdict === 'Rollback' ? 'destructive' : 'primary',
    };
  }

  if (applyState === 'loading') {
    return {
      show: true,
      disabled: true,
      label: 'Applying…',
      hint: null,
      variant: verdict === 'Rollback' ? 'destructive' : 'primary',
    };
  }

  return {
    show: true,
    disabled: false,
    label: verdict === 'Scale' ? 'Apply Scale — roll out Variant B' : 'Apply Rollback — revert to Variant A',
    hint: null,
    variant: verdict === 'Rollback' ? 'destructive-outline' : 'primary',
  };
}

export default function Decision({
  decision,
  onApply,
  applyState = 'idle',
  applyError = '',
  trafficSplit,
  experimentStatus,
  summaryBullets,
  hideExecutiveSummary = false,
}) {
  const b = BADGE[decision.decision] || BADGE.Stop;
  const apply = getApplyState(decision, applyState, trafficSplit, experimentStatus);

  return (
    <div className="decision-card">
      {!hideExecutiveSummary && (
        <ExecutiveSummary decision={decision} bullets={summaryBullets} />
      )}

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

      {apply.show && (
        <div className="decision-apply-footer">
          {apply.disabled && apply.label === 'Applied ✓' ? (
            <button type="button" className="btn btn-secondary decision-apply-btn" disabled>
              Applied ✓
            </button>
          ) : apply.disabled ? (
            <>
              <button
                type="button"
                className={`btn decision-apply-btn ${apply.variant === 'destructive' || apply.variant === 'destructive-outline' ? 'btn-danger-outline' : 'btn-primary'}`}
                disabled
                title={apply.hint || undefined}
              >
                {apply.label}
              </button>
              {apply.hint && <p className="decision-apply-hint muted">{apply.hint}</p>}
            </>
          ) : (
            <button
              type="button"
              className={`btn decision-apply-btn ${apply.variant === 'destructive-outline' ? 'btn-danger-outline' : 'btn-primary'}`}
              onClick={onApply}
            >
              {apply.label}
            </button>
          )}
          {applyError && <p className="error decision-apply-error">⚠ {applyError}</p>}
        </div>
      )}

      {!apply.show && (decision.decision === 'Continue' || decision.decision === 'Stop') && (
        <p className="decision-apply-hint muted">No traffic change recommended.</p>
      )}
    </div>
  );
}
