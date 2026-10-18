<template>
  <div class="mf-empty">
    <MfIcon :name="icon" size="26" />
    <p class="empty-title">{{ title }}</p>
    <p v-if="hint" class="empty-hint">{{ hint }}</p>
    <slot />
  </div>
</template>

<script setup>
import MfIcon from './MfIcon.vue'
defineProps({
  icon: { type: String, default: 'search' },
  title: { type: String, required: true },
  hint: { type: String, default: '' }
})
</script>

<style scoped>
.mf-empty { color: var(--mf-muted); }
.mf-empty .mf-icon { opacity: 0.5; }
.empty-title { font-weight: 700; color: var(--mf-ink-soft); margin: 8px 0 4px; font-size: 14px; }
.empty-hint { font-size: 12px; margin: 0 0 10px; }
</style>
