import { useCallback, useEffect, useState } from 'react';
import {
  getExperiment,
  setTrafficSplit,
  newSessionId,
  EXPERIMENT_ID,
} from './api.js';
import CopilotIcon from './components/CopilotIcon.jsx';
import ChatPanel from './components/ChatPanel.jsx';
import ExperimentDrawer from './components/ExperimentDrawer.jsx';
import SimulationMetricsPanel from './components/SimulationMetricsPanel.jsx';
import SessionSidebar from './components/SessionSidebar.jsx';
import { MoonIcon, SunIcon } from './components/Icons.jsx';
import { DeleteSessionModal, RenameSessionModal } from './components/SessionModals.jsx';
import { readTheme, saveTheme, applyTheme } from './lib/theme.js';

const SESSIONS_KEY = 'copilot_chat_sessions_v1';

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

  const orderedSessions = sortSessions(sessions);
  const activeSession = sessions.find((session) => session.id === activeSessionId) || sessions[0];
  const renameSessionTarget = sessions.find((session) => session.id === renameSessionId);
  const deleteSessionTarget = sessions.find((session) => session.id === deleteSessionId);

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
  }, [load]);

  useEffect(() => {
    const id = setInterval(() => { load(); }, 30_000);
    return () => clearInterval(id);
  }, [load]);

  useEffect(() => { applyTheme(theme); }, [theme]);
  useEffect(() => { localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions)); }, [sessions]);

  useEffect(() => {
    if (!activeSession && sessions.length > 0) setActiveSessionId(sessions[0].id);
  }, [activeSession, sessions]);

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
    updateActiveSession((session) => ({ ...session, decision: d }));
    load();
  };

  const onDemoReset = () => {
    setSimMeta(null);
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

  const startNewTest = () => {
    const session = makeSession();
    setSessions((current) => [session, ...current]);
    setActiveSessionId(session.id);
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
            <button
              type="button"
              className="icon-btn theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
              title={theme === 'light' ? 'Dark mode' : 'Light mode'}
            >
              {theme === 'light' ? <MoonIcon /> : <SunIcon />}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setDrawerOpen(true)}>
              Experiment
            </button>
          </div>
        </header>

        <div className={`main-split${metricsExpanded ? ' metrics-expanded' : ' metrics-collapsed'}`}>
          <SimulationMetricsPanel
            eventMatrix={eventMatrix}
            simMeta={simMeta}
            onRefresh={load}
            refreshing={refreshing}
            expanded={metricsExpanded}
            onToggle={() => setMetricsExpanded((v) => !v)}
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
            />
          )}
        </div>
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
        error={error}
        setError={setError}
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
