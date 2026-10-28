---
name: slidev-authoring
description: End-to-end Slidev presentation authoring — outline writing, slide generation, overflow verification, bilingual support, and multi-theme styling. Use when asked to "write outline", "revise outline", "create slides", "generate slides", "fix overflow", "add a slide", "translate slides", "switch theme", "create theme", or when working with Slidev markdown files.
---

# Slidev Authoring Skill

Slidev 演示文稿的全流程创作：提纲 → slides → 验证 → PDF 导出。支持多主题。

## 决策树

```
用户任务
├─ 写/改提纲 ─────────→ 读 OUTLINE_RULES.md，走「提纲」流程
├─ 生成/重写 slides ──→ 确定主题 → 读 LAYOUT_RULES.md + themes/<name>/theme.md，走「生成」流程
├─ 修溢出/布局 ───────→ 走「溢出修复」流程（不需要读完整规则文件）
├─ 加英文翻译 ────────→ 走「双语」流程
├─ 切换/创建主题 ─────→ 读 themes/theme-spec.md，走「主题」流程
├─ 从图片生成主题 ────→ 读 themes/theme-spec.md，走「主题生成」流程
└─ 导出/验证 PDF ─────→ 走「QA」流程
```

**只加载当前任务需要的文件。** 写提纲时不加载布局规则；修溢出时不加载主题定义。

## 主题系统

### 架构

```
CONTENT（slides.md）
    ↓
LAYOUT（LAYOUT_RULES.md — 通用布局规则，主题无关）
    ↓
VISUAL THEME（themes/<name>/ — 可替换的视觉皮肤）
```

### 主题确定

生成 slides 前必须确定主题。优先级：
1. 用户明确指定 → 使用指定主题
2. slides.md frontmatter 中有 `theme` 字段 → 使用该主题
3. 都没有 → 默认 `terminal-green`

### 可用主题

| 主题 | 目录 | 说明 |
|------|------|------|
| `terminal-green` | `themes/terminal-green/` | 赛博朋克终端风格，暗色 + 绿色荧光（默认） |
| `dracula` | `themes/dracula/` | Dracula 暗色多彩，紫色主调 + 高饱和度色板 |
| `roche-blue` | `themes/roche-blue/` | Roche 品牌风格，白底 + 暗色 section 页，蓝色主调 + 橙色点缀 |
| `claude` | `themes/claude/` | Anthropic Claude 设计语言，羊皮纸暖底 + 赭石橙品牌色 + Georgia 衬线标题 |
| `sketch-light` | `themes/sketch-light/` | 浅色手绘风格，Caveat 标题字体，与 Excalidraw light mode 协调 |
| `sketch-dark` | `themes/sketch-dark/` | 暗色极简风格，无装饰，与 Excalidraw dark mode 协调 |

### Frontmatter 主题切换

在 slides markdown 的 frontmatter 中设置 `customTheme` 字段即可切换主题：

```yaml
---
theme: default
customTheme: dracula    # terminal-green | dracula
title: My Presentation
---
```

Vite 插件 `slidev-theme-switcher`（`vite.config.ts`）会在构建/开发时读取 `customTheme` 字段，自动重写 `style.css` 中的主题 import 路径。不设置 `customTheme` 时默认使用 `terminal-green`。

**注意**：Slidev 原生的 `theme` 字段保持 `default`，不要改。`customTheme` 是我们自定义的字段。

### 文件加载规则

| 任务 | 加载文件 |
|------|---------|
| 生成 slides | `LAYOUT_RULES.md` + `themes/<name>/theme.md` |
| 修溢出 | 无需加载完整规则文件 |
| 切换主题 | `themes/theme-spec.md` + 目标 `theme.md` |
| 从图片生成主题 | `themes/theme-spec.md` |
| 查颜色/class | `themes/<name>/tokens.json` 或 slidev 的 `style.css` |

## 核心约束

- **提纲是 SSOT**：slides 不删减、不扩展、不改写提纲文本
- **脚本是黑盒**：`verify_slides.py`、`pdftoppm`、`slidev export` 直接调用，不要读源码
- **溢出只调视觉参数**：font-size / padding / margin / gap，永远不压缩文字内容
- **主题分离**：布局规则（LAYOUT_RULES.md）和视觉规则（theme.md）独立，不要在布局规则中硬编码颜色/字体

---

## 提纲流程

