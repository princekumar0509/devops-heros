import { useState } from 'react';
import { api } from '../api.js';
import { CATEGORIES, PRIORITIES, label } from '../format.js';

export default function NewTicketModal({ onClose, onCreated }) {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    const payload = Object.fromEntries(form.entries());
    payload.agent = payload.agent?.trim() || null;
    setBusy(true);
    try {
      onCreated(await api.create(payload));
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <form className="modal" onSubmit={submit} onClick={(e) => e.stopPropagation()}>
        <div className="modal-head">
          <div>
            <p className="eyebrow">New ticket</p>
            <h2>Log a support request</h2>
          </div>
          <button type="button" className="ghost close" onClick={onClose} aria-label="Close">
            ×
          </button>
        </div>

        {error && <div className="alert">{error}</div>}

        <label>
          Subject
          <input name="subject" required minLength={3} maxLength={200} placeholder="e.g. Checkout page returns 500" autoFocus />
        </label>
        <label>
          Description
          <textarea name="description" placeholder="Steps to reproduce, expected vs actual…" />
        </label>
        <div className="form-row">
          <label>
            Requester name
            <input name="requester_name" required placeholder="Customer name" />
          </label>
          <label>
            Requester email
            <input name="requester_email" type="email" required placeholder="customer@example.com" />
          </label>
        </div>
        <div className="form-row three">
          <label>
            Category
            <select name="category" defaultValue="GENERAL">
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {label(c)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Priority
            <select name="priority" defaultValue="MEDIUM">
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {label(p)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Agent (optional)
            <input name="agent" placeholder="Unassigned" />
          </label>
        </div>
        <button className="primary full" disabled={busy}>
          {busy ? 'Creating…' : 'Create ticket'}
        </button>
      </form>
    </div>
  );
}
