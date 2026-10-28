---
brand_id: roche-blue
kind: brand
summary: Roche Blue brand identity — technical/scientific talks, paper deep-reads, internal training, research updates
primary_color: "#0B41CD"
---

# Roche Blue Brand Specification

> Identity-only preset(ppt-master `kind: brand`)。无SVG页面roster——页面在这些约束下自由排布。
> 把这个目录路径作为ppt-master主管线Step 3的模板输入，任意论文/内容都会套上Roche Blue风格。
>
> **值全部派生自hub的Roche Blue SSOT token**(`assets/roche-brand/tokens/` +
> `slidev/themes/roche-blue/tokens.json`),经 `demos/ppt-master/scripts/build_roche_brand_spec.py`。
> token变了重跑脚本、回填本文件——不手改、不另立会漂移的定义。

## I. Brand Overview

| Property | Value |
|---|---|
| Brand Name | Roche |
| Use Cases | 技术/科学分享、论文深读、内部培训、研究进展、方案汇报 |
| Tone | 克制、专业、留白充分、单主色、结论先行 |

## II. Color Scheme

单主色克制 + 白底大留白是Roche视觉核心。**只有一个品牌主色**;层次靠"主色派生的蓝阶 + 克制渐变",不是第二主色。

| Role | HEX | Provenance | Notes |
|---|---|---|---|
| primary | `#0B41CD` | fact | Roche Blue — 唯一品牌主色(colors.json `roche_blue`);标题强调、表头、深块、边框、数字 |
| primary-hover | `#002DB9` | fact | 交互hover(colors.json `roche_blue_hover`) |
| bright | `#1482fa` | fact | 亮蓝accent(slidev `primaryDim`);竖条、eyebrow、关键数据 |
| blue-mid | `#0F5EE1` | derived | primary→bright插值0.45;层次过渡 |
| blue-light | `#5FAAFC` | derived | bright→white 0.32;第3级层次 |
| blue-lighter | `#95C7FD` | derived | bright→white 0.55;第4级层次 |
| tint | `#E9EEFA` | derived | primary→white 0.91;高亮行 / 面板块底 |
| bg | `#FFFFFF` | fact | 亮底页背景 |
| bg-section | `#0D0D0D` | fact | 暗色分节页背景(slidev `bgSection`) |
| surface | `#F5F7FA` | approx | 卡片 / takeaway面板底 |
| border | `#E0E0E0` | fact | 卡边 / 表格线(slidev `border`) |
| body-text | `#333333` | conv | 正文(官方text_primary为 #000;演示正文用 #333更柔) |
| muted-text | `#706B69` | fact | 次级文字 / 图注(slidev `textDim`) |
| success | `#007A3B` | fact | 正向 / 成功(colors.json callout tip) |
| warning | `#D0021B` | fact | 警告 / 错误(slidev `danger`) |

前几行是官方身份；blue-mid/light/lighter/tint是**主色SSOT锚(primary + bright)+ 白程序化派生**的层次梯度(规则见 `build_roche_brand_spec.py` `derive_blue_scale()`),不是新主色。克制渐变(少量):accent竖条 / 输出块primary→bright、面板底tint渐变、KPI/图例徽章primary→lighter进阶。语义色只在"读数"处(绿=好、红=差)。官方整套蓝阶在Frontify(colors.json `_todo` page 571),够到后resolve进token可换锚点。

## III. Typography

Roche官方typography:**Roche Sans是主字体**("key to all communication",Light用于display/headline/body);**Roche Serif是辅助**(quotes / small copy / footnotes)。

| Role | Family | Weight / 说明 |
|---|---|---|
| title / display / hero数字 | `'Roche Sans Light', sans-serif` | Roche招牌优雅Light —— **用独立family名，不是font-weight:300** |
| label / eyebrow / 表头 / 强调 / 反白 | `'Roche Sans Medium', sans-serif` | 需要对比处 |
| body / 正文说明 | `'Roche Sans', sans-serif` | Regular |
| quote / pull-quote / 作者 / 斜体图注 | `'Roche Serif Light', serif` + `font-style: italic` | Serif只用在它该用的地方 |
| code / 记号 | `'Consolas', 'DejaVu Sans Mono', monospace` | |
| 含CJK文本 | `'Noto Sans CJK SC'` 放字体栈首位 | 渲染tofu对策 |

字号基线(body):`text` 20 / `balanced` 24 / `presentation` 32(每档一个定值)。

> 字体文件在hub `assets/roche-brand/fonts/`(woff2)。**cairosvg预览**:toy font API只认normal/bold,
> `font-weight:300` 不是Light——真Light/Medium必须用独立family名(`Roche Sans Light` / `Roche Sans Medium` / `Roche Serif Light`);woff2→ttf装到 `~/.local/share/fonts/` 才渲得出。
> **pptx**:svg_to_pptx按family名导出字重，但**不嵌字体**;外发给没装Roche字体的人会回退系统sans。Roche Sans缺 `→`(其余 `√·—×÷²≤` 都有),箭头包进mono `<tspan>` 或改连字符。
>
> **字体嵌入stance(一律不嵌)**:两个原因——① 技术：实测PowerPoint **拒装**程序化嵌入的字体(子集+完整都报"一般错误",字体本身TrueType/fsType=0,已排除CFF/许可位);② 许可：`fsType=0` ≠ EULA允许外发再分发。所以导出即成品、不嵌；罗氏机器有Roche Sans正常显示，外部方自备字体或接受回退。工具 `../../examples/_pipeline/embed_fonts.py` 保留作参考(默认不用);完整口径见 [`../../examples/ADAPTATION.md`](../../examples/ADAPTATION.md) 字体嵌入节。

## IV. Logo

| File | Form | Usage |
|---|---|---|
| `./Roche_Logo_800px_Blue_RGB_200px.png` | 蓝色logo | **亮底页**——右上或左上角 |
| `./Roche_Logo_800px_White_RGB_200px.png` | 白色logo | **暗色分节页** |

- 内容页：右上角小尺寸；封面：左上角放大。
- Clearspace:四周留足边距；不拉伸、不改色、不叠在文字/图上。
- 宽高比固定1.923(200×104);缩放保持比例。

## V. Voice & Tone

- Formality:专业、克制。
- Person:we / you(英文),我们 / 你(中文)。
- Emoji:**禁用**(Roche brand明确)。
- 单主色克制点缀，不满屏蓝；白底大量留白，分节页深底反差。

## VI. Icon & Visual Vocabulary

**优先用官方Roche素材库**(`assets/roche-brand/`,不是通用图标)——罗氏适配的发挥空间在这：

| 素材 | 位置 | 数量 / 用法 |
|---|---|---|
| **官方Roche图标** | `assets/roche-brand/icons/svg/` | **1454个stroke图标**(628 Healthcare / 410 General / 276 Business / 92 Sustainability)。技术/科学deck首选Healthcare类；`<image>` 引用或inline path。**优先它，不用通用tabler** |
| 官方渐变 | `assets/roche-brand/gradients/` | 9张Roche品牌渐变PNG(Blue→Neutral等),分节页/封面氛围底 |
| 官方插画 | `assets/roche-brand/illustrations/` | 93张PNG,概念页/留白区点缀(图重格) |
| logos | `./`(本目录) | 见 §IV |

- Preference:stroke(线性),stroke-width 2px,不用filled——与官方图标库一致。
- **fallback**:官方库没有对应概念时才用 `tabler` / `carbon` 等stroke家族(inline path),风格对齐官方stroke。
- 完整资产索引见 `assets/roche-brand/INDEX.md`(快照8280项：图标/logo/照片/动画图标/插画/stock)。
- **合规**:图标/渐变/插画是内部brand资产，内部deck随用；外发同字体stance(见 §III)——品牌资产外发看许可。

---

> **范围**:本bundle只锁**身份**(色/字/logo/voice/图标)。**版式风格**(技术公式格的KPI卡 /
> 公式带 / 表格 / schematic画法)与**图像策略**(LaTeX公式 / Galileo氛围图 / 版权图不嵌)不在
> brand里——它们是页面层约定，见 [`../../examples/attention-transformer/design_spec.md`](../../examples/attention-transformer/design_spec.md)
> 与 [`../../examples/ADAPTATION.md`](../../examples/ADAPTATION.md)。任意论文 = 本brand(身份)+ 那套版式约定(风格)+ 主管线(内容)。
