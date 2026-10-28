<script setup>
const props = defineProps({
  name: { type: String, required: true },
  size: { type: String, default: '48' },
  label: { type: String, default: '' },
})
</script>

<template>
  <span class="aws-icon-wrapper" :style="{ display: 'inline-flex', alignItems: 'center', gap: '0.4em' }">
    <img
      class="aws-icon"
      :src="`/icons/aws/${name}.svg`"
      :alt="label || name"
      :width="size"
      :height="size"
    />
    <span v-if="label" class="aws-icon-label">{{ label }}</span>
  </span>
</template>

<style scoped>
.aws-icon-label {
  font-size: 0.85em;
  color: var(--text);
  white-space: nowrap;
}
</style>
