import { useEffect, useState } from 'react';
import { getExperiment, setTrafficSplit, newSessionId, EXPERIMENT_ID } from './api.js';
import CopilotIcon from './components/CopilotIcon.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import ExperimentDrawer from './components/ExperimentDrawer.jsx';
import { readTheme, saveTheme, applyTheme } from './lib/theme.js';

export default function App() {
  const [exp, setExp] = useState(null);
  const [summary, setSummary] = useState([]);
  const [split, setSplit] = useState(50);
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [theme, setTheme] = useState(readTheme);
  const [sessionId, setSessionId] = useState(newSessionId);

  const load = () =>
    getExperiment()
      .then((d) => { setExp(d.experiment); setSummary(d.summary); setSplit(d.experiment.traffic_split); })
      .catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);
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

  const onDecision = (d) => { setDecision(d); load(); };

  // Start a fresh, isolated conversation: new session id + clear the verdict.
  // The changed `key` on ChatPanel remounts it, wiping the chat history too.
  const startNewTest = () => {
    setSessionId(newSessionId());
    setDecision(null);
    setError('');
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
          <button type="button" className="btn btn-ghost" onClick={startNewTest} title="Start a fresh test session">
            + New Test
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => setDrawerOpen(true)}>
            Experiment
          </button>
        </div>
      </header>

      <ChatPanel key={sessionId} sessionId={sessionId} experiment={exp} onDecision={onDecision} decision={decision} />

      <ExperimentDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        split={split}
        onSplitChange={setSplit}
        onSplitCommit={onSplitCommit}
        summary={summary}
        metric={exp.primary_metric}
        onRefresh={load}
        error={error}
      />
    </div>
  );
}
