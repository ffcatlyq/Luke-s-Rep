<script setup>
defineProps({
  title: { type: String, default: 'terminal' },
  style: { type: String, default: '' },
  bodyStyle: { type: String, default: '' },
})
</script>

<template>
  <div class="terminal-window" :style="style">
    <div class="terminal-bar">
      <div class="terminal-dot r"></div>
      <div class="terminal-dot y"></div>
      <div class="terminal-dot g"></div>
      <span class="title">{{ title }}</span>
    </div>
    <div class="terminal-body" :style="bodyStyle">
      <slot />
    </div>
  </div>
</template>
