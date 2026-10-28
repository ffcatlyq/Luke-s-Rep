# Theme Specification

定义一个 Slidev 主题必须包含的所有字段。新建主题时按此模板填充。

## 文件结构

每个主题包含两部分：

```
themes/<theme-name>/
├── theme.md        ← Skill 侧：给 LLM 读的视觉规则和设计语言描述
└── tokens.json     ← Slidev 侧：结构化设计 token，生成 CSS 变量

（tokens.json 的运行时副本放在 slidev/themes/<theme-name>/tokens.json）
```

## tokens.json 字段定义

### meta（必填）

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `name` | string | 主题显示名 | `"Terminal Green"` |
| `description` | string | 一句话描述风格特征 | `"赛博朋克终端风格，暗色背景 + 绿色荧光"` |
| `colorSchema` | `"dark"` \| `"light"` | 明暗基调 | `"dark"` |
| `fontStyle` | `"monospace"` \| `"sans"` \| `"serif"` \| `"mixed"` | 主字体风格 | `"monospace"` |

### colors（必填）

所有颜色值使用 CSS 合法格式（hex、rgb、rgba、hsl）。

| 字段 | 语义 | 说明 |
|------|------|------|
| `bg` | 页面背景 | 整页底色 |
| `primary` | 主色 | 标题、强调、品牌色 |
| `primaryDim` | 主色弱化 | 边框、次要强调 |
| `primaryGlow` | 主色发光 | 光晕效果（可选，无则留空字符串） |
| `secondary` | 辅色 | 信息性内容、中性强调 |
| `warning` | 警告色 | 注意、提醒 |
| `accent` | 点缀色 | 补充、扩展信息 |
| `danger` | 危险色 | 否定、风险、错误 |
| `text` | 正文色 | 主要文字 |
| `textDim` | 弱化文字 | 次要信息、描述 |
| `border` | 边框色 | 分隔线、容器边框 |
| `surface` | 表面色 | 卡片、代码块、表头背景 |

### typography（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| `fontSans` | string | 无衬线字体名 |
| `fontMono` | string | 等宽字体名 |
| `fontSerif` | string \| `""` | 衬线字体名（无则留空） |
| `headingWeight` | `"400"` - `"900"` | 标题字重 |
| `bodyWeight` | `"300"` - `"500"` | 正文字重 |
| `fontImport` | string \| `""` | Google Fonts 导入 URL（无则留空） |

### decorations（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| `borderRadius` | string | 容器圆角 | 
| `scanlines` | boolean | 扫描线叠加效果 |
| `glowEffect` | boolean | 标题/元素发光效果 |
| `cursorBlink` | boolean | 闪烁光标动画 |
| `headingPrefix` | string \| `""` | 标题前缀（如 `"$ "`），空则无前缀 |
| `shadow` | string \| `""` | 容器阴影（CSS box-shadow 值） |

### icons（必填）

| 字段 | 类型 | 说明 |
|------|------|------|
| `style` | `"monochrome-unicode"` \| `"line-icons"` \| `"filled-icons"` \| `"emoji-allowed"` | 图标风格 |
| `banned` | string[] | 禁止的图标类型（如 `["emoji"]`） |
| `libraries` | string[] | 推荐的图标库（如 `["phosphor", "carbon"]`） |

### semanticColors（必填）

将语义角色映射到 colors 中的字段名。LLM 生成 slides 时按语义选色，不直接引用具体颜色。

| 字段 | 语义 | 说明 |
|------|------|------|
| `positive` | 正面/推荐/当前 | 映射到 colors 中的某个字段 |
| `negative` | 否定/风险/废弃 | |
| `neutral` | 中性/信息性 | |
| `highlight` | 警告/注意 | |
| `supplement` | 补充/扩展 | |
| `muted` | 次要/弱化 | |

## theme.md 必须包含的章节

### 1. 设计语言（必填）

用 2-3 句自然语言描述主题的视觉调性。LLM 据此做无法用 token 覆盖的设计决策。

示例：*"赛博朋克终端风格。所有元素模拟命令行界面，冷暗色调，绿色荧光强调。整体感觉像在一个高级黑客的终端里浏览信息。"*

### 2. 控件视觉规则（必填）

该主题下 14 种控件的特殊视觉处理。只写与通用 LAYOUT_RULES.md 不同的部分：
- 哪些控件有主题专属装饰（如 Terminal Green 的三色圆点标题栏）
- 控件的颜色分配规则
- 特殊效果（glow、shadow、gradient）

### 3. 颜色语义映射表（必填）

具体说明每个语义颜色在该主题下的使用场景。

### 4. 图标与符号规则（必填）

该主题允许/禁止的图标类型，推荐的符号集。

### 5. 反模式（必填）

该主题下常见的视觉错误，至少 3 条。

### 6. 示例（推荐）

1-2 个典型页面的 HTML 片段，展示该主题的标志性视觉效果。

## 从参考素材生成主题的流程

### 素材类型与可行性

| 素材类型 | 可行性 | 说明 |
|---------|--------|------|
| HTML/CSS 源码 | ✅ 最佳 | 直接提取 token 和结构，精确度最高 |
| 设计工具文件（Figma/Sketch） | ✅ 好 | 可导出精确的 CSS 属性 |
| Gemini Canvas / 在线编辑器导出 | ✅ 好 | 导出 HTML 源码，比截图有用 100 倍 |
| Slidev/PPT 模板源码 | ✅ 好 | 直接读 CSS 变量和组件结构 |
| 截图/图片 | ⚠️ 有限 | 颜色可取色，但间距/字号/对齐/嵌套关系全靠猜测，累积误差大，容易陷入盲改循环 |

**截图反推的局限性**：颜色可以用取色器提取，但间距、字号、圆角、对齐逻辑、容器嵌套关系全靠推测。每一层猜测都会累积误差，改了 A 又影响 B。如果用户只有截图，应优先要求提供源码或设计文件；实在没有时，只做 token 级别的适配（配色、字体、圆角），不要尝试像素级复刻布局。

### 流程

当用户提供参考素材时：

1. **判断素材类型**，优先要求源码/设计文件而非截图

2. **分析视觉特征**
   - 提取主色调（背景色、前景色、强调色）
   - 识别字体风格（衬线/无衬线/等宽）
   - 识别装饰风格（圆角/直角、阴影深浅、边框粗细）
   - 判断整体调性（专业/活泼/极简/赛博朋克/学术）

3. **填充 tokens.json**
   - 颜色：从素材提取的色值，调整为协调的色板
   - 字体：匹配最接近的 Google Fonts 字体
   - 装饰：根据素材风格设置 borderRadius、shadow 等
   - 图标：根据调性选择图标风格

4. **撰写 theme.md**
   - 设计语言：用自然语言描述提取到的风格特征
   - 控件规则：根据参考素材中的 UI 元素推断控件样式
   - 反模式：根据主题调性列出不协调的视觉元素

5. **生成 style.css**
   - 有源码时：直接从源码提取 CSS，适配到 Slidev 的选择器体系
   - 只有截图时：从 tokens.json 生成 CSS 变量声明 + 基础组件样式，不尝试复刻复杂布局

6. **用户预览 → 微调 → 确认**

## 约束

- tokens.json 的 colors 部分最少 12 个字段（上表全部必填）
- theme.md 控制在 200 行以内，避免上下文膨胀
- 每个主题必须能独立工作——不依赖其他主题的文件
- CSS 变量命名统一使用 `--<field>` 格式（如 `--bg`, `--primary`, `--text-dim`）
- 组件 class 名称主题无关（如 `.card`, `.terminal-window`），视觉差异通过 CSS 变量实现
