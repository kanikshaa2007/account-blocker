<template>
  <div class="cols">
    <section class="mf-card pad">
      <h2 class="card-title">Connected sources</h2>
      <ul class="rows">
        <li>
          <span><strong>Backend API</strong><br /><span class="mf-mono dim">{{ base }}</span></span>
          <MfBadge :tone="connOk ? 'green' : 'red'" :label="connOk ? 'Connected' : 'Disconnected'" />
        </li>
        <li>
          <span><strong>PIB Fact Check</strong><br /><span class="dim">Quota-free trigger feed</span></span>
          <MfBadge tone="gray" label="via RSS" />
        </li>
        <li>
          <span><strong>X · Instagram · YouTube</strong><br /><span class="dim">Official APIs only, keys stay server-side</span></span>
          <MfBadge tone="gray" label="Server-side" />
        </li>
      </ul>
      <button class="mf-btn" :disabled="checking" @click="recheck">{{ checking ? 'Loading…' : 'Recheck connection' }}</button>
      <p v-if="connDetail" class="hint">{{ connDetail }}</p>
    </section>

    <section class="mf-card pad">
      <h2 class="card-title">Language</h2>
      <LanguageSwitcher />
      <h2 class="card-title" style="margin-top: 18px">Data mode</h2>
      <label class="switch-row">
        <input type="checkbox" :checked="demoOn" @change="toggleDemo" />
        <span>Use demo fixtures</span>
      </label>
      <p class="hint">Off means live backend endpoints only, with honest empty states.</p>
      <h2 class="card-title" style="margin-top: 18px">Analyst profile</h2>
      <p class="hint">Single-analyst workspace in this build. Multi-analyst identity is not implemented.</p>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import MfBadge from '../components/MfBadge.vue'
import LanguageSwitcher from '../../components/LanguageSwitcher.vue'
import { probeConnection, connection } from '../connection.js'
import { isDemoMode, setDemoMode } from '../demoMode.js'
import { toast } from '../toasts.js'

const demoMode = isDemoMode()
const demoOn = computed(() => demoMode.value)
const connOk = computed(() => connection.status.value === 'online')
const base = computed(() => connection.base.value)
const connDetail = computed(() => connection.detail.value)
const checking = ref(false)

function toggleDemo(e) {
  setDemoMode(e.target.checked)
  toast(e.target.checked ? 'Demo mode on — fixtures in use' : 'Production mode — live endpoints only', 'ok')
  setTimeout(() => location.reload(), 600)
}
async function recheck() {
  checking.value = true
  await probeConnection()
  checking.value = false
}
</script>

<style scoped>
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pad { padding: 16px; }
.mf-card-title { margin: 0 0 8px; }
.mf-card-title:not(:first-child) { margin-top: 18px; }
.rows { list-style: none; margin: 0 0 12px; padding: 0; }
.rows li { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 9px 0; border-bottom: 1px solid #e5e7eb; font-size: 13px; }
.dim { color: #6b7280; font-size: 11px; }
.hint { font-size: 12px; color: #6b7280; }
.switch-row { display: flex; gap: 8px; align-items: center; font-size: 13px; font-weight: 600; }
@media (max-width: 900px) { .cols { grid-template-columns: 1fr; } }
</style>
