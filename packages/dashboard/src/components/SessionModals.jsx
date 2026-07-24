import { useEffect, useState } from 'react';

export function RenameSessionModal({ session, onCancel, onConfirm }) {
  const [title, setTitle] = useState(session?.title || '');

  useEffect(() => {
    setTitle(session?.title || '');
  }, [session]);

  if (!session) return null;

  const submit = (event) => {
    event.preventDefault();
    const nextTitle = title.trim();
    if (nextTitle) onConfirm(nextTitle);
  };

  return (
    <div className="modal-backdrop" role="presentation">
      <form className="dialog" onSubmit={submit}>
        <div className="dialog-head">
          <h2>Rename Chat</h2>
          <button type="button" className="icon-btn" onClick={onCancel} aria-label="Close">X</button>
        </div>
        <label className="dialog-field">
          <span>Chat name</span>
          <input
            autoFocus
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={80}
          />
        </label>
        <div className="dialog-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
          <button type="submit" className="btn btn-primary" disabled={!title.trim()}>Save</button>
        </div>
      </form>
    </div>
  );
}

export function DeleteSessionModal({ session, onCancel, onConfirm }) {
  if (!session) return null;

  return (
    <div className="modal-backdrop" role="presentation">
      <div className="dialog">
        <div className="dialog-head">
          <h2>Delete Chat</h2>
          <button type="button" className="icon-btn" onClick={onCancel} aria-label="Close">X</button>
        </div>
        <p className="dialog-copy">
          Delete "{session.title}" from this browser's chat history?
        </p>
        <div className="dialog-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>Cancel</button>
          <button type="button" className="btn btn-danger" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
}
