<script setup>
const props = defineProps({
  steps: { type: Array, required: true },
  direction: { type: String, default: 'horizontal' },
  arrow: { type: String, default: '→' },
  color: { type: String, default: '' },
})

// Normalize steps: accept strings or {label, desc, icon} objects
function normalize(step) {
  if (typeof step === 'string') return { label: step }
  return step
}
</script>

<template>
  <div class="flow" :class="[direction, color]">
    <template v-for="(step, i) in steps" :key="i">
      <div class="flow-step">
        <div v-if="normalize(step).icon" class="flow-icon" v-html="normalize(step).icon" />
        <div class="flow-label">{{ normalize(step).label }}</div>
        <div v-if="normalize(step).desc" class="flow-desc">{{ normalize(step).desc }}</div>
      </div>
      <div v-if="i < steps.length - 1" class="flow-arrow">{{ arrow }}</div>
    </template>
  </div>
</template>

<style scoped>
.flow {
  display: flex;
  align-items: center;
  gap: 0.4em;
}
.flow.vertical {
  flex-direction: column;
}
.flow.vertical .flow-arrow {
  transform: rotate(90deg);
}

.flow-step {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.35em 0.7em;
  text-align: center;
  flex-shrink: 0;
}
.flow-step:first-child,
.flow-step:last-child {
  border-color: var(--primary-dim);
}

.flow-icon {
  font-size: 1.2em;
  margin-bottom: 0.15em;
  color: var(--primary);
}

.flow-label {
  font-weight: 600;
  font-size: 0.85em;
  color: var(--text);
  white-space: nowrap;
}

.flow-desc {
  font-size: 0.72em;
  color: var(--text-dim);
  line-height: 1.4;
  margin-top: 0.1em;
}

.flow-arrow {
  color: var(--primary);
  font-size: 1em;
  flex-shrink: 0;
  opacity: 0.7;
}

/* Color variants */
.flow.blue .flow-step:first-child,
.flow.blue .flow-step:last-child { border-color: var(--secondary); }
.flow.blue .flow-arrow { color: var(--secondary); }
.flow.blue .flow-icon { color: var(--secondary); }

.flow.yellow .flow-step:first-child,
.flow.yellow .flow-step:last-child { border-color: var(--warning); }
.flow.yellow .flow-arrow { color: var(--warning); }
.flow.yellow .flow-icon { color: var(--warning); }

.flow.purple .flow-step:first-child,
.flow.purple .flow-step:last-child { border-color: var(--accent); }
.flow.purple .flow-arrow { color: var(--accent); }
.flow.purple .flow-icon { color: var(--accent); }

.flow.red .flow-step:first-child,
.flow.red .flow-step:last-child { border-color: var(--danger); }
.flow.red .flow-arrow { color: var(--danger); }
.flow.red .flow-icon { color: var(--danger); }
</style>
