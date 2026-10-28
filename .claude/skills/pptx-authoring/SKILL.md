---
name: pptx-authoring
description: 把论文/文档做成本地原生可编辑的 .pptx(Roche Blue风格),走ppt-master引擎。当用户要"做个pptx / PPT / 幻灯片(要PowerPoint能改的原生文件)"、"把这篇论文/文档做成ppt"、"native editable pptx"、"ppt-master"、"做份Roche风格的ppt发邮件附件"、"离线能改的slides"时触发。这是slide第三条路径——本地原生pptx(对照slidev=HTML / gslide=云端)。纯slidev HTML演示或Google Slides云端协作走各自的skill,不用本skill。
---

# pptx-authoring — Roche Blue原生可编辑pptx(ppt-master适配层)

**这是slide的第三条路径**:本地原生可编辑 `.pptx`(离线继续改、进邮件附件、不依赖Google账号),
对照 `slidev-authoring`(HTML)/ `gslide-authoring`(云端)。底层用上游 `hugohe3/ppt-master` 引擎
(SVG → 原生DrawingML custGeom),本skill只加 **Roche适配层**:品牌bundle + 版式配方 + 五个
cairosvg坑 + canonical导出命令 + 合规stance。**不vendor引擎**(见Step 0)。

内容SSOT、可抄配方、_pipeline工具、exemplar全在hub `demos/ppt-master/`,本skill指过去、不复制。

## 铁律(上游规定，别违)

- **主agent逐页手写SVG**——禁脚本批量生成SVG、禁子agent画页。公式/氛围图/预览等"非手写"产物才用 `_pipeline/` 脚本。
- 画布1280×720(ppt169)。每页顶层 `<g id="...">` 分组(动画按group作用)。

## Step 0 — 装引擎(不vendored,新容器里没有)

引擎大(examples ~1.3GB)、上游活跃维护、我们故意不改 → **不复制进hub**。按需装、float到最新：

```bash
bash .claude/skills/pptx-authoring/scripts/setup-engine.sh   # sparse clone/pull 最新 + venv + 冒烟测
source ~/ppt-master/.venv/bin/activate
```

`setup-engine.sh` 只拉引擎(sparse,跳过examples大二进制)、拿最新(不钉SHA,skill与时俱进)、
装完跑 `smoke_test.py` 金丝雀。**上游改了导出接口(如老版 `--only native` 新版已移除)冒烟会红**——
红了先看 `svg_to_pptx.py --help` 更新下方canonical命令，别照抄旧flag。

## Step 1 — 源转md

```bash
python3 ~/ppt-master/skills/ppt-master/scripts/source_to_md.py <pdf或url>   # PDF 需 PyMuPDF(setup 已装)
```

## Step 2 — Strategist:产design_spec + §IX逐页大纲

- **品牌**:引用 [`demos/ppt-master/brand/roche-blue/`](../../../demos/ppt-master/brand/roche-blue/design_spec.md)(身份：色/字/logo/voice/图标)当Step 3模板。
- **版式**:抄 [`demos/ppt-master/examples/attention-transformer/design_spec.md`](../../../demos/ppt-master/examples/attention-transformer/design_spec.md)(技术公式格：§II画布 / §IV字体 / §V版式 / §VIII管线原样保留，只改 §III强调分布 / §VI图策略 / §VII页清单)。
- **内容**:从 `sources/` 提炼进design_spec **§IX逐页大纲**(title/layout/content)——§IX是内容SSOT。
- 换任何论文：brand(身份)不变 + 版式约定不变 + §IX(内容)每篇重写。
- **叙事方法论(第三轴，罗氏/药企主题必读)**:做罗氏/药企/pipeline/投资者主题deck时，§IX大纲**先按** [`references/pharma-deck-narrative.md`](references/pharma-deck-narrative.md) 定叙事弧 + 幻灯片原型 + 术语(CER/NME/FIC/BIC/unmet need/SoC…)+ 框架(unmet need→market→positioning→evidence;Prevent/Stop/Cure;五大TA),再落版式。这让deck"讲得像药企在讲",不只"看着像罗氏"。**三轴 = 设计(brand)+ 合规(下 §合规)+ 叙事方法论(此)**。非药企主题(论文/技术)跳过本轴。

## Step 3 — 逐页手写SVG(工作大头)

字体约定(brand §III):display/标题/hero=`'Roche Sans Light'`;eyebrow/表头/反白=`'Roche Sans Medium'`;
正文=`'Roche Sans'`;引言/作者=`'Roche Serif Light'` italic;记号=mono;块公式=LaTeX PNG。

**图像分层**:schematic/架构/表格/图表=纯SVG(原生可编辑);块公式=`_pipeline/render_formula.py`;
氛围/封面=`_pipeline/gen_cover_image.py`(Galileo);**图标优先官方Roche图标库**
(`assets/roche-brand/icons/svg/`,1454个，Healthcare 628);论文/版权原图**不嵌**,原生重画。

