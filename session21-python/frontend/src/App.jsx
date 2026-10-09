import { useCallback, useEffect, useState } from 'react';
import { api } from './api.js';
import Sidebar, { VIEWS } from './components/Sidebar.jsx';
import StatCards from './components/StatCards.jsx';
import CategoryBreakdown from './components/CategoryBreakdown.jsx';
import TicketTable from './components/TicketTable.jsx';
import TicketDrawer from './components/TicketDrawer.jsx';
import NewTicketModal from './components/NewTicketModal.jsx';
import { PRIORITIES, STATUSES, label } from './format.js';

const EMPTY_STATS = { total: 0, open: 0, inProgress: 0, resolved: 0, closed: 0, urgentOpen: 0, unassigned: 0, byCategory: {} };

export default function App() {
  const [view, setView] = useState('all');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState(EMPTY_STATS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedId, setSelectedId] = useState(null);
  const [showNew, setShowNew] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const activeView = VIEWS.find((v) => v.id === view);

  const load = useCallback(async () => {
    try {
      setError('');
      const filters = { status: statusFilter, priority: priorityFilter, q: search.trim(), ...activeView.filters };
      const [list, summary] = await Promise.all([api.list(filters), api.stats()]);
      setTickets(activeView.predicate ? list.filter(activeView.predicate) : list);
      setStats(summary);
    } catch (e) {
      setError(e.message === 'Failed to fetch' ? 'Cannot reach the HelpDesk API' : e.message);
    } finally {
      setLoading(false);
    }
  }, [activeView, statusFilter, priorityFilter, search]);

  useEffect(() => {
    const timer = setTimeout(load, 250); // debounce typing in the search box
    return () => clearTimeout(timer);
  }, [load]);

  const chooseView = (id) => {
    setView(id);
    setStatusFilter('ALL');
    setPriorityFilter('ALL');
    setSidebarOpen(false);
  };

  return (
    <div className="shell">
      <Sidebar view={view} onSelect={chooseView} stats={stats} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <main className="main">
        <header className="topbar">
          <button className="ghost menu-btn" onClick={() => setSidebarOpen(true)} aria-label="Open navigation">
            ☰
          </button>
          <div className="title-block">
            <p className="eyebrow">Support console</p>
            <h1>{activeView.title}</h1>
          </div>
          <div className="search">
            <span aria-hidden="true">⌕</span>
            <input
              type="search"
              placeholder="Search subject, requester, agent…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search tickets"
            />
          </div>
          <button className="primary" onClick={() => setShowNew(true)}>
            + New ticket
          </button>
        </header>

        {error && (
          <div className="alert" role="alert">
            <strong>Backend unavailable.</strong> {error}. Start PostgreSQL and the API, then{' '}
            <button className="link" onClick={load}>
              retry
            </button>
            .
          </div>
        )}

        <StatCards stats={stats} />

        <section className="workspace">
          <div className="card tickets-card">
            <div className="card-head">
              <div>
                <h2>Tickets</h2>
                <p className="muted">
                  {tickets.length} shown · {stats.total} total
                </p>
              </div>
              <div className="filters">
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} aria-label="Status filter">
                  <option value="ALL">All statuses</option>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>
                      {label(s)}
                    </option>
                  ))}
                </select>
                <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)} aria-label="Priority filter">
                  <option value="ALL">All priorities</option>
                  {PRIORITIES.map((p) => (
                    <option key={p} value={p}>
                      {label(p)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <TicketTable tickets={tickets} loading={loading} selectedId={selectedId} onSelect={setSelectedId} />
          </div>

          <CategoryBreakdown byCategory={stats.byCategory} total={stats.total} />
        </section>
      </main>

      {selectedId && (
        <TicketDrawer
          ticketId={selectedId}
          onClose={() => setSelectedId(null)}
          onChanged={load}
          onDeleted={() => {
            setSelectedId(null);
            load();
          }}
        />
      )}

      {showNew && (
        <NewTicketModal
          onClose={() => setShowNew(false)}
          onCreated={(ticket) => {
            setShowNew(false);
            setSelectedId(ticket.id);
            load();
          }}
        />
      )}
    </div>
  );
}
