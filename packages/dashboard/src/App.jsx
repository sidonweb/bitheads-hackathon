import { useEffect, useState } from 'react';
import { getExperiment, setTrafficSplit, EXPERIMENT_ID } from './api.js';
import Metrics from './components/Metrics.jsx';
import Decision from './components/Decision.jsx';
import ChatPanel from './components/ChatPanel.jsx';

export default function App() {
  const [exp, setExp] = useState(null);
  const [summary, setSummary] = useState([]);
  const [split, setSplit] = useState(50);
  const [decision, setDecision] = useState(null);
  const [error, setError] = useState('');

  const load = () =>
    getExperiment()
      .then((d) => { setExp(d.experiment); setSummary(d.summary); setSplit(d.experiment.traffic_split); })
      .catch((e) => setError(e.message));

  useEffect(() => { load(); }, []);

  const onSplitCommit = async (value) => {
    setSplit(value);
    try { await setTrafficSplit(EXPERIMENT_ID, value); } catch (e) { setError(e.message); }
  };

  // When the copilot completes an analysis in chat, render the verdict card + refresh metrics.
  const onDecision = (d) => { setDecision(d); load(); };

  if (!exp) return <div className="app"><p>{error || 'Loading experiment…'}</p></div>;

  return (
    <div className="app">
      <header><h1>🧭 Experiment Copilot</h1></header>

      <section className="panel">
        <div className="field-label">Experiment</div>
        <h2>{exp.name}</h2>
        <p className="hypothesis">“{exp.hypothesis}”</p>
        <div className="variant-urls">
          <span>A ({exp.variant_a_name}): {exp.variant_a_url
            ? <a href={exp.variant_a_url} target="_blank" rel="noreferrer">{exp.variant_a_url}</a>
            : <em>no url</em>}</span>
          <span>B ({exp.variant_b_name}): {exp.variant_b_url
            ? <a href={exp.variant_b_url} target="_blank" rel="noreferrer">{exp.variant_b_url}</a>
            : <em>no url</em>}</span>
        </div>
        <div className="meta">
          Metric: <code>{exp.primary_metric || 'inferred by copilot'}</code> · Status: {exp.status}
        </div>
      </section>

      <section className="panel">
        <div className="field-label">Traffic allocation to Variant B — {split}%</div>
        <input
          type="range" min="0" max="100" value={split}
          onChange={(e) => setSplit(Number(e.target.value))}
          onMouseUp={(e) => onSplitCommit(Number(e.target.value))}
          onTouchEnd={(e) => onSplitCommit(Number(e.target.value))}
        />
        <div className="split-labels"><span>A: {100 - split}%</span><span>B: {split}%</span></div>
      </section>

      <section className="panel">
        <div className="field-label">Talk to the Copilot</div>
        <ChatPanel experiment={exp} onDecision={onDecision} />
      </section>

      <section className="panel">
        <Metrics summary={summary} metric={exp.primary_metric || 'conversions'} />
        <button className="btn refresh" onClick={load}>↻ Refresh metrics</button>
        {error && <p className="error">⚠ {error}</p>}
      </section>

      {decision && <Decision decision={decision} />}
    </div>
  );
}
