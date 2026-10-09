import { test } from 'node:test';
import assert from 'node:assert/strict';
import { initials, label, timeAgo } from './format.js';
import { buildQuery } from './api.js';

test('label turns enum values into readable text', () => {
  assert.equal(label('IN_PROGRESS'), 'In Progress');
  assert.equal(label('FEATURE_REQUEST'), 'Feature Request');
});

test('timeAgo buckets durations', () => {
  const now = Date.parse('2026-01-01T12:00:00Z');
  assert.equal(timeAgo('2026-01-01T11:59:30Z', now), 'just now');
  assert.equal(timeAgo('2026-01-01T11:15:00Z', now), '45m ago');
  assert.equal(timeAgo('2026-01-01T07:00:00Z', now), '5h ago');
  assert.equal(timeAgo('2025-12-29T12:00:00Z', now), '3d ago');
});

test('initials uses first two words', () => {
  assert.equal(initials('Asha Verma'), 'AV');
  assert.equal(initials(''), '?');
});

test('buildQuery skips empty and ALL filters', () => {
  assert.equal(buildQuery({ status: 'ALL', priority: '', q: 'login' }), '?q=login');
  assert.equal(buildQuery({}), '');
});
