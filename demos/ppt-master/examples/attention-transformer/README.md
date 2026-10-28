# attention-transformer — 技术公式格(首格exemplar)

把ppt-master上游example `attention_is_all_you_need`(《Attention Is All You Need》论文深读deck)
**完整16页**复刻成 **Roche Blue技术公式格**:学术极简 + 蓝图schematic、白底冷调、原生可编辑pptx。
它是五格计划的第一格，也是后续四格照抄结构的模板(配方见 [`design_spec.md`](design_spec.md))。

## 成品

- 预览：[`roche/preview/`](roche/preview/)(16页PNG,gitignore,本地渲染)
- SVG源：[`roche/svg/`](roche/svg/)(手写16页，可再编辑)
- pptx成品：[`roche/attention-transformer-roche.pptx`](roche/attention-transformer-roche.pptx)(原生可编辑，16页 + speaker notes)
- 视觉执行锁：[`roche/spec_lock.md`](roche/spec_lock.md)(Roche Blue派生配色 / 字体 / 蓝阶)
- 讲稿：[`roche/notes/`](roche/notes/)(16页 + `total.md`,conversational-academic)
- 原版对照：[`original-reference/preview/`](original-reference/preview/)(上游16页缩小图)

> 辅助文件全套(spec_lock / notes / animations.json / image_analysis.csv)在项目侧同时产出，验证
> ppt-master全流水线跑通；animations.json / image_analysis.csv是流水线中间产物，随pptx导出即用。

## 十六页

| 页 | 内容 | 版式 | 图依赖处理 |
|---|---|---|---|
| 01 cover | 标题 + 作者 + pull-quote + 蓝图氛围 | 左标题 / 右氛围 | Galileo Azure gpt-image蓝图底图，左半留白叠标题 |
| 02 why-it-matters | 4张KPI卡 + headline带 | kpi_cards | 零图 |
| 03 sequence-evolution | RNN链 / CNN局部场 / self-attention网三motif | 三schematic并排 | 纯SVG重画(替上游氛围图) |
| 04 rnn-cnn-limits | 三限制pillar + 顺序链schematic | vertical_pillars | 纯SVG重画(替上游瓶颈图) |
| 05 architecture | Encoder–Decoder栈 + 编号图例 | node-link + legend | 原生node-link重画(替上游论文Figure 1) |
| 06 encoder-decoder | Encoder 2子层vs Decoder 3子层对照 | comparison_columns | 零图 |
| 07 scaled-dot-product | 公式 + 4步 + dataflow | 公式带 + 步骤 + 流 | 块公式LaTeX PNG(Computer Modern);dataflow纯SVG |
| 08 multi-head-attention | 两行公式 + 4步 + h头并行流 | 公式带 + 步骤 + 流 | 块公式LaTeX PNG;h头dataflow纯SVG(替Figure 2右) |
| 09 three-uses | encoder / masked / cross三用途 | vertical_pillars | Q/K/V来源图纯SVG |
| 10 ffn-residual-layernorm | 子层剖面 + FFN / 残差 / LayerNorm三模块 | 剖面 + module_composition | 纯SVG重画(替上游子层图) |
| 11 positional-encoding | 两行PE公式 + sin/cos叠加曲线 | 公式带 + 曲线 | 块公式LaTeX PNG;正弦曲线纯SVG重画 |
| 12 complexity-table | Table 1复杂度对照 | basic_table | 零图 |
| 13 training-setup | 硬件 / 时间 / 优化器 / 正则4卡 | kpi_cards | 零图 |
| 14 results | Table 2 BLEU + FLOPs | basic_table | 零图 |
| 15 ablations | Table 3五条消融要点 | vertical_list | 零图 |
| 16 conclusion | 收束标题 + Transformer后代谱系树 | lineage_tree | 纯SVG重画(替上游氛围图) |

## 原版vs Roche:改了什么、为什么

| 维度 | 上游原版 | Roche版 | 为什么 |
|---|---|---|---|
| 主色 | navy `#1A365D` + `#3182CE` | Roche Blue `#0B41CD` + `#1482fa`,加中蓝/浅蓝层次 + 克制渐变 | 品牌主色；"单主色克制"靠深浅蓝 + 渐变做层次，不引入第二主色 |
| 标题字体 | Georgia(衬线) | **Roche Sans Light**(优雅无衬线display) | Roche官方typography:Sans是主字体，Light用于display/headline |
| 引言 / 作者 / 图注 | — | **Roche Serif Light italic** | Serif在Roche是辅助字体，恰用于quotes / small copy |
| 块公式 | codecogs LaTeX → PNG(外部服务) | **本地matplotlib LaTeX → PNG**(Computer Modern) | 数学规范性(斜体变量/正体函数名/真分式根号)通用字体给不了；本地渲染不依赖外部 |
| 封面底图 | AI生成蓝图氛围 | Galileo Azure gpt-image重生成Roche Blue冷调 | 氛围质感；经Galileo合规通道，非跨境硬阻塞 |
| 架构图 / Fig 2 | 嵌论文原图(位图) | 原生SVG重画(可编辑custGeom) | 可编辑是ppt-master卖点；论文原图有版权 |

