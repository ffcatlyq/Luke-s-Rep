<script setup>
defineProps({
  type: { type: String, default: 'info' },
  title: { type: String, default: '' },
})

const typeConfig = {
  info: { color: 'var(--secondary)' },
  warning: { color: 'var(--warning)' },
  danger: { color: 'var(--danger)' },
  tip: { color: 'var(--primary)' },
  success: { color: 'var(--accent)' },
}
</script>

<template>
  <div
    class="callout"
    :style="{ borderLeftColor: typeConfig[type]?.color || typeConfig.info.color }"
  >
    <div v-if="title" class="callout-title">
      <span :style="{ color: typeConfig[type]?.color || typeConfig.info.color }">{{ title }}</span>
    </div>
    <div class="callout-body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.callout {
  background: var(--surface);
  border-left: 3px solid var(--secondary);
  border-radius: 0 4px 4px 0;
  padding: 0.5em 0.8em;
  margin: 0;
}

.callout-title {
  display: flex;
  align-items: center;
  gap: 0.4em;
  font-weight: 600;
  font-size: 0.88em;
  margin-bottom: 0.3em;
}

.callout-body {
  color: var(--text-dim);
  line-height: 1.6;
}
</style>
