import { PriorityBadge, StatusBadge } from './Badges.jsx';
import { label, timeAgo } from '../format.js';

export default function TicketTable({ tickets, loading, selectedId, onSelect }) {
  if (loading) return <div className="empty">Loading tickets…</div>;
  if (!tickets.length) return <div className="empty">No tickets match this view. 🎉</div>;

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Subject</th>
            <th className="hide-sm">Requester</th>
            <th>Priority</th>
            <th>Status</th>
            <th className="hide-sm">Agent</th>
            <th className="hide-sm">Updated</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <tr
              key={t.id}
              className={selectedId === t.id ? 'selected' : ''}
              onClick={() => onSelect(t.id)}
              onKeyDown={(e) => e.key === 'Enter' && onSelect(t.id)}
              tabIndex={0}
            >
              <td className="mono">{t.id}</td>
              <td>
                <b className="subject">{t.subject}</b>
                <small className="muted">
                  {label(t.category)}
                  {t.comment_count > 0 && ` · 💬 ${t.comment_count}`}
                </small>
              </td>
              <td className="hide-sm">{t.requester_name}</td>
              <td>
                <PriorityBadge priority={t.priority} />
              </td>
              <td>
                <StatusBadge status={t.status} />
              </td>
              <td className="hide-sm">{t.agent || <span className="muted">—</span>}</td>
              <td className="hide-sm muted">{timeAgo(t.updated_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
