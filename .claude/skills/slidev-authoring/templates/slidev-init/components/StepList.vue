<script setup>
/**
 * StepList — 编号步骤列表，纵向排列。
 *
 * Props:
 *   items:  Array<{ title, desc? }>
 *   colors: Array<string> — 每步编号圆圈和左边框的颜色。
 *           长度不足时循环使用，默认 [var(--primary)]。
 */
const props = defineProps({
  items: { type: Array, required: true },
  colors: { type: Array, default: () => ['var(--primary)'] },
})

function stepColor(index) {
  return props.colors[index % props.colors.length]
}
</script>

<template>
  <div class="step-list">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="step-item"
      :style="{ borderLeftColor: stepColor(i) }"
    >
      <div class="step-header">
        <div
          class="step-number"
          :style="{ background: stepColor(i) }"
        >
          {{ i + 1 }}
        </div>
        <div class="step-text">
          <span class="step-title">{{ item.title }}</span><span v-if="item.desc" class="step-desc">：{{ item.desc }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.step-list {
  display: flex;
  flex-direction: column;
  gap: 0.35em;
}

.step-item {
  border-left: 3px solid var(--primary);
  border-radius: 0 4px 4px 0;
  padding: 0.3em 0.7em;
  background: var(--surface);
}

.step-header {
  display: flex;
  align-items: center;
  gap: 0.5em;
}

.step-number {
  width: 1.5em;
  height: 1.5em;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 0.75em;
  font-weight: 700;
  flex-shrink: 0;
}

.step-text {
  font-size: 0.85em;
  line-height: 1.4;
}

.step-title {
  font-weight: 600;
  color: var(--text);
}

.step-desc {
  font-weight: 400;
  color: var(--text-dim);
}
</style>
