# GALLIUM: 文献检索示例（血液 / 淋巴瘤）

本文件用**血液领域**的一个检索会话演示 literature-research 的五步流程。
研究选自本仓知识包（`knowledge-packs/hematology/products/obinutuzumab/product.md` 的核心循证），
PM 可照此流程套用到自己关注的任何研究。

> ⚠️ 本示例中的 PMID / 数值为**流程演示占位**，实际使用时须现场检索、逐字核对，
> 疗效数字以最新已发表原文/说明书为准（见 blog-writer / slide-ocr-verify 的数据核对铁律）。

## Step 1: Seed（定位主研究）

- 优先查项目内引用：`grep -ri "GALLIUM" knowledge-packs/ outputs/`
- 已知研究名、未知 PMID → PubMed 检索：`https://pubmed.ncbi.nlm.nih.gov/?term=GALLIUM+obinutuzumab+follicular`
- 提取：PMID、DOI、NCT ID、设计（一线 FL，G-chemo vs R-chemo）、样本量、主要终点（PFS）、申办方、作者组

## Step 2: Read（读全文，不止摘要）

- PMC 全文（若开放）→ 否则走 DOI
- 提取：随机化方法、干预/对照细节、**所有终点含 CI**、作者对局限性的讨论
- 数据提取清单：设计 / 人群(N、入排) / 干预 / 对照 / 主要终点(效应量、CI、p) / 亚组 / 资助与 COI

## Step 3: Expand（画引文网络）

- Google Scholar：`"GALLIUM" follicular lymphoma`，日期过滤 `as_ylo=<seed_year>`
- 捕获：总被引数、每篇相关论文的标题/作者/期刊年份/被引数/一句话结论
- 额外找：设计/方案论文、亚组与二次分析、同期社论、纳入本研究的系统综述、同团队后续研究

## Step 4: Classify（整理文献地图）

| # | 类别 | 论文 | 关键发现 |
|---|------|------|----------|
| 1 | Seed | GALLIUM 主结果 | 一线 FL：G-chemo 较 R-chemo 改善 PFS [数值待核实] |
| 2 | Sub-study | GALLIUM 亚组分析 | 不同化疗骨架下的 PFS 一致性 [待核实] |
| 3 | Sub-study | GALLIUM MRD 分析 | 分子学缓解与 PFS 的关联 [待核实] |
| 4 | Editorial | 同期社论 | 一线抗 CD20 升级的临床意义与代价权衡 |
| 5 | Related | CLL11 | 另一适应症(CLL)的抗 CD20 升级循证 [来源：product.md] |
| 6 | Review | 抗 CD20 一线治疗综述 | 糖基化改造机制在 FL/CLL 的循证定位 |

> 输出格式：`| # | 作者 | 标题 | 期刊年份 | 被引数 | 类别 | 关键发现 |`

## Step 5: Interpret（结合 PM 语境解读）

1. **这项研究说明什么** — 一线 FL 抗 CD20 从利妥昔单抗升级到奥妥珠单抗的循证支撑（PFS 获益）
2. **亚组/二次分析揭示了什么** — 不同化疗骨架、MRD 等维度的一致性与机制线索
3. **领域如何回应** — 社论共识、指南采纳、真实世界数据
4. **后续进展** — franchise 内的后续研究与联合方案探索
5. **对 PM 工作的含义** — 支撑信息屋"核心信息/支持信息"、竞品应对（见 product.md 的 Message House 与 Competitive Landscape）

## 合规提醒（血液 PM）

- 本流程产出若进入**对外/一线物料**，疗效数字须标 `[来源：<研究名>]`，比对 `product.md` 获批适应症，**不得 off-label**。
- 亚组/探索性终点不得当作已获批疗效宣称。
- 一切数值以说明书/已发表原文为准，OCR/检索读数均属"待核实证据"。
