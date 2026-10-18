<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <div v-if="error && !demoMode" class="mf-error-bar">
      <MfIcon name="alert" size="15" /><span>{{ error }}</span>
      <button class="mf-btn" @click="load">Retry</button>
    </div>

    <div v-if="loading" class="grid">
      <div v-for="i in 4" :key="i" class="mf-card pad"><div class="mf-skeleton" style="height: 64px"></div></div>
    </div>

    <template v-else>
      <section class="grid" aria-label="Queue summary">
        <div class="mf-card pad stat" v-for="s in tierStats" :key="s.tier">
          <span class="eyebrow">{{ s.label }}</span>
          <strong class="bignum mf-mono">{{ s.count }}</strong>
          <MfBadge :tone="s.tone" :label="s.tier.toUpperCase()" />
        </div>
      </section>

      <section class="grid two">
        <div class="mf-card pad">
          <h2 class="card-title">Incoming-post activity</h2>
          <p class="hint">Ingested posts per day (demo: fixture timestamps).</p>
          <div class="bars" role="img" aria-label="Incoming-post activity">
            <div v-for="b in activity" :key="b.label" class="bar-col">
              <span class="bar-val mf-mono">{{ b.count }}</span>
              <span class="bar tone-blue" :style="{ height: b.height + 'px' }"></span>
              <span class="bar-label">{{ b.label }}</span>
            </div>
          </div>
          <p v-if="!activity.length" class="hint">No data available</p>
        </div>

        <div class="mf-card pad">
          <h2 class="card-title">Verification status</h2>
          <p class="hint">Queue states across known claims.</p>
          <ul class="rows">
            <li v-for="r in statusRows" :key="r.status">
              <MfBadge :tone="r.tone" :label="r.label" />
              <span class="mf-mono">{{ r.count }}</span>
            </li>
          </ul>
          <h2 class="card-title" style="margin-top: 16px">Sources</h2>
          <ul class="rows">
            <li v-for="r in sourceRows" :key="r.source">
              <span>{{ r.source }}</span>
              <span class="mf-mono">{{ r.count }}</span>
            </li>
          </ul>
        </div>
      </section>

      <section class="grid two">
        <div class="mf-card pad">
          <div class="rowhead">
            <h2 class="card-title">Needs analyst attention</h2>
            <router-link to="/console/queue" class="link">View queue</router-link>
          </div>
          <ul class="claims">
            <li v-for="c in attention" :key="c.id">
              <router-link :to="`/console/investigate/${c.id}`" class="claim-link">
                <UrgencyMeter :score="c.score" :tier="c.tier" :harm="c.harm" :uncertainty="c.uncertainty" :spread="c.spread" :complexity="c.complexity" :spread-estimated="c.spreadEstimated" />
                <span class="claim-text">{{ c.claim }}</span>
              </router-link>
            </li>
          </ul>
          <p v-if="!attention.length" class="hint">No data available</p>
        </div>

        <div class="mf-card pad">
          <h2 class="card-title">Recent analyst actions</h2>
          <ul class="rows">
            <li v-for="(a, i) in actions" :key="i">
              <span>{{ a.action }} · <span class="mf-mono">{{ a.target }}</span></span>
              <span class="mf-mono dim">{{ fmtTime(a.at) }}</span>
            </li>
          </ul>
          <p v-if="!actions.length" class="hint">No data available</p>
          <h2 class="card-title" style="margin-top: 16px">Worker / job health</h2>
          <p class="hint">{{ healthLine }}</p>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import MfIcon from '../components/MfIcon.vue'
import UrgencyMeter from '../components/UrgencyMeter.vue'
import DemoBanner from '../components/DemoBanner.vue'
import { isDemoMode } from '../demoMode.js'
import { probeConnection, connection } from '../connection.js'
import { fetchMonitorQueue, fetchSimulations } from '../api.js'
import { DEMO_CLAIMS, DEMO_ACTIONS } from '../fixtures/demoClaims.js'
import { toast } from '../toasts.js'

const demoMode = isDemoMode()
const loading = ref(true)
const error = ref('')
const claims = ref([])
const actions = ref([])
const sims = ref([])

