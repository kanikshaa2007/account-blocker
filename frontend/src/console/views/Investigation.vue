<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <div v-if="loading" class="mf-card pad"><div class="mf-skeleton" style="height: 300px"></div></div>
    <EmptyState v-else-if="!claim" icon="search" title="Claim not found" hint="It may have been removed or the link is stale.">
      <router-link to="/console/queue" class="mf-btn">Back to queue</router-link>
    </EmptyState>

    <div v-else class="cols">
      <section class="mf-card pad">
        <p class="eyebrow">Observed data</p>
        <p class="meta mf-mono">{{ claim.platform }} · {{ claim.postId }} · {{ claim.language }} · {{ claim.contentType }}</p>
        <p class="post">{{ claim.text }}</p>
        <dl class="kv">
          <div><dt>Ingested</dt><dd class="mf-mono">{{ fmtTime(claim.postedAt) }} / {{ fmtTime(claim.ingestedAt) }}</dd></div>
          <div><dt>Source</dt><dd>{{ claim.author || '—' }} <span v-if="claim.followers" class="mf-mono dim">({{ claim.followers }} followers)</span></dd></div>
          <div><dt>Extracted claim</dt><dd>{{ claim.claim }}</dd></div>
        </dl>
        <div v-if="claim.url" class="row"><MfIcon name="link" size="13" /><a :href="claim.url" target="_blank" rel="noopener" class="link">{{ claim.url }}</a></div>

        <h3 class="card-title">Retrieved evidence</h3>
        <ul v-if="(claim.evidence || []).length" class="evi">
          <li v-for="(e, i) in claim.evidence" :key="i">
            <MfBadge :tone="e.relation === 'refutes' ? 'red' : e.relation === 'supports' ? 'green' : 'gray'" :label="e.relation" />
            <strong>{{ e.title }}</strong>
            <span class="dim">{{ e.publisher }} · {{ fmtTime(e.publishedAt) }}</span>
            <p>{{ e.excerpt }}</p>
          </li>
        </ul>
        <p v-else class="hint">No evidence attached yet.</p>

        <h3 class="card-title">Analyst notes</h3>
        <textarea v-model="notes" class="mf-input notes" rows="3" placeholder="Working notes (stored locally in this browser)…" @change="saveNotes" />
      </section>

      <section class="mf-card pad">
        <p class="eyebrow">Routing rationale</p>
        <UrgencyMeter :score="claim.score" :tier="claim.tier" :harm="claim.harm" :uncertainty="claim.uncertainty" :spread="claim.spread" :complexity="claim.complexity" :spread-estimated="claim.spreadEstimated" />
        <p class="semantics">Priority score means verification urgency, not the probability that a claim is false. Virality alone never implies guilt.</p>
        <p v-if="claim.spreadEstimated" class="warn">Spread is a fallback estimate, not an observed measurement.</p>

        <dl class="kv">
          <div><dt>Status</dt><dd><MfBadge :tone="statusTone(claim.status)" :label="statusLabel(claim.status)" /></dd></div>
          <div><dt>Selected workers</dt><dd class="mf-mono">{{ (claim.workers || []).join(', ') || '—' }}</dd></div>
          <div v-if="claim.deferred && claim.deferred.length"><dt>Deferred workers</dt><dd><span class="warn mf-mono">{{ claim.deferred.join(', ') }}</span></dd></div>
        </dl>
        <p v-if="claim.deferred && claim.deferred.length" class="warn">Some worker capabilities were deferred, so verification coverage is incomplete. Treat the result as partial.</p>

        <h3 class="card-title">Human conclusion</h3>
        <p v-if="claim.verdict" class="hint">Recorded verdict: <strong>{{ verdictLabel(claim.verdict) }}</strong></p>
        <p v-else class="hint">No verdict recorded yet — investigation open.</p>
        <div v-if="claim.notes" class="notes-saved">{{ claim.notes }}</div>

        <div class="actions">
          <router-link :to="`/console/review/${claim.id}`" class="mf-btn mf-btn-primary">Go to review</router-link>
          <router-link to="/console/queue" class="mf-btn">Back to queue</router-link>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
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
import { getNote, saveNote } from '../analystStore.js'

const route = useRoute()
const demoMode = isDemoMode()
const loading = ref(true)
const rows = ref([])
const notes = ref('')

const claim = computed(() => rows.value.find((c) => c.id === route.params.id))
function fmtTime(t) { try { return new Date(t).toLocaleString() } catch { return t || '—' } }
function statusTone(s) { return { new: 'gray', queued: 'blue', in_progress: 'amber', awaiting_review: 'amber', completed: 'green', failed: 'red' }[s] || 'gray' }
function statusLabel(s) { return { new: 'New', queued: 'Queued', in_progress: 'In progress', awaiting_review: 'Awaiting review', completed: 'Completed', failed: 'Failed' }[s] || s || '—' }
function verdictLabel(v) { return { verified: 'Verified with sufficient evidence', false_misleading: 'False or misleading with supporting evidence', inconclusive: 'Inconclusive — insufficient evidence', needs_work: 'Needs further investigation' }[v] || v }
function saveNotes() {
  if (claim.value) { saveNote(claim.value.id, notes.value); toast('Note saved locally', 'ok') }
}

onMounted(async () => {
  try {
    if (demoMode) {
      rows.value = DEMO_CLAIMS
    } else {
      await probeConnection()
      const q = await fetchMonitorQueue()
      rows.value = [...(q.jobs || []), ...(q.reviews || [])]
    }
    if (claim.value) notes.value = getNote(claim.value.id)
  } catch (e) { toast(e.message || 'Load failed', 'error') }
  finally { loading.value = false }
})
</script>

<style scoped>
.cols { display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; }
.pad { padding: 16px; }
.meta { color: #6b7280; font-size: 11px; margin: 4px 0 8px; }
.post { font-size: 14px; background: #f1f3f6; border: 1px solid #e5e7eb; border-radius: 4px; padding: 10px 12px; }
.kv { margin: 12px 0; }
.kv > div { display: grid; grid-template-columns: 150px 1fr; gap: 8px; padding: 6px 0; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
.kv dt { color: #6b7280; font-weight: 600; font-size: 12px; }
.kv dd { margin: 0; }
.card-title { margin: 16px 0 8px; }
.evi { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 10px; font-size: 13px; }
.evi p { margin: 4px 0 0; color: #374151; }
.dim { color: #6b7280; font-size: 12px; }
.hint { font-size: 12px; color: #6b7280; }
.semantics, .warn { font-size: 12px; }
.semantics { color: #6b7280; }
.warn { color: #92400e; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; padding: 6px 9px; }
.notes { width: 100%; resize: vertical; }
.notes-saved { font-size: 13px; background: #f1f3f6; border-left: 3px solid #ff5c00; padding: 8px 10px; margin-top: 8px; }
.actions { display: flex; gap: 8px; margin-top: 16px; flex-wrap: wrap; }
.row { display: flex; gap: 6px; align-items: center; font-size: 12px; }
.link { color: #1d4ed8; word-break: break-all; }
@media (max-width: 900px) { .cols { grid-template-columns: 1fr; } }
</style>
