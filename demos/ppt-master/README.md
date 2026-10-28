# ppt-master

合规分级：黄(可自用 + 社区分享，分享前看下方残留风险)

用AI从任意文档生成**本地原生可编辑的 .pptx**——真DrawingML形状、可改数据的图表/表格、speaker notes可转音频旁白。上游 [hugohe3/ppt-master](https://github.com/hugohe3/ppt-master)(MIT,开源),本demo是它的 **Roche接入模板**(锁Galileo + 从hub的Roche Blue SSOT派生品牌spec),不vendor上游代码。

## slide三条路径里它站哪

hub里slide authoring有三条路径，各自适用场景不同：

| 路径 | 产物 | 编辑方 | 适用 |
|---|---|---|---|
| [slidev-authoring](../../.claude/skills/slidev-authoring/) | HTML/web(markdown源) | 改markdown | 结构重复型页、需在线浏览/gh-pages发布、技术演讲 |
| [gslide-authoring](../gslide-authoring/) | Google Slides(云端) | 在Google Slides里改 | 需多人云端协作、Workspace生态内 |
| **ppt-master(本demo)** | **本地 .pptx** | **在PowerPoint/Keynote/WPS里改** | **业务方要真PowerPoint文件：离线继续改、进邮件附件、不依赖Google账号** |

三者共用同一套Roche Blue品牌SSOT(`assets/roche-brand/tokens` + `slidev/themes/roche-blue`),风格一致。ppt-master补的是前两条都填不了的「本地可编辑 .pptx」缺口。

它明确**不是**模板填充式或图片版——每个元素在PowerPoint里都能点开改(上游README的Product Positioning有对比)。

## 形态

ppt-master本身就是一个跑在Claude Code / Cursor里的 **workflow skill**:你在IDE chat里说「把这个PDF做成deck」,它按流程在本机产出 .pptx。推理用的是**你CC已经配好的模型**(hub环境 = Galileo),数据除了模型通信全程留本机。

## 风格×品牌解耦(白送的好看)

ppt-master内置19种视觉风格(`references/visual-styles/`:swiss-minimal / editorial / data-journalism / blueprint等),且**风格不锁颜色**——风格只管「怎么好看」(网格 / 留白 / 字体性格),配色另由品牌spec给。所以**任意风格×Roche Blue可自由组合**,不用重造版式：

```
你:用swiss-minimal风格 + roche-blue-brand-spec的品牌,把X做成deck
```

合规注意：gallery里那些漂亮示例靠AI生图(默认关)。**图轻 / 纯排版的风格零AI图就出好效果**——推荐 `swiss-minimal`、`data-journalism`、`blueprint`、`soft-rounded`;图重的(photo-editorial / memphis)要换本地素材。2026-07已用内部deck实测复刻两页(swiss-minimal数据密集风、零AI图),原生可编辑、效果达标；另复刻FNN/CNN/RNN三页AI模型node-link架构图(全原生custGeom形状、零AI图),证明它不止图表、复杂结构图也handle得住。

## 当前状态

接入模板 / 评估阶段。核心增量是Roche品牌适配，不改上游逻辑。跑通评估后再考虑是否提升为hub skill(同gslide节奏，先demo后skill)。

## 快速上手

1. 装上游(不vendor):推荐 `/plugin install`(CC自动加载skill),或git clone pin tag/SHA。见 [docs/roche-adaptation.md](docs/roche-adaptation.md) §安装
2. 生成Roche Blue品牌spec(从hub SSOT token派生):
   ```bash
   python3 scripts/build_roche_brand_spec.py > ~/ppt-master/projects/<你的项目>/roche-blue-brand-spec.md
   ```
3. 在Claude Code里让ppt-master按这份spec生成deck:见 [docs/roche-adaptation.md](docs/roche-adaptation.md) §两条模板路径

## 目录

| 路径 | 内容 |
|---|---|
| [README.md](README.md) | 本文件，入口 |
| [scripts/build_roche_brand_spec.py](scripts/build_roche_brand_spec.py) | 从Roche Blue SSOT token派生品牌spec(纯stdlib) |
| [docs/roche-adaptation.md](docs/roche-adaptation.md) | Roche适配：双轨安装、锁Galileo、两条模板路径、残留风险 |

## 合规残留风险(黄标的原因)

- **模型走Galileo,别用上游README里的第三方API relay**(PackyCode/APIKEY.FUN等是sponsor广告，把Roche内容发非授权中转 = 数据出境红线)。用CC已配的模型即可，那些链接无视。
- **AI生图默认关**。上游推荐的 `gpt-image-2` 会把内容发OpenAI(非Galileo通道),做敏感deck不要开。
- **敏感/内部deck自用，生成物别外发**;真放HCP/患者/临床数据需CCCA + 渠道review。
- **Roche字体外发许可**:嵌入Roche Sans的 .pptx发给外部方，需对方自备Roche字体。

完整四维判级见 [docs/topic/compliance-catalog.md](../../docs/topic/compliance-catalog.md) 的ppt-master行。

## 关联

- [slidev-authoring skill](../../.claude/skills/slidev-authoring/) — 第一条路径
- [gslide-authoring](../gslide-authoring/) — 第二条路径，本demo的姊妹对照组
- [assets/roche-brand/](../../assets/roche-brand/) — Roche品牌SSOT(颜色/字体/logo)
- [slidev/themes/roche-blue/](../../slidev/themes/roche-blue/) — 同源Roche Blue slidev主题
