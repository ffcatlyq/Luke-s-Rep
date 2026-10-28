<script setup>
defineProps({
  push: { type: Boolean, default: false },
})
</script>

<template>
  <div
    class="footnote"
    :style="{ marginTop: push ? 'auto' : undefined }"
  >
    <slot />
  </div>
</template>

<style scoped>
.footnote {
  border-top: 1px solid var(--border);
  padding-top: 0.3em;
  padding-bottom: 0.3em;
  font-size: 0.72em;
  color: var(--text-dim);
}
</style>
