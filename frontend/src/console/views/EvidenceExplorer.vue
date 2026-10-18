<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <section class="mf-card toolbar">
      <div class="filters">
        <div class="grow">
          <label class="mf-label" id="e-search">Search</label>
          <input id="e-search" v-model="query" class="mf-input" aria-labelledby="e-search" placeholder="Search titles, excerpts, publishers…" />
        </div>
        <div>
          <label class="mf-label" id="e-rel">Relationship</label>
          <select id="e-rel" v-model="relation" class="mf-select" aria-labelledby="e-rel">
            <option value="">All relationships</option>
            <option value="supports">Supports</option>
            <option value="refutes">Refutes</option>
            <option value="context">Context</option>
          </select>
        </div>
      </div>
      <p class="semantics">Only evidence actually attached to claims is shown. Nothing is manufactured here.</p>
    </section>

    <section class="mf-card">
      <div v-if="loading" class="pad"><div class="mf-skeleton" style="height: 200px"></div></div>
      <EmptyState v-else-if="!filtered.length" icon="evidence" title="No evidence" hint="Evidence appears once attached to a claim under investigation." />
      <ul v-else class="evi-list">
        <li v-for="(e, i) in filtered" :key="i" class="mf-card pad">
          <div class="evi-head">
            <MfBadge :tone="e.relation === 'refutes' ? 'red' : e.relation === 'supports' ? 'green' : 'gray'" :label="e.relation" />
            <strong>{{ e.title }}</strong>
          </div>
          <p class="meta">{{ e.publisher }} · {{ e.type }} · {{ e.language }} · Published {{ fmtTime(e.publishedAt) }} · Retrieved {{ fmtTime(e.retrievedAt) }}</p>
          <p class="excerpt">{{ e.excerpt }}</p>
          <p class="meta">About claim: <router-link :to="`/console/investigate/${e.claimId}`" class="link">{{ e.claimText }}</router-link></p>
          <p class="meta">Reliability: <MfBadge :tone="e.reliability === 'official' ? 'green' : e.reliability === 'medium' ? 'amber' : 'gray'" :label="e.reliability || 'unknown'" /></p>
          <a :href="e.url" target="_blank" rel="noopener" class="link mf-mono">{{ e.url }}</a>
        </li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import EmptyState from '../components/EmptyState.vue'
import DemoBanner from '../components/DemoBanner.vue'
import { isDemoMode } from '../demoMode.js'
import { DEMO_CLAIMS } from '../fixtures/demoClaims.js'

const demoMode = isDemoMode()
const loading = ref(true)
const query = ref('')
const relation = ref('')
const items = ref([])

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return items.value.filter((e) =>
    (!relation.value || e.relation === relation.value) &&
    (!q || (e.title + ' ' + e.excerpt + ' ' + e.publisher).toLowerCase().includes(q)))
})
function fmtTime(t) { try { return t ? new Date(t).toLocaleString() : '—' } catch { return t || '—' } }

onMounted(() => {
  const all = []
  for (const c of DEMO_CLAIMS) {
    for (const e of c.evidence || []) all.push({ ...e, claimId: c.id, claimText: c.claim })
  }
  items.value = all
  loading.value = false
})
</script>

<style scoped>
.toolbar { padding: 14px 16px; margin-bottom: 12px; }
.filters { display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap; }
.grow { flex: 1; min-width: 220px; }
.grow .mf-input { width: 100%; }
.semantics { font-size: 12px; color: #6b7280; margin: 10px 0 0; }
.pad { padding: 16px; }
.evi-list { list-style: none; margin: 0; padding: 12px; display: flex; flex-direction: column; gap: 10px; }
.evi-head { display: flex; gap: 8px; align-items: center; font-size: 14px; }
.meta { font-size: 12px; color: #6b7280; margin: 6px 0; }
.excerpt { font-size: 13px; margin: 6px 0; }
.link { color: #1d4ed8; font-size: 12px; word-break: break-all; }
</style>
