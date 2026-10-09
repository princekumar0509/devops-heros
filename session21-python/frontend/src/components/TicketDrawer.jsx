import { useCallback, useEffect, useState } from 'react';
import { api } from '../api.js';
import { PRIORITIES, STATUSES, initials, label, timeAgo } from '../format.js';
import { PriorityBadge, StatusBadge } from './Badges.jsx';

export default function TicketDrawer({ ticketId, onClose, onChanged, onDeleted }) {
  const [ticket, setTicket] = useState(null);
  const [comments, setComments] = useState([]);
  const [error, setError] = useState('');
  const [reply, setReply] = useState({ author: '', body: '', internal: false });
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const [t, c] = await Promise.all([api.get(ticketId), api.comments(ticketId)]);
      setTicket(t);
      setComments(c);
      setReply((r) => ({ ...r, author: r.author || t.agent || '' }));
    } catch (e) {
      setError(e.message);
    }
  }, [ticketId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);

  const change = async (changes) => {
    try {
      setError('');
      setTicket(await api.update(ticketId, changes));
      onChanged();
    } catch (e) {
      setError(e.message);
    }
  };

  const sendReply = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      setError('');
      await api.addComment(ticketId, reply);
      setReply((r) => ({ ...r, body: '' }));
      await refresh();
      onChanged();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!window.confirm(`Delete ticket #${ticketId}? This cannot be undone.`)) return;
    try {
      await api.remove(ticketId);
      onDeleted();
    } catch (e) {
      setError(e.message);
    }
  };

  return (
    <div className="drawer-backdrop" onClick={onClose}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()} aria-label="Ticket details">
        <div className="drawer-head">
          <p className="eyebrow">Ticket #{ticketId}</p>
          <button className="ghost close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <div className="alert">{error}</div>}
        {!ticket ? (
          <div className="empty">Loading…</div>
        ) : (
          <>
            <h2 className="drawer-title">{ticket.subject}</h2>
            <div className="badges">
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              <span className="badge neutral">{label(ticket.category)}</span>
            </div>

            <dl className="meta">
              <dt>Requester</dt>
              <dd>
                {ticket.requester_name}
                <small className="muted">{ticket.requester_email}</small>
              </dd>
              <dt>Opened</dt>
              <dd>{new Date(ticket.created_at).toLocaleString()}</dd>
              {ticket.resolved_at && (
                <>
                  <dt>Resolved</dt>
                  <dd>{new Date(ticket.resolved_at).toLocaleString()}</dd>
                </>
              )}
            </dl>

            {ticket.description && <p className="description">{ticket.description}</p>}

            <div className="controls">
              <label>
                Status
                <select value={ticket.status} onChange={(e) => change({ status: e.target.value })}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {label(s)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Priority
                <select value={ticket.priority} onChange={(e) => change({ priority: e.target.value })}>
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {label(p)}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Agent
                <input
                  defaultValue={ticket.agent ?? ''}
                  key={ticket.agent ?? ''}
                  placeholder="Unassigned"
                  onBlur={(e) => {
                    const agent = e.target.value.trim() || null;
                    if (agent !== ticket.agent) change({ agent });
                  }}
                />
              </label>
            </div>

            <h3>Conversation</h3>
            <ul className="thread">
              {comments.length === 0 && <li className="muted">No replies yet.</li>}
              {comments.map((c) => (
                <li key={c.id} className={c.internal ? 'internal' : ''}>
                  <span className="avatar">{initials(c.author)}</span>
                  <div>
                    <p className="who">
                      <b>{c.author}</b> <span className="muted">{timeAgo(c.created_at)}</span>
                      {c.internal && <span className="badge neutral">Internal note</span>}
                    </p>
                    <p>{c.body}</p>
                  </div>
                </li>
              ))}
            </ul>

            <form className="reply" onSubmit={sendReply}>
              <input
                required
                placeholder="Your name"
                value={reply.author}
                onChange={(e) => setReply({ ...reply, author: e.target.value })}
                aria-label="Reply author"
              />
              <textarea
                required
                placeholder={reply.internal ? 'Private note for the team…' : 'Reply to the customer…'}
                value={reply.body}
                onChange={(e) => setReply({ ...reply, body: e.target.value })}
                aria-label="Reply body"
              />
              <div className="reply-actions">
                <label className="check">
                  <input
                    type="checkbox"
                    checked={reply.internal}
                    onChange={(e) => setReply({ ...reply, internal: e.target.checked })}
                  />
                  Internal note
                </label>
                <button className="primary" disabled={busy}>
                  {busy ? 'Sending…' : reply.internal ? 'Add note' : 'Send reply'}
                </button>
              </div>
            </form>

            <button className="danger" onClick={remove}>
              Delete ticket
            </button>
          </>
        )}
      </aside>
    </div>
  );
}
