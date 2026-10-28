# Roche Blue · 技术公式格 — design_spec(exemplar模板)

> 本文件既是本样例(attention-transformer)的配方，也是后续四格(data-journalism /
> blueprint / consulting / swiss-minimal)照抄结构的模板：**§II画布 / §IV字体系统 /
> §V版式 / §VIII管线原样保留**,只改 §III配色强调分布、§VI图像策略、§VII页清单。
>
> 配色 / 字体的唯一SSOT是hub Roche brand token(`assets/roche-brand/tokens/` +
> `slidev/themes/roche-blue/tokens.json`),经 `demos/ppt-master/scripts/build_roche_brand_spec.py`
> 派生。本spec是"token落到技术公式格"的实例——token改了重跑脚本、回填本文件。

## I. 项目信息

| 项 | 值 |
|---|---|
| 样例 | attention-transformer(《Attention Is All You Need》深读的Roche Blue复刻) |
| 画布 | PPT 16:9(1280×720) |
| 风格格位 | 技术公式(technical-formula):学术极简 + 蓝图schematic,白底冷调 |
| 源配方 | 上游 `examples/ppt169_attention_is_all_you_need`(navy / cool-corporate) |

## II. 画布规格

| 属性 | 值 |
|---|---|
| viewBox | `0 0 1280 720` |
| 安全边距 | 左右60px、上下约50px;内容区1160×620 |
| 页眉 | 顶部约60px:6px accent竖条 + 标题 + 小写eyebrow |
| 页脚 | 底部约30px:来源注(左)+ 页码(右),tertiary色 |
| logo | 内容页右上角(亮底用Blue版);封面左上角放大 |

## III. 配色(Roche Blue)

单主色克制、白底大留白是Roche视觉核心。**"克制"靠蓝的深浅 + 克制渐变做层次，
不引入第二主色**(反例：v1只用两个蓝 → 单调)。

| 角色 | 源(navy) | Roche | 用途 |
|---|---|---|---|
| 背景 | `#FFFFFF` | `#FFFFFF`(封面 `#FBFBF9`) | 页底 |
| 面板 / 次背景 | `#F5F7FA` | `#F5F7FA` | 卡片、takeaway、容器 |
| Primary | `#1A365D` | `#0B41CD` | 标题、表头填充、深块、边框、数字 |
| Accent(亮蓝) | `#3182CE` | `#1482fa` | 竖条、eyebrow、关键数据 |
| 中蓝mid | `#63B3ED` | `#0F5EE1` | 层次过渡(徽章 / 卡条进阶) |
| 浅蓝light/lighter | — | `#5FAAFC` / `#95C7FD` | 第3-5级层次 |
| Accent tint | `#EBF4FB` | `#E9EEFA` / `#F0F4FC` | 高亮行 / sublayer块底 |
| 正文 | `#1A202C` | `#333333` | 主体 |
| 次文字 | `#4A5568` | `#706B69` | 图注 / 副标 |
| 三级文字 | `#A0AEC0` | `#A39F9C` | 页码 / footer |
| 边框 | `#E2E8F0` | `#E0E0E0` | 卡边 / 表格线 |
| 成功 | `#2F855A` | `#007A3B` | O(1)、BLEU提升 |
| 警告 | `#C53030` | `#D0021B` | O(n)、劣化 |

中/浅蓝与tint **不手填**——由 `demos/ppt-master/scripts/build_roche_brand_spec.py` 从两个
SSOT锚(primary `#0B41CD` + slidev primaryDim `#1482fa`)+ 白**程序化派生**(mid=插值0.45、
light/lighter=bright→白0.32/0.55、tint=primary→白0.91/0.94),规则固定可复现，不是第二主色。
官方整套蓝阶在Frontify(colors.json的 `_todo` page 571),够到后可resolve进token换锚点。

克制渐变(Roche也用，少量):accent竖条primary→bright、公式带底 `#F8FAFF`→`#E9EEFA`、
输出块primary→mid、KPI/图例徽章按primary→lighter进阶。语义色只在"读数"处(绿=好、红=差)。

## IV. 字体系统(回归Roche官方规范)

Roche typography guideline(`assets/roche-brand/pages/brand-elements/typography.md`)口径：
**Roche Sans是主字体**("key to all communication",Light用于display/headline/body);
**Roche Serif是辅助**("heroed within quotes, information design or small copy")。所以：

| 用途 | 字体(family名) | 说明 |
|---|---|---|
| display / 大标题 / 页标题 / hero数字 | **`'Roche Sans Light'`** | Roche招牌优雅Light;不是 `font-weight:300`(见下坑) |
| eyebrow / 标签 / 表头 / 强调 / 白底反白 | **`'Roche Sans Medium'`** | 需要对比处 |
| 正文 / 说明 | `'Roche Sans'`(Regular) | |
| 引言pull-quote / 作者 / 斜体图注 | **`'Roche Serif Light'`** + `font-style="italic"` | Serif只用在它该用的地方 |
| 代码 / 记号 | `'Consolas','DejaVu Sans Mono',monospace` | |
| 块级数学公式 | 不用字体——LaTeX渲染PNG(见 §VI) | |
| 含CJK文本 | `'Noto Sans CJK SC'` 放字体栈首位 | cairosvg tofu对策 |

