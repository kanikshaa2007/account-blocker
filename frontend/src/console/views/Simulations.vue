<template>
  <div>
    <div v-if="error" class="mf-error-bar">
      <MfIcon name="alert" size="15" /><span>{{ error }}</span>
      <button class="mf-btn" @click="load">Retry</button>
    </div>
    <p class="semantics">Simulated social environments. Outputs are forecasts, never real-world observations.</p>

    <section class="mf-card">
      <div v-if="loading" class="pad"><div class="mf-skeleton" style="height: 200px"></div></div>
      <EmptyState v-else-if="!sims.length" icon="sim" title="No simulations yet" hint="Create and run one from the MiroFish studio first.">
        <router-link to="/process/new" class="mf-btn">Open studio</router-link>
      </EmptyState>
      <div v-else class="mf-table-responsive">
        <table class="mf-table">
          <thead>
            <tr>
              <th>Simulation</th><th>Status</th><th>Round</th><th>Updated</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in sims" :key="s.simulation_id">
              <td class="mf-mono">{{ s.simulation_id }}<br /><span class="dim">{{ s.project_id }}</span></td>
              <td><MfBadge :tone="simTone(s.status)" :label="s.status || '—'" /></td>
              <td class="mf-mono">{{ s.current_round ?? '—' }}</td>
              <td class="mf-mono dim">{{ fmtTime(s.updated_at) }}</td>
              <td class="acts">
                <button class="mf-btn" :disabled="detailLoading === s.simulation_id" @click="inspect(s.simulation_id)">Inspect</button>
                <router-link :to="`/simulation/${s.simulation_id}`" class="mf-btn">Open in studio</router-link>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="detail" class="mf-card pad detail">
      <h2 class="card-title">Run detail · <span class="mf-mono">{{ detailId }}</span></h2>
      <p class="hint">Raw run-status payload returned by the backend.</p>
      <pre class="mf-mono dump">{{ JSON.stringify(detail, null, 2) }}</pre>
      <button class="mf-btn" @click="detail = null; detailId = ''">Close</button>
    </section>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import MfIcon from '../components/MfIcon.vue'
import EmptyState from '../components/EmptyState.vue'
import { probeConnection } from '../connection.js'
import { fetchSimulations, fetchRunStatusDetail } from '../api.js'
import { toast } from '../toasts.js'

const loading = ref(true)
const error = ref('')
const sims = ref([])
const detail = ref(null)
const detailId = ref('')
const detailLoading = ref('')

function simTone(s) {
  return { completed: 'green', running: 'blue', ready: 'blue', failed: 'red', preparing: 'amber' }[s] || 'gray'
}
function fmtTime(t) { try { return t ? new Date(t).toLocaleString() : '—' } catch { return '—' } }

async function load() {
  loading.value = true
  error.value = ''
  try {
    await probeConnection()
    sims.value = await fetchSimulations()
  } catch (e) {
    error.value = e.message || 'Load failed'
    toast(error.value, 'error')
  } finally {
    loading.value = false
  }
}

async function inspect(id) {
  detailLoading.value = id
  try {
    detail.value = await fetchRunStatusDetail(id)
    detailId.value = id
  } catch (e) {
    toast(e.message || 'Detail failed', 'error')
  } finally {
    detailLoading.value = ''
  }
}

onMounted(load)
</script>

<style scoped>
.semantics { font-size: 12px; color: #6b7280; margin: 0 0 12px; }
.pad { padding: 16px; }
.dim { color: #6b7280; font-size: 11px; }
.acts { display: flex; gap: 6px; white-space: nowrap; }
.detail { margin-top: 12px; }
.hint { font-size: 12px; color: #6b7280; }
.dump { background: #0b1322; color: #d1fae5; font-size: 11px; padding: 12px; border-radius: 4px; overflow: auto; max-height: 320px; }
.mf-error-bar { margin-bottom: 12px; }
</style>
