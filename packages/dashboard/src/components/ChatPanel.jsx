import { useState, useRef, useEffect } from 'react';
import { chat } from '../api.js';

// Conversational panel: the PM discusses the A/B change with the copilot and asks
// for a recommendation. When the agent completes an analysis, it hands the
// structured decision up to the parent via onDecision (rendered as a card).
export default function ChatPanel({ experiment, onDecision }) {
  const seed = experiment?.variant_b_url
    ? `Try: "Compare ${experiment.variant_a_url} vs ${experiment.variant_b_url} and tell me what changed, then recommend."`
    : 'Ask the copilot to analyze the experiment and recommend a decision.';

  const [messages, setMessages] = useState([
    { role: 'assistant', text: `Hi — I'm your Experiment Copilot. ${seed}` },
  ]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const endRef = useRef(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, busy]);

  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', text }]);
    setBusy(true);
    try {
      const res = await chat(text);
      setMessages((m) => [...m, { role: 'assistant', text: res.reply }]);
      if (res.decision) onDecision?.(res.decision);
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', text: `⚠ ${e.message}`, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="chat">
      <div className="chat-log">
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}${m.error ? ' error' : ''}`}>
            <div className="msg-role">{m.role === 'user' ? 'You' : 'Copilot'}</div>
            <div className="msg-text">{m.text}</div>
          </div>
        ))}
        {busy && (
          <div className="msg assistant">
            <div className="msg-role">Copilot</div>
            <div className="msg-text thinking">analyzing… (opening variant pages, querying events)</div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      <div className="chat-input">
        <textarea
          rows={2}
          value={input}
          placeholder="Describe the A/B change or ask for a recommendation…"
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKey}
          disabled={busy}
        />
        <button className="btn" onClick={send} disabled={busy}>Send</button>
      </div>
    </div>
  );
}
