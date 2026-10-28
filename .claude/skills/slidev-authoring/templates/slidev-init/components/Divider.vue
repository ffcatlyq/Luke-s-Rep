<script setup>
defineProps({
  text: { type: String, required: true },
  mt: { type: String, default: '0.6em' },
  mb: { type: String, default: '0.3em' },
})
</script>

<template>
  <div style="display:flex; align-items:center; gap:0.8em;" :style="{ marginTop: mt, marginBottom: mb }">
    <div style="flex:1; height:1px; background:var(--border);"></div>
    <span style="font-size:1.05em; color:var(--text); font-weight:600;">{{ text }}</span>
    <div style="flex:1; height:1px; background:var(--border);"></div>
  </div>
</template>
