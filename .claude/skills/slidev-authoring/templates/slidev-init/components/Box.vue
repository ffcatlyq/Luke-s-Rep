<script setup>
defineProps({
  title: { type: String, default: '' },
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
  <fieldset
    class="box"
    :style="{
      borderColor: colorMap[color] || 'var(--border)',
    }"
  >
    <legend
      v-if="title"
      class="box-legend"
      :style="{ color: colorMap[color] || 'var(--primary)' }"
    >
      {{ title }}
    </legend>
    <slot />
  </fieldset>
</template>

<style scoped>
.box {
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.4em 0.8em 0.8em;
  margin: 0;
}

.box-legend {
  font-weight: 600;
  padding: 0 0.4em;
  font-size: 0.9em;
}
</style>
