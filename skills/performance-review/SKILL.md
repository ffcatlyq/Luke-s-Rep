---
name: performance-review
description: >
  销售管理层的业绩复盘与达成归因：目标 vs 实际 → 差距归因 → 行动建议 →
  复盘会材料。把销售/市场数据变成可决策的复盘输出，服务圈长 LEL 及以上。
  Use when a sales manager needs to review team/territory performance, analyze
  gaps between target and actual, attribute causes, or prepare a review deck.
  Triggers on "业绩复盘", "达成", "复盘", "归因", "gap 分析", "目标 vs 实际",
  "performance review", "达成率", "月度回顾", "季度复盘".
tier: domain
uses: [data-analysis, bilingual-report]
freq: 中
---

# 业绩复盘 / 达成归因（Performance Review）

把一堆销售数字，变成"为什么达成/没达成、下一步做什么"的结构化复盘。

## 何时用 / 人群

**主要人群：销售管理层**（LEL/REL/RCL）。也服务区域市场 PSL 的区域业绩回顾。

| 人群 | 视角 |
|---|---|
| 销售管理（sales-mgmt） | ✅ 主用——团队/辖区达成、成员差距 |
| 区域市场（pst） | 部分——PSL 看区域市场活动产出 |
| 中央市场（central-marketing） | 部分——PM 看产品层面市场表现（走竞品/汇报技能更合适） |

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 达成分析 | "看下这个月达成"、"目标 vs 实际" | 数据 → 达成率 → 按维度拆解（大区/医院分级/产品/成员） |
| 2. 差距归因 | "为什么没达成"、"gap 归因" | 差距 → 归因（量/价/结构/覆盖/外部）→ 定位可改进项 |
| 3. 复盘会材料 | "做复盘会材料"、"月度回顾包" | 达成 + 归因 + 行动 → 结构化复盘包（可双语） |

数据处理（清洗/透视/图表）交给 `data-analysis` 工具技能；本技能负责**业务解读与归因框架**。
需要一页式 KPI/图表看板（复盘会开场概览）时，交 `dashboard-builder` 出自包含 HTML 仪表盘。
归因方法论见 `references/attribution-framework.md`；复盘包结构见 `templates/review-deck.md`。

## 数据维度

复盘常按这些维度拆解（分级/大区定义见 `knowledge-packs/hematology/customers/segmentation.md`）：
- **销售大区**：东/南/西/北/中
- **医院分级**：C30 / T70 / T300
- **产品**：6 个血液产品
- **团队成员 / 辖区**

## 合规注意

- ⚠️ **数据分级（敏感）**：销售数据、医院名单、成员业绩属敏感级——不外传、不写入可外发产出、不进 git。复盘材料默认内部使用。
- 归因与行动聚焦**业务与能力**，成员评价不以单一销量数字定论，结合过程指标。
- 复盘结论不得转化为与处方/采购量挂钩的激励承诺。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景的逐步流程 | `references/workflows.md` |
| 归因框架（量价结构分解、覆盖漏斗、5 类归因） | `references/attribution-framework.md` |
| 复盘会材料模板 | `templates/review-deck.md` |
