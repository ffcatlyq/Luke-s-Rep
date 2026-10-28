# 我们对ppt-master做了什么 · 为什么

给社区成员一处看清：这套Roche exemplar相对上游 `hugohe3/ppt-master` **改了什么、增量在哪、
没做什么、合规如何**。诚实分清"适配/封装"和"真创新",不吹。

## 一句话

**不vendor上游**(核心引擎一行没碰),只加一层"Roche品牌化 + 合规接入 + 社区可复用"的适配。
价值在**让上游这套在罗氏能合规跑、给社区能照抄、把坑写清楚**,不在技术突破。

## 适配一份deck到底做了什么(不是"只改design_spec")

上游一份example的组成，对照我们做/没做：

| 上游example组成 | 我们做了吗 | 说明 |
|---|---|---|
| `design_spec.md` | 做(重写) | 配方/输入，不是deck本体；Roche版见 [attention-transformer/design_spec.md](attention-transformer/design_spec.md) |
| `svg_output/` `svg_final/`(逐页SVG) | **做(手写16页)** | **这才是deck本体、工作大头**——主agent逐页手写，不是"改一个文件" |
| `exports/`(pptx) | 做 | svg_to_pptx转原生可编辑pptx(16页 + speaker notes) |
| `spec_lock.md`(执行真相锁) | 做(补全) | Roche Blue派生配色/字体/蓝阶，结构照上游 |
| `animations.json`(动画) | 做(补全) | animation_config.py scaffold自动配，导pptx时挂入 |
| `notes/`(演讲备注) | 做(补全) | 16页 + total.md,total_md_split.py拆 |
| `image_analysis.csv`(图分析) | 做(补全) | analyze_images.py自动产 |
| — brand-spec派生脚本 | **额外加** | `../scripts/build_roche_brand_spec.py` 从SSOT token派生品牌spec |
| — `_pipeline/` 工具 | **额外加** | 公式渲染 / 生图 / 预览，跨exemplar共用 |
| — LaTeX公式PNG | **额外加** | 块公式本地渲染(上游用外部codecogs) |
| — Galileo封面图 | **额外加** | 见下"适配验证点" |
| — 字体嵌入工具 | **额外加(默认不用)** | `_pipeline/embed_fonts.py`;实测PowerPoint拒装程序化嵌入，三份pptx一律不嵌，见下"字体嵌入" |
| — original-reference对照 | **额外加** | 原版缩小预览，便于对照 |

结论：**design_spec是配方，16页手写SVG是本体**;适配 = 派生brand-spec + 写Roche design_spec +
手写SVG + pipeline,不是"改一个文件就换皮"。

## 适配点(把上游搬到罗氏能用)

- **品牌**:brand-spec从hub Roche Blue SSOT token派生(不走Software Center);字体回归官方规范
  (Roche Sans Light主导、Serif仅引言，依据typography guideline);蓝阶从两个SSOT锚程序化派生。
- **合规接入**:块公式改**本地LaTeX**(不出境到codecogs);氛围图走 **Galileo gateway**(合规通道);
  论文原图不嵌(版权),改原生重画。
- **可复用**:exemplar库结构 + design_spec模板化(风格 ⊥ 颜色解耦)+ `_pipeline` 共用工具。
- **知识沉淀**:cairosvg五个坑(unsafe / 字体不回退 / 字重只认normal-bold / middle-anchor测宽 /
  缺 → )+ 字体安装，写进 [_pipeline/README.md](_pipeline/README.md)。

## 适配验证点：Galileo生图实测可用

本example封面 `cover_bg.png` 是 **Galileo Azure gpt-image(`gpt-image-1.5-2025-12-16`)实弹产出**,
不只是"配了张图",而是把生图这条适配路验证通了：

- `POST {GALILEO_ENDPOINT}/images/generations` HTTP 200真出图；用**用户自己的Galileo key**(非harness token)。
- 质量：`gpt-image-1.5` > `gpt-image-1` > `-mini`(封面精度用1.5);`gpt-image-2-2026-04-21` 当前Azure端 `unknown_model` 不可用。
- 提示词要点：描述块内结构 / 双描边 / 输入输出引脚 / 网格密度 / 留白构图，否则得空心块。

意义：生图从早前认为的"跨境硬阻塞"翻案为"走Galileo合规、开关是质量/成本取舍"。工具在 [_pipeline/gen_cover_image.py](_pipeline/gen_cover_image.py)。

## 创新？诚实的边界

如果"创新"指"做出上游做不到的新能力"——**没有**。核心引擎(SVG→原生可编辑pptx的custGeom、
风格库、主管线)全是上游的，我们没碰也没重写。我们的增量是三类，该打引号叫"适配层增量":

1. **合规接入**:本地LaTeX / Galileo gateway生图 / 不嵌版权图——让上游能力在罗氏合规落地。
2. **可复用化 / SSOT**:brand-spec从token派生、design_spec模板化、`_pipeline` 共用——把一次性
   产物变成社区可抄的库。
3. **工程知识沉淀**:cairosvg坑、字体约定、生图实测清单。

真正的"能力增量"候选是 **OMML可编辑公式**(让块公式既规范又能在PowerPoint里改)——上游也没有，
但需python-pptx注入 `<a:oMath>`,工作量大，列为follow-up。

## 字体嵌入(一律不嵌：PowerPoint拒装 + 许可双重原因)

svg_to_pptx **不嵌字体**——导出的pptx `ppt/fonts/` 为空，发给没装Roche Sans的人会回退系统字体。
三份exemplar pptx(attention / deepseek-r1 / claude-code-auto-mode)**都不嵌字体**,干净打开、优雅回退。

**为什么不嵌(两个原因)**:

1. **技术：PowerPoint拒装(实测2026-07-12,Windows)**。`_pipeline/embed_fonts.py` 按OOXML把Roche
   字体嵌进pptx后，PowerPoint打开弹"无法安装演示稿中的某些嵌入字体…一般错误"——**子集嵌入和
   `--no-subset` 完整字体嵌入都报**(字体本身是TrueType、`fsType=0`,已排除CFF / 许可位)。根因：
   PowerPoint只认它自己"嵌入字体"功能产的结构，拒装第三方工具程序化嵌入的字体。
2. **许可**:`fsType=0` 是技术标志，**不等于** EULA允许把字体随pptx外发再分发；即便技术通了，
   外发外部方仍须brand/legal确认。

**做法**:什么都不做——默认导出就不嵌。罗氏机器有Roche Sans正常显示；外部方自备字体或接受回退
(见brand bundle §III)。`embed_fonts.py` 保留作参考 / 供非PowerPoint阅读器测试，**默认不用**。

## 合规

三个"涉外/调外部服务"点经 `compliance-self-check` 四维定级**均为黄(可用，非红)**:Galileo生图、
公式渲染(已用本地matplotlib提到绿)、edge-tts旁白。黄 = 自用/内部可用 + 标注，不是"不能用";
红线只有"喂PII/HCP/患者/临床"(走CCCA)和"build-cli token挪用"。明细见 [README.md](README.md) 合规节。

## 局限 / 没做(诚实)

- 架构图是原生重画，结构忠实但**非1:1**(风格差异 + 多头h分叉未画),见
  [attention-transformer/README.md](attention-transformer/README.md);要1:1可用原图 + 出处。
- 块公式是图片，**不可编辑**(行内小数学仍是text);可编辑公式待OMML follow-up。
