# Terminal Green — 主题视觉规则

## 设计语言

赛博朋克终端风格。所有元素模拟命令行界面，暗色背景（`#0d1117`）配绿色荧光（`#39d353`）强调。整体感觉像在一个高级开发者的终端里浏览信息——冷峻、精确、信息密度高。

字体统一使用 JetBrains Mono 等宽字体，包括标题和正文。这是该主题最显著的视觉特征之一——等宽字体让所有文字都带有"代码"质感。

## 控件视觉规则

以下仅列出 Terminal Green 专属的视觉处理。控件的结构和布局规则见 LAYOUT_RULES.md。

### 终端窗口（Terminal）

该主题的标志性控件。三色圆点标题栏（红黄绿）是最强视觉锚点。

- 标题栏：`background: var(--border)`，三个 10px 圆点（`.terminal-dot.r/y/g`）
- 窗体：`background: var(--surface)`，圆角 8px
- 内部行类型：`.prompt`（绿色 `$`）、`.cmd`（白色命令）、`.comment`（灰色注释）、`.output`（绿色输出）
- 使用 `<Terminal>` 组件，不要手写 HTML

### 卡片（Card）

- 顶部 2px 色条区分类别：默认绿、`.blue`、`.yellow`、`.purple`、`.red`
- 背景 `var(--surface)`，边框 `var(--border)`
- 使用 `<Card>` 组件，通过 `color` prop 控制色条颜色
- 数据点行用 `margin-top:auto` 推到底部，颜色与色条一致

### 标题

- h1：绿色 + glow 效果（`text-shadow: 0 0 20px var(--green-glow)`）
- h2：绿色，非 cover/section 页自动加 `$ ` 前缀（模拟命令提示符）
- h3：白色，无特殊效果

### 表格

- 表头：`background: var(--surface)`，绿色文字，底部 2px 绿色边框
- 行悬停：微弱绿色高亮（`rgba(57, 211, 83, 0.03)`）
- 单元格文字：`var(--text-dim)`

### 高亮条带

- 正面结论：`background: var(--green-glow)`，`border: 1px solid var(--green-dim)`
- 可替换为其他颜色变量表达不同语义

### 条带列表

- 左边框 4px 彩色（按语义选色）
- 符号使用单色 Unicode（`▶`, `●`, `■`），颜色与左边框一致

### Blockquote

- 左边框 3px `var(--green-dim)`
- 背景 `rgba(57, 211, 83, 0.04)`
- 字号 0.82em

### 特效

- **扫描线（Scanlines）**：全页叠加水平条纹，模拟 CRT 显示器效果。通过 `::after` 伪元素实现，`pointer-events: none` 不影响交互
- **标题发光（Glow）**：h1 的 `text-shadow` 产生绿色光晕
- **光标闪烁（Cursor Blink）**：封面页的闪烁光标，`.cursor-blink` class

## 颜色语义映射

| 语义 | 颜色变量 | CSS class | 使用场景 |
|------|---------|-----------|---------|
| 正面/推荐/当前 | `var(--green)` | `.green` | ONA 相关、正确做法、当前状态 |
| 信息/中性 | `var(--blue)` | `.blue` | CC 相关、中性信息、技术概念 |
| 警告/注意 | `var(--yellow)` | `.yellow` | 注意事项、变化趋势 |
| 补充/扩展 | `var(--purple)` | `.purple` | 扩展阅读、高级概念 |
| 否定/风险 | `var(--red)` | `.red` | 错误示例、风险、不推荐 |
| 次要/弱化 | `var(--text-dim)` | `.dim` | 描述文字、补充说明 |

**提纲加粗 → 彩色高亮**：提纲中的 `**加粗**` 迁移到 slide 时，用 `<span class="red/yellow/blue">` 替代纯 `<strong>`。Terminal Green 主题下白色加粗与正文对比度不足，彩色更醒目。颜色根据语义选择。

## 图标与符号规则

**禁止彩色 emoji**（📡🧠🛠️🚀🐴🔧🧑等）。彩色 emoji 是 AI 生成内容的典型特征，与暗色终端风格严重冲突。

**允许的符号**：
- 列表项：`▶`, `●`, `■`, `◆`
- 状态：`✅`, `❌`, `⚠️`（例外允许，语义明确且终端常见）
- 树状：`├──`, `└──`, `│`
- 箭头：`→`, `←`, `↑`, `↓`
- 分隔：`·`, `|`, `—`

符号颜色通过 CSS 变量控制，不依赖 emoji 自带颜色。

**图标库**：需要具象图标时，使用 Phosphor（`i-ph-*`，优先）或 Carbon（`i-carbon-*`）。两个库都是线性风格，与终端主题一致。

**自绘 SVG** 必须匹配 Phosphor 风格：`viewBox="0 0 256 256"`, `fill="none"`, `stroke="var(--颜色)"`, `stroke-width="16"`, `stroke-linecap="round"`, `stroke-linejoin="round"`。

## 反模式

1. **使用彩色 emoji** — 破坏暗色终端的视觉一致性。用单色 Unicode 符号 + CSS 颜色替代
2. **用终端窗口展示非操作性内容** — `$ echo "哲学思考"` 很违和。认知性内容用引用卡片或高亮条带
3. **用终端窗口画二维架构图** — 等宽字体的 ASCII box-drawing 右侧必然留白，中文双宽导致对齐困难。用 HTML div 嵌套架构图
4. **白色加粗替代彩色高亮** — Terminal Green 暗色背景下，白色加粗与正文对比度不足，用 `.red/.yellow/.blue` 等 class
5. **亮色背景的控件** — 任何 `background: white` 或浅色背景都会破坏暗色主题的沉浸感
6. **圆角过大** — Terminal Green 使用 4px 小圆角（终端窗口 8px），不要用 12px+ 的圆润风格

## 示例

### 封面页

```html
<Terminal title="hackathon-training.sh" bodyStyle="padding:1.4em 1.6em; line-height:2.2; font-size:1.1em;">
  <div class="line"><span class="prompt">$</span> <span class="cmd">./hackathon-training.sh</span></div>
  <div class="line"><span class="output">Initializing AI Hackathon Training...</span></div>
  <div class="line"><span class="comment"># Context Engineering × Harness Engineering</span></div>
  <div class="line"><span class="output">Ready.</span> <span class="cursor-blink"></span></div>
</Terminal>
```

### 对比卡片

```html
<div class="card-grid">
  <Card color="blue" title="Claude Code">
    <div class="card-desc">本地终端 AI 编程助手</div>
    <div style="margin-top:auto; padding-top:0.5em; font-size:0.85em; color:var(--blue);">
      SWE-bench: 72.7%
    </div>
  </Card>
  <Card color="green" title="ONA">
    <div class="card-desc">云端开发环境 + AI</div>
    <div style="margin-top:auto; padding-top:0.5em; font-size:0.85em; color:var(--green);">
      浏览器即开即用
    </div>
  </Card>
</div>
```
