---
name: regional-plan
description: >
  区域计划落地：把中央品牌策略/cycle plan 本地化为区域执行计划——结合区域格局、
  客户覆盖、资源与时间线。服务区域市场（PST）把中央策略落到本区域。
  Use when a regional user needs to localize a central brand/cycle plan into a
  regional execution plan, adapt tactics to local context, or build a regional roadmap.
  Triggers on "区域计划", "区域执行计划", "本地化", "落地计划", "regional plan",
  "把中央策略落地", "区域 roadmap", "区域战术", "cycle plan 本地化".
tier: domain
uses: [customer-segmentation, territory-management, central-regional-align]
freq: 中
---

# 区域计划落地（Regional Plan）

把中央的品牌策略，翻译成"我这个区域具体怎么打"的执行计划。

## 何时用 / 人群

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 区域市场（pst） | ✅ 主用 | PSM/PSL 把中央策略本地化为区域计划 |
| 销售管理（sales-mgmt） | 部分 | 与区域计划对齐团队执行 |
| 中央市场（central-marketing） | 部分 | 了解区域如何落地、收集反馈 |

## 核心：本地化而非照搬

中央策略给"打什么、为什么"；区域计划补"在本区域怎么打"——结合：
- **区域格局**（`knowledge-packs/hematology/regions/china-market.md`）：本区医院分布、准入、竞争
- **客户覆盖**（接 `customer-segmentation`）：本区客户分层与 gap
- **资源与团队**（接 `territory-management`）：辖区、产能、预算

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 中央策略解读 | "解读这份 brand plan""中央要什么" | 提取中央目标/策略/关键战术，标注需本地化的点 |
| 2. 区域计划制定 | "做区域执行计划""本地化落地" | 目标下沉 + 区域格局 + 客户覆盖 + 资源 + 时间线 |
| 3. 计划-资源校验 | "计划能落吗""资源够不够" | 计划 vs 团队产能/预算，识别缺口与取舍 |

方法论（本地化框架、区域计划结构）见 `references/methods.md`；模板见 `templates/`。
区域反馈上传中央走 `central-regional-align`。

## 合规注意

- 区域计划中的客户/医院/销售数据属敏感级——不外传、不写入可外发产出、不进 git。
- 计划中的推广内容/活动须走对应合规（物料走 MLR、活动走 regional-event 的合规留痕）。
- 资源分配留痕，不与处方/采购量挂钩。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景逐步流程 | `references/workflows.md` |
| 本地化框架、区域计划结构 | `references/methods.md` |
| 区域执行计划模板 | `templates/regional-plan.md` |
