import axios from 'axios'

// Relative base by default — the Vite dev server proxies /api to the FastAPI backend
// (see vite.config.js). Override with VITE_API_BASE for a deployed backend.
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  headers: { 'Content-Type': 'application/json' },
})

/** Pull a human-friendly message out of an axios error (FastAPI puts it in `detail`). */
export function detail(err) {
  return err?.response?.data?.detail || err?.message || 'Something went wrong'
}

// ── Feature #1 + #2 — intake + adaptive questioning (WIRED) ──────────────────────

export async function startTriage() {
  // → { session_id, question, progress }
  const { data } = await api.post('/api/triage/start')
  return data
}

export async function respond(sessionId, message) {
  // → { session_id, question, rationale, is_complete, progress, fail_closed }
  const { data } = await api.post('/api/triage/respond', {
    session_id: sessionId,
    message,
  })
  return data
}

// ── Feature #3 + #5 — NOT integrated yet (backends return 501). Wired here so the UI
//    lights up the moment those features land. ──────────────────────────────────

export async function assessUrgency(sessionId) {
  const { data } = await api.post('/api/triage/assess', { session_id: sessionId })
  return data
}

export async function getSummary(sessionId) {
  const { data } = await api.post('/api/summary', { session_id: sessionId })
  return data
}

export default api
