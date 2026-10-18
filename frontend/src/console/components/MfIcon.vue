<template>
  <svg
    class="mf-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    v-html="path"
  />
</template>

<script setup>
import { computed } from 'vue'
import { ICONS } from '../icons.js'

const props = defineProps({
  name: { type: String, required: true },
  size: { type: [Number, String], default: 16 }
})
const path = computed(() => ICONS[props.name] || '')
</script>

<style scoped>
.mf-icon { flex: none; vertical-align: -3px; }
</style>
