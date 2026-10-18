<template>
  <div class="urgency" :title="title">
    <div class="urgency-top">
      <span class="urgency-score mf-mono">{{ score.toFixed(2) }}</span>
      <MfBadge :tone="tierTone" :label="tierLabel" />
      <span v-if="spreadEstimated" class="est">spread estimated</span>
    </div>
    <div class="urgency-bar" role="img" :aria-label="title">
      <span class="seg harm" :style="{ width: pct.harm + '%' }"></span>
      <span class="seg unc" :style="{ width: pct.unc + '%' }"></span>
      <span class="seg spread" :style="{ width: pct.spread + '%' }"></span>
      <span class="seg cx" :style="{ width: pct.cx + '%' }"></span>
    </div>
    <div class="urgency-legend">
      <span><i class="sw harm"></i>Harm</span>
      <span><i class="sw unc"></i>Uncertainty</span>
      <span><i class="sw spread"></i>Spread</span>
      <span><i class="sw cx"></i>Complexity</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import MfBadge from './MfBadge.vue'

const props = defineProps({
  score: { type: Number, default: 0 },
  tier: { type: String, default: 'normal' },
  harm: { type: Number, default: 0 },
  uncertainty: { type: Number, default: 0 },
  spread: { type: Number, default: 0 },
  complexity: { type: Number, default: 0 },
  spreadEstimated: { type: Boolean, default: false },
  title: { type: String, default: 'Verification urgency: weighted harm, uncertainty, spread, complexity. Not a falsity score.' }
})
const total = computed(() => (props.harm + props.uncertainty + props.spread + props.complexity) || 1)
const pct = computed(() => ({
  harm: (props.harm / total.value) * 100,
  unc: (props.uncertainty / total.value) * 100,
  spread: (props.spread / total.value) * 100,
  cx: (props.complexity / total.value) * 100
}))
const tierTone = computed(() => ({ low: 'gray', normal: 'blue', high: 'amber', urgent: 'red' }[props.tier] || 'gray'))
const tierLabel = computed(() => props.tier.toUpperCase())
</script>

<style scoped>
.urgency { min-width: 170px; }
.urgency-top { display: flex; align-items: center; gap: 8px; margin-bottom: 5px; }
.urgency-score { font-weight: 700; font-size: 13px; }
.est { font-size: 10px; font-weight: 700; letter-spacing: 0.05em; color: #92400e; background: #fef3c7; padding: 1px 6px; border-radius: 999px; }
.urgency-bar { display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: #eef1f5; }
.seg.harm { background: #dc2626; } .seg.unc { background: #d97706; }
.seg.spread { background: #1d4ed8; } .seg.cx { background: #6b7280; }
.urgency-legend { display: flex; gap: 8px; margin-top: 4px; font-size: 10px; color: #6b7280; flex-wrap: wrap; }
.sw { display: inline-block; width: 7px; height: 7px; border-radius: 2px; margin-right: 3px; }
.sw.harm { background: #dc2626; } .sw.unc { background: #d97706; }
.sw.spread { background: #1d4ed8; } .sw.cx { background: #6b7280; }
</style>
