const pct = (rate) => (rate != null && Number.isFinite(rate) ? `${(rate * 100).toFixed(1)}%` : '—');

export default function SimulationMetricsPanel({
  eventMatrix,
  simMeta,
  onRefresh,
  refreshing,
}) {
  const matrix = eventMatrix || { eventNames: [], rows: [] };
  const events = matrix.eventNames || [];
  const rows = matrix.rows || [];
  const hasData = events.length > 0 && rows.some((r) =>
    Object.values(r.counts || {}).some((n) => n > 0));

  return (
    <section className="sim-metrics-panel">
      <div className="sim-metrics-head">
        <div>
          <h2>Simulation metrics</h2>
          <p className="sim-metrics-sub">
            Dynamic event breakdown per variant
            {matrix.conversionEvent ? ` · conversion: ${matrix.conversionEvent}` : ''}
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={onRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : '↻ Refresh'}
        </button>
      </div>

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
