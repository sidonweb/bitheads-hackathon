import { useCallback, useEffect, useState } from 'react';
import { getPreflight } from '../api/lifecycle.js';
import { formatRelativeTime } from '../lib/formatRelativeTime.js';

const HINTS = {
  C1b: 'Enter both variant URLs in the Analysis section.',
  C1: 'Verify the storefront is running and the URL includes ?variant=A',
  C2: 'Verify the storefront is running (localhost:5173) and the URL includes ?variant=B',
  C3: 'Simulate traffic or run demo seed to collect events',
  C4: 'Ensure both variants receive page views before analyzing',
  C6: 'Use the Hypothesis panel above to generate or enter a hypothesis',
  C7: 'Increase simulated users or wait for more traffic before analyzing',
};

const STATUS_ICON = {
  pass: { icon: '✓', className: 'preflight-pass' },
  warn: { icon: '⚠', className: 'preflight-warn' },
  fail: { icon: '✗', className: 'preflight-fail' },
};

export default function PreflightCard({
  experimentId,
  open,
  variantAUrl,
  variantBUrl,
  setError,
}) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastRunAt, setLastRunAt] = useState(null);
  const [, setTick] = useState(0);

  const runPreflight = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getPreflight(experimentId, {
        variantAUrl: variantAUrl.trim(),
        variantBUrl: variantBUrl.trim(),
      });
      setResult(data);
      setLastRunAt(data.evaluatedAt ? new Date(data.evaluatedAt).getTime() : Date.now());
    } catch (e) {
      if (e.code === 'UPSTREAM_ERROR') {
        setError('Cannot load preflight checks — database unavailable');
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  }, [experimentId, variantAUrl, variantBUrl, setError]);

  useEffect(() => {
    if (open) runPreflight();
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!lastRunAt) return undefined;
    const id = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(id);
  }, [lastRunAt]);

  const failedChecks = (result?.checks || []).filter((c) => c.status === 'fail');
  const passedCount = (result?.checks || []).filter((c) => c.status === 'pass').length;
  const totalCount = result?.checks?.length || 0;
  const lastRunLabel = lastRunAt ? formatRelativeTime(lastRunAt) : null;

  return (
    <section className="drawer-section preflight-card">
      <div className="preflight-head">
        <h3>Pre-flight checks</h3>
        <button
          type="button"
          className="btn btn-secondary btn-sm"
          onClick={runPreflight}
          disabled={loading}
        >
          {loading ? 'Running…' : 'Re-run checks'}
        </button>
      </div>

      {result && (
        <>
          <p className={`preflight-ready ${result.ready ? 'ready-yes' : 'ready-no'}`}>
            {result.ready
              ? '✓ Ready to analyze'
              : `✗ Not ready (${passedCount}/${totalCount} passed)`}
          </p>
          {lastRunLabel && (
            <p className="muted preflight-meta">Last run: {lastRunLabel}</p>
          )}

          <ul className="preflight-checklist">
            {(result.checks || []).map((check) => {
              const meta = STATUS_ICON[check.status] || STATUS_ICON.warn;
              return (
                <li key={check.id} className={`preflight-item ${meta.className}`}>
                  <span className="preflight-icon" aria-hidden>{meta.icon}</span>
                  <span className="preflight-id">{check.id}</span>
                  <span className="preflight-message">{check.message || check.name}</span>
                </li>
              );
            })}
          </ul>

          {failedChecks.length > 0 && (
            <div className="preflight-hints">
              <p className="field-label">Failed checks:</p>
              <ul>
                {failedChecks.map((check) => (
                  <li key={check.id}>
                    {check.id}: {HINTS[check.id] || check.message}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </section>
  );
}
