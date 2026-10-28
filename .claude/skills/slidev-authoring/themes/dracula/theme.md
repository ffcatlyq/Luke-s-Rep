# Dracula — 主题视觉规则

## 设计语言

Dracula 暗色多彩主题。深灰紫背景（`#282A36`）搭配高饱和度色板——紫色（Purple）作为主色用于标题和常量，青色（Cyan）用于链接和辅助信息，粉色（Pink）用于关键字和点缀，橙色（Orange）用于警告和强调，绿色（Green）用于正面/成功状态。

与 Terminal Green 的单色极客风不同，Dracula 通过**多色语义映射**区分信息层次，视觉上更活泼丰富。无特效装饰（无 scanlines、无 glow、无 cursor blink），纯粹靠色彩和排版驱动。

字体使用 Inter 无衬线字体（正文），代码块使用 Fira Code。

## 色彩来源

所有色值来自 Dracula 官方规范：https://spec.draculatheme.com/

| Dracula 名称 | 色值 | 映射到 |
|-------------|------|--------|
| Background | #282A36 | --bg |
| Purple | #BD93F9 | --primary |
| Comment | #6272A4 | --primary-dim, --text-dim |
| Cyan | #8BE9FD | --secondary |
| Orange | #FFB86C | --warning |
| Pink | #FF79C6 | --accent |
| Red | #FF5555 | --danger |
| Foreground | #F8F8F2 | --text |
| Current Line | #44475A | --border |
| (自定义) | #343746 | --surface |

## 控件视觉规则

### 标题

- h1：紫色（`var(--primary)`），`font-weight: 700`，无 glow，无前缀
- h2：紫色（`var(--primary)`），`font-weight: 600`，无 `$ ` 前缀
- h3：前景色（`var(--text)`），`font-weight: 500`

### 卡片

- 背景 `var(--surface)`，边框 `var(--border)`
- 顶部 2px 色条使用语义色：默认紫色，`.blue` 青色，`.yellow` 橙色，`.purple` 粉色，`.red` 红色
- 圆角 8px（比 Terminal Green 的 4px 更圆润）

### Terminal 窗口

- 背景 `var(--surface)`，边框 `var(--border)`
- 三个圆点：红/橙/绿（使用 Dracula 的 Red/Orange/Green 而非 Yellow）
- prompt 颜色：紫色（`var(--primary)`）
- 输出颜色：紫色（`var(--primary)`）

### 表格

- 表头背景 `var(--surface)`，文字紫色
- 行 hover 背景使用 `var(--primary-glow)`

### 代码

- inline code：背景 `var(--surface)`，文字青色（`var(--secondary)`）——Dracula 中 code 用 Cyan
- 代码块：背景比页面更深（`#1E1F29`）

### 语义色映射

| 语义 | 颜色 | 用途 |
|------|------|------|
| 正面/成功 | Cyan (#8BE9FD) | 完成、通过、推荐 |
| 负面/风险 | Red (#FF5555) | 错误、禁止、危险 |
| 中性/信息 | Purple (#BD93F9) | 标题、默认强调 |
| 注意/警告 | Orange (#FFB86C) | 提醒、注意事项 |
| 补充/扩展 | Pink (#FF79C6) | 点缀、次要强调 |
| 弱化/描述 | Comment (#6272A4) | 次要信息、备注 |

## 图标规则

- 允许彩色 emoji 和图标（与 Terminal Green 不同）
- 推荐使用 Phosphor 或 Carbon 图标库
- 图标颜色应匹配语义色

## 反模式

- ❌ 不要使用 scanlines 或 glow 效果
- ❌ 不要在 h2 前加 `$ ` 前缀
- ❌ 不要使用等宽字体作为正文字体
- ❌ 不要使用 Green (#50FA7B) 作为主色——Dracula 的主色是 Purple
- ❌ 不要把所有强调都用同一个颜色——Dracula 的核心是多色语义区分
