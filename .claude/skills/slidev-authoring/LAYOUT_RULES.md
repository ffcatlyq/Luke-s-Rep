# Slidev 布局规则

## 三层模型

```
画布 (960×540, 16:9)
+------------------------------------------+
|  标题区 (h1 + 引导句，自然高度)             |
+------------------------------------------+
|                                          |
|  内容区 (flex:1, display:flex, gap:1.2em) |
|  +----------+  +----------+             |
|  |  槽位 A   |  |  槽位 B   |             |
|  |  组件群    |  |  组件群    |             |
|  +----------+  +----------+             |
|                                          |
+------------------------------------------+
|  <Footnote push> (底边文字)               |
+------------------------------------------+
```

- **画布层**：每页 slide 的根容器，`display:flex; flex-direction:column; height:100%`
- **槽位层**：内容区内的分栏，用 inline style（flex/grid）控制，不需要组件化
- **组件层**：槽位内的可视化元素，使用 `components/` 下的 Vue 组件

## 填充规则

1. 槽位内用 `justify-content:space-evenly` 纵向均匀分布组件
2. 填充不足时调节顺序：
   - 第一：增大组件间 gap
   - 第二：增大组件内 padding / row-gap
   - 第三：增大图形元素尺寸（漏斗行高、色块宽度等）
   - **禁止**：改变 font-size 来填充空间
3. 组件自身 margin 为 0，间距由外部布局控制
4. **标题-内容内聚**：`.section-title` 和它描述的内容块必须包裹在同一个 `<div>` 内形成语义组，`space-evenly` 作用于语义组之间而非标题和内容之间。标题与内容的间距由组内 `gap` 或 `margin` 控制（通常 0.2–0.3em），语义组之间的间距由外层 flex 布局控制。

```html
<!-- ✅ 正确：标题和内容包裹为一个语义组 -->
<div>
  <div class="section-title">标题</div>
  <!-- 内容组件 -->
</div>

<!-- ❌ 错误：标题和内容是平级 flex children -->
<div class="section-title">标题</div>
<!-- 内容组件 -->
```

## 组件变体选择矩阵

N 个并列概念根据数量和可用空间选择布局：

| 数量 | 空间宽 > 高 | 空间高 > 宽 |
|---|---|---|
| 2 | `<Flow>` 横排 | 2 个 `<Box>` 纵排 |
| 3 | 3 个 `<Stat>` 或 `<Flow>` 横排 | 3 个 `<Box>` 纵排 |
| 4 | 2×2 CSS Grid + `<Box>` | 4 个 `<Box>` 纵排 |
| 5-6 | `<Flow>` 横排 | `<StepList>` 纵排 |
| 7+ | 表格或纵排条带 | 表格或纵排条带 |

选择规则：看可用空间宽高比，宽 > 高选横排，高 > 宽选纵排。4 个且空间接近正方形用田字格。

## 组件库

### 信息展示

| 组件 | 用途 | 关键 Props |
|---|---|---|
| `<Callout type title>` | 强调框 | `type`(info/warning/danger/tip/success), `title`, slot |
| `<Box title color>` | 信息卡片 | `title`, `color`, slot |
| `<Card title color>` | 通用卡片 | `title`, `color`, slot |
| `<Stat value label color>` | 数字条带 | `value`, `label`, `color` |
| `<Badge color>` | 状态标签 | `color`, slot |

### 流程与步骤

| 组件 | 用途 | 关键 Props |
|---|---|---|
| `<Flow :steps direction arrow>` | 流程步骤（横排/纵排） | `steps`, `direction`, `arrow`, `color` |
| `<StepList :items colors>` | 编号步骤列表 | `items`[{title, desc?}], `colors`[] |
| `<Funnel :items width>` | 漏斗图 + 右侧文字 | `items`[{label, desc, color}], `width`, `height`, `rowGap` |
| `<Timeline :items color>` | 时间线 | `items`[{date, title, desc?}], `color` |

### 结构与装饰

| 组件 | 用途 | 关键 Props |
|---|---|---|
| `<Architecture :labels>` | 架构层图 | `labels`, `arrows`, `gap`, slots |
| `<Divider text>` | 分隔线 | `text`, `mt`, `mb` |
| `<Footnote push>` | 底边文字 | `push`(boolean), slot |
| `<Terminal title>` | 终端窗口 | `title`, `style`, `bodyStyle`, slot |
| `<Chart type :data>` | D3 可视化 | `type`, `data`, `width`, `height` |

### CSS Class

| Class | 用途 |
|---|---|
| `.section-title` | 区域标题（font-weight:600, font-size:0.88em, color:var(--primary)） |

### 不需要组件化

| 元素 | 原因 |
|---|---|
| Markdown 表格 | base.css 已统一样式 |
| Mermaid 图 | 独立渲染引擎 |
| 槽位布局 | 页面级，inline style 合理 |
| 区域标题 | `.section-title` CSS class 即可 |

## 用法示例

### Funnel

```html
<Funnel :items="[
  { label: 'Step 1', desc: '<strong>描述</strong>', color: '#0b41cd' },
  { label: 'Step 2', desc: '描述文字', color: '#5aad3a' },
]" />
```

### Callout

```html
<Callout type="success" title="标题">正文内容</Callout>
<Callout type="warning">无标题的强调框</Callout>
```

### StepList

```html
<StepList :items="[
  { title: '步骤一', desc: '描述' },
  { title: '步骤二', desc: '描述' },
]" :colors="['#0b41cd', '#5aad3a']" />
```

### Timeline

```html
<Timeline :items="[
  { date: '2026-Q1', title: '里程碑', desc: '详细描述' },
  { date: '2026-Q2', title: '里程碑' },
]" />
```

### Footnote

```html
<Footnote>底边注释文字</Footnote>
<!-- push 到底部 -->
<Footnote push>底边注释文字</Footnote>
```
