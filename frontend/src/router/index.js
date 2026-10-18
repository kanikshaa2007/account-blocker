import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '../console/AppShell.vue'
import Overview from '../console/views/Overview.vue'
import LiveMonitor from '../console/views/LiveMonitor.vue'
import VerifyQueue from '../console/views/VerifyQueue.vue'
import Investigation from '../console/views/Investigation.vue'
import EvidenceExplorer from '../console/views/EvidenceExplorer.vue'
import Simulations from '../console/views/Simulations.vue'
import Review from '../console/views/Review.vue'
import AuditLog from '../console/views/AuditLog.vue'
import Settings from '../console/views/Settings.vue'

const routes = [
  { path: '/', component: AppShell, redirect: '/console/monitor' },
  {
    path: '/console',
    component: AppShell,
    children: [
      { path: '', name: 'ConsoleOverview', component: Overview },
      { path: 'monitor', name: 'ConsoleMonitor', component: LiveMonitor },
      { path: 'queue', name: 'ConsoleQueue', component: VerifyQueue },
      { path: 'investigate/:id', name: 'ConsoleInvestigate', component: Investigation },
      { path: 'evidence', name: 'ConsoleEvidence', component: EvidenceExplorer },
      { path: 'simulations', name: 'ConsoleSimulations', component: Simulations },
      { path: 'review', name: 'ConsoleReview', component: Review },
      { path: 'audit', name: 'ConsoleAudit', component: AuditLog },
      { path: 'settings', name: 'ConsoleSettings', component: Settings }
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })
export default router
