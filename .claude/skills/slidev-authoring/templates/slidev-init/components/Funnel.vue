<script setup>
/**
 * Funnel — CSS Grid 两列漏斗图 + 右侧对齐文字。
 *
 * Props:
 *   items: Array<{ label, desc, color }>
 *     - label: 色块内白色文字
 *     - desc:  右侧描述（支持 HTML）
 *     - color: 色块背景色（CSS color string）
 *   width:    色块列宽度（CSS length，默认 '16em'）
 *   height:   每行色块高度（CSS length，默认 '2.2em'）
 *   rowGap:   行间距（CSS length，默认 '0.35em'）
 *
 * 色块宽度自动从 100% 线性递减到 ~30%。
 */
const props = defineProps({
  items: { type: Array, required: true },
  width: { type: String, default: '16em' },
  height: { type: String, default: '2.2em' },
  rowGap: { type: String, default: '0.35em' },
})

function barWidth(index) {
  const n = props.items.length
  if (n <= 1) return '100%'
  // Linear from 100% to 30%
  const pct = 100 - (70 * index) / (n - 1)
  return `${pct}%`
}
</script>

<template>
  <div
    class="funnel"
    :style="{ gridTemplateColumns: `${width} 1fr`, rowGap }"
  >
    <template v-for="(item, i) in items" :key="i">
      <div class="funnel-bar-cell">
        <div
          class="funnel-bar"
          :style="{
            width: barWidth(i),
            height,
            background: item.color,
          }"
        >
          <span class="funnel-bar-label">{{ item.label }}</span>
        </div>
      </div>
      <div
        class="funnel-desc"
        v-html="item.desc"
      />
    </template>
  </div>
</template>

<style scoped>
.funnel {
  display: grid;
  column-gap: 1.2em;
}

.funnel-bar-cell {
  display: flex;
  justify-content: center;
  align-items: center;
}

.funnel-bar {
  border-radius: 3px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.funnel-bar-label {
  color: #fff;
  font-size: 0.82em;
  font-weight: 600;
}

.funnel-desc {
  display: flex;
  align-items: center;
  font-size: 0.82em;
  color: var(--text-dim);
}

.funnel-desc :deep(strong) {
  margin-right: 0.4em;
}
</style>
