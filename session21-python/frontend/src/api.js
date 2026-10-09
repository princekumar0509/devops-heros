const BASE = '/api/tickets';

async function request(path, options = {}) {
  const response = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) detail = body.detail.map((e) => `${e.loc.at(-1)}: ${e.msg}`).join(', ');
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return response.status === 204 ? null : response.json();
}

export function buildQuery(filters) {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value && value !== 'ALL') params.set(key, value);
  }
  const query = params.toString();
  return query ? `?${query}` : '';
}

export const api = {
  list: (filters = {}) => request(buildQuery(filters)),
  stats: () => request('/stats'),
  get: (id) => request(`/${id}`),
  create: (ticket) => request('', { method: 'POST', body: JSON.stringify(ticket) }),
  update: (id, changes) => request(`/${id}`, { method: 'PUT', body: JSON.stringify(changes) }),
  remove: (id) => request(`/${id}`, { method: 'DELETE' }),
  comments: (id) => request(`/${id}/comments`),
  addComment: (id, comment) => request(`/${id}/comments`, { method: 'POST', body: JSON.stringify(comment) }),
};
