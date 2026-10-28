<script setup>
import { useNav } from '@slidev/client'
const { currentLayout } = useNav()
</script>

<template>
  <!-- Footer on content pages. Customize text below. -->
  <div v-if="currentLayout !== 'cover' && currentLayout !== 'section'" class="global-footer">
    <span class="footer-text">Presentation Title</span>
  </div>
</template>

<style scoped>
.global-footer {
  position: absolute;
  bottom: 0.8em;
  left: 1.5em;
  z-index: 20;
  pointer-events: none;
}
.footer-text {
  font-size: 0.6em;
  color: var(--text-dim);
  opacity: 0.4;
}
</style>
