---
name: project-management
description: >
  单个项目的全生命周期管理通用技能：WBS 分解、时间线/甘特、RACI 职责矩阵、
  风险管理、预算管理、里程碑与进度追踪。聚焦"有明确起止、需交付的具体项目"
  （产品上市准备、大型学术会/巡讲、患者项目、跨部门协作项目等）。服务三类人群。
  边界：一场普通区域学术会/科室会的策划执行走 `regional-event`；跨部门常态化
  日常协同（品牌团队例会、行动项追踪）走 `central-regional-align` 的横向协作。
  Use when asked to manage a project, create a project plan, build a WBS/Gantt,
  track milestones, manage risks or budget, or run a project end-to-end.
  Triggers on "项目管理", "project management", "WBS", "甘特", "Gantt",
  "风险管理", "risk register", "时间线", "timeline", "里程碑",
  "milestone", "项目进度", "项目提醒", "预算管理", "进度追踪", "项目启动", "项目复盘".
tier: domain
uses: [email-authoring, meeting-minutes]
freq: 中
---

# 项目管理（Project Management）

用 WBS / RACI / 甘特 / 风险登记 / 预算，把一个**有明确起止、需交付的具体项目**从立项跑到复盘。主文件只做分流，步骤细节按需读 references。

## 何时用 / 人群

**通用方法论**，三类人群的项目型工作都可用。

| 人群 | 是否主用 | 典型项目 |
|---|---|---|
| 中央市场（central-marketing） | ✅ 主用 | 产品上市准备、全国大型学术会/AdBoard、患者项目 |
| 区域市场（pst） | 部分 | 大型区域会、区域上市落地、多城市巡讲 |
| 销售管理（sales-mgmt） | 部分 | 团队级专项（区域启动会、专项攻坚） |

## 与 regional-event 的边界（重要）

| | regional-event | project-management（本技能） |
|---|---|---|
| 对象 | **一场**区域学术会/科室会/卫星会 | **一个**有明确起止的复杂项目 |
| 方法 | 照 checklist 把会办完（执行导向） | WBS/RACI/风险/预算拆解管控（规划导向） |
| 典型 | 一次科室会、一场卫星会 | 上市准备、多城市巡讲、患者项目 |

> **一场普通会** → `regional-event`。**一个大项目**（含多场会、多部门、长周期）→ 本技能。
> 大型活动可由 regional-event **委派**本技能做整体项目管理，活动执行细节仍回 regional-event。

### 适用项目类型

| 项目类型 | 典型场景 | 复杂度 |
|----------|---------|:------:|
| 产品上市准备 | Launch Readiness 跨部门协作 | 高 |
| 大型学术会/巡讲 | 全国/多城市学术会、多城市巡讲、AdBoard | 高 |
| 患者项目 | 患者教育、诊疗规范化、疾病管理项目 | 中 |
| 跨部门协作项目 | 准入/医保准备、指南共识推动 | 中 |
| 上市后专项 | 新适应症推广、生命周期专项 | 中 |

## 项目生命周期

```
Phase 1: 立项（Initiation）
    │  项目目标、范围、stakeholder 识别、初步时间线
    ↓
Phase 2: 规划（Planning）
    │  WBS 分解、RACI 制定、风险评估、预算编制、详细时间线
    ↓
Phase 3: 准备（Preparation）
    │  资源落实、材料准备、合规审批、stakeholder 沟通
    ↓
Phase 4: 执行（Execution）
    │  任务执行、进度追踪、风险监控、问题升级
    ↓
Phase 5: 收尾（Closure）
    │  复盘总结、洞察汇总、文档归档、经验沉淀
```

## 核心功能（细节见 `references/core-functions.md`）

按用户意图分流到六项功能：

| 功能 | 触发说法 |
|------|---------|
| 一、项目启动与规划（WBS/RACI/风险/预算） | "启动项目""新建项目""项目规划" |
| 二、进度提醒与待办 | "今天项目有什么安排""本周待办""项目提醒" |
| 三、进度反馈与更新 | "XXX 已完成""XXX 搞定了""XXX 已提交" |
| 四、风险监控 | "风险检查""项目风险" |
| 五、Stakeholder 沟通（邮件委派 `email-authoring`、纪要委派 `meeting-minutes`） | "起草邮件""通知 XXX""会议纪要" |
| 六、项目收尾与复盘 | "项目复盘""总结""经验教训" |

## 通用模板（`templates/`，复制后填具体项目）

| 模板 | 用途 |
|------|------|
| `project-charter.md` | 项目章程：目标、范围、stakeholder、成功标准 |
| `wbs-template.md` | WBS 分解：Phase → 工作包 → 任务 |
| `raci-template.md` | RACI 职责矩阵 |
| `risk-register-template.md` | 风险登记表 |
| `budget-template.md` | 预算管理 |
| `meeting-checklist-template.md` | 会议准备 Checklist |
| `email-templates.md` | 常用邮件模板（启动/进度/风险预警/邀请确认等） |
| `retrospective-template.md` | 项目复盘 |

## 合规注意

- 涉及推广物料的项目交付走 MLR；讲者/费用不与处方/采购量挂钩（细节见 `references/compliance-and-roles.md`）。
- 项目实例含客户/预算/名单等敏感信息——存 `outputs/` 内部使用，**不外传、不进 git**。
- 项目产出面向外部时，先脱敏并走对应业务技能的合规检查。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 六项核心功能详细步骤 + 项目实例目录结构 | `references/core-functions.md` |
| 项目合规要求 + 三类人群项目职责 | `references/compliance-and-roles.md` |
| 章程/WBS/RACI/风险/预算/会议/邮件/复盘模板 | `templates/`（见上表） |
