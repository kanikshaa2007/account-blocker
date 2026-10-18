import service from '../api/index.js'

// GET /api/report/list exists in backend; the frontend report.js client lacks it.
export async function listReportsShim(limit = 50) {
  const res = await service.get('/api/report/list', { params: { limit } })
  const data = res.data ?? res
  return Array.isArray(data) ? data : data.reports ?? data.items ?? []
}
