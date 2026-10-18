<template>
  <div class="lang-switcher">
    <span class="lang-label">Language: English</span>
    <select class="mf-select" disabled>
      <option>English</option>
    </select>
  </div>
</template>

<script setup></script>

<style scoped>
.lang-switcher { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #6b7280; }
.lang-switcher select { font-size: 12px; padding: 4px 8px; border-radius: 4px; border: 1px solid #d1d5db; background: #fff; color: #111827; cursor: not-allowed; }
</style>
