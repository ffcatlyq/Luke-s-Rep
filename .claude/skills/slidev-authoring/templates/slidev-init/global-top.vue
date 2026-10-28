<script setup>
import { useNav } from '@slidev/client'
import { computed, ref, onMounted } from 'vue'
const { currentLayout } = useNav()

const isLightTheme = ref(false)
onMounted(() => {
  const bg = getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()
  isLightTheme.value = bg === '#ffffff' || bg === '#fff' || bg === 'white' || bg === '#f3f3f3'
})

const logoSrc = computed(() => isLightTheme.value ? '/logo-dark.png' : '/logo-light.png')
</script>

<template>
  <!-- Logo on content pages. Place logo-dark.png / logo-light.png in public/ -->
  <div v-if="currentLayout !== 'cover' && currentLayout !== 'section'" class="global-top-bar">
    <img :src="logoSrc" alt="Logo" class="global-logo" />
  </div>
</template>

<style scoped>
.global-top-bar {
  position: absolute;
  top: 1.2em;
  right: 1.5em;
  z-index: 20;
  display: flex;
  align-items: center;
}
.global-logo {
  width: 80px;
  height: auto;
  object-fit: contain;
  opacity: var(--logo-opacity, 0.6);
  pointer-events: none;
}
</style>
