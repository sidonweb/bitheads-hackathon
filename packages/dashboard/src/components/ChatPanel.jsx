import { useState, useRef, useEffect } from 'react';
import { chat } from '../api.js';
import CopilotIcon from './CopilotIcon.jsx';
import Decision from './Decision.jsx';

function buildSuggestions(experiment) {
  if (!experiment?.variant_a_name || !experiment?.variant_b_name) {
    return [
      'Analyze the experiment and recommend a decision',
      'What metric should we use to judge success?',
    ];
  }
  return [
    `Is ${experiment.variant_b_name} beating ${experiment.variant_a_name}?`,
    'Compare both variants and tell me what changed',
    'Discover the experiment funnel',
    'Should we roll out variant B to everyone?',
  ];
}

export default function ChatPanel({ experiment, onDecision, decision, onRecipeDiscovered }) {
  const suggestions = buildSuggestions(experiment);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);
  const hasUserMessages = messages.some((m) => m.role === 'user');

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, busy, decision]);

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim();
    if (!text || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    setBusy(true);
    try {
      const res = await chat(text);
      setMessages((m) => [...m, { role: 'assistant', text: res.reply }]);
      if (res.decision) onDecision?.(res.decision);
      if (res.recipe) onRecipeDiscovered?.(res.recipe);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: `Something went wrong: ${e.message}`, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="copilot-chat">
      <div className="chat-scroll">
        {!hasUserMessages && (
          <div className="welcome">
            <div className="welcome-icon"><CopilotIcon size={48} /></div>
            <h1>What would you like to analyze today?</h1>
            <p className="welcome-sub">
              I can compare variants, explain what&apos;s different, and recommend whether to scale, iterate, or stop.
            </p>
            <div className="suggestions">
              {suggestions.map((s) => (
                <button key={s} type="button" className="suggestion-chip" onClick={() => send(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`turn ${m.role}${m.error ? ' error' : ''}`}>
            {m.role === 'assistant' && (
              <div className="turn-avatar"><CopilotIcon size={24} /></div>
            )}
            <div className="turn-body">
              {m.role === 'user' ? (
                <div className="user-bubble">{m.text}</div>
              ) : (
                <div className="assistant-text">{m.text}</div>
              )}
            </div>
          </div>
        ))}

        {busy && (
          <div className="turn assistant">
            <div className="turn-avatar"><CopilotIcon size={24} /></div>
            <div className="turn-body">
              <div className="assistant-text thinking">
                <span className="typing-dots"><span /><span /><span /></span>
                Analyzing variants and querying experiment data…
              </div>
            </div>
          </div>
        )}

        {decision && (
          <div className="turn assistant">
            <div className="turn-avatar"><CopilotIcon size={24} /></div>
            <div className="turn-body turn-card">
              <Decision decision={decision} />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      <div className="composer-wrap">
        <div className="composer">
          <textarea
            rows={1}
            value={input}
            placeholder="Message Copilot"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            disabled={busy}
          />
          <button
            type="button"
            className="composer-send"
            onClick={() => send()}
            disabled={busy || !input.trim()}
            aria-label="Send message"
          >
            ↑
          </button>
        </div>
        <p className="composer-note">Copilot can make mistakes. Verify recommendations before shipping.</p>
      </div>
    </div>
  );
}
