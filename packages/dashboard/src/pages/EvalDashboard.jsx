import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from 'recharts';
import { getEvalDashboard } from '../api/evals.js';
import CopilotIcon from '../components/CopilotIcon.jsx';
import { MoonIcon, SunIcon } from '../components/Icons.jsx';
import { applyTheme, readTheme, saveTheme } from '../lib/theme.js';

const POLL_MS = Number(import.meta.env.VITE_METRICS_POLL_MS) || 30_000;

function pct(value) {
  if (value == null || Number.isNaN(value)) return '—';
  return `${(value * 100).toFixed(1)}%`;
}

function MetricCard({ title, value, subtitle, formula }) {
  return (
    <article className="eval-metric-card">
      <div className="eval-metric-header">
        <h3 className="eval-metric-title">{title}</h3>
        {formula && (
          <span className="eval-metric-info-wrap">
            <button
              type="button"
              className="eval-metric-info"
              aria-label={`How ${title} is calculated`}
            >
              i
            </button>
            <span className="eval-metric-tooltip" role="tooltip">
              {formula}
            </span>
          </span>
        )}
      </div>
      <p className="eval-metric-value">{value}</p>
      {subtitle && <p className="eval-metric-subtitle">{subtitle}</p>}
    </article>
  );
}

export default function EvalDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [theme, setTheme] = useState(readTheme);

  const load = useCallback(() => {
    setLoading(true);
    return getEvalDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_MS);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    saveTheme(next);
  };

  const creation = data?.creationTimeReduction;
  const analysis = data?.analysisTimeReduction;
  const config = data?.configAcceptanceRate;
  const recAcc = data?.recommendationAccuracy;
  const sigAcc = data?.significanceAccuracy;
  const adoption = data?.adoptionRate;
  const trendData = data?.trends?.daily || [];

  return (
    <div className="copilot-app eval-dashboard-app">
      <div className="main-panel eval-main-panel">
        <header className="copilot-header">
          <div className="brand">
            <CopilotIcon size={24} />
            <span className="brand-name">Agent Eval Dashboard</span>
          </div>
          <div className="header-actions">
            <Link to="/" className="btn btn-ghost">← PM Copilot</Link>
            <button
              type="button"
              className="icon-btn theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
            >
              {theme === 'light' ? <MoonIcon /> : <SunIcon />}
            </button>
          </div>
        </header>

        <main className="eval-dashboard-content">
          {error && <p className="eval-error">{error}</p>}
          {loading && !data && <p className="eval-loading">Loading eval metrics…</p>}

          {data && (
            <>
              <p className="eval-intro">
                Live instrumentation from hypothesis, config, analysis, and apply flows.
                Metrics refresh every 30s.
              </p>

              <div className="eval-metrics-grid">
                <MetricCard
                  title="Creation time reduction"
                  value={creation ? `${creation.reductionPct}%` : '—'}
                  subtitle={
                    creation?.sampleSize
                      ? `AI avg ${creation.avgAiMinutes} min vs ${creation.baselineMinutes} min manual baseline`
                      : 'Run hypothesis setup to record'
                  }
                  formula="Time saved compared to manual setup: (manual baseline minus average AI setup time) divided by manual baseline, shown as a percentage."
                />
                <MetricCard
                  title="Config acceptance rate"
                  value={pct(config?.rate)}
                  subtitle={
                    config?.recommended
                      ? `${config.accepted} accepted of ${config.recommended} recommendations`
                      : 'Get metric recommendations in Experiment drawer'
                  }
                  formula="Share of AI metric recommendations the PM accepted: accepted recommendations divided by total recommendations, shown as a percentage."
                />
                <MetricCard
                  title="Recommendation accuracy"
                  value={pct(recAcc?.rate)}
                  subtitle={
                    recAcc?.total
                      ? `${recAcc.correct}/${recAcc.total} match expert (SQL recomputed)`
                      : 'Run full analysis to compare'
                  }
                  formula="How often the agent's Scale/Continue/Stop/Rollback verdict matches the expert decision: matching analyses divided by total analyses. Expert verdict is recomputed from the same SQL data using fixed statistical rules."
                />
                <MetricCard
                  title="Significance detection accuracy"
                  value={pct(sigAcc?.rate)}
                  subtitle={
                    sigAcc?.total
                      ? `${sigAcc.correct}/${sigAcc.total} significant calls correct`
                      : 'Requires completed analyses'
                  }
                  formula="How often the agent correctly identifies statistical significance (p < 0.05): correct significance calls divided by total analyses, shown as a percentage."
                />
                <MetricCard
                  title="Analysis time reduction"
                  value={analysis ? `${analysis.reductionPct}%` : '—'}
                  subtitle={
                    analysis?.sampleSize
                      ? `AI avg ${analysis.avgAiSeconds}s vs ${analysis.baselineMinutes} min manual baseline`
                      : 'Run full analysis to record'
                  }
                  formula="Time saved compared to manual analysis: (manual baseline minus average AI analysis time) divided by manual baseline, shown as a percentage."
                />
                <MetricCard
                  title="Recommendation adoption"
                  value={pct(adoption?.rate)}
                  subtitle={
                    adoption?.eligible
                      ? `${adoption.applied} applied of ${adoption.eligible} Scale/Rollback verdicts`
                      : 'Apply a Scale or Rollback decision'
                  }
                  formula="Share of actionable AI verdicts the PM applied to traffic: applied Scale or Rollback decisions divided by total Scale or Rollback recommendations, shown as a percentage."
                />
              </div>

              {trendData.length > 0 && (
                <section className="eval-chart-section">
                  <h2>7-day activity</h2>
                  <div className="eval-chart-wrap">
                    <ResponsiveContainer width="100%" height={240}>
                      <LineChart data={trendData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                        <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                        <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="analyses" name="Analyses" stroke="var(--accent)" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="configAccepted" name="Config accepted" stroke="#107c10" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="applied" name="Applied" stroke="#ca5010" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </section>
              )}

              <section className="eval-recent-section">
                <h2>Recent events</h2>
                {data.recentEvents?.length ? (
                  <table className="eval-events-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Experiment</th>
                        <th>Event</th>
                        <th>Summary</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recentEvents.map((evt) => (
                        <tr key={evt.id}>
                          <td>{evt.createdAt ? new Date(evt.createdAt).toLocaleString() : '—'}</td>
                          <td><code>{evt.experimentId}</code></td>
                          <td>{evt.eventType.replace(/_/g, ' ')}</td>
                          <td>{evt.summary}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p className="eval-empty">No events yet. Use the PM Copilot to generate data.</p>
                )}
              </section>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
