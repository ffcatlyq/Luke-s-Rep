<script setup>
defineProps({
  color: { type: String, default: 'green' },
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
  <span
    class="badge"
    :style="{
      color: colorMap[color] || 'var(--primary)',
      borderColor: colorMap[color] || 'var(--primary)',
    }"
  >
    <slot />
  </span>
</template>

<style scoped>
.badge {
  display: inline-block;
  font-size: 0.75em;
  font-weight: 600;
  border: 1px solid;
  border-radius: 3px;
  padding: 0.05em 0.45em;
  line-height: 1.5;
  white-space: nowrap;
  vertical-align: middle;
}
</style>
