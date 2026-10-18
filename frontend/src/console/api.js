// Production adapters: confirmed backend endpoints only.
// Anything not served by the backend comes from fixtures/demoClaims.js (demo mode).
import service from '../api/index.js'
import { listReportsShim } from './reportShim.js'

export { fetchMonitorQueue, approveMonitorJob, ingestLiveFeed } from '../api/index.js'

export async function fetchHealth() {
  const res = await service.get('/health', { timeout: 8000 })
  return res
}

export async function fetchSimulations(projectId) {
  const res = await service.get('/api/simulation/list', { params: { project_id: projectId } })
  const data = res.data ?? res
  return Array.isArray(data) ? data : data.simulations ?? data.items ?? []
}

export async function fetchReports() {
  return listReportsShim()
}

export async function fetchRunStatus(simulationId) {
  const res = await service.get(`/api/simulation/${simulationId}/run-status`)
  return res.data ?? res
}

export async function fetchRunStatusDetail(simulationId) {
  const res = await service.get(`/api/simulation/${simulationId}/run-status/detail`)
  return res.data ?? res
}
