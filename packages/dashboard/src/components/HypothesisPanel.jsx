import { useEffect, useRef, useState } from 'react';
import { logEvalEvent } from '../api/evals.js';
import { generateHypothesis, saveHypothesis } from '../api/lifecycle.js';

const GOAL_MAX = 2000;

export default function HypothesisPanel({
  experimentId,
  experiment,
  onSaved,
  setError,
}) {
  const [businessGoal, setBusinessGoal] = useState('');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [editableHypothesis, setEditableHypothesis] = useState('');
  const [editableName, setEditableName] = useState('');
  const [editableVariantA, setEditableVariantA] = useState('');
  const [editableVariantB, setEditableVariantB] = useState('');
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [llmWarning, setLlmWarning] = useState('');
  const [hasDraft, setHasDraft] = useState(false);
  const creationStartedAt = useRef(null);

  useEffect(() => {
    if (!experiment) return;
    setEditableHypothesis(experiment.hypothesis || '');
    setEditableName(experiment.name || '');
    setEditableVariantA(experiment.variant_a_name || '');
    setEditableVariantB(experiment.variant_b_name || '');
  }, [experiment]);

  const handleGenerate = async () => {
    if (!businessGoal.trim() || generating) return;
    if (!creationStartedAt.current) {
      creationStartedAt.current = Date.now();
      logEvalEvent({ eventType: 'creation_started' }).catch(() => {});
    }
    setGenerating(true);
    setError('');
    setLlmWarning('');
    try {
      const draft = await generateHypothesis(experimentId, {
        businessGoal: businessGoal.trim(),
        context: context.trim(),
      });
      setEditableHypothesis(draft.hypothesis || '');
      setEditableName(draft.suggestedName || '');
      setEditableVariantA(draft.suggestedVariantAName || '');
      setEditableVariantB(draft.suggestedVariantBName || '');
      setHasDraft(true);
    } catch (e) {
      if (e.code === 'LLM_UNAVAILABLE') {
        setLlmWarning('LLM unavailable — enter hypothesis manually.');
      } else if (e.code === 'VALIDATION_ERROR') {
        setLlmWarning(e.message);
      } else {
        setError(e.message);
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleSave = async () => {
    if (!editableHypothesis.trim() || saving) return;
    setSaving(true);
    setError('');
    try {
      await saveHypothesis(experimentId, {
        hypothesis: editableHypothesis.trim(),
        name: editableName.trim() || undefined,
        variantAName: editableVariantA.trim() || undefined,
        variantBName: editableVariantB.trim() || undefined,
      });
      await onSaved?.();
      setHasDraft(false);
      if (creationStartedAt.current) {
        const durationMs = Date.now() - creationStartedAt.current;
        logEvalEvent({
          eventType: 'creation_completed',
          durationMs,
          payload: { durationMs },
        }).catch(() => {});
        creationStartedAt.current = null;
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="drawer-section hypothesis-panel">
      <h3>Hypothesis</h3>
      <label className="field-label" htmlFor="business-goal">Business goal *</label>
      <textarea
        id="business-goal"
        className="hypothesis-textarea drawer-input"
        rows={3}
        maxLength={GOAL_MAX}
        value={businessGoal}
        onChange={(e) => setBusinessGoal(e.target.value)}
        placeholder="Increase checkout conversion on mobile"
        disabled={generating || saving}
      />
      <p className="char-count">{businessGoal.length}/{GOAL_MAX}</p>

      {!showContext ? (
        <button
          type="button"
          className="btn btn-ghost btn-sm context-toggle"
          onClick={() => setShowContext(true)}
        >
          + Add context (optional)
        </button>
      ) : (
        <>
          <label className="field-label" htmlFor="hypothesis-context">Context</label>
          <textarea
            id="hypothesis-context"
            className="hypothesis-textarea drawer-input"
            rows={2}
            value={context}
            onChange={(e) => setContext(e.target.value)}
            disabled={generating || saving}
          />
        </>
      )}

      <button
        type="button"
        className="btn btn-secondary drawer-action"
        onClick={handleGenerate}
        disabled={!businessGoal.trim() || generating || saving}
      >
        {generating ? 'Generating…' : 'Generate hypothesis'}
      </button>

      {llmWarning && <p className="warning-inline">{llmWarning}</p>}

      {(hasDraft || editableHypothesis) && (
        <div className="draft-panel">
          <p className="draft-label">Draft</p>
          <label className="field-label" htmlFor="exp-name">Experiment name</label>
          <input
            id="exp-name"
            className="drawer-input"
            value={editableName}
            onChange={(e) => setEditableName(e.target.value)}
            disabled={saving}
          />
          <label className="field-label" htmlFor="hypothesis-text">Hypothesis</label>
          <textarea
            id="hypothesis-text"
            className="hypothesis-textarea drawer-input"
            rows={3}
            value={editableHypothesis}
            onChange={(e) => setEditableHypothesis(e.target.value)}
            disabled={saving}
          />
          <div className="drawer-field-row">
            <div>
              <label className="field-label" htmlFor="variant-a-name">Variant A name</label>
              <input
                id="variant-a-name"
                className="drawer-input"
                value={editableVariantA}
                onChange={(e) => setEditableVariantA(e.target.value)}
                disabled={saving}
              />
            </div>
            <div>
              <label className="field-label" htmlFor="variant-b-name">Variant B name</label>
              <input
                id="variant-b-name"
                className="drawer-input"
                value={editableVariantB}
                onChange={(e) => setEditableVariantB(e.target.value)}
                disabled={saving}
              />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-primary drawer-action"
            onClick={handleSave}
            disabled={!editableHypothesis.trim() || saving}
          >
            {saving ? 'Saving…' : 'Accept & save'}
          </button>
        </div>
      )}
    </section>
  );
}
