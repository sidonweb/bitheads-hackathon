import { useEffect, useState } from 'react';
import {
  DEMO_MODE,
  SCENARIOS,
  readSimSettings,
  saveSimSettings,
  toConvFraction,
} from '../lib/demoSim.js';
import { demoReset, demoSimulate } from '../api.js';
import HypothesisPanel from './HypothesisPanel.jsx';
import ConfigRecommendPanel from './ConfigRecommendPanel.jsx';
import PreflightCard from './PreflightCard.jsx';
import AnalyzePanel, { formatAnalyzeError } from './AnalyzePanel.jsx';

export default function ExperimentDrawer({
  open,
  onClose,
  experiment,
  experimentId,
  variationId,
  variationMeta,
  split,
  onSplitChange,
  onSplitCommit,
  onRefresh,
  onDemoReset,
  onSimulateComplete,
  variantAUrl,
  variantBUrl,
  onVariantAUrlChange,
  onVariantBUrlChange,
  onAnalyze,
  analyzeBusy,
  error,
  setError,
}) {
  const [simUsers, setSimUsers] = useState(() => readSimSettings().users);
  const [convA, setConvA] = useState(() => variationMeta?.defaultConvA ?? readSimSettings().convA);
  const [convB, setConvB] = useState(() => variationMeta?.defaultConvB ?? readSimSettings().convB);
  const [scenario, setScenario] = useState(() => readSimSettings().scenario);
  const [scenarioLabel, setScenarioLabel] = useState('');
  const [simBusy, setSimBusy] = useState(false);
  const [resetBusy, setResetBusy] = useState(false);

  const persistSim = (next) => {
    saveSimSettings({
      users: next.users ?? simUsers,
      convA: next.convA ?? convA,
      convB: next.convB ?? convB,
      scenario: next.scenario ?? scenario,
    });
  };

  const onUsersChange = (v) => {
    const n = Math.min(10_000, Math.max(1, Number(v) || 1));
    setSimUsers(n);
    persistSim({ users: n });
  };

  const onConvAChange = (v) => {
    const n = Math.min(100, Math.max(0, Number(v) || 0));
    setConvA(n);
    persistSim({ convA: n });
  };

  const onConvBChange = (v) => {
    const n = Math.min(100, Math.max(0, Number(v) || 0));
    setConvB(n);
    persistSim({ convB: n });
  };

  const onScenarioChange = (id) => {
    setScenario(id);
    persistSim({ scenario: id });
  };

  useEffect(() => {
    if (!variationMeta) return;
    setConvA(variationMeta.defaultConvA);
    setConvB(variationMeta.defaultConvB);
    persistSim({ convA: variationMeta.defaultConvA, convB: variationMeta.defaultConvB });
  }, [variationId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSimulate = async () => {
    setSimBusy(true);
    setError('');
    try {
      const res = await demoSimulate({
        users: simUsers,
        convA: toConvFraction(convA),
        convB: toConvFraction(convB),
        id: experimentId,
        variation: variationId?.startsWith('custom-') ? null : variationId,
      });
      onSimulateComplete?.({
        usersSimulated: res.usersSimulated,
        eventsInserted: res.eventsInserted,
      });
      await onRefresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setSimBusy(false);
    }
  };

  const handleReset = async () => {
    setResetBusy(true);
    setError('');
    try {
      const res = await demoReset(scenario, experimentId, variationId?.startsWith('custom-') ? null : variationId);
      setScenarioLabel(res.label || '');
      onDemoReset?.(res);
      await onRefresh();
    } catch (e) {
      setError(e.message);
    } finally {
      setResetBusy(false);
    }
  };

  const handleAnalyze = async ({ variantAUrl: urlA, variantBUrl: urlB }) => {
    if (analyzeBusy) return;
    setError('');
    try {
      await onAnalyze?.({ variantAUrl: urlA, variantBUrl: urlB });
    } catch (e) {
      setError(formatAnalyzeError(e));
    }
  };

  const busy = simBusy || resetBusy || analyzeBusy;

  return (
    <>
      <div className={`drawer-backdrop${open ? ' open' : ''}`} onClick={onClose} aria-hidden />
      <aside className={`experiment-drawer${open ? ' open' : ''}`} aria-hidden={!open}>
        <div className="drawer-head">
          <h2>Experiment controls</h2>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close panel">✕</button>
        </div>

        <div className="drawer-body">
          {experiment && experimentId && (
            <HypothesisPanel
              experimentId={experimentId}
              experiment={experiment}
              onSaved={onRefresh}
              setError={setError}
            />
          )}

          {experiment && experimentId && (
            <ConfigRecommendPanel
              experimentId={experimentId}
              experiment={experiment}
              variantAUrl={variantAUrl}
              variantBUrl={variantBUrl}
              onSaved={onRefresh}
              setError={setError}
            />
          )}

          <AnalyzePanel
            variantAUrl={variantAUrl}
            variantBUrl={variantBUrl}
            onVariantAUrlChange={onVariantAUrlChange}
            onVariantBUrlChange={onVariantBUrlChange}
            onAnalyze={handleAnalyze}
            analyzeBusy={analyzeBusy}
            disabled={busy}
          />

          {(variantAUrl || variantBUrl) && (
            <section className="drawer-section inspect-links">
              <h3>Inspect in browser</h3>
              <p className="drawer-desc">Open seeded variant URLs to preview the A/B diff.</p>
              {variantAUrl && (
                <a className="inspect-link" href={variantAUrl} target="_blank" rel="noreferrer">
                  Variant A preview
                </a>
              )}
              {variantBUrl && (
                <a className="inspect-link" href={variantBUrl} target="_blank" rel="noreferrer">
                  Variant B preview
                </a>
              )}
            </section>
          )}

          {experimentId && (
            <PreflightCard
              experimentId={experimentId}
              open={open}
              variantAUrl={variantAUrl}
              variantBUrl={variantBUrl}
              setError={setError}
            />
          )}

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

          {DEMO_MODE && (
            <>
              <section className="drawer-section">
                <h3>Traffic simulation</h3>
                <p className="drawer-desc">
                  Generates synthetic users using traffic split and conversion rates below.
                </p>
                <label className="field-label" htmlFor="sim-users">Simulated users</label>
                <input
                  id="sim-users"
                  className="drawer-input"
                  type="number"
                  min="1"
                  max="10000"
                  value={simUsers}
                  onChange={(e) => onUsersChange(e.target.value)}
                  disabled={busy}
                />
                <div className="drawer-field-row">
                  <div>
                    <label className="field-label" htmlFor="conv-a">Conv. rate A (%)</label>
                    <input
                      id="conv-a"
                      className="drawer-input"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={convA}
                      onChange={(e) => onConvAChange(e.target.value)}
                      disabled={busy}
                    />
                  </div>
                  <div>
                    <label className="field-label" htmlFor="conv-b">Conv. rate B (%)</label>
                    <input
                      id="conv-b"
                      className="drawer-input"
                      type="number"
                      min="0"
                      max="100"
                      step="0.1"
                      value={convB}
                      onChange={(e) => onConvBChange(e.target.value)}
                      disabled={busy}
                    />
                  </div>
                </div>
                <button
                  type="button"
                  className="btn btn-secondary drawer-action"
                  onClick={handleSimulate}
                  disabled={busy}
                >
                  {simBusy ? `Simulating ${simUsers} users…` : 'Simulate traffic'}
                </button>
              </section>

              <section className="drawer-section">
                <h3>Demo reset</h3>
                <label className="field-label" htmlFor="demo-scenario">Scenario</label>
                <select
                  id="demo-scenario"
                  className="drawer-select"
                  value={scenario}
                  onChange={(e) => onScenarioChange(e.target.value)}
                  disabled={busy}
                >
                  {SCENARIOS.map((s) => (
                    <option key={s.id} value={s.id}>{s.label}</option>
                  ))}
                </select>
                {scenarioLabel && <p className="drawer-badge">{scenarioLabel}</p>}
                <button
                  type="button"
                  className="btn btn-secondary drawer-action"
                  onClick={handleReset}
                  disabled={busy}
                >
                  {resetBusy ? 'Resetting…' : 'Reset demo'}
                </button>
              </section>
            </>
          )}

          {error && <p className="error drawer-error">⚠ {error}</p>}
          <p className="drawer-hint">Metrics table is on the main dashboard panel.</p>
        </div>
      </aside>
    </>
  );
}