**前置**：读 `OUTLINE_RULES.md`（本目录下）。

1. 每页结构：`## Slide N: 标题` → 引导句 → 语义块 → speaker notes
2. 预估纵向空间（Rule 7 高度预算表），超过 85% 标记风险
3. 表格只用于多维对比（Rule 3），并列概念用分段
4. 单元格 ≤ 40 字（Rule 4），数据点独立成行（Rule 5）
5. 加粗标题不带冒号（Rule 2）
6. 改完提纲后，如果对应 slide 已存在，跑验证：`python3 scripts/verify_slides.py --slide <N>`

---

## 生成流程

**前置**：确定主题 → 读 `LAYOUT_RULES.md` + `themes/<name>/theme.md`。

每页必须走完 6 步（不可跳过、不可批量简化）：

1. **读提纲** — 标注语义块和块边界
2. **选控件** — 每个语义块映射到视觉控件（LAYOUT_RULES 规则 3 + 规则 4）
3. **纵向预检** — 数纵向块数，按规则 2 预检表判断风险
4. **从零生成** — 不在现有页面上打补丁，重写整页。颜色/字体/装饰按 theme.md 规则
5. **跑验证** — `python3 scripts/verify_slides.py --slide <N>`
6. **人工复核** — 比喻/金句是否保留，加粗是否转彩色，有无静默丢弃

---

## 溢出修复流程

不需要加载完整规则文件，按以下优先级操作：

1. 外层 wrapper 缩小字号：`<div style="font-size:0.82em">`（范围 0.72em–0.88em）
2. 压缩控件间距：margin / padding / gap / line-height
3. 拆页（最后手段，两页标题体现从属关系）

**禁止**：压缩文字内容、删减提纲中的信息、用 `flex:1` 强制撑大。

修完后必须走 QA 流程验证。

---

## 主题流程

### 切换主题

1. 修改 slides.md frontmatter 的 `customTheme` 字段为目标主题名
2. 读目标主题的 `theme.md` 了解视觉规则
3. 重新构建验证（`npm run build`）
4. Vite 插件自动处理 CSS import 重写，无需手动改 `style.css`

### 从图片生成主题

1. 读 `themes/theme-spec.md`
2. 分析参考图片的视觉特征（配色、字体、装饰、调性）
3. 按 theme-spec.md 生成 `tokens.json` + `theme.md`
4. 从 tokens 生成 `style.css`
5. 用户预览 → 微调 → 确认

---

## 双语流程

- ZH 和 EN 共享 `components/`、`style.css`、`global-top.vue`、`global-bottom.vue`
- ZH 端口 3030：`npx slidev --open false`
- EN 端口 3031：`npx slidev --open false --entry slides-en.md --port 3031`
- `global-top.vue` 用 `window.location.hostname` + 端口号做语言切换，不硬编码 localhost
- EN 通常需要比 ZH 更小的 font-size（英文字符宽度更大）
- 保持中英文 slide 编号和结构同步

---

## QA 流程

**假设有问题，你的任务是找到它们。** 第一次渲染几乎不可能完美。如果检查后发现零问题，说明没有认真看。

### 导出与转换

```bash
# 从 slidev 项目目录执行
npx slidev export --output <name>.pdf
npx slidev export --entry slides-en.md --output <name>-en.pdf

# 转 PNG 逐页检查
pdftoppm -png -r 150 <name>.pdf /tmp/slide
```

### 逐页检查清单

每页必须检查：
- 内容溢出（底部文字被截断）
- 填充不足（空白面积 > 20%）
- 表格列对齐
- 卡片/终端视觉平衡
- 中英文版本是否同步

### 验证循环

1. 导出 → 转 PNG → 逐页检查
2. **列出发现的问题**（如果没发现，再看一遍）
3. 修复问题
4. **重新验证受影响的页面** — 一个修复经常引入新问题
5. 重复直到完整一轮检查无新问题

**至少完成一次"修复→重新验证"循环后才能宣布完成。**

### 上下文管理（防止会话崩溃）

长会话中反复读取 PNG 截图会导致上下文膨胀，触发 LLM proxy 400 错误（"The input data is not valid json"）。以下纪律必须遵守：

