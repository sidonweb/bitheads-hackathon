import { useEffect, useRef, useState } from 'react';
import { formatRelativeTime } from '../lib/formatRelativeTime.js';

const pct = (rate) => (rate != null && Number.isFinite(rate) ? `${(rate * 100).toFixed(1)}%` : '—');

export default function SimulationMetricsPanel({
  eventMatrix,
  simMeta,
  onRefresh,
  refreshing,
  expanded,
  onToggle,
  lastRefreshedAt,
  autoRefreshEnabled,
  onAutoRefreshChange,
  metricsRefreshError,
  justRefreshed,
}) {
  const [relativeLabel, setRelativeLabel] = useState(null);
  const prefersReducedMotion = useRef(
    typeof window !== 'undefined'
    && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
  );

  useEffect(() => {
    if (!lastRefreshedAt) {
      setRelativeLabel(null);
      return undefined;
    }
    const update = () => setRelativeLabel(formatRelativeTime(lastRefreshedAt));
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, [lastRefreshedAt]);

  const matrix = eventMatrix || { eventNames: [], rows: [] };
  const events = matrix.eventNames || [];
  const rows = matrix.rows || [];
  const hasData = events.length > 0 && rows.some((r) =>
    Object.values(r.counts || {}).some((n) => n > 0));

  const pulseClass = justRefreshed && !prefersReducedMotion.current ? ' sim-metrics-pulse' : '';

  if (!expanded) {
    return (
      <aside className="sim-metrics-panel collapsed">
        <button
          type="button"
          className="sim-metrics-expand"
          onClick={onToggle}
          aria-expanded={false}
          aria-label="Show simulation metrics"
          title={relativeLabel ? `Metrics · updated ${relativeLabel}` : 'Show simulation metrics'}
        >
          <span className="sim-metrics-chevron" aria-hidden>›</span>
          <span className="sim-metrics-collapsed-label">Metrics</span>
        </button>
      </aside>
    );
  }

  return (
    <section className="sim-metrics-panel expanded">
      <div className="sim-metrics-head">
        <div className="sim-metrics-title-row">
          <button
            type="button"
            className="sim-metrics-collapse"
            onClick={onToggle}
            aria-expanded
            aria-label="Hide simulation metrics"
            title="Hide metrics"
          >
            ‹
          </button>
          <div>
            <h2>Simulation metrics</h2>
            <p className="sim-metrics-sub">
              Dynamic event breakdown per variant
              {matrix.conversionEvent ? ` · conversion: ${matrix.conversionEvent}` : ''}
            </p>
            {relativeLabel && (
              <p className={`sim-metrics-meta${pulseClass}`}>
                Last updated {relativeLabel}
                {!autoRefreshEnabled && ' · auto-refresh paused'}
              </p>
            )}
          </div>
        </div>
        <div className="sim-metrics-actions">
          <label className="auto-refresh-toggle">
            <span>Auto-refresh</span>
            <input
              type="checkbox"
              checked={autoRefreshEnabled}
              onChange={(e) => onAutoRefreshChange?.(e.target.checked)}
            />
            <span className="auto-refresh-state">{autoRefreshEnabled ? 'on' : 'off'}</span>
          </label>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={onRefresh}
            disabled={refreshing}
          >
            {refreshing ? 'Refreshing…' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {!autoRefreshEnabled && (
        <p className="sim-metrics-paused-hint muted">
          Auto-refresh paused · manual refresh still available.
        </p>
      )}

      {metricsRefreshError && (
        <div className="metrics-warning-banner" role="status">
          ⚠ {metricsRefreshError}
        </div>
      )}

      {simMeta?.usersSimulated && (
        <p className="sim-run-meta">
          Last simulation: {simMeta.usersSimulated} users · {simMeta.eventsInserted} events inserted
        </p>
      )}

      {!hasData ? (
        <div className="sim-metrics-empty">
          <p>No event data yet.</p>
          <p className="muted">Reset demo, then simulate traffic to populate metrics.</p>
        </div>
      ) : (
        <div className="sim-table-wrap">
          <table className="sim-metrics-table">
            <thead>
              <tr>
                <th>Variant</th>
                {events.map((e) => (
                  <th key={e} className={e === matrix.conversionEvent ? 'col-conversion' : ''}>
                    {e}
                  </th>
                ))}
                <th>Conv. rate</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.variant_id}>
                  <td><strong>{r.variant_id}</strong></td>
                  {events.map((e) => (
                    <td key={e}>{Number(r.counts?.[e] ?? 0)}</td>
                  ))}
                  <td>{pct(r.conversionRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
