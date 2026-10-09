import { CATEGORIES, label } from '../format.js';

export default function CategoryBreakdown({ byCategory, total }) {
  return (
    <aside className="card breakdown">
      <div className="card-head">
        <div>
          <h2>By category</h2>
          <p className="muted">Where requests come from</p>
        </div>
      </div>
      <ul>
        {CATEGORIES.map((category) => {
          const count = byCategory?.[category] ?? 0;
          const pct = total ? Math.round((count / total) * 100) : 0;
          return (
            <li key={category}>
              <div className="row">
                <span>{label(category)}</span>
                <span className="muted">
                  {count} · {pct}%
                </span>
              </div>
              <div className="bar" role="presentation">
                <i className={`cat-${category.toLowerCase()}`} style={{ width: `${pct}%` }} />
              </div>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}