1. **减少读图频率**：只在结构性改动（新页面、大改布局、跨栏对齐）后才导出 PNG 验证。微调间距/字号/padding 等参数由用户在 dev server 上目视确认，不需要读图。
2. **读完即弃**：读截图后立即给出判断和修改方案，后续对话不再引用历史截图内容。每轮验证结束后执行 `rm -f /tmp/p*.pdf /tmp/p*.png` 清理临时文件。
3. **复杂页面拆会话**：一页如果需要 5+ 轮视觉调整迭代，中间主动提醒用户存档进度、开新会话继续，避免单次会话上下文爆炸。

---

## 关键文件

| 文件 | 用途 | 何时加载 |
|------|------|---------|
| `OUTLINE_RULES.md` | 提纲写作规则（10 条） | 写/改提纲时 |
| `LAYOUT_RULES.md` | 通用布局规则（17 条） | 生成 slides 时 |
| `themes/theme-spec.md` | 主题规范定义 | 切换/创建主题时 |
| `themes/<name>/theme.md` | 主题视觉规则 | 生成 slides 时 |
| `themes/<name>/tokens.json` | 设计 token | 查颜色/生成 CSS 时 |
| `vite.config.ts` | Vite 插件（主题切换） | 修改主题切换逻辑时 |
| `slides.md` | 中文 slides（terminal-green） | 生成/修改时 |
| `slides-en.md` | 英文 slides（terminal-green） | 翻译/同步时 |
| `slides-dracula-test.md` | Dracula 主题测试 | 验证 Dracula 视觉效果时 |
| `slides-roche-test.md` | Roche Blue 主题测试 | 验证 Roche Blue 视觉效果时 |
| `components/*.vue` | 共享组件（14 个，见下表） | 需要查 props 时 |
| `public/icons/aws/*.svg` | AWS 服务图标（Bedrock, Lambda, S3, ECS 等 20 个） | 架构图中引用 `<img src="/icons/aws/bedrock.svg">` |
| `public/diagrams/` | Excalidraw 手绘图表模板 | 嵌入 `<Excalidraw>` 组件时 |
| `public/roche-logo-blue.png` | Roche 蓝色 logo（浅色主题用） | `global-top.vue` 自动切换 |
| `public/roche-logo-white.png` | Roche 白色 logo（暗色主题用） | `global-top.vue` 自动切换 |

### 组件速查

| 组件 | 用途 | 关键 props |
|------|------|-----------|
| `<Terminal>` | 终端窗口 | `title`, `style`, `bodyStyle` |
| `<Card>` | 卡片 | `color` (green/blue/yellow/purple/red), `title` |
| `<Divider>` | 分隔线标题 | `text`, `mt`, `mb` |
| `<Footnote>` | 底部备注栏 | `push` (Boolean) |
| `<Architecture>` | 分层架构图 | `labels` (Array), `arrows`, `gap`；slot: `layer0`/`top`/`middle`/`bottom` |
| `<AwsIcon>` | AWS 服务图标 | `name` (svg 文件名), `size`, `label` |
| `<Badge>` | 行内标签 | `color` |
| `<Box>` | fieldset 容器 | `title`, `color` |
| `<Callout>` | 提示/警告框 | `type` (info/warning/danger/tip/success), `title` |
| `<Chart>` | SVG 图表 | `type` (bar), `data` (Array), `width`, `height`, `color`, `title` |
| `<Excalidraw>` | 嵌入手绘图 | `src` (.excalidraw 路径), `width`, `dark`, `background` |
| `<Flow>` | 流程步骤图 | `steps` (Array), `direction` (horizontal/vertical), `arrow`, `color` |
| `<Funnel>` | 漏斗图 + 右侧文字 | `items` [{label, desc, color}], `width`, `height`, `rowGap` |
| `<Stat>` | 大数字指标 | `value`, `label`, `color` |
| `<StepList>` | 编号步骤列表 | `items` [{title, desc?}], `colors` [] |
| `<Timeline>` | 纵向时间线 | `items` [{date, title, desc?}], `color` |

### 已废弃文件

| 文件 | 替代 |
|------|------|
| `DESIGN_RULES.md`（slidev 目录下） | 拆分为 `LAYOUT_RULES.md` + `themes/terminal-green/theme.md` |

## 项目初始化

新建 slidev 项目（`npx slidev create`、`npm init slidev`、或从已有项目拷贝模板）后，**第一件事检查根目录 `.gitignore` 是否包含 `node_modules` 和 `dist`**。少了就立刻补上：

```gitignore
node_modules
dist
```

