---
name: central-regional-align
description: >
  协作对齐（纵向 + 横向）：管好 PM 的两类日常协同。
  纵向——中央市场↔区域市场（PST）的策略下达、反馈上传、闭环跟踪；
  横向——与 Medical/Access/销售/PDMA/财务等跨部门的品牌团队例会、
  RACI 分工、行动项追踪、stakeholder 沟通。核心：对齐到无歧义、行动有闭环。
  Use when the user needs to align central strategy with regional execution,
  run a cross-functional / brand-team meeting, design a RACI, track action items
  across departments, or manage stakeholder communication and alignment.
  Triggers on "中央区域协同", "中央区域对齐", "策略下达", "区域反馈上传", "下达包",
  "对齐会", "闭环跟踪", "跨部门协作", "跨职能协作", "品牌团队会议", "brand team meeting",
  "BT 会议", "行动项追踪", "action item", "RACI", "跨部门对齐", "stakeholder 沟通",
  "cross functional", "central regional align".
tier: domain
uses: [regional-plan, field-insight-synthesis, bilingual-report, meeting-minutes, email-authoring]
freq: 中
---

# 协作对齐（Collaboration & Alignment）

管好 PM 的两类协同：**纵向**（中央↔区域）别让策略失真、洞察石沉大海；**横向**（跨部门）别让协作停在"开了会没结论、定了事没人追"。核心一句话：**对齐到无歧义、行动有闭环**。

## 两个维度

```
纵向（Vertical）：中央市场 ⇅ 区域市场（PST）
    下达：策略/物料/目标 → 结构化下达包 → 区域无歧义接住
    上传：执行反馈/一线洞察 → 结构化回流 → 中央消化反哺 → 闭环回应

横向（Horizontal）：PM ⇄ Medical / Access / 销售 / PDMA / 财务 …
    协同：品牌团队例会、RACI 分工、行动项追踪、stakeholder 沟通
    闭环：每个行动项有责任人/时间，会后 24h 纪要，下次会先追未完成项
```

## 何时用 / 人群

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 中央市场（central-marketing） | ✅ 主用 | 纵向下达/收反馈；横向牵头品牌团队跨部门协同 |
| 区域市场（pst） | ✅ 主用 | 纵向接下达/上传反馈；横向与区域跨职能协作 |
| 销售管理（sales-mgmt） | 部分 | 纵向执行侧参与；横向与市场/医学对接 |

## 与相邻技能的边界

| | 本技能 | 相邻技能 |
|---|---|---|
| 纵向中央-区域 | 策略下达/反馈闭环的**通道管理** | 区域接住后做落地计划 → `regional-plan` |
| 横向跨部门 | 常态化协同（例会/RACI/行动项） | 有明确起止的**大项目**跨部门管控 → `project-management` |
| 会议 | 定协作节奏、议程、行动项闭环 | 把录音转规范纪要 → `meeting-minutes` |

> **一次跨部门协作会** → 本技能。**一个跨部门大项目**（WBS/风险/预算）→ `project-management`。

## 工作流骨架

**纵向（中央↔区域）**

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 策略下达包 | "把这份策略下达区域""做下达包" | 提炼中央要点 → 结构化下达包 → 标注区域动作项 |
| 2. 对齐会组织 | "开个对齐会""组织中央区域对齐" | 议程 + 材料 + 决议/action + 责任人时间 |
| 3. 反馈回流与闭环 | "汇总区域反馈上传""闭环跟踪" | 归集区域反馈 → 结构化上传 → 跟踪中央回应闭环 |

**横向（跨部门）**

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 4. 品牌团队/跨部门例会 | "准备品牌团队会议""跨部门对齐会" | 议程 + 各方预读 + 每议题明确产出（讨论/决策/同步） |
| 5. 行动项追踪 | "行动项追踪""上次会定的事追一下" | 归集 action → 责任人/截止/状态 → 逾期预警 → 闭环 |
| 6. RACI 分工 | "定个 RACI""这事谁负责" | 列任务 × 角色 → 每任务唯一 A → 消除职责真空/重叠 |
| 7. Stakeholder 沟通 | "通知相关部门""跨部门邮件" | 按 stakeholder 地图定对象 → 委派 `email-authoring` |

纵向方法论（下达失真的坑、闭环机制、对齐节奏）见 `references/methods.md`；
横向方法论（协作地图、例会效率、行动项/RACI、升级机制）见 `references/cross-functional.md`；
逐场景流程见 `references/workflows.md`；模板见 `templates/`。

## 合规注意

- 下达包/跨部门共享的物料须已过 MLR 或标 `⚠️ MLR 送审前草稿`，未审材料不得对外。
- 区域反馈、跨部门共享的客户/销售信息属敏感——聚焦趋势、脱敏个案，不外传 PII、不进 git。
- 目标/资源分配与执行跟踪不与处方/采购量挂钩。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 7 个场景逐步流程 | `references/workflows.md` |
| 纵向：下达失真、闭环机制、对齐节奏 | `references/methods.md` |
| 横向：协作地图、例会效率、行动项/RACI、升级机制 | `references/cross-functional.md` |
| 下达包/对齐会议程/反馈回流/RACI/行动项/stakeholder 模板 | `templates/` |
