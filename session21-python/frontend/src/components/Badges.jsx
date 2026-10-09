import { label } from '../format.js';

export const StatusBadge = ({ status }) => <span className={`badge status-${status.toLowerCase()}`}>{label(status)}</span>;

export const PriorityBadge = ({ priority }) => (
  <span className={`badge priority-${priority.toLowerCase()}`}>{label(priority)}</span>
);
