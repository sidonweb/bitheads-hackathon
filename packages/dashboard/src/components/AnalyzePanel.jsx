function isValidUrl(url) {
  const trimmed = url.trim();
  return trimmed.startsWith('http://') || trimmed.startsWith('https://');
}

function formatAnalyzeError(e) {
  const hints = {
    VALIDATION_ERROR: 'Fix URL fields before analyzing.',
    AGENT_TOOL_LIMIT: 'Agent hit tool budget — try again later.',
    AGENT_NO_DECISION: 'Analysis incomplete — retry.',
    LLM_UNAVAILABLE: 'Copilot temporarily unavailable.',
  };
  const hint = hints[e.code];
  if (hint) return e.retryable ? `${hint} Try again.` : hint;
  return e.message || 'Analysis failed';
}

export default function AnalyzePanel({
  variantAUrl,
  variantBUrl,
  onVariantAUrlChange,
  onVariantBUrlChange,
  onAnalyze,
  analyzeBusy,
  disabled,
}) {
  const urlsValid = isValidUrl(variantAUrl) && isValidUrl(variantBUrl);
  const showInvalidHint = (variantAUrl.trim() || variantBUrl.trim()) && !urlsValid;

  const handleAnalyze = () => {
    if (analyzeBusy || !urlsValid || disabled) return;
    onAnalyze?.({ variantAUrl: variantAUrl.trim(), variantBUrl: variantBUrl.trim() });
  };

  return (
    <section className="drawer-section analyze-panel">
      <h3>Analysis</h3>
      <p className="drawer-desc">Provide both URLs before running full analysis.</p>

      <label className="field-label" htmlFor="variant-a-url">Variant A URL</label>
      <input
        id="variant-a-url"
        className="drawer-input"
        type="url"
        value={variantAUrl}
        onChange={(e) => onVariantAUrlChange(e.target.value)}
        placeholder="https://example.com/?variant=A"
        disabled={analyzeBusy || disabled}
      />

      <label className="field-label" htmlFor="variant-b-url">Variant B URL</label>
      <input
        id="variant-b-url"
        className="drawer-input"
        type="url"
        value={variantBUrl}
        onChange={(e) => onVariantBUrlChange(e.target.value)}
        placeholder="https://example.com/?variant=B"
        disabled={analyzeBusy || disabled}
      />

      {showInvalidHint && (
        <p className="warning-inline">URLs must start with http:// or https://</p>
      )}

      <button
        type="button"
        className="btn btn-primary drawer-action"
        onClick={handleAnalyze}
        disabled={analyzeBusy || !urlsValid || disabled}
      >
        {analyzeBusy ? 'Analyzing…' : 'Run full analysis'}
      </button>
    </section>
  );
}

export { formatAnalyzeError, isValidUrl };