**cairosvg五坑**(预览必知，详见 [`_pipeline/README.md`](../../../demos/ppt-master/examples/_pipeline/README.md)):
① `unsafe=True` 才渲外部 `<image>` ② 字体不per-glyph回退(缺字形=tofu;CJK行Noto首位)
③ 字重只认normal/bold(真Light用独立family名 `'Roche Sans Light'`)④ `text-anchor="middle"` 里
换字体/baseline-shift的tspan会算错宽度(居中文本只改颜色；上下标/换字体改 `start` 手动定x)
⑤ Roche Sans缺 `→`(其余 `√·—×÷²≤` 都有)——`→` 包mono tspan,居中文本改 `·`;Greek `θ` 缺→spell out。

## Step 4 — 辅助文件

- `notes/NN_*.md` 逐页演讲备注(导出自动挂)。
- `animations.json`:`animation_config.py scaffold <proj>` 自动配，`... validate <proj>` 校验group id对得上(group级别没有 `stagger` 字段；效果名如 `wipe` 不是 `wipe-right`)。

## Step 5 — 导出(canonical,SSOT,随上游漂移就更新这条)

**导出前必须有 `$PROJ/spec_lock.md` 主题契约**(上游新增的硬前置——缺了 `svg_to_pptx.py` 会红)。
最小契约(自由设计 / 仅品牌色的项目)四个段,行格式一律 `- key: value`:

```markdown
## pptx_structure
- mode: flat          # 自由设计走 flat；结构化/套模板项目改走 workflows/restore-pptx-structure.md

## typography
- title: 40           # px
- body: 18            # px
- font_family: Arial  # major/minor 字面

## colors
- bg: FFFFFF          # HEX,映射到 theme 槽位
- text: 1A1A1A
- primary: 0B41CD
- accent: 00A3E0

## canvas
- viewBox: 0 0 1280 720
```

> `mode: flat` 是关键——声明本项目按扁平(自由设计)结构导出,不套版式母版。
> 若 `## pptx_structure`/`- mode:` 缺失或写错,导出直接失败;解析见上游 `theme_fonts.py`/`theme_colors.py` 的 `_LOCK_ROW_RE`。

```bash
python3 ~/ppt-master/skills/ppt-master/scripts/svg_quality_checker.py $PROJ
python3 ~/ppt-master/skills/ppt-master/scripts/animation_config.py validate $PROJ
python3 ~/ppt-master/skills/ppt-master/scripts/finalize_svg.py $PROJ
# 确保 $PROJ/spec_lock.md 已就位(见上)
python3 ~/ppt-master/skills/ppt-master/scripts/svg_to_pptx.py $PROJ   # native 默认;自动挂 animations.json + notes/
python3 demos/ppt-master/examples/_pipeline/render_preview.py --in $PROJ/svg_final --out $PROJ/preview
```

**别用 `--only native`**(老flag,新版移除；native已是默认)。以setup冒烟测 + `--help` 为准。

## Step 6 — 验可编辑性

pptx每页slide XML应有：真 `<a:t>` 文本run + `<a:custGeom>`/`<a:prstGeom>` 矢量形状 + logo `<p:pic>`
(非整页图片版);带动画的页有 `<p:timing>`,备注在 `ppt/notesSlides/`。

## Step 7 —(opt-in)嵌字体

```bash
python3 demos/ppt-master/examples/_pipeline/embed_fonts.py --in $PROJ/exports/<f>.pptx --out <name>-roche.pptx
```

**默认不嵌**——Roche字体 `fsType=0` 技术上可嵌，但 **fsType≠授权协议**。内部自用 / committed内部
demo可嵌；**外发外部方须brand/legal确认**;否则外部方自备字体。完整口径见ADAPTATION.md字体嵌入节。

## 合规

黄档(可用):驱动LLM = Galileo;氛围图 = Galileo gateway(你自己的key);块公式本地LaTeX;
schematic纯本地SVG。**红线**:别喂PII/HCP/患者/临床(走CCCA),别build-cli token挪用，
别拿fsType=0当字体外发许可。详见 [`demos/ppt-master/examples/ADAPTATION.md`](../../../demos/ppt-master/examples/ADAPTATION.md)。

## 参考(hub SSOT,skill不复制)

- exemplar库 + 可抄配方：`demos/ppt-master/examples/`(attention-transformer / deepseek-r1)
- 品牌bundle:`demos/ppt-master/brand/roche-blue/`
- 共用工具：`demos/ppt-master/examples/_pipeline/`(render_formula / gen_cover_image / render_preview / embed_fonts)
- 适配说明 + 合规 + 字体stance:`demos/ppt-master/examples/ADAPTATION.md`
