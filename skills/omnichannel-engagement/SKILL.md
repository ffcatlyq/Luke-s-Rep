---
name: omnichannel-engagement
description: >
  全渠道客户互动规划：把面对面与数字渠道整合成客户旅程，规划触点、
  匹配内容与渠道、设计跨渠道节奏。服务区域市场与中央市场的客户互动设计。
  Use when the user needs to plan a customer journey, design multi-channel
  touchpoints, match content to channels, or coordinate face-to-face + digital.
  Triggers on "全渠道", "omnichannel", "客户旅程", "customer journey", "触点",
  "渠道规划", "数字渠道", "内容渠道匹配", "多渠道", "触点规划".
tier: domain
uses: [customer-segmentation, promo-material-mlr]
freq: 中
---

# 全渠道客户互动规划（Omnichannel Engagement）

把散落的面对面拜访和数字触点，编排成一条连贯的客户旅程。

## 何时用 / 人群

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 区域市场（pst） | ✅ 主用 | 区域客户旅程、面对面+数字触点编排 |
| 中央市场（central-marketing） | ✅ 主用 | 全国渠道内容策略、旅程框架设计 |
| 销售管理（sales-mgmt） | 部分 | 团队渠道执行标准 |

## 核心概念：旅程 × 触点 × 渠道

- **客户旅程**：客户从认知 → 兴趣 → 尝试 → 采用 → 忠诚的阶段。
- **触点**：每个阶段与客户的接触点（拜访、会议、邮件、平台内容、直播）。
- **渠道**：面对面（拜访/科室会/大会）+ 数字（邮件/平台/直播/推送）。
- **原则**：不同阶段、不同客户分层，用不同渠道组合；跨渠道信息一致、节奏协同。

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 客户旅程设计 | "设计客户旅程""旅程地图" | 定阶段 → 每阶段目标 → 触点与渠道 |
| 2. 触点-内容-渠道匹配 | "内容配什么渠道""触点规划" | 内容按阶段/分层匹配到合适渠道 |
| 3. 跨渠道节奏编排 | "多渠道节奏""互动排期" | 按周期编排面对面+数字触点，避免冲突/遗漏 |

方法论（旅程阶段、渠道特性、内容-渠道矩阵）见 `references/methods.md`；模板见 `templates/`。
客户分层输入接 `customer-segmentation`；数字内容/物料走 `promo-material-mlr` 做合规。

## 合规注意

- ⚠️ **所有对外/对客户内容**（邮件、平台、直播材料）均须走 `promo-material-mlr` 的 MLR 送审与 off-label 检查——本技能规划渠道与节奏，**内容合规不在此豁免**。
- 数字互动须符合客户同意（consent）与数据隐私要求；客户 PII 不入非授权系统。
- 互动记录合规登记，不与产品推广不当挂钩。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景逐步流程 | `references/workflows.md` |
| 旅程阶段、渠道特性、内容-渠道矩阵 | `references/methods.md` |
| 旅程地图 / 触点计划 / 节奏排期模板 | `templates/` |
