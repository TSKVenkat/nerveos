const API_BASE = '/api';

async function fetchJSON(url, options = {}) {
  const resp = await fetch(`${API_BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!resp.ok) throw new Error(`API ${resp.status}: ${resp.statusText}`);
  return resp.json();
}

// ── Dashboard ────────────────────────────────────
export const getDashboard = () => fetchJSON('/dashboard/');
export const getAnomalies = () => fetchJSON('/dashboard/anomalies');
export const recordMetric = (data) => fetchJSON('/dashboard/metrics', { method: 'POST', body: JSON.stringify(data) });
export const askQuestion = (question) => fetchJSON('/dashboard/ask', { method: 'POST', body: JSON.stringify({ question }) });
export const getMorningBriefing = () => fetchJSON('/dashboard/briefing', { method: 'POST' });

// ── Market Intel ─────────────────────────────────
export const getCompetitors = () => fetchJSON('/market/competitors');
export const addCompetitor = (data) => fetchJSON('/market/competitors', { method: 'POST', body: JSON.stringify(data) });
export const deleteCompetitor = (id) => fetchJSON(`/market/competitors/${id}`, { method: 'DELETE' });
export const getTopics = () => fetchJSON('/market/topics');
export const addTopic = (data) => fetchJSON('/market/topics', { method: 'POST', body: JSON.stringify(data) });
export const getReports = (limit = 30) => fetchJSON(`/market/reports?limit=${limit}`);
export const markReportRead = (id) => fetchJSON(`/market/reports/${id}/read`, { method: 'POST' });
export const runMarketScan = () => fetchJSON('/market/scan', { method: 'POST' });
export const scanCompetitor = (id) => fetchJSON(`/market/scan/competitor/${id}`, { method: 'POST' });
export const getDigest = (days = 1) => fetchJSON(`/market/digest?days=${days}`);
export const quickSearch = (q) => fetchJSON(`/market/search?q=${encodeURIComponent(q)}`);
export const getTrends = (keywords) => fetchJSON(`/market/trends?keywords=${encodeURIComponent(keywords)}`);
export const getTrending = (country = 'india') => fetchJSON(`/market/trends/trending?country=${country}`);
export const getStockInfo = (ticker) => fetchJSON(`/market/finance/${ticker}`);
export const getStockHistory = (ticker, period = '3mo') => fetchJSON(`/market/finance/${ticker}/history?period=${period}`);
export const getStockAnomalies = (ticker) => fetchJSON(`/market/finance/${ticker}/anomalies`);

// ── Email ────────────────────────────────────────
export const getEmailAccounts = () => fetchJSON('/email/accounts');
export const addEmailAccount = (data) => fetchJSON('/email/accounts', { method: 'POST', body: JSON.stringify(data) });
export const getInbox = (limit = 30, category = null) => {
  let url = `/email/inbox?limit=${limit}`;
  if (category) url += `&category=${category}`;
  return fetchJSON(url);
};
export const getInboxSummary = () => fetchJSON('/email/inbox/summary');
export const getEmailDetail = (id) => fetchJSON(`/email/inbox/${id}`);
export const generateDrafts = (emailId, tones) => fetchJSON(`/email/inbox/${emailId}/draft`, { method: 'POST', body: JSON.stringify({ tones }) });
export const getDrafts = () => fetchJSON('/email/drafts');
export const approveDraft = (id) => fetchJSON(`/email/drafts/${id}/approve`, { method: 'POST' });
export const rejectDraft = (id) => fetchJSON(`/email/drafts/${id}/reject`, { method: 'POST' });
export const syncEmails = () => fetchJSON('/email/sync', { method: 'POST' });
export const getFollowUps = () => fetchJSON('/email/follow-ups');
export const getContacts = () => fetchJSON('/email/contacts');
export const addContact = (data) => fetchJSON('/email/contacts', { method: 'POST', body: JSON.stringify(data) });
export const updateContact = (id, data) => fetchJSON(`/email/contacts/${id}`, { method: 'PUT', body: JSON.stringify(data) });

// ── Actions & Guardrails ─────────────────────────
export const getPendingActions = () => fetchJSON('/actions/pending');
export const approveAction = (id) => fetchJSON(`/actions/${id}/approve`, { method: 'POST' });
export const rejectAction = (id, reason = '') => fetchJSON(`/actions/${id}/reject`, { method: 'POST', body: JSON.stringify({ reason }) });
export const getAuditTrail = () => fetchJSON('/actions/audit');
export const getPolicies = () => fetchJSON('/actions/policies');
export const addPolicy = (data) => fetchJSON('/actions/policies', { method: 'POST', body: JSON.stringify(data) });
export const deletePolicy = (id) => fetchJSON(`/actions/policies/${id}`, { method: 'DELETE' });

// ── Settings ─────────────────────────────────────
export const getHealth = () => fetchJSON('/settings/health');
export const getConfig = () => fetchJSON('/settings/config');
