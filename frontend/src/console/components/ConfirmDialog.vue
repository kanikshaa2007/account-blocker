<template>
  <div v-if="open" class="dlg-backdrop" @click.self="cancel">
    <div class="dlg mf-card" role="dialog" aria-modal="true" :aria-label="title">
      <h3 class="dlg-title">{{ title }}</h3>
      <p class="dlg-body"><slot>{{ body }}</slot></p>
      <div v-if="requireReason" class="dlg-reason">
        <label class="mf-label" :for="reasonId">{{ reasonLabel }}</label>
        <textarea :id="reasonId" v-model="reason" class="mf-input" rows="3" />
      </div>
      <div class="dlg-actions">
        <button class="mf-btn" @click="cancel">{{ cancelLabel }}</button>
        <button class="mf-btn" :class="danger ? 'mf-btn-danger' : 'mf-btn-primary'" :disabled="requireReason && !reason.trim()" @click="confirm">
          {{ confirmLabel }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const props = defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
  body: { type: String, default: '' },
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
  danger: { type: Boolean, default: false },
  requireReason: { type: Boolean, default: false },
  reasonLabel: { type: String, default: 'Reason' }
})
const emit = defineEmits(['confirm', 'cancel'])
const reason = ref('')
const reasonId = `dlg-reason-${Math.random().toString(36).slice(2)}`
function confirm() { emit('confirm', reason.value); reason.value = '' }
function cancel() { emit('cancel'); reason.value = '' }
</script>

<style scoped>
.dlg-backdrop { position: fixed; inset: 0; background: rgba(11, 19, 34, 0.5); display: flex; align-items: center; justify-content: center; z-index: 100; padding: 16px; }
.dlg { max-width: 460px; width: 100%; padding: 20px; }
.dlg-title { font-family: var(--mf-font-display); font-size: 16px; margin: 0 0 8px; }
.dlg-body { font-size: 13px; color: var(--mf-ink-soft); margin: 0 0 12px; }
.dlg-reason textarea { width: 100%; resize: vertical; }
.dlg-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 14px; }
</style>
