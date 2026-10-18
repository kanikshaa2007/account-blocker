<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed }">
      <div class="brand">
        <span class="brand-mark" aria-hidden="true">MF</span>
        <span v-if="!collapsed" class="brand-text"><strong>MiroFish</strong><small>INTELLIGENCE</small></span>
      </div>
      <nav class="nav" aria-label="Console">
        <router-link v-for="item in nav" :key="item.to" :to="item.to" class="nav-item" active-class="active">
          <MfIcon :name="item.icon" size="17" />
          <span v-if="!collapsed">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="side-foot">
        <button class="collapse-btn" @click="collapsed = !collapsed" :aria-label="collapsed ? 'Expand' : 'Collapse'">
          <MfIcon name="chevron" size="16" />
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="title-wrap">
          <h1>{{ pageTitle }}</h1>
          <p v-if="pageSub" class="subtitle">{{ pageSub }}</p>
        </div>
        <div class="top-actions">
          <div class="conn" :class="connClass" role="status" :title="connTitle">
            <span class="dot" aria-hidden="true"></span>{{ connLabel }}
          </div>
          <span class="analyst"><MfIcon name="user" size="15" />analyst</span>
        </div>
      </header>

      <div v-if="demoMode" class="demo-strip">
        <DemoBanner />
      </div>

      <main class="content"><router-view /></main>
    </div>

    <div class="toast-stack" aria-live="polite">
      <div v-for="t in toasts" :key="t.id" :class="['toast', `toast-${t.tone}`]">{{ t.message }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import MfIcon from './components/MfIcon.vue'
import DemoBanner from './components/DemoBanner.vue'
import { toasts } from './toasts.js'
import { connection } from './connection.js'
import { isDemoMode } from './demoMode.js'

const route = useRoute()
const collapsed = ref(false)
const demoMode = isDemoMode()

const nav = [
  { to: '/console/monitor', label: 'Live Monitor', icon: 'activity' },
  { to: '/console/queue', label: 'Verification Queue', icon: 'queue' },
  { to: '/console/investigate', label: 'Claim Investigation', icon: 'search' },
  { to: '/console/evidence', label: 'Evidence Explorer', icon: 'evidence' },
  { to: '/console/simulations', label: 'Simulations', icon: 'sim' },
  { to: '/console/review', label: 'Moderation Review', icon: 'check' },
  { to: '/console/audit', label: 'Audit Log', icon: 'history' },
  { to: '/console/settings', label: 'Settings', icon: 'settings' }
]

const pageTitle = computed(() => {
  const match = nav.find((n) => n.to === route.path) || { label: 'MiroFish' }
  return match.label
})
const pageSub = computed(() => '')
const connClass = computed(() => ({ online: 'ok', offline: 'bad', degraded: 'warn' }[connection.status.value]))
const connLabel = computed(() => connection.status.value === 'online' ? 'API online' : connection.status.value === 'offline' ? 'API offline' : 'API degraded')
const connTitle = computed(() => `Backend ${connection.base.value}: ${connection.status.value}`)

onMounted(() => { probeConnection() })
</script>

<style scoped>
.shell { display: flex; min-height: 100vh; background: #f7f8fa; color: #111827; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
.sidebar { width: 228px; flex: none; background: #0e1626; color: #cbd5e1; display: flex; flex-direction: column; transition: width 0.15s ease; }
.sidebar.collapsed { width: 60px; }
.brand { display: flex; align-items: center; gap: 10px; padding: 16px 14px; border-bottom: 1px solid #16233a; }
.brand-mark { width: 30px; height: 30px; flex: none; display: flex; align-items: center; justify-content: center; background: #ff5c00; color: #fff; font-weight: 700; font-size: 13px; border-radius: 3px; }
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-text strong { color: #fff; font-size: 14px; letter-spacing: 0.04em; }
.brand-text small { font-size: 10px; letter-spacing: 0.14em; color: #94a3b8; }
.nav { display: flex; flex-direction: column; gap: 2px; padding: 12px 8px; flex: 1; }
.nav-item { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border-radius: 4px; color: #cbd5e1; text-decoration: none; font-size: 13px; font-weight: 600; }
.nav-item:hover { background: #16233a; color: #fff; }
.nav-item.active { background: #fff; color: #0e1626; }
.side-foot { padding: 12px; border-top: 1px solid #16233a; display: flex; align-items: center; gap: 8px; }
.collapse-btn { background: transparent; border: 1px solid #16233a; color: #cbd5e1; border-radius: 4px; padding: 5px 7px; cursor: pointer; }
.main { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.topbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 22px; background: #fff; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; z-index: 20; }
.topbar h1 { font-size: 18px; margin: 0; }
.subtitle { margin: 2px 0 0; font-size: 12px; color: #6b7280; }
.top-actions { display: flex; align-items: center; gap: 10px; }
.conn { display: inline-flex; align-items: center; gap: 6px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 999px; border: 1px solid; }
.conn .dot { width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
.conn.ok { color: #166534; background: #dcfce7; border-color: #86efac; }
.conn.bad { color: #991b1b; background: #fee2e2; border-color: #fca5a5; }
.conn.warn { color: #92400e; background: #fef3c7; border-color: #fcd34d; }
.analyst { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-weight: 600; color: #4b5563; }
.demo-strip { padding: 10px 22px 0; }
.content { padding: 18px 22px 40px; max-width: 1280px; width: 100%; margin: 0 auto; }
.toast-stack { position: fixed; right: 16px; bottom: 16px; display: flex; flex-direction: column; gap: 8px; z-index: 200; }
.toast { background: #0e1626; color: #fff; font-size: 13px; padding: 10px 14px; border-radius: 4px; max-width: 340px; box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25); }
.toast-error { background: #7f1d1d; }
.toast-ok { background: #14532d; }
@media (max-width: 900px) {
  .sidebar { width: 60px; }
  .sidebar .brand-text, .sidebar .nav-item span { display: none; }
  .content { padding: 14px 12px 40px; }
  .topbar { padding: 12px; flex-wrap: wrap; }
}
</style>
