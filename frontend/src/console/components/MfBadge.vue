<template>
  <span :class="['mf-badge', toneClass]"><span class="dot" aria-hidden="true"></span>{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tone: { type: String, default: 'gray' }, // gray | amber | red | green | blue
  label: { type: String, required: true }
})
const toneClass = computed(() => `mf-badge-${props.tone}`)
</script>
