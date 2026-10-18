import { ref } from 'vue'
import service from '../api/index.js'

// Shared backend connection probe for the console shell.
export const connection = {
  status: ref('offline'), // online | degraded | offline
  detail: ref(''),
  base: ref(service.defaults.baseURL || '')
}

let probed = false
export async function probeConnection() {
  try {
    await service.get('/health', { timeout: 8000 })
    connection.status.value = 'online'
    connection.detail.value = ''
  } catch (err) {
    connection.status.value = 'offline'
    connection.detail.value = err?.message || 'unreachable'
  }
  probed = true
  return connection.status.value
}
export function wasProbed() { return probed }
