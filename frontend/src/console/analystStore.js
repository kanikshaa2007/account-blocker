// Local analyst workspace: notes + action log kept in localStorage.
// Explicitly non-durable: surfaced in UI as "local only, not a backend record".
const NOTES_KEY = 'mf-console-notes'
const LOG_KEY = 'mf-console-actions'

function read(key) {
  try { return JSON.parse(localStorage.getItem(key) || '{}') } catch { return {} }
}
function write(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)) } catch { /* storage unavailable */ }
}

export function getNote(id) { return read(NOTES_KEY)[id] || '' }
export function saveNote(id, text) {
  const all = read(NOTES_KEY)
  all[id] = text
  write(NOTES_KEY, all)
}

export function logAction(entry) {
  const all = read(LOG_KEY)
  const id = `local-${Date.now()}`
  all[id] = { id, at: new Date().toISOString(), durable: false, ...entry }
  write(LOG_KEY, all)
  return all[id]
}
export function listLocalActions() {
  return Object.values(read(LOG_KEY)).sort((a, b) => String(b.at).localeCompare(String(a.at)))
}
