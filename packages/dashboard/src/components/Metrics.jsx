// Live per-variant funnel from the experiment summary.
const pct = (c, e) => (e > 0 ? `${((c / e) * 100).toFixed(1)}%` : '—');

export default function Metrics({ summary, metric }) {
  const byVariant = Object.fromEntries(summary.map((s) => [s.variant_id, s]));
  const rows = ['A', 'B'].map((v) => byVariant[v] || { variant_id: v, exposures: 0, conversions: 0 });

  return (
    <div className="metrics">
      <div className="field-label">Live metrics · {metric}</div>
      <table>
        <thead>
          <tr><th>Variant</th><th>Exposures</th><th>Conversions</th><th>Rate</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.variant_id}>
              <td><strong>{r.variant_id}</strong></td>
              <td>{Number(r.exposures)}</td>
              <td>{Number(r.conversions)}</td>
              <td>{pct(Number(r.conversions), Number(r.exposures))}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
