import { useEffect, useRef } from 'react';

const COPY = {
  Scale: {
    title: 'Send 100% traffic to Variant B?',
    body: 'This will stop splitting traffic and show Variant B to all new users.',
    confirm: 'Apply',
    destructive: false,
  },
  Rollback: {
    title: 'Revert to 100% Variant A?',
    body: 'This will stop the test and route all traffic to the control.',
    confirm: 'Apply',
    destructive: true,
  },
};

export default function ApplyConfirmModal({
  open,
  decision,
  onConfirm,
  onCancel,
  loading,
}) {
  const cancelRef = useRef(null);

  useEffect(() => {
    if (open) cancelRef.current?.focus();
  }, [open]);

  useEffect(() => {
    if (!open || loading) return undefined;
    const onKey = (e) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, loading, onCancel]);

  if (!open || !decision) return null;

  const copy = COPY[decision.decision];
  if (!copy) return null;

  const handleBackdrop = () => {
    if (!loading) onCancel();
  };

  return (
    <div className="modal-backdrop" role="presentation" onClick={handleBackdrop}>
      <div
        className="dialog apply-confirm-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="apply-confirm-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="dialog-head">
          <h2 id="apply-confirm-title">{copy.title}</h2>
        </div>
        <p className="dialog-copy">{copy.body}</p>
        <div className="dialog-actions">
          <button
            type="button"
            className="btn btn-ghost"
            ref={cancelRef}
            onClick={onCancel}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            type="button"
            className={`btn ${copy.destructive ? 'btn-danger' : 'btn-primary'}`}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? 'Applying…' : copy.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}
