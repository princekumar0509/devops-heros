const CARDS = [
  { key: 'open', label: 'Open', tone: 'blue', hint: 'Waiting for an agent' },
  { key: 'inProgress', label: 'In progress', tone: 'violet', hint: 'Being worked on' },
  { key: 'urgentOpen', label: 'Urgent & active', tone: 'red', hint: 'Needs attention now' },
  { key: 'unassigned', label: 'Unassigned', tone: 'amber', hint: 'No owner yet' },
  { key: 'resolved', label: 'Resolved', tone: 'green', hint: 'Fixed, awaiting close' },
];

export default function StatCards({ stats }) {
  return (
    <section className="stats" aria-label="Ticket summary">
      {CARDS.map((card) => (
        <div key={card.key} className={`stat tone-${card.tone}`}>
          <small>{card.label}</small>
          <strong>{stats[card.key] ?? 0}</strong>
          <span>{card.hint}</span>
        </div>
      ))}
    </section>
  );
}