const tierStats = computed(() => ['urgent', 'high', 'normal', 'low'].map((t) => ({
  tier: t, label: t === 'urgent' ? 'Urgent queue' : t === 'high' ? 'High queue' : t === 'normal' ? 'Normal queue' : 'Low queue',
  count: claims.value.filter((c) => c.tier === t).length,
  tone: { urgent: 'red', high: 'amber', normal: 'blue', low: 'gray' }[t]
})))

const activity = computed(() => {
  const byDay = {}
  for (const c of claims.value) {
    const d = (c.ingestedAt || '').slice(0, 10)
    if (d) byDay[d] = (byDay[d] || 0) + 1
  }
  const days = Object.keys(byDay).sort().slice(-7)
  const max = Math.max(1, ...days.map((d) => byDay[d]))
  return days.map((d) => ({ label: d.slice(5), count: byDay[d], height: Math.round((byDay[d] / max) * 90) + 6, tone: 'blue' }))
})

const statusRows = computed(() => {
  const order = [['new', 'gray', 'New'], ['queued', 'blue', 'Queued'], ['in_progress', 'amber', 'In progress'], ['awaiting_review', 'amber', 'Awaiting review'], ['completed', 'green', 'Completed'], ['failed', 'red', 'Failed']]
  return order.map(([s, tone, label]) => ({ status: s, tone, label, count: claims.value.filter((c) => c.status === s).length }))
})

const sourceRows = computed(() => {
  const map = {}
  for (const c of claims.value) map[c.platform] = (map[c.platform] || 0) + 1
  return Object.keys(map).map((s) => ({ source: s, count: map[s] }))
})

const attention = computed(() => claims.value.filter((c) => c.tier === 'urgent' || c.tier === 'high').slice(0, 5))
const healthLine = computed(() => {
  if (demoMode) return `Demo adapter · ${claims.value.length} claims · simulations not run in demo`
  return `${sims.value.length} simulations known · queue jobs ${claims.value.length} · backend ${connection.status.value}`
})

function fmtTime(t) { try { return new Date(t).toLocaleString() } catch { return t } }

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (demoMode) {
      claims.value = DEMO_CLAIMS
      actions.value = DEMO_ACTIONS
    } else {
      await probeConnection()
      const q = await fetchMonitorQueue()
      claims.value = [...(q.jobs || []), ...(q.reviews || [])]
      actions.value = q.actions || []
      try { sims.value = await fetchSimulations() } catch { sims.value = [] }
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
.grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 12px; }
.grid.two { grid-template-columns: 1fr 1fr; }
.pad { padding: 16px; }
.stat { display: flex; flex-direction: column; gap: 6px; }
.bignum { font-size: 30px; font-weight: 700; }
.eyebrow { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; color: #6b7280; text-transform: uppercase; }
.card-title { font-size: 13px; font-weight: 700; margin-bottom: 8px; }
.rowhead { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.link { font-size: 12px; font-weight: 600; color: #1d4ed8; }
.hint { font-size: 12px; color: #6b7280; }
.rows { list-style: none; margin: 8px 0 0; padding: 0; }
.rows li { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
.dim { color: #6b7280; }
.claims { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.claim-link { display: flex; gap: 12px; text-decoration: none; color: inherit; border: 1px solid #e5e7eb; border-radius: 4px; padding: 10px; }
.claim-link:hover { border-color: #111827; }
.claim-text { font-size: 13px; }
.bars { display: flex; align-items: flex-end; gap: 10px; height: 140px; padding-top: 8px; }
.bar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.bar { width: 100%; max-width: 44px; background: #93c5fd; border-radius: 3px 3px 0 0; }
.bar-val { font-size: 11px; font-weight: 700; }
.bar-label { font-size: 10px; color: #6b7280; }
.mf-error-bar { margin-bottom: 12px; }
@media (max-width: 900px) { .grid, .grid.two { grid-template-columns: 1fr 1fr; } }
@media (max-width: 600px) { .grid, .grid.two { grid-template-columns: 1fr; } }
</style>
