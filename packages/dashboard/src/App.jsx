import { useCallback, useEffect, useState } from 'react';
import {
  getExperiment,
  getJourneyRecipe,
  setTrafficSplit,
  EXPERIMENT_ID,
} from './api.js';
import CopilotIcon from './components/CopilotIcon.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import ExperimentDrawer from './components/ExperimentDrawer.jsx';
import SimulationMetricsPanel from './components/SimulationMetricsPanel.jsx';
import { readTheme, saveTheme, applyTheme } from './lib/theme.js';

export default function App() {
  const [exp, setExp] = useState(null);
  const [eventMatrix, setEventMatrix] = useState(null);
  const [journeyRecipe, setJourneyRecipe] = useState(null);
  const [simMeta, setSimMeta] = useState(null);
  const [split, setSplit] = useState(50);
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [theme, setTheme] = useState(readTheme);
  const [chatKey, setChatKey] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  const loadRecipe = useCallback(() =>
    getJourneyRecipe()
      .then((d) => setJourneyRecipe(d.recipe))
      .catch(() => {}), []);

  const load = useCallback(() => {
    setRefreshing(true);
    return getExperiment()
      .then((d) => {
        setExp(d.experiment);
        setEventMatrix(d.eventMatrix);
        setSplit(d.experiment.traffic_split);
      })
      .catch((e) => setError(e.message))
      .finally(() => setRefreshing(false));
  }, []);

  useEffect(() => {
    load();
    loadRecipe();
  }, [load, loadRecipe]);

  useEffect(() => {
    const id = setInterval(() => { load(); }, 30_000);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => { applyTheme(theme); }, [theme]);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    saveTheme(next);
  };

  const onSplitCommit = async (value) => {
    setSplit(value);
    try { await setTrafficSplit(EXPERIMENT_ID, value); } catch (e) { setError(e.message); }
  };

  const onDecision = (d) => {
    setDecision(d);
    load();
    if (d?.inferred_metric) loadRecipe();
  };

  const onDemoReset = () => {
    setDecision(null);
    setSimMeta(null);
    setChatKey((k) => k + 1);
  };

  const onSimulateComplete = (meta) => {
    setSimMeta(meta);
    load();
  };

  const onDiscoverComplete = (recipe) => {
    if (recipe) setJourneyRecipe(recipe);
    loadRecipe();
  };

  if (!exp) {
    return (
      <div className="copilot-app loading">
        <CopilotIcon size={36} />
        <p>{error || 'Loading…'}</p>
      </div>
    );
  }

  return (
    <div className="copilot-app">
      <header className="copilot-header">
        <div className="brand">
          <CopilotIcon size={24} />
          <span className="brand-name">Experiment Copilot</span>
        </div>
        <div className="header-actions">
          <button
            type="button"
            className="icon-btn theme-toggle"
            onClick={toggleTheme}
            aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            title={theme === 'light' ? 'Dark mode' : 'Light mode'}
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => setDrawerOpen(true)}>
            Experiment
          </button>
        </div>
      </header>

      <div className="main-split">
        <SimulationMetricsPanel
          eventMatrix={eventMatrix}
          journeyRecipe={journeyRecipe}
          simMeta={simMeta}
          onRefresh={load}
          refreshing={refreshing}
        />
        <ChatPanel
          key={chatKey}
          experiment={exp}
          onDecision={onDecision}
          decision={decision}
          onRecipeDiscovered={onDiscoverComplete}
        />
      </div>

      <ExperimentDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        split={split}
        onSplitChange={setSplit}
        onSplitCommit={onSplitCommit}
        onRefresh={load}
        onDemoReset={onDemoReset}
        onSimulateComplete={onSimulateComplete}
        onDiscoverComplete={onDiscoverComplete}
        error={error}
        setError={setError}
      />
    </div>
  );
}
