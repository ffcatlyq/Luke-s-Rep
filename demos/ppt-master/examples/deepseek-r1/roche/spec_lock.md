# spec_lock — deepseek-r1(Roche Blue技术公式格)

> 执行真相锁：design_spec是「配方/意图」,本文件锁**逐页实际落地的视觉执行值**,供复现与回归比对。
> 只记「锁死不许漂」的量，内容语义见 [`../design_spec.md`](../design_spec.md) §IX。

## 画布 / 全局

| 项 | 锁定值 |
|---|---|
| viewBox | `0 0 1280 720` |
| 安全边距 | 左60 / 右60(logo右缘1220);上32(logo)/ header竖条y=56 |
| 内容页logo | Blue版，`x=1136 y=32 w=84 h=43.7`(比例1.923) |
| 封面logo | Blue版，`x=64 y=52 w=118 h=61.4`(放大) |
| 页眉 | 6px accent竖条 `x=60 y=56 w=6 h=40 fill #1482fa` + 标题 `x=84 y=90 Roche Sans Light 34 #0B41CD` + eyebrow `x=84 y=116 Roche Sans Medium 13 #706B69 ls 1.5` |
| 页脚 | source注 `x=60 y≈694 Roche Sans 11 #A39F9C` + 页码 `x=1220 text-anchor=end` |

## 配色(全篇仅这些值，派生自SSOT锚)

| token | HEX | 用途 |
|---|---|---|
| primary | `#0B41CD` | 标题/表头填充/深块/边框/数字 |
| bright | `#1482fa` | 竖条/eyebrow/关键数据/accent |
| blue-mid | `#0F5EE1` | 层次徽章第2级 |
| blue-light | `#5FAAFC` | 第3级 |
| blue-lighter | `#95C7FD` | 第4级 |
| tint | `#E9EEFA` / `#F0F4FC` | 高亮行 / 块底 |
| surface | `#F5F7FA` | 卡片/takeaway面板底 |
| border | `#E0E0E0` | 卡边/表格线 |
| body / muted / tertiary | `#333333` / `#706B69` / `#A39F9C` | 正文 / 副 / 页码 |
| success / warning | `#007A3B` / `#D0021B` | 读数：好 / 差(仅读数处) |
| cover bg | `#FBFBF9` | 封面底 |

## 字体(family名锁定，cairosvg只认独立family名不认font-weight:300)

`'Roche Sans Light'`(display/标题/hero数字)· `'Roche Sans Medium'`(eyebrow/表头/强调/反白)·
`'Roche Sans'`(正文)· `'Roche Serif Light',italic`(引言/作者/斜体注)· `'Consolas','DejaVu Sans Mono'`(记号/公式变量/数字表)。
箭头 `→` 必须包mono `<tspan>`(Roche Sans缺该字形)。

## 资产(LaTeX公式 + AI封面，绝对路径引用，finalize时嵌入)

| 文件 | 尺寸(px) | 页 |
|---|---|---|
| `assets/cover_bg.png` | 1536×1024(Galileo gpt-image-1.5) | 01 |
| `assets/formula_grpo_objective.png` | 5218×418 → 页内约1100×88 | 05 |
| `assets/formula_grpo_ratio_adv.png` | 2624×410 → 页内约640×100 | 05 |

## 页数 / 命名

16页，`NN_slug.svg`,`01`–`16` 连续(本篇是完整deck,非选页)。

## 可编辑性验证口径

pptx每页slide XML应有：真 `<a:t>` 文本run + `<a:custGeom>` 矢量形状 + logo `<p:pic>`;
公式/封面页额外含 `<p:pic>`(嵌入的PNG)。表格页以 `<a:custGeom>` 画线框 + `<a:t>` 填字，非整页图片。