字号阶：cover hero 72、页标题34-36、KPI数42-62、副标19-25、正文14-16、eyebrow 12-13、
页码/footer 11。

### cairosvg四个坑(预览必读，详见 `../_pipeline/README.md`)

1. `unsafe=True` 必开(否则外部 `<image>` 白块)。
2. 字体不做per-glyph回退——缺字形 = tofu;Roche Sans缺 `→`(其余 `√·—×÷²≤` 都有),
   箭头包mono `<tspan>` 或改连字符。
3. **字重只认normal/bold**——`font-weight:300` 渲染成bold,不是Light!真Light用独立
   family名 `'Roche Sans Light'`。
4. `text-anchor="middle"` 的 `<text>` 里含改font-family / baseline-shift的tspan会算错
   宽度→甩偏；居中文本只用改颜色的tspan,要上下标/换字体改 `text-anchor="start"` 定x。

## V. 版式原则

- 页眉：6px accent竖条 + Roche Sans Light标题 + Roche Sans Medium eyebrow(letter-spacing 1.5)。
- takeaway带：面板底 + 左竖条 + eyebrow + 一句"读数"结论(每页给读者落点)。
- 卡片：白底 + `#E0E0E0` 边 + 轻投影 + 左色条 + 圆角12。
- 表格：外框primary 2px;表头primary填充 + Medium白字；关键行accent tint高亮；列分隔 `#E0E0E0`。
- 填充率 ≥ 80%;不动已验证通过的页面。

## VI. 图像策略(混合，分层)

技术公式格图依赖低，但**不一刀切"零AI图"**——氛围图该用就用，只是分层：

| 类型 | 做法 | 工具 |
|---|---|---|
| 块级数学公式 | LaTeX渲染Roche Blue透明PNG(Computer Modern);行内小数学仍用可编辑text | `_pipeline/render_formula.py` |
| 氛围 / 装饰背景(封面蓝图等) | Galileo Azure gpt-image生成Roche Blue冷调 | `_pipeline/gen_cover_image.py` |
| schematic / 架构 / dataflow / 图表 | 纯SVG手写(原生 `<a:custGeom>`,可编辑) | agent手写 |
| 论文 / 版权原图 | **不嵌**,原生重画替代 | agent手写 |

封面氛围图prompt要点(否则得空心块):具体描述块内部结构(H形节点)、双描边、输入输出
引脚、网格密度、**左半留白构图**(叠标题)。模型用 `gpt-image-1.5-2025-12-16`(比mini精);
`gpt-image-2` 那个带日期ID当前Azure端不认。

**公式可编辑性follow-up**:块公式当前是图片(不可编辑),换来数学规范。可编辑 + 规范的
PowerPoint原生公式(OMML)需python-pptx注入(svg_to_pptx不支持),列为后续task。

## VII. 页清单

| 页 | 版式 | 图 |
|---|---|---|
| 01 cover | 左标题 / 右蓝图氛围；Serif Light pull-quote + 作者 | AI底图 |
| 02 why-it-matters | 1×4 KPI卡(Light大数字)+ takeaway | 零 |
| 05 architecture | 左node-link图 / 右5条编号图例 | 零(重画) |
| 07 scaled-dot-product | LaTeX公式带 + 左4步 / 右dataflow | 公式PNG |
| 12 complexity-table | 全宽表 + takeaway | 零 |
| 14 results | 全宽表(末两行高亮)+ takeaway | 零 |

## VIII. 管线

见 [`../_pipeline/README.md`](../_pipeline/README.md)。概要：`project_manager.py init` →
主agent逐页手写SVG(公式/氛围图先用 `_pipeline` 脚本产出、`<image>` 引用)→
quality_checker → finalize → svg_to_pptx `--only native` → render_preview。可编辑性验证：
slide XML有真 `<a:t>` + `<a:custGeom>` + logo `<p:pic>`。

## IX. 作为后续四格模板

保留 §II / §IV(含四个cairosvg坑)/ §V / §VIII;按格位改：
- §III配色：保留角色表，调强调分布——data-journalism暗底 `#0d0d0d` + 单暖色pop;
  swiss-minimal极浅灰阶大留白；blueprint加密node-link;consulting走矩阵 / 象限 / harvey balls。
- §VI图像：图轻格(本格 / data-journalism / blueprint / swiss-minimal)可零AI图或仅氛围图；
  图重格换本地素材，不默认开生图。
- §VII页清单：换成该格代表页；每格附自己的design_spec.md。
