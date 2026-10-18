<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <div v-if="error && !demoMode" class="mf-error-bar">
      <MfIcon name="alert" size="15" /><span>{{ error }}</span>
      <button class="mf-btn" @click="load">Retry</button>
    </div>

    <section class="mf-card toolbar">
      <div class="filters">
        <div class="grow">
          <label class="mf-label" for="m-search">Search</label>
          <input id="m-search" ref="searchBox" v-model="query" class="mf-input" placeholder="Search posts…" />
        </div>
        <div>
          <label class="mf-label" for="m-src">Source</label>
          <select id="m-src" v-model="source" class="mf-select">
            <option value="">All sources</option>
            <option v-for="s in sources" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
        <div>
          <label class="mf-label" for="m-lang">Language</label>
          <select id="m-lang" v-model="lang" class="mf-select">
            <option value="">All languages</option>
            <option v-for="l in langs" :key="l" :value="l">{{ l }}</option>
          </select>
        </div>
        <div>
          <label class="mf-label" for="m-type">Content type</label>
          <select id="m-type" v-model="ctype" class="mf-select">
            <option value="">All types</option>
            <option v-for="t in ctypes" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div>
          <label class="mf-label" for="m-tier">Priority</label>
          <select id="m-tier" v-model="tier" class="mf-select">
            <option value="">All priorities</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="normal">Normal</option>
            <option value="low">Low</option>
          </select>
        </div>
      </div>
      <p class="semantics">Only connected and authorized sources are shown. Private content is never accessible here.</p>
      <div class="ingest-row">
        <button class="mf-btn mf-btn-accent" :disabled="ingesting || demoMode" @click="ingest" :title="demoMode ? 'Turn off demo mode in Settings to fetch live data' : ''">
          {{ ingesting ? 'Fetching…' : 'Fetch live feed' }}
        </button>
        <span v-if="ingestSummary" class="hint">{{ ingestSummary }}</span>
      </div>
    </section>

    <section class="mf-card">
      <div v-if="loading" class="pad"><div class="mf-skeleton" style="height: 220px"></div></div>
      <EmptyState v-else-if="!filtered.length" icon="activity" title="No incoming posts" hint="Posts appear as connectors ingest them. Check connection status in Settings." />
      <div v-else class="mf-table-responsive">
        <table class="mf-table">
          <thead>
            <tr>
              <th>Post</th><th>Urgency</th><th>Status</th><th>Evidence</th><th>Ingested</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in filtered" :key="p.id">
              <td>
                <div class="claim-cell">
                  <span class="meta mf-mono">{{ p.platform }} · {{ p.postId }}</span>
                  <span v-if="p.author" class="meta">account: <strong>{{ p.author }}</strong></span>
                  <span class="claim">{{ truncate(p.text, 220) }}</span>
                  <span class="meta">{{ p.language }} · {{ p.contentType }} · {{ fmtTime(p.postedAt) }}</span>
                </div>
              </td>
              <td><UrgencyMeter :score="p.score" :tier="p.tier" :harm="p.harm" :uncertainty="p.uncertainty" :spread="p.spread" :complexity="p.complexity" :spread-estimated="p.spreadEstimated" /></td>
              <td><MfBadge :tone="statusTone(p.status)" :label="statusLabel(p.status)" /></td>
              <td class="mf-mono dim">{{ (p.evidence || []).length ? p.evidence.length + ' ▸' : '—' }}</td>
              <td class="mf-mono dim">{{ fmtTime(p.ingestedAt) }}</td>
              <td class="mf-table-actions">
                <a :href="p.url" target="_blank" rel="noopener" class="mf-btn mf-btn-link">Open source</a>
                <router-link :to="`/console/investigate/${p.id}`" class="mf-btn">Investigate</router-link>
              </td>
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
import MfIcon from '../components/MfIcon.vue'
import UrgencyMeter from '../components/UrgencyMeter.vue'
import EmptyState from '../components/EmptyState.vue'
import DemoBanner from '../components/DemoBanner.vue'
import { isDemoMode } from '../demoMode.js'
import { probeConnection } from '../connection.js'
import { fetchMonitorQueue, ingestLiveFeed } from '../api.js'
import { DEMO_CLAIMS } from '../fixtures/demoClaims.js'
import { toast } from '../toasts.js'

const demoMode = isDemoMode()
const loading = ref(true)
const error = ref('')
const rows = ref([])
const query = ref('')
const source = ref('')
const lang = ref('')
const ctype = ref('')
const tier = ref('')
const searchBox = ref(null)
const ingesting = ref(false)
const ingestSummary = ref('')

