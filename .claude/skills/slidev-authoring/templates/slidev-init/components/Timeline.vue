<script setup>
/**
 * Timeline — 纵向时间线，圆点 + 日期 + 描述。
 *
 * Props:
 *   items: Array<{ date, title, desc? }>
 *   color: 圆点和连线颜色（CSS color string，默认 var(--primary)）
 */
defineProps({
  items: { type: Array, required: true },
  color: { type: String, default: 'var(--primary)' },
})
</script>

<template>
  <div class="timeline">
    <div
      v-for="(item, i) in items"
      :key="i"
      class="timeline-item"
    >
      <div class="timeline-track">
        <div class="timeline-dot" :style="{ background: color }" />
        <div
          v-if="i < items.length - 1"
          class="timeline-line"
          :style="{ background: color }"
        />
      </div>
      <div class="timeline-content">
        <div class="timeline-date" :style="{ color }">{{ item.date }}</div>
        <div class="timeline-title">{{ item.title }}</div>
        <div v-if="item.desc" class="timeline-desc">{{ item.desc }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-item {
  display: flex;
  gap: 0.8em;
  min-height: 2.4em;
}

.timeline-track {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 0.7em;
  flex-shrink: 0;
}

.timeline-dot {
  width: 0.55em;
  height: 0.55em;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 0.25em;
}

.timeline-line {
  width: 2px;
  flex: 1;
  opacity: 0.3;
}

.timeline-content {
  padding-bottom: 0.8em;
}

.timeline-date {
  font-size: 0.75em;
  font-weight: 600;
}

.timeline-title {
  font-size: 0.85em;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
}

.timeline-desc {
  font-size: 0.75em;
  color: var(--text-dim);
  line-height: 1.5;
  margin-top: 0.1em;
}
</style>
