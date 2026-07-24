import Metrics from './Metrics.jsx';

export default function ExperimentDrawer({
  open,
  onClose,
  split,
  onSplitChange,
  onSplitCommit,
  summary,
  metric,
  onRefresh,
  error,
}) {
  return (
    <>
      <div className={`drawer-backdrop${open ? ' open' : ''}`} onClick={onClose} aria-hidden />
      <aside className={`experiment-drawer${open ? ' open' : ''}`} aria-hidden={!open}>
        <div className="drawer-head">
          <h2>Experiment controls</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close panel">✕</button>
        </div>

        <div className="drawer-body">
          <section className="drawer-section">
            <h3>Traffic allocation</h3>
            <p className="drawer-desc">Variant B receives {split}% of traffic.</p>
            <input
              type="range"
              min="0"
              max="100"
              value={split}
              onChange={(e) => onSplitChange(Number(e.target.value))}
              onMouseUp={(e) => onSplitCommit(Number(e.target.value))}
              onTouchEnd={(e) => onSplitCommit(Number(e.target.value))}
            />
            <div className="split-labels"><span>A: {100 - split}%</span><span>B: {split}%</span></div>
          </section>

          <section className="drawer-section">
            <Metrics summary={summary} metric={metric || 'conversions'} />
            <button type="button" className="btn btn-secondary" onClick={onRefresh}>↻ Refresh metrics</button>
            {error && <p className="error">⚠ {error}</p>}
          </section>
        </div>
      </aside>
    </>
  );
}