一句话：**图像分层**——氛围图走AI(有质感),schematic/公式走纯可编辑SVG(锐利 + 可编辑),
论文原图不嵌(版权);字体回归Roche规范(Sans主、Serif仅引言),公式回归LaTeX(规范)。

## 架构图：自画到了什么程度 + 用原图的备选

P05是纯SVG重画(原生可编辑),对齐了论文Figure 1的主结构：Encoder/Decoder双栈、
各sublayer + Add & Norm、embedding + positional encoding、Linear/Softmax、encoder→decoder
的K/V跨注意力、以及每个sublayer的**残差skip连接弧线**(近版本补的，对应
LayerNorm(x + Sublayer(x)))。

诚实说清没做到原图的地方(受半幅双列版式所限，再堆会糊):
- 残差弧线是**示意的左侧短弧**,不是论文那种完整环绕整个sublayer的绕线；
- 多头内部的h头分叉、注意力块的V/K/Q三路输入箭头**没画**(此尺度画上会杂乱)。

**备选：直接用论文原图 + 出处。** 复杂结构图(那些精细箭头/绕线)自画到像素级性价比低。
若某页只是要讲清结构、不追求可编辑与品牌统一，**内部教学/分享**场景可直接嵌论文Figure
(带出处引用，如 "Vaswani et al. 2017, Figure 1")——学术引用低风险。取舍准则：
**exemplar为展示"复杂图也能做成原生可编辑矢量"的能力 → 自画；日常内部deck求快求全 → 用原图。**
版权注意见下节follow-up + 上游SECURITY.md。

## 已知取舍 / follow-up

- **块公式是图片，不可编辑**(行内小数学如 `d_model=512`、`O(n)` 仍是可编辑text)。想要
  "可编辑 + 规范"的PowerPoint原生公式(OMML)是follow-up,见
  [`../README.md`](../README.md) 与 [`design_spec.md`](design_spec.md) §公式。
- **Roche字体外发许可**:嵌Roche Sans/Serif的pptx外发给外部方需对方自备字体，否则回退
  系统字体；敏感deck自用不外发。
- **cairosvg预览的字重**近似(toy API只normal/bold);pptx里字重由svg_to_pptx按
  family名(`Roche Sans Light` 等)正确导出。

## 复现

字体安装、cairosvg四个坑、完整管线命令见 [`../_pipeline/README.md`](../_pipeline/README.md)。
本例专属产物的生成：

```bash
# 块公式(P07 attention · P08 multi-head 两行 · P11 positional 两行)
python3 ../_pipeline/render_formula.py --out roche/assets/formula_attention.png
python3 ../_pipeline/render_formula.py --out roche/assets/formula_mha_top.png --fontsize 30 \
  --expr '\mathrm{MultiHead}(Q,K,V)=\mathrm{Concat}(\mathrm{head}_1,\dots,\mathrm{head}_h)\,W^{O}'
python3 ../_pipeline/render_formula.py --out roche/assets/formula_mha_bot.png --fontsize 30 \
  --expr '\mathrm{head}_i=\mathrm{Attention}(QW_i^{Q},\,KW_i^{K},\,VW_i^{V})'
python3 ../_pipeline/render_formula.py --out roche/assets/formula_pe_sin.png --fontsize 30 \
  --expr 'PE_{(pos,\,2i)}=\sin\!\left(pos\,/\,10000^{\,2i/d_{model}}\right)'
python3 ../_pipeline/render_formula.py --out roche/assets/formula_pe_cos.png --fontsize 30 \
  --expr 'PE_{(pos,\,2i+1)}=\cos\!\left(pos\,/\,10000^{\,2i/d_{model}}\right)'
# 封面氛围图(需 GALILEO_ENDPOINT + GALILEO_AZURE_API_KEY)——prompt 见 design_spec.md §图像策略
python3 ../_pipeline/gen_cover_image.py --out /tmp/cover_raw.png --prompt-file /tmp/cover_prompt.txt
# 之后 center-crop 到 16:9 存 roche/assets/cover_bg.png
# 预览
python3 ../_pipeline/render_preview.py --in roche/svg --out roche/preview
```

全流水线(项目侧，含四类辅助文件):`svg_quality_checker` → `finalize_svg` →
`svg_to_pptx --only native --source final --animation-config animations.json`(+ 讲稿自动挂notes);
辅助文件由 `total_md_split.py`(拆讲稿)/ `analyze_images.py`(→ image_analysis.csv)/
`animation_config.py scaffold`(→ animations.json)产出。命令与顺序见 [`../_pipeline/README.md`](../_pipeline/README.md)。
