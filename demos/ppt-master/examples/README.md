# ppt-master · Roche exemplar库

给社区成员的**可抄配方库**:每个exemplar = 一种演示风格 × Roche Blue品牌，附原版对照 +
可复现的SVG源 + `design_spec.md`(拿去改皮就能做自己的deck)。厚在可复用价值，不厚在静态产物。

> 背景：ppt-master是slide的第三条路径——**本地原生可编辑 .pptx**(离线继续改、进邮件附件、
> 不依赖Google账号),对照slidev(HTML)/ gslide(云端)。接入与合规见上级
> [`../README.md`](../README.md) 和 [`../docs/roche-adaptation.md`](../docs/roche-adaptation.md)。

> **想先搞清"我们相对上游改了什么、增量在哪、没做什么、合规如何"?** 看
> [ADAPTATION.md](ADAPTATION.md)——适配点 / 创新边界(诚实，不吹)/ Galileo生图验证点 / 合规综述。

## 为什么做"精选exemplar"而不是全量复刻上游

ppt-master上游有20+ example,但题材多与罗氏无关(糖果节 / 时尚周)、图重、二进制膨胀
innersource。所以改为：**1个Roche品牌bundle + 5个精选exemplar**,每格占一种风格、
各自带 `design_spec.md` 当配方。风格 ⊥ 颜色解耦——上游 `references/visual-styles/` 的风格
"carry no hex",任意风格都能 × Roche Blue。

## 五格计划与状态

| 格位 | 风格 | 图依赖 | 状态 | 目录 |
|---|---|---|---|---|
| 技术公式 | 学术极简 + 蓝图schematic,白底冷调 | 低(封面AI氛围图，其余纯SVG) | **已完成** | [`attention-transformer/`](attention-transformer/) |
| 数据新闻 | 暗底 + 单暖色pop,真图表 | 低(零AI图) | 小样在 `ppt-master-sample/`,待正式化 | `data-journalism/`(待建) |
| 技术公式(from scratch) | 同上 × DeepSeek-R1论文 | 低(封面AI氛围图，其余纯SVG) | **已完成** — 16页，验证Step1源转换 + Strategist自动大纲 + 全套辅助 | [`deepseek-r1/`](deepseek-r1/) |
| 暗色科技(B类本地化) | 深空黑底 + 辉光/网格 + 单主色蓝阶 | 低(零AI图) | **已完成** — 10页，上游auto-mode例逐页本地化为罗氏亲历(两道闸/#307被拦/搬家坑),含original-reference对照 | [`claude-code-auto-mode/`](claude-code-auto-mode/) |
| blueprint架构 | node-link结构图 | 低(零AI图) | 小样在 `ppt-master-sample/ai-model-viz/`,待正式化 | `blueprint/`(待建) |
| consulting战略 | 矩阵 / 象限 / harvey balls | 中 | 待做 | `consulting/`(待建) |
| swiss-minimal报告 | 极简大留白 | 低 | 待做 | `swiss-minimal/`(待建) |

## 目录约定(每个exemplar同构，方便复制扩展)

```
<exemplar>/
  README.md            # 本例说明 + 原版 vs Roche 对照 + 关键决策
  design_spec.md       # 本格配方(配色/字体/版式/图像策略/页清单),也是"可抄模板"
  roche/
    svg/               # 6 页手写 SVG 源(lean,引用 assets/ 与共享 logo 的绝对路径)
    preview/           # 6 页 PNG 预览(cairosvg 渲染)
    assets/            # 该例专属图(AI 封面底图、LaTeX 公式 PNG 等)
    <name>-roche.pptx  # 成品:原生可编辑 pptx
  original-reference/
    preview/           # 上游原版对应页的缩小预览(仅对照,不 vendor 上游大文件)
    README.md          # 指向上游完整 example 路径 + 原版配色/字体口径
_pipeline/             # 所有 exemplar 共用的复现脚本(SSOT):公式/生图/预览
```

## 复现一个exemplar

见 [`_pipeline/README.md`](_pipeline/README.md)(完整管线命令 + cairosvg四个坑 + 字体安装)。
概要：`project_manager.py init` → 主agent逐页手写SVG(需要的公式/氛围图先用 `_pipeline`
脚本产出、SVG里 `<image>` 引用)→ quality_checker → finalize → svg_to_pptx → render_preview。

## 配色 / 字体的SSOT

**不硬编码**:配色与字体的唯一来源是hub Roche brand token
(`assets/roche-brand/tokens/` + `slidev/themes/roche-blue/tokens.json`),经
[`../scripts/build_roche_brand_spec.py`](../scripts/build_roche_brand_spec.py) 派生品牌spec。
各exemplar的 `design_spec.md` 是"token落到某风格"的实例——token改了重跑脚本、回填spec。

Roche官方typography定位(见 `assets/roche-brand/pages/brand-elements/typography.md`):
**Roche Sans是主字体**(Light用于display/headline/body,是"key to all communication");
**Roche Serif是辅助**(用于quotes / small copy / footnotes)。所以exemplar里正文与标题走
Roche Sans(Light做优雅display),Serif只留给引言 / 作者 / 图注。

## 原版vs Roche的对照约定

`original-reference/preview/` 只放**上游原版对应页的缩小PNG**(看得到差异即可),不拷上游的
大SVG / 大原图(避免vendor上游 + 膨胀innersource)。原版完整配方见上游
`~/ppt-master/examples/<id>/`(clone上游后本地可得),各例 `original-reference/README.md` 会指明。

## 合规

黄档(可发布，非卡点):驱动LLM已是Galileo;**氛围图生成经Galileo gateway合规通道**
(用你自己的Galileo key,非跨境硬阻塞);schematic/公式纯本地SVG;论文原图不嵌(版权)。
详见 [`../docs/roche-adaptation.md`](../docs/roche-adaptation.md) 与上游SECURITY.md的out-of-scope说明。

三个"涉外/调外部服务"点经 `compliance-self-check` 四维定级，**均为黄(可用，非红)**:

| 涉外点 | 总标 | 关键维度 | 处置 |
|---|---|---|---|
| Galileo生图(gpt-image) | 黄 | D3跨境低敏(Galileo官方网关) | **默认可用**,prompt别含敏感内容 |
| LaTeX公式渲染 | 黄 | D3 codecogs出境低敏 | 我们用**本地matplotlib**(D3提到绿);复杂公式需完整LaTeX时codecogs仍合法 |
| edge-tts旁白 | 黄 | D1非官方端点 + D3讲稿出境 | 非敏感讲稿可用；敏感讲稿不外发 |

口径：黄 = 自用/内部可用 + 标注，**不是"不能用"**。别因"出域"就整个跳过一个有用功能；
唯一红线是别喂PII/HCP/患者/临床(那会打到红，走CCCA `cbdt.china@roche.com`)、别做
build-cli token挪用。工程信号非合规裁决，体系待RDT InfoSec背书。

## 加下一个exemplar

1. `cp -r attention-transformer <newname>`,清空 `roche/` 与 `original-reference/`。
2. 复用 `design_spec.md` 的骨架：**§画布 / 字体系统 / 版式 / 管线原样保留**,只改
   §配色强调分布、§图像策略(图重度)、§页清单。
3. 走 `_pipeline` 管线产6页，填 `roche/`;渲染上游对应页填 `original-reference/`。
4. 回填本表的状态行。
