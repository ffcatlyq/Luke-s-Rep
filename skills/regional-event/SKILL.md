---
name: regional-event
description: >
  区域学术活动执行：区域学术会/科室会/卫星会的策划、执行清单、合规留痕。
  从立项到会后跟进的全流程，强合规（讲者、内容、费用、留痕）。服务区域市场与销售管理。
  Use when the user needs to plan a regional academic event, build an execution
  checklist, manage speakers/logistics, or ensure compliance documentation.
  Triggers on "区域活动", "学术会", "科室会", "卫星会", "会议策划", "活动执行",
  "regional event", "活动清单", "会议合规", "讲者安排", "会后跟进".
tier: domain
uses: [speaker-management, promo-material-mlr, project-management]
freq: 中
---

# 区域学术活动执行（Regional Event）

把一场区域学术会，从立项到会后跟进，管到每个执行细节与合规留痕。

## 何时用 / 人群

| 人群 | 是否主用 | 视角 |
|---|---|---|
| 区域市场（pst） | ✅ 主用 | 区域学术会/科室会策划与执行 |
| 销售管理（sales-mgmt） | 部分 | 团队协办、辖区活动 |
| 中央市场（central-marketing） | 部分 | 大型区域会与中央活动衔接 |

## 强合规提示（先读）

区域活动是**高合规敏感**场景。全程守：
- **讲者**：遴选基于学术资质、劳务符合 FMV、场次留痕、利益冲突申报（走 `speaker-management`）。
- **内容**：讲者材料循证、不 off-label、经 MLR（走 `promo-material-mlr`）。
- **费用**：合规范围、留痕、不与处方/采购挂钩。
- **留痕**：立项、审批、签到、费用、材料全程留档备查。

## 工作流骨架

| 场景 | 触发说法 | 一句话 |
|---|---|---|
| 1. 活动策划 | "策划一场区域会""立项" | 目标 → 形式/规模 → 讲者 → 内容 → 预算 → 合规预检 |
| 2. 执行清单 | "做执行清单""会务安排" | 会前/会中/会后全流程 checklist + 责任人 + 留痕点 |
| 3. 会后跟进 | "会后跟进""效果评估" | 签到/费用/材料归档 + 效果评估 + 洞察回流 |

方法论（活动类型、合规留痕清单、效果评估）见 `references/methods.md`；模板见 `templates/`。
讲者走 `speaker-management`，内容走 `promo-material-mlr`，会后洞察走 `field-insight-synthesis`。

> **一场会 vs 一个大项目**：本技能管**单场**区域会的策划-执行-会后。若是**大型/长周期/多场次/多部门**的活动（如多城市巡讲、上市系列会），委派 `project-management` 做整体项目管理（WBS/RACI/风险/预算），单场执行细节仍回本技能。

## 合规注意（贯穿）

- ⚠️ 讲者遴选/劳务、内容、费用**全程合规**，任何环节不与处方/采购量挂钩。
- 所有活动产出顶部标注合规状态；讲者材料标 `⚠️ MLR 送审前草稿`。
- 参会/费用/签到数据含 PII，属敏感级，不外传、不进 git。

## 参考文件（progressive disclosure）

| 需要 | 读这个 |
|---|---|
| 3 个场景逐步流程 | `references/workflows.md` |
| 活动类型、合规留痕清单、效果评估 | `references/methods.md` |
| 策划案 / 执行清单 / 会后报告模板 | `templates/` |
