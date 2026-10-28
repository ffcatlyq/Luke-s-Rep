# Claude — 主题视觉规则

## 设计语言

Anthropic Claude 原生设计语言。羊皮纸暖白背景（`#FAF9F5`）搭配赭石橙品牌色（`#D97757`），温暖、知性、有质感。这是一个**浅色主题**，与 Terminal Green 和 Dracula 的暗色风格形成对比。

标题使用 Georgia 衬线字体，正文使用 Inter 无衬线字体。无任何装饰效果（无 scanlines、无 glow、无 cursor blink、无 heading prefix），纯粹靠排版层次和暖色调驱动视觉节奏。

整体气质：温暖但不花哨，专业但不冰冷。像一本精心排版的技术书籍。

## 色彩来源

从 Claude 产品界面（claude.ai）和 Anthropic 品牌资产提取。

| 用途 | 色值 | 映射到 |
|------|------|--------|
| 羊皮纸背景 | #FAF9F5 | --bg |
| 赭石橙（品牌色） | #D97757 | --primary |
| 深赭石 | #B8624A | --primary-dim |
| 赭石微光 | rgba(217,119,87,0.10) | --primary-glow |
| 蓝色（链接/信息） | #4A7FC1 | --secondary |
| 琥珀（警告） | #C4841D | --warning |
| 紫色（补充） | #7C5CBF | --accent |
| 红色（危险） | #C4453A | --danger |
| 暖黑（正文） | #1A1915 | --text |
| 橄榄灰（弱化） | #6B6A62 | --text-dim |
| 暖奶油边框 | #E0DDD4 | --border |
| 浅灰表面 | #F0EEE6 | --surface |

## 控件视觉规则

### 标题

- h1：赭石橙（`var(--primary)`），Georgia 衬线，`font-weight: 700`，无 glow，无前缀
- h2：赭石橙（`var(--primary)`），Georgia 衬线，`font-weight: 600`
- h3：暖黑（`var(--text)`），Inter 无衬线，`font-weight: 500`

### 卡片

- 背景 `var(--surface)`（`#F0EEE6`），边框 `var(--border)`（`#E0DDD4`）
- 顶部 2px 色条使用语义色：默认赭石橙
- 圆角 8px
- 阴影：`rgba(0,0,0,0.05) 0px 4px 24px, rgba(38,37,30,0.08) 0px 0px 0px 1px`

### Terminal 窗口

- 背景 `var(--surface)`，边框 `var(--border)`
- 三个圆点：红/橙/绿（使用标准 macOS 窗口按钮色）
- prompt 颜色：赭石橙（`var(--primary)`）
- 输出颜色：暖黑（`var(--text)`）

### 表格

- 表头背景 `var(--surface)`，文字赭石橙
- 行 hover 背景使用 `var(--primary-glow)`
- 边框使用 `var(--border)`

### 代码

- inline code：背景 `var(--surface)`，文字 `var(--text)`，JetBrains Mono
- 代码块：背景 `#EDEAE2`（比 surface 略深）

### 语义色映射

| 语义 | 颜色 | 用途 |
|------|------|------|
| 正面/成功 | 赭石橙 (#D97757) | 完成、推荐、品牌强调 |
| 负面/风险 | 红色 (#C4453A) | 错误、禁止、危险 |
| 中性/信息 | 蓝色 (#4A7FC1) | 链接、信息提示 |
| 注意/警告 | 琥珀 (#C4841D) | 提醒、注意事项 |
| 补充/扩展 | 紫色 (#7C5CBF) | 次要强调、分类标签 |
| 弱化/描述 | 橄榄灰 (#6B6A62) | 次要信息、备注 |

## 图标规则

- 允许彩色图标
- 推荐使用 Carbon 或 Tabler 图标库（线条风格，与 Inter 字体协调）
- 图标颜色应匹配语义色或使用 `var(--text-dim)` 弱化

## 排版特殊规则

- 浅色背景下文字对比度要求更高——正文必须用 `var(--text)`（`#1A1915`），不要用 `var(--text-dim)` 作为正文色
- 强调文字用 `var(--primary)` 赭石橙，不要用加粗替代颜色区分
- 代码块内文字用 JetBrains Mono，与正文 Inter 形成字体对比

## 反模式

- ❌ 不要使用 scanlines 或 glow 效果——这是暖色知性风格，不是赛博朋克
- ❌ 不要在 h2 前加 `$ ` 前缀
- ❌ 不要使用等宽字体作为正文字体——正文用 Inter
- ❌ 不要使用冷色调蓝灰（如 `#64748b`）作为弱化色——用暖灰 `#6B6A62`
- ❌ 不要使用纯白 `#FFFFFF` 作为背景——用羊皮纸 `#FAF9F5`
- ❌ 不要使用纯黑 `#000000` 作为文字——用暖黑 `#1A1915`
