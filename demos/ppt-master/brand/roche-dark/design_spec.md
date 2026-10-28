---
brand_id: roche-dark
kind: brand
summary: Roche Dark brand identity — dark-tech / dark-mode decks, keeping full Roche color provenance
primary_color: "#0B41CD"
background: "#2D3232"
---

# Roche Dark Brand Specification

> Identity-only preset(ppt-master `kind: brand`),roche-blue的**暗色场景孪生**。无页面roster——页面在这些约束下自由排布。把本目录路径作为主管线Step 3模板，任意内容套上Roche暗色风。
>
> **每个色都溯源到Roche官方色板**(`assets/roche-brand/tokens/colors.json` 的 `palette_families`,2026-07-12从Frontify认证API拉全)。**不是把roche-blue压黑，也不是GitHub暗色**——底用官方登录页暗底、accent用官方橙、语义用官方status,全官方。见 [[reference_roche_full_palette_frontify_api]] 派生源。

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Roche(dark mode) |
| Use Cases | 暗色科技风分享、technical deep-read、engineering/AI主题、需要暗底反差的场合 |
| Tone | 克制、专业、暖调深底(非纯黑)、单主色蓝 + 一个暖accent、结论先行 |
| 配套 | 亮底场景用 [`../roche-blue/`](../roche-blue/design_spec.md);二者共用同一官方色板，只是明暗取向不同 |

## II. Color Scheme(全官方，暗底取向)

底色用Roche官方**登录页暗底 `#2D3232`**(暖灰，非纯黑/非navy);层次靠官方grey阶 + 蓝阶；**暖accent用官方orange**(Roche确有橙色族),语义用官方status + green/red。

| Role | HEX | 官方来源(colors.json) | Notes |
|---|---|---|---|
| bg | `#2D3232` | neutral.background_dark | 页底，暖灰暗底 |
| surface | `#3A3F3F` | grey_1提亮 | 卡面 |
| panel | `#353A3A` | 同源 | takeaway / 次容器 |
| terminal | `#202525` | 底压深 | 代码 / 终端卡 |
| border | `#544F4F` | grey.grey_1 | 卡边 / 分隔 |
| primary | `#0B41CD` | blue.roche_blue | 唯一品牌主色；竖条、强调、深块 |
| blue-dark | `#022366` | blue.dark | 深蓝层次 / 反白块 |
| blue-light | `#1482FA` | blue.light | accent蓝、关键数据 |
| blue-extra-light | `#BDE3FF` | blue.extra_light | 暗底高亮蓝(eyebrow / 徽章) |
| **warm accent** | `#FF7D29` | **orange.orange** | 暖accent(caution / 强调),暗底上给"暖"的那一笔；深用 `#ED4A0D` |
| warm-2 | `#FAC9B5` | neutral.neutral_1 | 暖桃点缀(可选) |
| text | `#F5F5F2` | grey.grey_5 | 主体文字 |
| text-muted | `#C2BAB5` | grey.grey_3 | 次级 / 副标 |
| text-tertiary | `#706B69` | grey.grey_2 | 页码 / footer(暗底低调) |
| success / pass | `#4CBB17` | green.green | 放行 / 通过(暗底亮绿);语义严谨处用status.green `#007C6B` |
| danger / block | `#FF1F26` | red.red | 拦 / 危险；或status.red `#CC0033` |
| warning | `#FFC414` | status.yellow | 注意 |

**单主色仍是蓝**;orange是**暖accent(点缀，非第二主色)**,只在需要"暖"的强调/caution处少量用。语义色只在读数/状态。暗底辉光用低透明度蓝 `radialGradient` + 网格线 `#544F4F` opacity 0.3。**白logo**(暗底)。

## III. Typography

与roche-blue同(官方typography:Roche Sans主字体，Serif仅引言)。**暗底文字用grey_5/3/2暖灰阶**,不用纯白。

| Role | Family |
|---|---|
| title / display / hero | `'Roche Sans Light', sans-serif`(纯拉丁)/ `'Noto Sans CJK SC'`(含CJK) |
| label / eyebrow / 表头 / 强调 | `'Noto Sans CJK SC','Roche Sans Medium', sans-serif` |
| body | `'Noto Sans CJK SC','Roche Sans', sans-serif` |
| quote / 作者 / 斜体图注 | `'Noto Serif CJK SC','Roche Serif Light', serif` + italic(**CJK引言用Noto Serif CJK SC首位**,否则豆腐) |
| code / 记号 | `'Consolas','DejaVu Sans Mono', monospace` |

> cairosvg预览：CJK行 `Noto Sans CJK SC` 首位(坑②);Serif+CJK行 `Noto Serif CJK SC` 首位；字重独立family名；居中文本零tspan(坑④)。EU容器先 `apt-get install fonts-noto-cjk`。**字体不嵌**(实测PowerPoint拒装程序化嵌入，见 [`../../examples/ADAPTATION.md`](../../examples/ADAPTATION.md))。

## IV. Logo

| File | Form | Usage |
|---|---|---|
| `./Roche_Logo_800px_White_RGB_200px.png` | 白色logo | **暗底页——主用**(右上 / 封面左上) |
| `./Roche_Logo_800px_Blue_RGB_200px.png` | 蓝色logo | 备用(浅色插页) |

## V. Voice & Tone / VI. Icon Style

同 [`../roche-blue/design_spec.md`](../roche-blue/design_spec.md) §V/§VI:克制专业、we/you、**禁emoji**;图标优先官方Roche图标库(`assets/roche-brand/icons/svg/` 1454个),stroke 2px,暗底用浅色描边。

---

> **范围**:只锁**身份**(暗底色/字/logo/voice/图标)。版式风格(暗色科技格的KPI/schematic/终端卡画法)是页面层约定，见 [`../../examples/claude-code-auto-mode/design_spec.md`](../../examples/claude-code-auto-mode/design_spec.md)。任意内容 = 本brand(暗色身份)+ 那套版式约定 + 主管线(内容)。参照实例：claude-code-auto-mode exemplar。
