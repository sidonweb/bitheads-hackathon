import { useCallback, useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  getExperiment,
  setTrafficSplit,
  patchExperiment,
  newSessionId,
  analyze,
  EXPERIMENT_ID,
} from './api.js';
import {
  readActiveVariation,
  saveActiveVariation,
  VARIATION_CATALOG,
  buildVariationUrls,
} from './lib/variationCatalog.js';
import { saveHypothesis } from './api/lifecycle.js';
import CopilotIcon from './components/CopilotIcon.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import ExperimentDrawer from './components/ExperimentDrawer.jsx';
import SimulationMetricsPanel from './components/SimulationMetricsPanel.jsx';
import SessionSidebar from './components/SessionSidebar.jsx';
import ApplyConfirmModal from './components/ApplyConfirmModal.jsx';
import { MoonIcon, SunIcon } from './components/Icons.jsx';
import { DeleteSessionModal, RenameSessionModal } from './components/SessionModals.jsx';
import { readTheme, saveTheme, applyTheme } from './lib/theme.js';
import { readAutoRefresh, saveAutoRefresh } from './lib/metricsPrefs.js';
import { logEvalEvent } from './api/evals.js';

const SESSIONS_KEY = 'copilot_chat_sessions_v1';
const METRICS_POLL_INTERVAL_MS = Number(import.meta.env.VITE_METRICS_POLL_MS) || 30_000;

function makeSession(title = 'New test') {
  const now = new Date().toISOString();
  return {
    id: newSessionId(),
    title,
    pinned: false,
    createdAt: now,
    updatedAt: now,
    messages: [],
    decision: null,
  };
}

function readSessions() {
  try {
    const parsed = JSON.parse(localStorage.getItem(SESSIONS_KEY) || '[]');
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map((session) => ({
        ...makeSession(),
        ...session,
        messages: Array.isArray(session.messages) ? session.messages : [],
        pinned: Boolean(session.pinned),
      }));
    }
  } catch {
    // Start fresh if saved state is malformed.
  }
  return [makeSession()];
}

function sortSessions(sessions) {
  return [...sessions].sort((a, b) => {
    if (a.pinned !== b.pinned) return a.pinned ? -1 : 1;
    return new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime();
  });
}

function titleFromMessage(message) {
  const singleLine = message.replace(/\s+/g, ' ').trim();
  if (!singleLine) return 'New test';
  return singleLine.length > 44 ? `${singleLine.slice(0, 41)}...` : singleLine;
}

