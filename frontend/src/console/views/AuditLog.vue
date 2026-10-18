<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <section class="mf-card toolbar">
      <div class="filters">
        <div>
          <label class="mf-label" id="a-actor">Actor</label>
          <select id="a-actor" v-model="actor" class="mf-select" aria-labelledby="a-actor">
            <option value="">All actors</option>
            <option v-for="a in actors" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
        <div>
          <label class="mf-label" id="a-action">Action</label>
          <select id="a-action" v-model="action" class="mf-select" aria-labelledby="a-action">
            <option value="">All actions</option>
            <option v-for="a in actionNames" :key="a" :value="a">{{ a }}</option>
          </select>
        </div>
        <div class="grow">
          <label class="mf-label" id="a-q">Search</label>
          <input id="a-q" v-model="query" class="mf-input" aria-labelledby="a-q" placeholder="Search actions, targets, reasons…" />
        </div>
      </div>
      <p class="semantics">Local-only rows are browser records, not durable backend audit entries.</p>
    </section>

    <section class="mf-card">
      <div v-if="loading" class="pad"><div class="mf-skeleton" style="height: 200px"></div></div>
      <EmptyState v-else-if="!filtered.length" icon="history" title="No audit events" hint="Analyst actions and backend reports will appear here." />
      <div v-else class="mf-table-responsive">
        <table class="mf-table">
          <thead>
            <tr>
              <th>Time</th><th>Actor</th><th>Target</th><th>Action</th><th>Transition</th><th>Reason</th><th>Source</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in filtered" :key="a.id || a.at + a.action">
              <td class="mf-mono">{{ fmtTime(a.at) }}</td>
              <td>{{ a.actor }}</td>
              <td class="mf-mono">{{ a.target }}</td>
              <td>{{ a.action }}</td>
              <td class="mf-mono dim">{{ a.from || '—' }} → {{ a.to || '—' }}</td>
              <td>{{ a.reason || '—' }}</td>
              <td><MfBadge :tone="a.durable === false ? 'amber' : 'green'" :label="a.durable === false ? 'local only' : 'backend'" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import EmptyState from '../components/EmptyState.vue'
import DemoBanner from '../components/DemoBanner.vue'
import { isDemoMode } from '../demoMode.js'
import { probeConnection } from '../connection.js'
import { fetchMonitorQueue } from '../api.js'
import { DEMO_ACTIONS } from '../fixtures/demoClaims.js'
import { listLocalActions } from '../analystStore.js'
import { toast } from '../toasts.js'

const demoMode = isDemoMode()
const loading = ref(true)
const entries = ref([])
const actor = ref('')
const action = ref('')
const query = ref('')

const actors = computed(() => [...new Set(entries.value.map((e) => e.actor))])
const actionNames = computed(() => [...new Set(entries.value.map((e) => e.action))])
const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return entries.value.filter((e) =>
    (!actor.value || e.actor === actor.value) &&
    (!action.value || e.action === action.value) &&
    (!q || JSON.stringify(e).toLowerCase().includes(q)))
})
function fmtTime(t) { try { return new Date(t).toLocaleString() } catch { return t || '—' } }

onMounted(async () => {
  try {
    const local = listLocalActions()
    if (demoMode) {
      entries.value = [...DEMO_ACTIONS.map((a, i) => ({ id: `demo-${i}`, durable: false, ...a })), ...local]
    } else {
      await probeConnection()
      const q = await fetchMonitorQueue()
      const backend = (q.actions || []).map((a, i) => ({ id: `backend-${i}`, durable: true, ...a }))
      entries.value = [...local, ...backend]
    }
  } catch (e) { toast(e.message || 'Load failed', 'error') }
  finally { loading.value = false }
})
</script>

<style scoped>
.toolbar { padding: 14px 16px; margin-bottom: 12px; }
.filters { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.grow { flex: 1; min-width: 200px; }
.grow .mf-input { width: 100%; }
.semantics { font-size: 12px; color: #6b7280; margin: 10px 0 0; }
.pad { padding: 16px; }
.dim { color: #6b7280; font-size: 12px; }
</style>
