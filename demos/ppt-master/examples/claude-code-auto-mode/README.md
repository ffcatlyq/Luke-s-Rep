# claude-code-auto-mode — 暗色科技格exemplar(B类：罗氏相关topic深度本地化)

上游 `general_dark_tech_claude_code_auto_mode` 的Roche版。**不是换色，是内容本地化**——保留暗色科技
骨架，逐页把"通用Claude Code Auto Mode讲解"重写成**罗氏AI社区的真实实战**:就在做这套slides
的会话里，一次approve被auto-mode拦了、还踩了US→EU搬家丢配置的坑，整份deck拿这段亲历讲。

> 这是21例适配框架里 **B类(罗氏相关topic)** 的样板。适配三层：L1身份换肤 + L2版式保留 +
> **L3内容本地化(真适配)**。对照A类(纯风格模板)/ C类(无关topic,降级或跳过)。框架见
> [`../README.md`](../README.md)、[`ADAPTATION.md`](../ADAPTATION.md)。

## 原版vs Roche对照

| 维度 | 上游原版 | 本Roche版 |
|---|---|---|
| 题材 | 通用Claude Code Auto Mode(Anthropic工程博客) | 罗氏社区实战：PR #307被拦复盘 + 搬家坑 |
| 主色 | amber `#D4A574`(Anthropic resonance)+ sky blue | 暗底Roche Blue `#1482fa` 蓝阶(单主色) |
| 04架构页 | "Two Layers of Defense"(分类器防御层) | **"两道闸":auto-mode(本地)≠ GitHub(服务端)** |
| 07/08 | 分类器原理 / 性能指标 | **PR #307 approve被判自审实录** / settings.local.json的一生 |
| 内容来源 | 博客 | **本会话亲历**(自我印证) |

逐页对照见 [`original-reference/README.md`](original-reference/README.md);原版缩小图在 `original-reference/preview/`。

## 页清单(10页，暗底)

封面 · 审批疲劳 · 什么是Auto Mode(三态对比)· **两道闸架构** · 威胁模型(三类真实拦截)·
权限(settings.local.json)· **分类器：一次真实拦截** · 结果(老容器→搬家丢→加回)· 设计决策 · 收尾。

预览见 [`roche/preview/`](roche/preview/);配方见 [`design_spec.md`](design_spec.md)。

## 关键决策

- **B类适配 = 保骨架 + 换内容**:暗色科技风的辉光/网格/卡片/终端卡(L2)保留；amber→Roche Blue(L1);
  每页含义换成罗氏能直接用的实战(L3)。04页最典型：占同一个"架构"槽位，讲完全不同的"两道闸"。
- **内容SSOT = 本会话亲历**:04/07/08的内容是我们做slides时真实踩出来的(两道闸、#307被拦、搬家丢配置),
  不是编的——deck自我印证。
- **暗色Roche调色(可复用)**:bg `#0D0D0D` + 主蓝 `#1482fa` + 蓝阶 `#5FAAFC/#95C7FD/#0B41CD`;
  语义绿 `#34D399`(放行)/ 橙 `#F97316`(拦)/ 红 `#F85149`(硬拦);文字 `#E6EDF3/#8B949E/#6E7681`;白logo。
- **中文deck的cairosvg坑**(英文deck没踩到，详见 [`../_pipeline/README.md`](../_pipeline/README.md)):
  CJK行 `'Noto Sans CJK SC'` 首位、CJK别混进mono组、`✗`/`⏸` 缺字形(用 `×`/`‖`)、
  **居中文本零tspan**(即便只改色也算错宽 → 溢出重叠)。

## 可编辑性验证(实测)

pptx 10页，native 10/10成功。slide XML:**262个 `<a:t>` 文本run + 379个 `<a:custGeom>`/`<a:prstGeom>`
矢量形状 + 10页 `<p:timing>` 动画 + 10 notesSlides**。**不嵌字体**(实测PowerPoint拒装程序化嵌入，见 [`../ADAPTATION.md`](../ADAPTATION.md) 字体嵌入节)——罗氏机器有Roche Sans优雅回退。
成品：[`roche/pptx/claude-code-auto-mode-roche.pptx`](roche/pptx/claude-code-auto-mode-roche.pptx)(~112KB)。

## 合规

低敏：讲的是自己的工作流经验，无PII;暗色氛围/图标纯本地SVG,无生图。详见 [`../ADAPTATION.md`](../ADAPTATION.md)。