export default function App() {
  const [initialSessions] = useState(readSessions);
  const [activeVariationId, setActiveVariationId] = useState(readActiveVariation);
  const [exp, setExp] = useState(null);
  const [eventMatrix, setEventMatrix] = useState(null);
  const [simMeta, setSimMeta] = useState(null);
  const [split, setSplit] = useState(50);
  const [error, setError] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [renameSessionId, setRenameSessionId] = useState(null);
  const [deleteSessionId, setDeleteSessionId] = useState(null);
  const [theme, setTheme] = useState(readTheme);
  const [refreshing, setRefreshing] = useState(false);
  const [metricsExpanded, setMetricsExpanded] = useState(false);
  const [sessions, setSessions] = useState(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState(initialSessions[0].id);

  const [lastRefreshedAt, setLastRefreshedAt] = useState(null);
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(readAutoRefresh);
  const [metricsRefreshError, setMetricsRefreshError] = useState('');
  const [pollStopped, setPollStopped] = useState(false);
  const [justRefreshed, setJustRefreshed] = useState(false);
  const [initialLoadDone, setInitialLoadDone] = useState(false);

  const [variantAUrl, setVariantAUrl] = useState('');
  const [variantBUrl, setVariantBUrl] = useState('');
  const [analyzeBusy, setAnalyzeBusy] = useState(false);

  const [applyModalOpen, setApplyModalOpen] = useState(false);
  const [applyState, setApplyState] = useState('idle');
  const [applyError, setApplyError] = useState('');
  const [toast, setToast] = useState('');

  const prevRefreshing = useRef(false);
  const pulseTimer = useRef(null);

  const orderedSessions = sortSessions(sessions);
  const activeSession = sessions.find((session) => session.id === activeSessionId) || sessions[0];
  const renameSessionTarget = sessions.find((session) => session.id === renameSessionId);
  const deleteSessionTarget = sessions.find((session) => session.id === deleteSessionId);

  const load = useCallback((options = {}) => {
    const { isInitial = false } = options;
    setRefreshing(true);
    return getExperiment()
      .then((d) => {
        setExp(d.experiment);
        setEventMatrix(d.eventMatrix);
        setSplit(d.experiment.traffic_split);
        setLastRefreshedAt(Date.now());
        setMetricsRefreshError('');
        setInitialLoadDone(true);

        if (d.experiment.variant_a_url) setVariantAUrl(d.experiment.variant_a_url);
        if (d.experiment.variant_b_url) setVariantBUrl(d.experiment.variant_b_url);
      })
      .catch((e) => {
        if (isInitial || !initialLoadDone) {
          setError(e.message);
        } else {
          setMetricsRefreshError('Could not refresh metrics. Showing last loaded data.');
        }
        if (e.message?.includes('404') || e.message?.includes('not found')) {
          setPollStopped(true);
          setError('Experiment not found.');
        }
      })
      .finally(() => setRefreshing(false));
  }, [initialLoadDone]);

  useEffect(() => {
    load({ isInitial: true });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (pollStopped) return undefined;
    const id = setInterval(() => {
      if (autoRefreshEnabled) load();
    }, METRICS_POLL_INTERVAL_MS);
    return () => clearInterval(id);
  }, [load, autoRefreshEnabled, pollStopped]);

  useEffect(() => {
    if (prevRefreshing.current && !refreshing && !metricsRefreshError) {
      setJustRefreshed(true);
      if (pulseTimer.current) clearTimeout(pulseTimer.current);
      pulseTimer.current = setTimeout(() => setJustRefreshed(false), 600);
    }
    prevRefreshing.current = refreshing;
  }, [refreshing, metricsRefreshError]);

  useEffect(() => { applyTheme(theme); }, [theme]);
  useEffect(() => { localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions)); }, [sessions]);

  useEffect(() => {
    if (!activeSession && sessions.length > 0) setActiveSessionId(sessions[0].id);
  }, [activeSession, sessions]);

  useEffect(() => {
    if (!toast) return undefined;
    const id = setTimeout(() => setToast(''), 4000);
    return () => clearTimeout(id);
  }, [toast]);

  const toggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    saveTheme(next);
  };

  const onSplitCommit = async (value) => {
    setSplit(value);
    try { await setTrafficSplit(EXPERIMENT_ID, value); } catch (e) { setError(e.message); }
  };

  const updateActiveSession = (updater) => {
    if (!activeSession) return;
    setSessions((current) => current.map((session) => {
      if (session.id !== activeSession.id) return session;
      const next = updater(session);
      return { ...next, updatedAt: new Date().toISOString() };
    }));
  };

  const onMessagesChange = (nextMessages) => {
    updateActiveSession((session) => {
      const firstUser = nextMessages.find((message) => message.role === 'user')?.text;
      const shouldRetitle = session.title === 'New test' && firstUser;
      return {
        ...session,
        title: shouldRetitle ? titleFromMessage(firstUser) : session.title,
        messages: nextMessages,
      };
    });
  };

  const onDecision = (d) => {
    setApplyState('idle');
    setApplyError('');
    updateActiveSession((session) => ({ ...session, decision: d }));
    load();
  };

  const onDemoReset = () => {
    setSimMeta(null);
    setApplyState('idle');
    setApplyError('');
    updateActiveSession((session) => ({
      ...session,
      messages: [],
      decision: null,
    }));
  };

  const onSimulateComplete = (meta) => {
    setSimMeta(meta);
    load();
  };

  const handleAnalyze = async ({ variantAUrl: urlA, variantBUrl: urlB }) => {
    if (analyzeBusy) return;
    setAnalyzeBusy(true);
    setError('');
    try {
      const result = await analyze({ variantAUrl: urlA, variantBUrl: urlB });
      onDecision(result.decision);
      updateActiveSession((session) => ({
        ...session,
        messages: [
          ...session.messages,
          {
            role: 'user',
            text: `Run full analysis\nA: ${urlA}\nB: ${urlB}`,
          },
          {
            role: 'assistant',
            text: result.reply || result.decision?.reasoning || 'Analysis complete.',
            blocks: result.blocks || [],
          },
        ],
      }));
      setDrawerOpen(false);
    } finally {
      setAnalyzeBusy(false);
    }
  };

  const handleApplyRequest = () => {
    setApplyError('');
    setApplyModalOpen(true);
  };

  const handleApplyConfirm = async () => {
    const decision = activeSession?.decision;
    if (!decision) return;
    const targetSplit = decision.decision === 'Scale' ? 100 : 0;
    setApplyState('loading');
    setApplyError('');
    try {
      await setTrafficSplit(EXPERIMENT_ID, targetSplit);
      setSplit(targetSplit);
      setApplyState('applied');
      setApplyModalOpen(false);
      setToast(
        decision.decision === 'Scale'
          ? 'Variant B is now at 100% traffic.'
          : 'Reverted to 100% Variant A.',
      );
      logEvalEvent({
        eventType: 'recommendation_applied',
        payload: {
          decision: decision.decision,
          trafficSplit: targetSplit,
        },
      }).catch(() => {});
      load();
    } catch (e) {
      setApplyState('error');
      setApplyError(e.message || 'Could not update traffic. Try again.');
    }
  };

  const startNewTest = () => {
    const session = makeSession();
    setSessions((current) => [session, ...current]);
    setActiveSessionId(session.id);
    setApplyState('idle');
    setApplyError('');
    setError('');
  };

  const renameSession = (id, nextTitle) => {
    setSessions((current) => current.map((item) => (
      item.id === id ? { ...item, title: titleFromMessage(nextTitle), updatedAt: new Date().toISOString() } : item
    )));
    setRenameSessionId(null);
  };

  const deleteSession = (id) => {
    setSessions((current) => {
      const remaining = current.filter((item) => item.id !== id);
      if (remaining.length === 0) {
        const replacement = makeSession();
        setActiveSessionId(replacement.id);
        return [replacement];
      }
      if (id === activeSessionId) setActiveSessionId(sortSessions(remaining)[0].id);
      return remaining;
    });
    setDeleteSessionId(null);
  };

  const togglePinSession = (id) => {
    setSessions((current) => current.map((item) => (
      item.id === id ? { ...item, pinned: !item.pinned, updatedAt: new Date().toISOString() } : item
    )));
  };

  const handleAutoRefreshChange = (enabled) => {
    setAutoRefreshEnabled(enabled);
    saveAutoRefresh(enabled);
  };

  const applyVariationPreset = async (nextId) => {
    const preset = VARIATION_CATALOG[nextId];
    if (!preset) return;
    const urls = buildVariationUrls(nextId);
    setVariantAUrl(urls.variantAUrl);
    setVariantBUrl(urls.variantBUrl);
    try {
      await patchExperiment({
        variantAUrl: urls.variantAUrl,
        variantBUrl: urls.variantBUrl,
      });
      await saveHypothesis(EXPERIMENT_ID, {
        name: preset.name,
        hypothesis: preset.hypothesis,
        variantAName: preset.variantAName,
        variantBName: preset.variantBName,
      });
      await load();
    } catch (e) {
      setError(e.message);
    }
  };

  const handleVariationChange = async (nextId) => {
    if (nextId === activeVariationId) return;
    saveActiveVariation(nextId);
    setActiveVariationId(nextId);
    setSimMeta(null);
    setError('');
    await applyVariationPreset(nextId);
  };

  const activeVariationMeta = VARIATION_CATALOG[activeVariationId];

  if (!exp) {
    return (
      <div className="copilot-app loading">
        <CopilotIcon size={36} />
        <p>{error || 'Loading...'}</p>
      </div>
    );
  }

  return (
    <div className="copilot-app">
      {toast && (
        <div className="app-toast" role="status">
          ✓ {toast}
          <button type="button" className="toast-dismiss" onClick={() => setToast('')} aria-label="Dismiss">✕</button>
        </div>
      )}

      <SessionSidebar
        sessions={orderedSessions}
        activeSessionId={activeSession?.id}
        onSelect={setActiveSessionId}
        onNew={startNewTest}
        onRename={setRenameSessionId}
        onDelete={setDeleteSessionId}
        onTogglePin={togglePinSession}
      />

      <div className="main-panel">
        <header className="copilot-header">
          <div className="brand">
            <CopilotIcon size={24} />
            <span className="brand-name">Experiment Copilot</span>
          </div>
          <div className="header-actions">
            <label className="experiment-picker-wrap">
              <span className="sr-only">Storefront variation</span>
              <select
                className="experiment-picker"
                value={activeVariationId}
                onChange={(e) => handleVariationChange(e.target.value)}
                aria-label="Select storefront variation"
              >
                {Object.values(VARIATION_CATALOG).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="icon-btn theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              title={theme === 'light' ? 'Dark mode' : 'Light mode'}
            >
              {theme === 'light' ? <MoonIcon /> : <SunIcon />}
            </button>
            <Link to="/evals" className="btn btn-ghost">Agent Evals</Link>
            <button type="button" className="btn btn-ghost" onClick={() => setDrawerOpen(true)}>
              Experiment
            </button>
          </div>
        </header>

        <div className={`main-split${metricsExpanded ? ' metrics-expanded' : ' metrics-collapsed'}`}>
          <SimulationMetricsPanel
            eventMatrix={eventMatrix}
            simMeta={simMeta}
            onRefresh={() => load()}
            refreshing={refreshing}
            expanded={metricsExpanded}
            onToggle={() => setMetricsExpanded((v) => !v)}
            lastRefreshedAt={lastRefreshedAt}
            autoRefreshEnabled={autoRefreshEnabled}
            onAutoRefreshChange={handleAutoRefreshChange}
            metricsRefreshError={metricsRefreshError}
            justRefreshed={justRefreshed}
          />
          {activeSession && (
            <ChatPanel
              key={activeSession.id}
              sessionId={activeSession.id}
              experiment={exp}
              onDecision={onDecision}
              decision={activeSession.decision}
              messages={activeSession.messages}
              onMessagesChange={onMessagesChange}
              onApplyRequest={handleApplyRequest}
              applyState={applyState}
              applyError={applyError}
              trafficSplit={split}
              analyzeBusy={analyzeBusy}
            />
          )}
        </div>
      </div>

      <ExperimentDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        experiment={exp}
        experimentId={EXPERIMENT_ID}
        variationId={activeVariationId}
        variationMeta={activeVariationMeta}
        split={split}
        onSplitChange={setSplit}
        onSplitCommit={onSplitCommit}
        onRefresh={load}
        onDemoReset={onDemoReset}
        onSimulateComplete={onSimulateComplete}
        onAnalyze={handleAnalyze}
        analyzeBusy={analyzeBusy}
        variantAUrl={variantAUrl}
        variantBUrl={variantBUrl}
        onVariantAUrlChange={setVariantAUrl}
        onVariantBUrlChange={setVariantBUrl}
        error={error}
        setError={setError}
      />

      <ApplyConfirmModal
        open={applyModalOpen}
        decision={activeSession?.decision}
        onConfirm={handleApplyConfirm}
        onCancel={() => !applyState.startsWith('loading') && setApplyModalOpen(false)}
        loading={applyState === 'loading'}
      />

      <RenameSessionModal
        session={renameSessionTarget}
        onCancel={() => setRenameSessionId(null)}
        onConfirm={(nextTitle) => renameSession(renameSessionTarget.id, nextTitle)}
      />
      <DeleteSessionModal
        session={deleteSessionTarget}
        onCancel={() => setDeleteSessionId(null)}
        onConfirm={() => deleteSession(deleteSessionTarget.id)}
      />
    </div>
  );
}
