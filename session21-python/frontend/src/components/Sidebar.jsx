export const VIEWS = [
  { id: 'all', title: 'All tickets', icon: '▤', filters: {} },
  { id: 'active', title: 'Active queue', icon: '◷', filters: {}, predicate: (t) => t.status === 'OPEN' || t.status === 'IN_PROGRESS' },
  { id: 'unassigned', title: 'Unassigned', icon: '◌', filters: {}, predicate: (t) => !t.agent && t.status !== 'RESOLVED' && t.status !== 'CLOSED' },
  { id: 'urgent', title: 'Urgent', icon: '⚑', filters: { priority: 'URGENT' } },
  { id: 'resolved', title: 'Resolved', icon: '✓', filters: { status: 'RESOLVED' } },
];

const counts = (stats) => ({
  all: stats.total,
  active: stats.open + stats.inProgress,
  unassigned: stats.unassigned,
  urgent: stats.urgentOpen,
  resolved: stats.resolved,
});

export default function Sidebar({ view, onSelect, stats, open, onClose }) {
  const badge = counts(stats);
  return (
    <>
      <div className={`scrim ${open ? 'show' : ''}`} onClick={onClose} />
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            🎧
          </span>
          <div>
            <b>HelpDesk</b>
            <small>Customer support · v2 live demo</small>
          </div>
        </div>

        <p className="nav-label">Views</p>
        <nav>
          {VIEWS.map((v) => (
            <button key={v.id} className={view === v.id ? 'active' : ''} onClick={() => onSelect(v.id)}>
              <span className="nav-icon">{v.icon}</span>
              <span>{v.title}</span>
              <span className="count">{badge[v.id] ?? 0}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar-foot">
          <p className="nav-label">Delivery pipeline</p>
          <ol className="pipeline">
            {['Test', 'Build', 'Scan', 'Push', 'Deploy'].map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
          <p className="build">
            API <code>/docs</code> · metrics <code>/metrics</code>
          </p>
        </div>
      </aside>
    </>
  );
}
