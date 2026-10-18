<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <div v-if="error && !demoMode" class="mf-error-bar">
      <MfIcon name="alert" size="15" /><span>{{ error }}</span>
      <button class="mf-btn" @click="load">Retry</button>
    </div>

    <section class="mf-card toolbar">
      <div class="filters">
        <div>
          <label class="mf-label" id="q-tier">Priority</label>
          <select id="q-tier" v-model="tier" class="mf-select" aria-labelledby="q-tier">
            <option value="">All priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="normal">Normal</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label class="mf-label" id="q-status">Status</label>
          <select id="q-status" v-model="status" class="mf-select" aria-labelledby="q-status">
            <option value="">All statuses</option>
            <option v-for="s in statuses" :key="s" :value="s">{{ statusLabel(s) }}</option>
          </select>
        </div>
        <div>
          <label class="mf-label" id="q-sort">Sort by</label>
          <select id="q-sort" v-model="sort" class="mf-select" aria-labelledby="q-sort">
            <option value="priority">Priority then score</option>
            <option value="time">Newest first</option>
          </select>
        </div>
        <div class="grow">
          <label class="mf-label" id="q-search">Search</label>
          <input id="q-search" v-model="query" class="mf-input" aria-labelledby="q-search" placeholder="Search posts…" />
        </div>
      </div>
      <p class="semantics">Priority score means verification urgency, not the probability that a claim is false. Virality alone never implies guilt.</p>
    </section>

    <section class="mf-card">
      <div v-if="loading" class="pad"><div class="mf-skeleton" style="height: 220px"></div></div>
      <EmptyState v-else-if="!page.length && !filtered.length" icon="queue" title="Queue is empty" hint="New items appear here when the router triggers. In production, connect sources first." />
      <EmptyState v-else-if="!page.length" icon="search" title="No items match these filters" hint="Try widening the priority, status or search text.">
        <button class="mf-btn" @click="resetFilters">Clear filters</button>
      </EmptyState>
      <div v-else class="mf-table-responsive">
        <table class="mf-table">
          <thead>
            <tr>
              <th>Claim</th><th>Urgency</th><th>Status</th><th>Coverage</th><th>Age</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in page" :key="c.id">
              <td>
                <div class="claim-cell">
                  <span class="meta mf-mono">{{ c.platform }} · {{ c.postId }} · {{ c.language }} · {{ c.contentType }}</span>
                  <span class="claim">{{ c.claim }}</span>
                </div>
              </td>
              <td><UrgencyMeter :score="c.score" :tier="c.tier" :harm="c.harm" :uncertainty="c.uncertainty" :spread="c.spread" :complexity="c.complexity" :spread-estimated="c.spreadEstimated" /></td>
              <td><MfBadge :tone="statusTone(c.status)" :label="statusLabel(c.status)" /></td>
              <td>
                <span v-if="c.deferred && c.deferred.length" class="cov-warn">
                  <MfIcon name="alert" size="13" /> Incomplete coverage: <span class="mf-mono">{{ c.deferred.join(', ') }}</span>
                </span>
                <span v-else-if="c.workers" class="mf-mono dim">{{ c.workers.join(', ') }}</span>
                <span v-else class="dim">Coverage reporting not available</span>
              </td>
              <td class="mf-mono dim">{{ age(c.ingestedAt) }}</td>
              <td><router-link :to="`/console/investigate/${c.id}`" class="mf-btn">Open</router-link></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="pages > 1" class="pager">
        <button class="mf-btn" :disabled="pageNum <= 1" @click="pageNum--">‹</button>
        <span class="mf-mono dim">{{ pageNum }} / {{ pages }}</span>
        <button class="mf-btn" :disabled="pageNum >= pages" @click="pageNum++">›</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import MfIcon from '../components/MfIcon.vue'
import UrgencyMeter from '../components/UrgencyMeter.vue'
import EmptyState from '../components/EmptyState.vue'
import DemoBanner from '../components/DemoBanner.vue'
import { isDemoMode } from '../demoMode.js'
import { probeConnection } from '../connection.js'
import { fetchMonitorQueue } from '../api.js'
import { DEMO_CLAIMS } from '../fixtures/demoClaims.js'
import { toast } from '../toasts.js'

const demoMode = isDemoMode()
const loading = ref(true)
const error = ref('')
const rows = ref([])
const tier = ref('')
const status = ref('')
const query = ref('')
const sort = ref('priority')
const pageNum = ref(1)
const PAGE = 10
const statuses = ['new', 'queued', 'in_progress', 'awaiting_review', 'completed', 'failed']
const TIER_RANK = { urgent: 0, high: 1, normal: 2, low: 3 }

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  let list = rows.value.filter((c) =>
    (!tier.value || c.tier === tier.value) &&
    (!status.value || c.status === status.value) &&
    (!q || (c.claim + ' ' + c.text + ' ' + c.postId).toLowerCase().includes(q)))
  list = [...list].sort((a, b) => sort.value === 'time'
    ? String(b.ingestedAt || '').localeCompare(String(a.ingestedAt || ''))
    : (TIER_RANK[a.tier] ?? 9) - (TIER_RANK[b.tier] ?? 9) || (b.score - a.score))
  return list
})
const pages = computed(() => Math.max(1, Math.ceil(filtered.value.length / PAGE)))
const page = computed(() => filtered.value.slice((pageNum.value - 1) * PAGE, pageNum.value * PAGE))
watch([tier, status, query, sort], () => { pageNum.value = 1 })

function statusTone(s) { return { new: 'gray', queued: 'blue', in_progress: 'amber', awaiting_review: 'amber', completed: 'green', failed: 'red' }[s] || 'gray' }
function statusLabel(s) { return { new: 'New', queued: 'Queued', in_progress: 'In progress', awaiting_review: 'Awaiting review', completed: 'Completed', failed: 'Failed' }[s] || s }
function age(t) {
  if (!t) return '—'
  const mins = Math.max(0, Math.round((Date.now() - new Date(t).getTime()) / 60000))
  if (mins < 60) return `${mins}m`
  const h = Math.floor(mins / 60)
  return h < 48 ? `${h}h` : `${Math.floor(h / 24)}d`
}
function resetFilters() { tier.value = ''; status.value = ''; query.value = '' }

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (demoMode) {
      rows.value = DEMO_CLAIMS
    } else {
      await probeConnection()
      const q = await fetchMonitorQueue()
      rows.value = [...(q.jobs || []), ...(q.reviews || [])]
    }
  } catch (e) {
    error.value = e.message || 'Load failed'
    toast(error.value, 'error')
  } finally {
    loading.value = false
  }
}
onMounted(load)
</script>

<style scoped>
.toolbar { padding: 14px 16px; margin-bottom: 12px; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.grow { flex: 1; min-width: 200px; }
.grow .mf-input { width: 100%; }
.semantics { font-size: 12px; color: #6b7280; margin: 10px 0 0; }
.pad { padding: 16px; }
.claim-cell { display: flex; flex-direction: column; gap: 3px; max-width: 380px; }
.meta { color: #6b7280; font-size: 11px; }
.claim { font-size: 13px; }
.cov-warn { display: inline-flex; align-items: center; gap: 5px; font-size: 12px; color: #92400e; }
.dim { color: #6b7280; font-size: 12px; }
.pager { display: flex; align-items: center; gap: 10px; justify-content: flex-end; padding: 10px 14px; }
.mf-error-bar { margin-bottom: 12px; }
</style>