const sources = computed(() => [...new Set(rows.value.map((r) => r.platform))])
const langs = computed(() => [...new Set(rows.value.map((r) => r.language).filter(Boolean))])
const ctypes = computed(() => [...new Set(rows.value.map((r) => r.contentType).filter(Boolean))])

const filtered = computed(() => {
  const q = query.value.trim().toLowerCase()
  return rows.value
    .filter((p) =>
      (!source.value || p.platform === source.value) &&
      (!lang.value || p.language === lang.value) &&
      (!ctype.value || p.contentType === ctype.value) &&
      (!tier.value || p.tier === tier.value) &&
      (!q || (p.text + ' ' + p.claim + ' ' + p.postId).toLowerCase().includes(q)))
    .sort((a, b) => String(b.ingestedAt || '').localeCompare(String(a.ingestedAt || '')))
})

function truncate(t, n) { return t && t.length > n ? t.slice(0, n) + '…' : t || '' }
function fmtTime(t) { try { return new Date(t).toLocaleString() } catch { return t || '—' } }
function statusTone(s) { return { new: 'gray', queued: 'blue', in_progress: 'amber', awaiting_review: 'amber', completed: 'green', failed: 'red' }[s] || 'gray' }
function statusLabel(s) { return { new: 'New', queued: 'Queued', in_progress: 'In progress', awaiting_review: 'Awaiting review', completed: 'Completed', failed: 'Failed' }[s] || s || '—' }

async function load() {
  loading.value = true
  error.value = ''
  try {
    if (demoMode) {
      rows.value = DEMO_CLAIMS
    } else {
      await probeConnection()
      const q = await fetchMonitorQueue()
      rows.value = [
        ...(q.sightings || []).map((s) => ({
          id: `${s.platform}:${s.post_id}`, platform: s.platform, postId: s.post_id,
          author: s.author || '', text: s.text, claim: s.text, language: s.language || 'en', contentType: s.content_type || 'link',
          status: s.triggered ? 'awaiting_review' : 'new', tier: s.tier, score: s.score ?? 0,
          harm: 0, uncertainty: 0, spread: 0, complexity: 0, spreadEstimated: true,
          evidence: [], postedAt: s.ingested_at, ingestedAt: s.ingested_at, url: s.url
        })),
        ...(q.jobs || []).map((j) => ({
          id: `job:${j.job_id}`, platform: j.platform, postId: j.post_id,
          text: j.text, claim: j.text, language: j.language || 'en', contentType: 'link',
          status: 'awaiting_review', tier: j.tier, score: j.score ?? 0,
          harm: 0, uncertainty: 0, spread: 0, complexity: 0, spreadEstimated: true,
          evidence: [], postedAt: '', ingestedAt: '', url: j.url
        }))
      ]
    }
  } catch (e) {
    error.value = e.message || 'Load failed'
    toast(error.value, 'error')
  } finally {
    loading.value = false
  }
}

async function ingest() {
  ingesting.value = true
  ingestSummary.value = ''
  try {
    const summary = await ingestLiveFeed()
    ingestSummary.value = `fetched ${JSON.stringify(summary.fetched)} · routed ${summary.routed} · jobs ${summary.jobs} · reviews ${summary.reviews}`
    toast('Live ingest complete', 'ok')
    await load()
  } catch (e) {
    toast(e.message || 'Ingest failed', 'error')
  } finally {
    ingesting.value = false
  }
}

onMounted(async () => {
  await load()
})
</script>

<style scoped>
.toolbar { padding: 14px 16px; margin-bottom: 12px; }
.filters { display: flex; gap: 12px; flex-wrap: wrap; align-items: flex-end; }
.grow { flex: 1; min-width: 220px; }
.grow .mf-input { width: 100%; }
.semantics { font-size: 12px; color: #6b7280; margin: 10px 0 0; }
.pad { padding: 16px; }
.claim-cell { display: flex; flex-direction: column; gap: 3px; max-width: 460px; }
.meta { color: #6b7280; font-size: 11px; }
.claim { font-size: 13px; }
.dim { color: #6b7280; font-size: 12px; }
.mf-error-bar { margin-bottom: 12px; }
.mf-table-actions { display: flex; gap: 6px; }
.mf-btn-link { background: transparent; border-color: transparent; color: #1d4ed8; padding: 7px 12px; text-decoration: underline; }
.mf-btn-link:hover { color: #c2410c; text-decoration: underline; }
@media (max-width: 900px) { .filters { flex-direction: column; align-items: stretch; } .grow { min-width: unset; } }
</style>
