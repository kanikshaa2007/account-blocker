import axios from 'axios'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001',
  timeout: 300000,
  headers: { 'Content-Type': 'application/json' }
})

service.interceptors.response.use(
  (response) => {
    const res = response.data
    if (!res.success && res.success !== undefined) {
      return Promise.reject(new Error(res.error || res.message || 'Error'))
    }
    return res
  },
  (error) => {
    const apiError = error.response?.data?.error || error.response?.data?.message
    if (typeof apiError === 'string' && apiError) {
      error.message = apiError
    }
    return Promise.reject(error)
  }
)

export function fetchMonitorQueue() {
  return service.get('/api/monitor/queue').then((res) => res.data ?? res)
}

export function approveMonitorJob(job_id, reviewer = 'reviewer') {
  return service.post('/api/monitor/approve', { job_id, reviewer }).then((res) => res.data ?? res)
}

export function ingestLiveFeed(queries, limit = 10) {
  return service.post('/api/monitor/ingest', { queries, limit }).then((res) => res.data ?? res)
}

export default service
