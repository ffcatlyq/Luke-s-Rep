# Roche Blue 主题视觉规则

## 设计来源

基于 PDALM China AI Strategy.pdf 和 Rojectory.pdf 的视觉分析：
- PDALM 的克制白底 + 深灰文字 + 蓝色强调色
- Rojectory 的暗色 section 页面

## 色彩体系

### 主色

| Token | 色值 | 用途 |
|-------|------|------|
| `--primary` | `#0b41cd` | Roche 蓝，标题、强调、链接 |
| `--primary-dim` | `#1482fa` | 亮蓝，次级强调、图表辅助色 |
| `--warning` | `#ed4a0d` | Roche 橙，少量点缀、关键数据、callout |
| `--accent` | `#7ab33a` | 绿色，正面/成功指标 |
| `--danger` | `#d0021b` | 红色，风险/错误 |

### 背景

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg` | `#ffffff` | 内容页白底 |
| `--bg-section` | `#0d0d0d` | Section/Cover 页暗底 |
| `--surface` | `#f3f3f3` | 卡片、表头、代码块背景 |
| `--surface-blue` | `#bde3ff` | 蓝色高亮带背景 |

### 文字

| Token | 色值 | 用途 |
|-------|------|------|
| `--text` | `#434343` | 正文（深灰，非纯黑） |
| `--text-dim` | `#706b69` | 辅助文字、备注 |
| `--text-on-dark` | `#f3f3f3` | 暗底页面文字 |

## 配色规则

1. **橙色克制使用** — `--warning` 只用于关键数据点、callout 边框、少量强调文字。一页不超过 2 处
2. **蓝色是主角** — 标题、表头、链接、分隔线统一用 `--primary`
3. **正文不用纯黑** — 用 `#434343`，视觉更柔和
4. **暗页只用于 section 和 cover** — 内容页始终白底

## 字体

| 用途 | 字体 | 回退 |
|------|------|------|
| 正文/标题 | Inter | Noto Sans SC, system-ui |
| 中文 | Noto Sans SC | — |
| 代码 | JetBrains Mono | monospace |
| 引用斜体 | Lora (italic) | serif |

### 字体规则

1. 标题 `font-weight: 600`（Semi-bold），不用 700 Bold
2. 正文 `font-weight: 400`
3. 中英文混排时 Noto Sans SC 自动接管 CJK 字符
4. 引用中的斜体用 Lora serif 字体，增加视觉区分

## 页面类型

### 内容页 (default)
- 白底 `#ffffff`
- 顶部 3px 渐变色条：`--primary` → `--primary-dim` → `--warning`
- 标题蓝色，正文深灰

### Section 页
- 纯黑底 `#0d0d0d`
- 白色大标题，无装饰
- 副标题 60% 白色透明度

### Cover 页
- 同 section 页暗底
- 标题 2.5em，副标题 70% 白色透明度

## 专属控件

### `.highlight-band`
蓝色高亮带，用于重要信息：
```html
<div class="highlight-band">关键信息</div>
```
- 背景 `--surface-blue`，左边框 `--primary`

### `.callout-orange`
橙色 callout，用于警告或关键数据：
```html
<div class="callout-orange">注意事项</div>
```
- 背景 `rgba(237, 74, 13, 0.08)`，左边框 `--warning`

### `.surface-card`
浅灰卡片容器：
```html
<div class="surface-card">内容</div>
```

### `.roche-divider`
蓝色渐变分隔线：
```html
<hr class="roche-divider" />
```

## 与其他主题的差异

| 维度 | Terminal Green | Dracula | **Roche Blue** |
|------|---------------|---------|---------------|
| 底色 | 暗色 | 暗色 | **白色**（section 暗色） |
| 主色 | 绿色荧光 | 紫色 | **蓝色** |
| 字体 | JetBrains Mono | Inter | **Inter + Noto Sans SC** |
| 装饰 | 扫描线 + 光晕 | 阴影 | **顶部色条 + 渐变分隔线** |
| 调性 | 赛博朋克 | 暗色多彩 | **企业正式** |
