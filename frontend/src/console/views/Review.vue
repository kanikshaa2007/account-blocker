<template>
  <div>
    <DemoBanner v-if="demoMode" />
    <EmptyState v-if="!claim && !loading" icon="check" title="Select a claim to review" hint="Open an investigation first, then continue to review.">
      <router-link to="/console/queue" class="mf-btn">Back to queue</router-link>
    </EmptyState>

    <div v-else-if="claim" class="cols">
      <section class="mf-card pad">
        <p class="eyebrow">Claim and evidence summary</p>
        <p class="claim">{{ claim.claim }}</p>
        <p class="meta mf-mono">{{ claim.platform }} · {{ claim.postId }} · {{ claim.language }} · {{ claim.contentType }}</p>
        <UrgencyMeter :score="claim.score" :tier="claim.tier" :harm="claim.harm" :uncertainty="claim.uncertainty" :spread="claim.spread" :complexity="claim.complexity" :spread-estimated="claim.spreadEstimated" />
        <p v-if="claim.deferred && claim.deferred.length" class="warn">Some worker capabilities were deferred, so verification coverage is incomplete. Treat the result as partial.</p>
        <h3 class="card-title">Retrieved evidence ({{ (claim.evidence || []).length }})</h3>
        <ul v-if="(claim.evidence || []).length" class="evi">
          <li v-for="(e, i) in claim.evidence" :key="i">“{{ e.excerpt }}” <span class="dim">— {{ e.publisher }}</span></li>
        </ul>
        <p v-else class="hint">No evidence attached yet.</p>
      </section>

      <section class="mf-card pad">
        <p class="eyebrow">Decision</p>
        <div class="opts" role="radiogroup" aria-label="Decision">
          <label v-for="o in outcomes" :key="o.value" class="opt" :class="{ sel: outcome === o.value }">
            <input type="radio" v-model="outcome" :value="o.value" />
            <span><strong>{{ o.label }}</strong><small>{{ o.hint }}</small></span>
          </label>
        </div>
        <label class="mf-label" id="rev-notes">Analyst notes</label>
        <textarea id="rev-notes" v-model="notes" class="mf-input notes" rows="4" placeholder="Working notes…" />

        <div v-if="isDemoClaim" class="mf-demo-banner">Demo claim: review actions are recorded locally only.</div>

        <div class="actions">
          <button class="mf-btn mf-btn-primary" :disabled="!canSubmit || submitting" @click="askConfirm = true">Submit review</button>
          <router-link :to="`/console/investigate/${claim.id}`" class="mf-btn">Back to investigation</router-link>
        </div>
        <p class="hint">Human approval is required. Nothing here blocks third-party accounts; production approval drafts a platform report.</p>

        <h3 class="card-title">Review history</h3>
        <ul class="hist">
          <li v-for="(h, i) in history" :key="i"><span class="mf-mono dim">{{ fmtTime(h.at) }}</span> · {{ h.actor }} · {{ h.action }}<span v-if="h.reason"> — {{ h.reason }}</span></li>
        </ul>
        <p v-if="!history.length" class="hint">No data available</p>
      </section>
    </div>

    <ConfirmDialog :open="askConfirm" title="Confirm review" body="This records a human moderation decision. Continue?" confirm-label="Submit review" require-reason reason-label="Reason" @confirm="submit" @cancel="askConfirm = false" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import UrgencyMeter from '../components/UrgencyMeter.vue'
import EmptyState from '../components/EmptyState.vue'
import DemoBanner from '../components/DemoBanner.vue'
import ConfirmDialog from '../components/ConfirmDialog.vue'
import { isDemoMode } from '../demoMode.js'
import { probeConnection } from '../connection.js'
import { fetchMonitorQueue, approveMonitorJob } from '../api.js'
import { DEMO_CLAIMS, DEMO_ACTIONS } from '../fixtures/demoClaims.js'
import { toast } from '../toasts.js'
import { logAction, listLocalActions } from '../analystStore.js'

