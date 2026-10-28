---
name: customer-segmentation
description: >
  客户分层与覆盖：基于医院分级（C30/T70/T300）与 HCP 画像，建立客户分层、
  评估覆盖 gap、设计 A/B/C 分级覆盖策略。服务区域市场与销售管理人群的客户运营。
  Use when the user needs to segment customers/hospitals, build a coverage plan,
  find coverage gaps, or design a tiered engagement strategy.
  Triggers on "客户分层", "分级", "覆盖 gap", "覆盖率", "客户画像", "HCP 画像",
  "segmentation", "coverage", "分级策略", "客户覆盖", "医院分级".
tier: domain
uses: [data-analysis, territory-management]
freq: 中
---

# 客户分层与覆盖（Customer Segmentation & Coverage）

把客户/医院分层，找出覆盖缺口，设计"谁该被多覆盖、怎么覆盖"的分级策略。

## 何时用 / 人群

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 区域市场（pst） | ✅ 主用 | 区域客户分层、覆盖 gap、触点规划 |
| 销售管理（sales-mgmt） | ✅ 主用 | 辖区客户分级、团队覆盖资源分配 |
| 中央市场（central-marketing） | 部分 | 全国客户分层框架、KOL 分层输入 |

## 两套分层维度

客户分层是**医院维度**与**人（HCP）维度**的叠加（数据见 `knowledge-packs/hematology/customers/segmentation.md`）：

- **医院分级**：C30（核心）/ T70（重点）/ T300（全部目标）——决定医院覆盖优先级
- **HCP 画像**：科室/职级/学术影响力/处方潜力/当前态度——决定人的互动深度
- **叠加**：高分级医院 × 高影响力 HCP = 最高优先级客户

> 与 KOL/讲者分层（如 I/N/R/L）是互补维度：客户分层看覆盖，KOL 分层看学术合作，可交叉。

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 建立分层 | "给客户分层""建分级模型" | 拉数据 → 医院分级 × HCP 画像 → 分层清单 |
| 2. 覆盖 gap | "看覆盖缺口""哪些没覆盖到" | 目标分层 vs 实际覆盖 → 漏斗 → gap 清单 |
| 3. 分级策略 | "分级覆盖策略""资源怎么分" | 按分层设互动深度/频次/渠道 → A/B/C 策略 |

方法论（分层矩阵、覆盖漏斗、A/B/C 策略设计）见 `references/methods.md`；
产出模板见 `templates/`。数据透视交给 `data-analysis`，辖区落地交给 `territory-management`。

## 合规注意

- ⚠️ **数据分级（敏感）**：客户名单、HCP 画像、处方潜力属敏感级——不外传、不写入可外发产出、不进 git。
- HCP 画像基于**学术与专业维度**，处方潜力用于覆盖资源规划，**不得**转化为与个人处方量挂钩的不当激励。
- 客户 PII 不入非授权系统。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景逐步流程 | `references/workflows.md` |
| 分层矩阵、覆盖漏斗、A/B/C 策略、HCP 画像维度 | `references/methods.md` |
| 分层清单 / 覆盖 gap / 分级策略模板 | `templates/` |
