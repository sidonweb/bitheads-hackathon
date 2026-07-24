import { useEffect, useRef, useState } from 'react';
import { recommendConfig, savePrimaryMetric } from '../api/lifecycle.js';
import { logEvalEvent } from '../api/evals.js';

export default function ConfigRecommendPanel({
  experimentId,
  experiment,
  variantAUrl,
  variantBUrl,
  onSaved,
  setError,
}) {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('');
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    setAccepted(false);
    setRecommendation(null);
    setSelectedMetric('');
  }, [variantAUrl, variantBUrl]);

  const handleRecommend = async () => {
    if (recommendation && !accepted) {
      logEvalEvent({
        eventType: 'config_rejected',
        payload: { recommendedMetric: recommendation.primaryMetric?.eventName },
      }).catch(() => {});
    }
    setLoading(true);
    setError('');
    setAccepted(false);
    try {
      const data = await recommendConfig(experimentId, {
        hypothesis: experiment?.hypothesis || '',
        variantAUrl: variantAUrl.trim(),
        variantBUrl: variantBUrl.trim(),
      });
      setRecommendation(data);
      setSelectedMetric(data.primaryMetric?.eventName || '');
    } catch (e) {
      if (e.code === 'LLM_UNAVAILABLE') {
        setError('Recommendations unavailable — select metric manually from list.');
      } else {
        setError(e.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAccept = async () => {
    if (!selectedMetric || saving) return;
    setSaving(true);
    setError('');
    try {
      await savePrimaryMetric(experimentId, selectedMetric);
      await onSaved?.();
      setAccepted(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  const currentMetric = experiment?.primary_metric;
  const events = recommendation?.availableEvents || [];

  return (
    <section className="drawer-section config-recommend-panel">
      <h3>Measurement plan</h3>
      {currentMetric && (
        <p className="drawer-badge">Current: {currentMetric}</p>
      )}
      <p className="drawer-desc">
        Get metric recommendations using the variant URLs from the Analysis section below.
      </p>

      <button
        type="button"
        className="btn btn-secondary drawer-action"
        onClick={handleRecommend}
        disabled={loading || !variantAUrl.trim() || !variantBUrl.trim()}
      >
        {loading ? 'Loading recommendations…' : 'Get recommendations'}
      </button>

      {recommendation?.warning && (
        <p className="warning-inline">{recommendation.warning}</p>
      )}

      {recommendation && (
        <div className="draft-panel recommendation-results">
          <p className="field-label">Primary metric</p>
          <select
            className="drawer-select"
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            disabled={saving || accepted}
          >
            {events.map((e) => (
              <option key={e} value={e}>{e}</option>
            ))}
          </select>
          {recommendation.primaryMetric?.rationale && (
            <p className="drawer-desc">{recommendation.primaryMetric.rationale}</p>
          )}
          {recommendation.primaryMetric?.alternatives?.length > 0 && (
            <p className="muted">
              Alternatives: {recommendation.primaryMetric.alternatives.join(', ')}
            </p>
          )}

          {recommendation.featureFlag && (
            <>
              <p className="field-label">Feature flag (documentation)</p>
              <p className="drawer-desc">{recommendation.featureFlag.summary}</p>
              {recommendation.featureFlag.suggestedTrafficSplit != null && (
                <p className="muted">
                  Suggested split: {recommendation.featureFlag.suggestedTrafficSplit}%
                </p>
              )}
            </>
          )}

          {recommendation.audience && (
            <>
              <p className="field-label">Audience</p>
              <p className="drawer-desc">
                {recommendation.audience.suggestion}
                {recommendation.audience.note ? ` — ${recommendation.audience.note}` : ''}
              </p>
            </>
          )}

          <button
            type="button"
            className="btn btn-primary drawer-action"
            onClick={handleAccept}
            disabled={!selectedMetric || saving || accepted}
          >
            {accepted ? 'Metric saved ✓' : saving ? 'Saving…' : 'Accept metric'}
          </button>
        </div>
      )}
    </section>
  );
}