const route = useRoute()
const demoMode = isDemoMode()
const loading = ref(true)
const rows = ref([])
const outcome = ref('')
const notes = ref('')
const askConfirm = ref(false)
const submitting = ref(false)
const localLog = ref([])

const claim = computed(() => rows.value.find((c) => c.id === route.params.id))
const isDemoClaim = computed(() => !!(claim.value && String(claim.value.id).startsWith('demo-')))
const outcomes = [
  { value: 'verified', label: 'Verified — sufficient evidence', hint: 'Evidence supports the claim.' },
  { value: 'false_misleading', label: 'False or misleading — with evidence', hint: 'At least one citation attached.' },
  { value: 'inconclusive', label: 'Inconclusive — insufficient evidence', hint: 'No decision can be defended yet.' },
  { value: 'needs_work', label: 'Needs further investigation', hint: 'Assigns follow-up work.' }
]
const canSubmit = computed(() => !!outcome.value)
const history = computed(() => {
  const all = [...localLog.value.filter((l) => l.target === route.params.id)]
  if (!demoMode) return all
  return [...DEMO_ACTIONS.filter((a) => a.target === route.params.id).map((a) => ({ ...a, actor: a.actor })), ...all]
})

function fmtTime(t) { try { return new Date(t).toLocaleString() } catch { return t || '—' } }

async function submit(reason) {
  submitting.value = true
  try {
    if (isDemoClaim.value) {
      logAction({ actor: 'analyst', action: `review:${outcome.value}`, target: claim.value.id, from: claim.value.status, to: outcome.value, reason, job: null })
      localLog.value = listLocalActions()
      toast('Demo review recorded locally', 'ok')
    } else {
      const job = (await fetchMonitorQueue()).jobs?.find((j) => j.post_id === claim.value.postId)
      if (!job) throw new Error('No monitor job for this claim yet — report drafting unavailable.')
      await approveMonitorJob(job.job_id, 'analyst')
      logAction({ actor: 'analyst', action: `approve_report:${outcome.value}`, target: claim.value.id, reason, job: job.job_id })
      localLog.value = listLocalActions()
      toast('Platform report drafted for human submission', 'ok')
    }
    outcome.value = ''
  } catch (e) {
    toast(e.message || 'Submit failed', 'error')
  } finally {
    submitting.value = false
    askConfirm.value = false
  }
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
    localLog.value = listLocalActions()
  } catch (e) { toast(e.message || 'Load failed', 'error') }
  finally { loading.value = false }
})
</script>

<style scoped>
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pad { padding: 16px; }
.claim { font-size: 15px; font-weight: 600; }
.meta { color: #6b7280; font-size: 11px; margin: 6px 0 10px; }
.evi { margin: 8px 0; padding-left: 18px; font-size: 13px; }
.dim { color: #6b7280; font-size: 12px; }
.hint { font-size: 12px; color: #6b7280; }
.warn { font-size: 12px; color: #92400e; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; padding: 6px 9px; }
.opts { display: flex; flex-direction: column; gap: 8px; margin: 10px 0 12px; }
.opt { display: flex; gap: 8px; border: 1px solid #e5e7eb; border-radius: 4px; padding: 9px 10px; font-size: 13px; cursor: pointer; }
.opt.sel { border-color: #0e1626; background: #f1f3f6; }
.opt small { display: block; color: #6b7280; font-size: 12px; }
.notes { width: 100%; resize: vertical; }
.actions { display: flex; gap: 8px; margin: 12px 0; flex-wrap: wrap; }
.hist { list-style: none; margin: 0; padding: 0; font-size: 13px; display: flex; flex-direction: column; gap: 6px; }
.card-title { margin: 14px 0 6px; }
@media (max-width: 900px) { .cols { grid-template-columns: 1fr; } }
</style>
