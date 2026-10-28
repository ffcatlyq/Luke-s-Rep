---
name: business-review
description: >
  业务例会/QBR：月度/季度业务回顾包，整合销售达成、市场活动、客户覆盖、竞品动态
  于一份结构化例会材料，服务销售管理层（LEL 及以上）主持业务例会。
  Use when a sales manager needs to prepare a monthly/quarterly business review,
  build an MBR/QBR deck, or integrate sales+market+customer into one review pack.
  Triggers on "业务例会", "月度回顾", "季度回顾", "QBR", "MBR", "业务回顾",
  "business review", "例会材料", "季度复盘会", "月会包", "经营分析会".
tier: domain
uses: [performance-review, field-insight-synthesis, bilingual-report]
freq: 中
---

# 业务例会 / QBR（Business Review）

把一个周期里散落在各处的销售、市场、客户、竞品信息，整合成一份"讲得清、拍得了板"的业务例会材料。

## 何时用 / 人群

**主要人群：销售管理层**（LEL/REL/RCL）主持月度/季度业务例会。

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 销售管理（sales-mgmt） | ✅ 主用 | 主持业务例会，整合团队/辖区全景 |
| 区域市场（pst） | 部分 | 提供区域市场活动产出、纳入例会 |
| 中央市场（central-marketing） | 部分 | 提供产品市场表现输入 |

## 与 performance-review 的分工

| | performance-review | business-review（本技能） |
|---|---|---|
| 焦点 | 销售达成的**深度归因** | 一个周期的**整合全景例会** |
| 范围 | 目标 vs 实际、gap 归因 | 销售 + 市场 + 客户 + 竞品 + 下步 |
| 产出 | 归因分析、复盘 deck | 例会包（MBR/QBR）|

> 例会中的达成归因部分**接 `performance-review`**；本技能负责把各板块整合成一份例会材料。

## 例会内容板块

| 板块 | 内容 | 输入来源 |
|---|---|---|
| 业绩达成 | 目标 vs 实际、达成率、趋势 | performance-review |
| 市场活动 | 本周期活动执行与产出 | regional-event / regional-plan |
| 客户覆盖 | 分层覆盖、KOL/讲者运营 | customer-segmentation / speaker-management |
| 市场洞察 | 一线反馈、竞品动态 | field-insight-synthesis / competitive-brief |
| 下周期计划 | 重点、目标、资源、action | — |

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 例会框架搭建 | "搭个季度例会框架""QBR 大纲" | 按板块搭结构 → 明确每块负责人与数据源 |
| 2. 例会包整合 | "整合业务例会材料""做月会包" | 汇各板块输入 → 提炼要点 → 整合成 deck（可双语）|
| 3. 例会决议跟踪 | "例会 action 跟踪""上次例会决议" | 决议登记 → 责任人/时间 → 跨周期跟踪闭环 |

方法论（例会节奏、整合框架、常见坑）见 `references/methods.md`；模板见 `templates/`。
达成归因接 `performance-review`；洞察接 `field-insight-synthesis`；对上双语呈现接 `bilingual-report`。
需要"一眼看全"的 KPI/图表看板（开场概览、发给管理层）时，交 `dashboard-builder` 出自包含 HTML 仪表盘。

## 合规注意

- ⚠️ **数据分级（敏感）**：销售数据、医院名单、客户/成员信息属敏感级——不外传、不写入可外发产出、不进 git。例会材料默认内部使用。
- KOL/讲者运营板块不与处方/采购量挂钩；讲者数据走 speaker-management 合规。
- 涉及产品声明/物料的内容须循证、经 MLR。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景逐步流程 | `references/workflows.md` |
| 例会节奏、整合框架、常见坑 | `references/methods.md` |
| 例会包 / 议程 / action 跟踪模板 | `templates/` |
