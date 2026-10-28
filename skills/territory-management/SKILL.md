---
name: territory-management
description: >
  销售管理层的辖区与资源管理：辖区划分、目标分解、资源/覆盖分配、拜访计划。
  基于医院分级（C30/T70/T300）× 5 大销售区，把区域目标落到辖区与团队。
  Use when a sales manager needs to divide territories, cascade targets,
  allocate resources/coverage, or build a call plan across a region/team.
  Triggers on "辖区", "territory", "目标分解", "资源分配", "覆盖分配",
  "拜访计划", "call plan", "辖区划分", "区域目标", "覆盖规划".
tier: domain
uses: [data-analysis]
freq: 中
---

# 辖区 / 资源管理（Territory Management）

把区域目标，拆成"每个辖区/成员管哪些医院、投多少资源、怎么覆盖"。

## 何时用 / 人群

**主要人群：销售管理层**（LEL/REL/RCL）。区域市场 PSL 做区域覆盖规划时也可用。

| 人群 | 视角 |
|---|---|
| 销售管理（sales-mgmt） | ✅ 主用——辖区划分、目标分解、团队资源分配 |
| 区域市场（pst） | 部分——PSL 做区域客户覆盖规划 |
| 中央市场（central-marketing） | 否 |

## 核心维度：分级 × 大区

辖区管理的基础是医院分级与大区（定义见 `knowledge-packs/hematology/customers/segmentation.md`）：

- **医院分级**：C30（核心）/ T70（重点）/ T300（全部目标）——决定覆盖优先级与频次
- **5 大销售区**：东 / 南 / 西 / 北 / 中
- **覆盖梯度**：C30 优先（高频深度）→ T70 → T300 长尾

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 辖区划分 | "划分辖区"、"重新分配医院" | 按分级+地理+工作量均衡，把医院分给辖区/成员 |
| 2. 目标分解 | "把大区目标拆到辖区"、"目标下沉" | 区域目标 → 按辖区潜力/基数分解到人 |
| 3. 资源/覆盖分配 | "资源怎么投"、"拜访频次" | 按分级设覆盖标准，分配拜访/活动/费用资源 |
| 4. 拜访计划 | "做 call plan"、"拜访排期" | 按覆盖标准生成周期拜访计划 |

方法论（划分原则、覆盖频次标准、目标分解方法）见 `references/methods.md`；
产出模板见 `templates/`。数据透视（潜力测算/工作量）交给 `data-analysis`。

## 合规注意

- 辖区数据、医院名单、成员目标属**敏感级**——不外传、不写入可外发产出、不进 git。
- 目标分解与资源分配须留痕，规则透明。
- 覆盖与资源分配**不得**转化为与处方/采购量挂钩的不当激励。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 4 个场景逐步流程 | `references/workflows.md` |
| 划分原则、按分级的覆盖频次标准、目标分解方法 | `references/methods.md` |
| 辖区分配表 / 覆盖计划 / call plan 模板 | `templates/` |
