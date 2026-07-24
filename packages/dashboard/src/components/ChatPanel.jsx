import { useEffect, useMemo, useRef, useState } from 'react';
import { chat, chatStream } from '../api.js';
import CopilotIcon from './CopilotIcon.jsx';
import Decision from './Decision.jsx';
import FormattedMessage from './FormattedMessage.jsx';
import StreamStepIndicator from './StreamStepIndicator.jsx';
import BlockRenderer, { hasDecisionCardBlock } from '../sdui/BlockRenderer.jsx';

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
    'Should we roll out variant B to everyone?',
  ];
}

export default function ChatPanel({
  experiment,
  onDecision,
  decision,
  sessionId,
  messages,
  onMessagesChange,
  onApplyRequest,
  applyState,
  applyError,
  trafficSplit,
  analyzeBusy,
}) {
  const suggestions = buildSuggestions(experiment);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [warning, setWarning] = useState(null);
  const [streamSteps, setStreamSteps] = useState([]);
  const [streamError, setStreamError] = useState(null);
  const [lastSentText, setLastSentText] = useState('');
  const endRef = useRef(null);
  const abortRef = useRef(null);
  const hasUserMessages = messages.some((m) => m.role === 'user');
  const composerBusy = busy || analyzeBusy;
  const streamingMessageIndex = messages.findIndex((m) => m.streaming);
  const inlineDecision = messages.some((m) => hasDecisionCardBlock(m.blocks));

  const sduiHandlers = useMemo(() => ({
    onApply: onApplyRequest,
    applyState,
    applyError,
    trafficSplit,
    experimentStatus: experiment?.status,
    onAction: (actionId) => {
      if (actionId === 'apply_scale' || actionId === 'apply_rollback') {
        onApplyRequest?.();
      }
    },
  }), [onApplyRequest, applyState, applyError, trafficSplit, experiment?.status]);

  const blocksForMessage = (message) => {
    if (!message.blocks?.length) return [];
    if (message.text?.trim()) {
      return message.blocks.filter((block) => block.type !== 'markdown');
    }
    return message.blocks;
  };

  useEffect(() => () => abortRef.current?.abort(), []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, busy, decision, analyzeBusy, streamSteps]);

  const finalizeAssistant = (withUserMessage, text, extras = {}) => {
    onMessagesChange([
      ...withUserMessage,
      { role: 'assistant', text, ...extras },
    ]);
  };

  const sendWithFallback = async (text, withUserMessage) => {
    const res = await chat(text, sessionId);
    finalizeAssistant(withUserMessage, res.reply, { blocks: res.blocks || [] });
    if (res.warning) setWarning(res.warning);
    if (res.decision) onDecision?.(res.decision);
  };

  const send = async (textOverride) => {
    const text = (textOverride ?? input).trim();
    if (!text || composerBusy) return;

    abortRef.current?.abort();
    const ac = new AbortController();
    abortRef.current = ac;

    setInput('');
    setLastSentText(text);
    setStreamError(null);
    setStreamSteps([]);

    const priorMessages = messages.map((m) => (
      m.streaming ? { role: m.role, text: m.text, ...(m.error ? { error: true } : {}) } : m
    ));
    const withUserMessage = [...priorMessages, { role: 'user', text }];
    onMessagesChange([
      ...withUserMessage,
      { role: 'assistant', text: '', streaming: true },
    ]);
    setBusy(true);
    setWarning(null);

    let streamingText = '';
    let streamingBlocks = [];
    let gotStreamEvent = false;
    let terminal = false;
    let stepSeq = 0;

    const updateAssistant = () => {
      onMessagesChange([
        ...withUserMessage,
        {
          role: 'assistant',
          text: streamingText,
          blocks: streamingBlocks,
          streaming: !terminal,
        },
      ]);
    };

    const handleEvent = ({ event, data }) => {
      if (ac.signal.aborted || abortRef.current !== ac) return;
      gotStreamEvent = true;

      if (event === 'token' && data?.content) {
        streamingText += data.content;
        updateAssistant();
        return;
      }

      if (event === 'tool_start') {
        const id = stepSeq++;
        setStreamSteps((prev) => [
          ...prev,
          {
            id,
            name: data?.name,
            label: data?.label || 'Running analysis step',
            status: 'active',
          },
        ]);
        return;
      }

      if (event === 'tool_end') {
        setStreamSteps((prev) => {
          const next = [...prev];
          for (let i = next.length - 1; i >= 0; i -= 1) {
            if (next[i].name === data?.name && next[i].status === 'active') {
              next[i] = {
                ...next[i],
                status: data?.ok === false ? 'error' : 'done',
              };
              break;
            }
          }
          return next;
        });
        return;
      }

      if (event === 'warning') {
        setWarning(data);
        if (!streamingText.trim() && data?.message) {
          streamingText = data.message;
          updateAssistant();
        }
        return;
      }

      if (event === 'block' && data?.type) {
        streamingBlocks = [...streamingBlocks, data];
        updateAssistant();
        return;
      }

      if (event === 'decision') {
        onDecision?.(data);
        return;
      }

      if (event === 'error') {
        terminal = true;
        updateAssistant();
        setStreamError({
          message: data?.message || 'Could not complete streaming analysis.',
          retryable: data?.retryable ?? false,
        });
        setStreamSteps([]);
        setBusy(false);
        return;
      }

      if (event === 'done') {
        terminal = true;
        updateAssistant();
        setStreamSteps([]);
        setBusy(false);
      }
    };

    try {
      await chatStream(text, sessionId, handleEvent, ac.signal);

      if (ac.signal.aborted || abortRef.current !== ac) return;

      if (!terminal) {
        if (gotStreamEvent) {
          terminal = true;
          updateAssistant();
          setStreamError({
            message: 'Connection lost before the analysis finished.',
            retryable: true,
          });
        }
        setStreamSteps([]);
        setBusy(false);
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        if (abortRef.current === ac) {
          setStreamSteps([]);
          setBusy(false);
        }
        return;
      }

      if (!gotStreamEvent) {
        try {
          await sendWithFallback(text, withUserMessage);
        } catch (fallbackErr) {
          onMessagesChange([
            ...withUserMessage,
            {
              role: 'assistant',
              text: `Something went wrong: ${fallbackErr.message}`,
              error: true,
            },
          ]);
        }
      } else {
        terminal = true;
        updateAssistant();
        setStreamError({
          message: e.message || 'Connection lost before the analysis finished.',
          retryable: true,
        });
      }
      setStreamSteps([]);
      setBusy(false);
    }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const showLegacyBusy = (busy || analyzeBusy) && streamingMessageIndex === -1;

  return (
    <div className="copilot-chat">
      <div className="chat-scroll">
        {!hasUserMessages && !decision && (
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

        {messages.map((m, i) => {
          const messageBlocks = blocksForMessage(m);
          const showText = Boolean(m.text?.trim()) && !m.blocks?.some((b) => b.type === 'markdown');

          return (
            <div key={i} className={`turn ${m.role}${m.error ? ' error' : ''}`}>
              {m.role === 'assistant' && (
                <div className="turn-avatar"><CopilotIcon size={24} /></div>
              )}
              <div className="turn-body">
                {m.role === 'user' ? (
                  <div className="user-bubble">{m.text}</div>
                ) : m.error ? (
                  <div className="assistant-text">{m.text}</div>
                ) : m.streaming && !m.text && !messageBlocks.length ? (
                  <div className="assistant-text thinking">
                    <span className="typing-dots"><span /><span /><span /></span>
                  </div>
                ) : showText ? (
                  <FormattedMessage text={m.text} />
                ) : null}
                {messageBlocks.length > 0 && (
                  <BlockRenderer blocks={messageBlocks} handlers={sduiHandlers} />
                )}
                {m.streaming && i === streamingMessageIndex && (
                  <StreamStepIndicator steps={streamSteps} />
                )}
              </div>
            </div>
          );
        })}

        {showLegacyBusy && (
          <div className="turn assistant">
            <div className="turn-avatar"><CopilotIcon size={24} /></div>
            <div className="turn-body">
              <div className="assistant-text thinking">
                <span className="typing-dots"><span /><span /><span /></span>
                {analyzeBusy ? 'Running full analysis…' : 'Analyzing variants and querying experiment data…'}
              </div>
            </div>
          </div>
        )}

        {decision && !busy && !analyzeBusy && !inlineDecision && (
          <div className="turn assistant">
            <div className="turn-avatar"><CopilotIcon size={24} /></div>
            <div className="turn-body turn-card">
              <Decision
                decision={decision}
                onApply={onApplyRequest}
                applyState={applyState}
                applyError={applyError}
                trafficSplit={trafficSplit}
                experimentStatus={experiment?.status}
              />
            </div>
          </div>
        )}

        <div ref={endRef} />
      </div>

      <div className="composer-wrap">
        {streamError && (
          <div className="stream-error-banner" role="alert">
            <span>
              Could not complete streaming analysis. {streamError.message}
            </span>
            {streamError.retryable && lastSentText && (
              <button
                type="button"
                className="stream-error-retry"
                onClick={() => send(lastSentText)}
              >
                Retry
              </button>
            )}
            <button
              type="button"
              className="stream-error-dismiss"
              onClick={() => setStreamError(null)}
              aria-label="Dismiss"
            >
              ✕
            </button>
          </div>
        )}
        {warning && (
          <div className="chat-warning-banner" role="status">
            <span>{warning.message}</span>
            <button type="button" className="chat-warning-dismiss" onClick={() => setWarning(null)} aria-label="Dismiss">✕</button>
          </div>
        )}
        <div className="composer">
          <textarea
            rows={1}
            value={input}
            placeholder="Message Copilot"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            disabled={composerBusy}
          />
          <button
            type="button"
            className="composer-send"
            onClick={() => send()}
            disabled={composerBusy || !input.trim()}
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
