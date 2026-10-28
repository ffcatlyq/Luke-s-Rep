<script setup>
defineProps({
  value: { type: String, required: true },
  label: { type: String, default: '' },
  color: { type: String, default: '' },
})

const colorMap = {
  green: 'var(--primary)',
  blue: 'var(--secondary)',
  yellow: 'var(--warning)',
  purple: 'var(--accent)',
  red: 'var(--danger)',
}
</script>

<template>
  <div class="stat">
    <div class="stat-value" :style="{ color: colorMap[color] || 'var(--primary)' }">
      {{ value }}
    </div>
    <div v-if="label" class="stat-label">{{ label }}</div>
  </div>
</template>

<style scoped>
.stat {
  text-align: center;
  min-width: 4em;
}

.stat-value {
  font-size: 2em;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.78em;
  color: var(--text-dim);
  margin-top: 0.2em;
}
</style>
