<script setup>
defineProps({
  color: { type: String, default: '' },
  title: { type: String, default: '' },
})
</script>

<template>
  <div class="card" :class="color" style="padding:1.2em 1.4em; display:flex; flex-direction:column;">
    <div v-if="title" class="card-title">
      <span :class="color">{{ title }}</span>
    </div>
    <div class="card-desc">
      <slot />
    </div>
  </div>
</template>
