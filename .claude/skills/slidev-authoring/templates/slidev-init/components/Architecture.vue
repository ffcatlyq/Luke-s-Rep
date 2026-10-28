<script setup>
defineProps({
  labels: { type: Array, default: () => [] },
  arrows: { type: Boolean, default: true },
  gap: { type: String, default: '0.5em' },
})

// Slot names: layer0, layer1, layer2, ... (or top, middle, bottom for 3-layer)
const slotAliases = { top: 'layer0', middle: 'layer1', bottom: 'layer2' }
</script>

<template>
  <div class="arch" :style="{ gap }">
    <template v-for="(label, i) in labels" :key="i">
      <div class="arch-layer">
        <div v-if="label" class="arch-label">{{ label }}</div>
        <div class="arch-content">
          <slot :name="`layer${i}`" />
          <!-- Aliases for convenience -->
          <slot v-if="i === 0" name="top" />
          <slot v-if="i === 1" name="middle" />
          <slot v-if="i === 2" name="bottom" />
        </div>
      </div>
      <div v-if="arrows && i < labels.length - 1" class="arch-arrow">▼</div>
    </template>
  </div>
</template>

<style scoped>
.arch {
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.arch-layer {
  display: flex;
  align-items: center;
  gap: 0.6em;
}

.arch-label {
  font-size: 0.72em;
  color: var(--text-dim);
  font-weight: 600;
  min-width: 4em;
  text-align: right;
  flex-shrink: 0;
}

.arch-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6em;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.5em 0.8em;
}

.arch-arrow {
  text-align: center;
  color: var(--primary);
  font-size: 0.8em;
  opacity: 0.6;
  line-height: 1;
  padding: 0.1em 0;
}
</style>