**Why**：`npx slidev create` 在某些版本/路径下不生成 `.gitignore`，或者从已有项目拷贝模板时漏掉。一旦少了，`npm install` 之后 git 把几万个 node_modules 文件全部计为 untracked——VS Code SCM badge 直接爆 10K+，影响整个 IDE 响应、所有 git 操作变慢、`git status` 一屏滚不完。已经踩过两次（anand-visit 一次、pd-china-ai-seminar 一次），是稳定 trap 不是偶然。

**触发条件**：任何 `cd <某目录> && npm install` 之前，先 `ls .gitignore` 或 `cat .gitignore | grep node_modules` 确认。没有就先建。

## 开发服务器

```bash
cd slidev && npm run dev          # 中文（terminal-green，端口 3030）
cd slidev && npm run dev:en       # 英文（terminal-green，端口 3031）
```

用 `exec` 启动（不要用 `exec_preview`，该环境下不可用）。用户通过 VS Code Ports 面板转发端口访问。

## ⚠️ 最高优先级规则

1. **迭代 5 轮强制 commit。** Slidev 迭代过程中，每完成 5 轮改动（无论大小），必须暂停工作，请求用户批准后立即 commit + push。不等用户主动提出。这是防止会话崩溃或误操作导致大量工作丢失的硬性要求。
2. **禁止未经批准的 `git checkout`。** 任何对 slides.md 或其他已修改文件的 `git checkout`、`git restore`、`git reset` 操作，必须先向用户说明将丢失哪些改动，获得明确批准后才能执行。违反此规则等同于删除用户的工作成果。

## 组件优先规则

1. 开始任何页面的可视化实现前，先检查 `components/` 目录下已有哪些组件
2. 优先使用现有组件，不足时扩展组件，最后才考虑 inline style
3. 修改样式参数前，先检查是否有多处定义同名 class
4. 布局用 inline style（flex/grid），排版参数（padding/font-size/line-height）用组件 class
5. 填充空间用间距和行高，不改字号
6. 提纲一页对应一页 slide，不允许未经用户批准拆页

完整的组件库清单、变体选择矩阵和填充规则见 `LAYOUT_RULES.md`。

## 反模式

1. **压缩文字修溢出** — 只调 font-size/spacing/padding，提纲文字不可动
2. **在现有 slide 上打补丁** — 改内容时从提纲重新生成整页
3. **slide 中添加提纲没有的内容** — 先改提纲，再同步 slide
4. **实质内容放 speaker notes** — 有独立信息价值的内容属于提纲正文
5. **同维度数据拆两张表** — 合并为一张表，用分类列区分
6. **语言切换硬编码 localhost** — 用 `window.location.hostname`
7. **跳过 PDF 验证** — Slidev 开发预览看不出溢出，必须导出检查
8. **一次性加载所有规则文件** — 只加载当前任务需要的文件，控制上下文占用
9. **读脚本源码** — `verify_slides.py` 等脚本直接调用，不要读源码污染上下文
10. **在布局规则中硬编码颜色** — 布局规则用 `var(--*)` 引用，具体值由主题决定
11. **用原生 div 包裹 Vue 组件** — `<Divider>` 等 Vue 组件放在 `<div>` 内部会导致解析错误，把样式加到相邻原生 div 上
12. **编辑 HTML 后不验证 div 平衡** — 每次编辑后用 `grep -c '<div'` / `grep -c '</div>'` 检查该 slide 范围内开闭标签数量匹配
13. **攒多个改动再验证** — 每次 HTML 结构变更后必须立即导出 PNG 验证渲染结果，不要攒改动批量验证
14. **验证截图不清理** — 每轮验证结束后删除 `/tmp/` 下的中间 PDF/PNG，不要让临时文件累积
15. **对齐差不多就行** — 同栏内子模块边缘必须严格对齐，导出 PNG 后目视确认
16. **跨栏对齐用 margin hack** — 左右栏子模块需要底边对齐时，用 CSS Grid 统一行定义，不要用 `margin-top:auto` 或固定 padding 凑对齐
17. **同实体跨图颜色不一致** — 同一实体（如"中间商"）在同页不同 Mermaid 图中必须使用相同 classDef 颜色
18. **验证截图大量读入上下文** — 每次验证只读取当前修改的页面截图，读完立即清理。长会话中截图累积会导致上下文膨胀，触发 LLM proxy 400 错误
