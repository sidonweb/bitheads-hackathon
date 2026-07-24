import CopilotIcon from './CopilotIcon.jsx';
import { PencilIcon, PinIcon, TrashIcon } from './Icons.jsx';

function formatTime(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

export default function SessionSidebar({
  sessions,
  activeSessionId,
  onSelect,
  onNew,
  onRename,
  onDelete,
  onTogglePin,
}) {
  return (
    <aside className="session-sidebar">
      <div className="session-sidebar-head">
        <div className="session-brand">
          <CopilotIcon size={22} />
          <span>Chats</span>
        </div>
        <button type="button" className="new-chat-btn" onClick={onNew}>
          + New Test
        </button>
      </div>

      <div className="session-list">
        {sessions.map((session) => {
          const active = session.id === activeSessionId;
          return (
            <div key={session.id} className={`session-row${active ? ' active' : ''}`}>
              <button
                type="button"
                className="session-main"
                onClick={() => onSelect(session.id)}
                title={session.title}
              >
                <span className="session-title">
                  {session.pinned && <span className="pin-mark" aria-label="Pinned">Pinned</span>}
                  {session.title}
                </span>
                <span className="session-meta">
                  {session.messages.length} messages - {formatTime(session.updatedAt)}
                </span>
              </button>
              <div className="session-actions">
                <button
                  type="button"
                  className={`session-icon${session.pinned ? ' pinned' : ''}`}
                  onClick={() => onTogglePin(session.id)}
                  aria-label={session.pinned ? 'Unpin chat' : 'Pin chat'}
                  title={session.pinned ? 'Unpin' : 'Pin'}
                >
                  <PinIcon filled={session.pinned} />
                </button>
                <button
                  type="button"
                  className="session-icon"
                  onClick={() => onRename(session.id)}
                  aria-label="Rename chat"
                  title="Rename"
                >
                  <PencilIcon />
                </button>
                <button
                  type="button"
                  className="session-icon danger"
                  onClick={() => onDelete(session.id)}
                  aria-label="Delete chat"
                  title="Delete"
                >
                  <TrashIcon />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
