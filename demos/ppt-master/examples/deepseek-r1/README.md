# deepseek-r1 — 技术公式格exemplar(from scratch全主管线)

《DeepSeek-R1》论文深读的 **16页Roche Blue** 复刻。与 [attention-transformer](../attention-transformer/) 同属
**技术公式格**(学术极简 + 蓝图schematic,白底冷调)——刻意做成**一套体系**:换一篇论文，只换内容不换风格。

> 这份的特殊意义：它是**从零走完ppt-master完整主管线**的验证样本。attention那份是复用上游 §IX大纲、
> 手写6页；这份补齐了两个此前没测到的环节——**Step 1源转换**(PDF → Markdown,`source_to_md.py`)与
> **Strategist自动从论文提炼 §IX逐页大纲**,并产出**全套辅助**(spec_lock / notes / image_analysis / animations)。

## 一句话

同一套技术公式格版式 × Roche Blue品牌，套到一篇全新论文上，端到端跑通：
PDF抓取 → 转Markdown → Strategist提炼大纲 → 逐页手写16页SVG → 原生可编辑pptx。

## 原版vs Roche对照

| 维度 | 原版论文 | 本Roche版 |
|---|---|---|
| 载体 | PDF(双栏学术排版) | 本地原生可编辑 .pptx(16页16:9) |
| 品牌 | 无统一色；衬线正文 | Roche Blue单主色 + 蓝阶层次；Roche Sans Light主导、Serif仅引言 |
| 图表 | matplotlib折线 / 论文图 | 全部**原生重画**(折线图 / schematic / 表格 = 可编辑 `<a:custGeom>`) |
| 公式 | 排版内嵌 | GRPO目标函数 = 本地LaTeX渲染PNG(Computer Modern) |
| 封面 | 无 | Galileo gpt-image生成的RL分支搜索树氛围图(一条高亮路径 = 习得的推理轨迹) |
| 原图版权 | — | **不嵌**论文原图，原生重画替代 |

## 页清单(16页)

封面 · KPI · 核心思想(纯RL vs传统)· 两个模型(R1-Zero vs R1)· **GRPO公式** · 奖励设计 ·
自演化图表 · aha moment引言页 · 从Zero到R1 · **多阶段pipeline** · 四阶段图例 ·
**benchmark表(R1 vs o1)** · 阶段进步表 · 蒸馏schematic · **蒸馏benchmark表** · 结论 + 局限。

预览见 [`roche/preview/`](roche/preview/);配方见 [`design_spec.md`](design_spec.md)(§IX有逐页大纲)。

## 关键决策

- **风格锁定，不重造**:画布 / 字体 / 蓝阶 / 页眉 / takeaway带 / 卡片 / 表格规则全部沿用
  [attention的design_spec](../attention-transformer/design_spec.md);本篇只改 §III强调分布、§VI图像策略、§VII页清单。
  身份引用 [Roche Blue brand bundle](../../brand/roche-blue/design_spec.md)。
- **内容SSOT = 源文档**:内容来自 `sources/deepseek-r1.md`(论文转的md),Strategist提炼进design_spec §IX,
  不硬编码、不手搓slide文案。数字全部溯源到论文的表 / 节(footer标source)。
- **图分层**:schematic / 表格 / 图表纯SVG(可编辑);块公式本地LaTeX;封面氛围图走Galileo;论文原图不嵌。
- **cairosvg五坑**全部规避(见 [`../_pipeline/README.md`](../_pipeline/README.md)):`→` 包mono tspan、
  Greek θ 不入Roche Sans、居中文本不换字体、独立family名认Light/Medium、`unsafe=True` 渲外部图。

## 可编辑性验证(实测)

pptx 16页，`svg_to_pptx --only native` 16/16成功。slide XML统计：
**545个真 `<a:t>` 文本run + 75个 `<a:custGeom>` 矢量形状**,4张去重嵌入图(封面底图 / 2张公式 / logo)。
即每页都是真文本 + 真矢量，不是整页图片版——在PowerPoint里可直接改字、改图形、改表格数据。

成品：[`roche/pptx/deepseek-r1-roche.pptx`](roche/pptx/deepseek-r1-roche.pptx)(~480KB)。

## 目录

```
deepseek-r1/
  README.md              # 本文件
  design_spec.md         # 配方 + §IX 逐页大纲(Strategist 产出)
  roche/
    svg/                 # 16 页手写 SVG 源(引用 assets/ 与 logo 绝对路径)
    preview/             # 16 页 PNG 预览(cairosvg)
    assets/              # 封面 AI 底图 + 2 张 LaTeX 公式 PNG
    notes/               # 16 页演讲备注
    pptx/                # 成品原生可编辑 pptx
    spec_lock.md         # 视觉执行真相锁
    animations.json      # 过场 / 出场动画规格
    image_analysis.csv   # 图像尺寸 / 版式分析
  original-reference/
    preview/             # 论文原页缩小 PNG(对照,不 vendor 全文)
    README.md            # 指向 arXiv + 原版口径
```

## 合规

低敏：DeepSeek-R1是公开论文；生图走Galileo gateway(用你自己的key,合规通道)= 黄(可用)。
详见 [`../ADAPTATION.md`](../ADAPTATION.md) 合规节与 [`../README.md`](../README.md)。
