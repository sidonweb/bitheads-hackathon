import { useMemo } from 'react';
import { buildExecutiveSummary } from '../lib/executiveSummary.js';

export default function ExecutiveSummary({ decision, bullets: bulletsOverride }) {
  const bullets = useMemo(() => {
    if (bulletsOverride?.length) return bulletsOverride;
    return buildExecutiveSummary(decision);
  }, [decision, bulletsOverride]);
  if (!bullets.length) return null;

  return (
    <section className="executive-summary" aria-label="Executive summary">
      <h3 className="executive-summary-title">Executive Summary</h3>
      <ul className="executive-summary-list">
        {bullets.map((text, i) => (
          <li key={i}>{text}</li>
        ))}
      </ul>
    </section>
  );
}
