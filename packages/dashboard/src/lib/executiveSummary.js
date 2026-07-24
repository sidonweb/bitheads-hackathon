export function humanizeMetric(name) {
  if (!name) return 'the primary success metric';
  return name.replace(/_/g, ' ');
}

function signedPct(uplift) {
  const pct = (uplift * 100).toFixed(1);
  return `${uplift >= 0 ? '+' : ''}${pct}%`;
}

const RECOMMENDATIONS = {
  Scale: 'Recommendation: Scale — roll out Variant B to all traffic.',
  Rollback: 'Recommendation: Rollback — revert to Variant A.',
  Continue: 'Recommendation: Continue — keep the experiment running.',
  Stop: 'Recommendation: Stop — no meaningful difference detected.',
};

export function buildExecutiveSummary(decision) {
  if (!decision) return [];

  const metric = humanizeMetric(decision.inferred_metric);
  const uplift = decision.uplift ?? 0;

  const bullet1 = `Variant B drove ${signedPct(uplift)} relative uplift in ${metric}.`;

  let bullet2;
  const pValue = decision.p_value ?? 1;
  const sampleA = decision.sample_size?.A;
  const sampleB = decision.sample_size?.B;

  if (pValue < 0.05 && sampleA != null && sampleB != null) {
    bullet2 = `Result is statistically significant (p = ${pValue.toFixed(4)}) with ${sampleA} users in Variant A and ${sampleB} in Variant B.`;
  } else if (pValue < 0.05) {
    bullet2 = `Result is statistically significant (p = ${pValue.toFixed(4)}); insufficient sample data for per-variant counts.`;
  } else {
    bullet2 = `Result is not yet statistically significant (p = ${pValue.toFixed(4)}); continue collecting data before acting.`;
  }

  const bullet3 = RECOMMENDATIONS[decision.decision] || RECOMMENDATIONS.Stop;

  return [bullet1, bullet2, bullet3];
}
