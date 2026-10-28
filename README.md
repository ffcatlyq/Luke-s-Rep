# 罗氏中国 Customer Engagement 部门智能体（Ona CE Agent）

面向罗氏制药中国 Customer Engagement（CE）部门的工作智能体，服务三类人群——**中央市场**（PM）、**区域市场**（PST：PSM/PSL）、**销售管理**（圈长 LEL 及以上）。既是**助理**（帮你把活干了）、**参谋**（帮你想清楚）、也是**赋能工具**（帮你复用与成长）。

你直接在 ONA 界面通过对话使用——本仓库是智能体的**知识库、能力库与产出沉淀**。首次使用时智能体会问你的角色/负责区域/汇报对象，写入 profile 后记住，之后按你的人群视角工作。

> 🚀 **第一次使用？** 先读 **[新人上手指南 ONBOARDING.md](ONBOARDING.md)** —— 从 fork 仓库、创建 Ona 环境，到 5 分钟跑通第一个真实任务。

## 核心设计：通用引擎 + 可插拔知识包

```
通用引擎（一次搭建，所有治疗领域 + 三类人群共用）
├─ AGENTS.md        智能体行为总纲：人群 / 角色 / 合规红线 / 产出规范
├─ profile          人群识别：中央市场 / 区域市场 / 销售管理（.claude/skills/profile.yaml）
├─ skills/          通用技能：技能内按人群分流，取对应视角
└─ compliance/      合规护栏：RDPAC / 反商业贿赂 / MLR 通用规则

可插拔知识包（按治疗领域切换，血液先做，兼作模板）
└─ knowledge-packs/
   ├─ hematology/   🩸 血液（demo，含产品 + 组织 + 客户分级 + 区域）
   └─ _TEMPLATE/    新增领域（眼科/神经/免疫…）从此复制
```

底层技能与任务流跨治疗领域、跨人群**通用**，变的只是产品知识包与人群视角。新增一个治疗领域 = 照 `_TEMPLATE` 再填一个知识包，无需改动技能层。

## 目录导航

| 路径 | 内容 |
|---|---|
| `AGENTS.md` | 智能体行为总纲（最先读） |
| `docs/architecture.md` | 平台架构设计 |
| `docs/jd-alignment.md` | PM 岗位要求（JD）对齐设计 |
| `skills/` | PM 业务技能（纯 Markdown 任务流） |
| `.claude/skills/` | 工具型技能（含脚本，生成幻灯/pptx、创建 skill） |
| `compliance/` | 合规护栏规则 |
| `knowledge-packs/hematology/` | 血液知识包（6 个产品） |
| `knowledge-packs/README.md` | 如何新增治疗领域知识包 |
| `outputs/` | 产出物沉淀（汇报、简报、物料等） |
| `assets/roche-brand/` | Roche 品牌资产快照（icon/logo/字体/色板，季度刷新，见其 `README.md`） |
| `demos/ppt-master/` | pptx-authoring 技能的资源 hub（品牌 bundle / exemplar / 管线工具） |
| `demos/google-workspace/` | Google Workspace 基建脚本（gw_client / auth 等），meeting-prep 底座 |
| `demos/meeting-transcribe/` | 会议脚本（find-meeting / build-context），meeting-prep 用 |
| `docs/google-workspace-setup.md` | Google Workspace OAuth 配置与授权指南 |

## 技能总览

技能分两处存放，定位不同：**业务技能**（`skills/`）是无依赖的 Markdown 任务流，**工具技能**（`.claude/skills/`）含脚本、按 Claude Code 约定组织。技能对三类人群通用——SKILL.md 内按人群分流取对应视角。

> 📖 **完整技能清单、触发语、状态标记以 [`skills/README.md`](skills/README.md) 为唯一信源**。下面只给按能力方向的分类概览，方便快速了解覆盖面；新增技能只需登记到 `skills/README.md`，本页不再逐条枚举。

### 业务技能（按能力方向）

| 方向 | 主要人群 | 技能 |
|---|---|---|
| **客户互动** | 区域 + 中央 | 客户分层与覆盖、全渠道互动规划、一线反馈闭环 |
| **区域落地** | 区域市场 | 区域计划落地、区域活动执行、协作对齐（纵向+横向）、项目管理 |
| **销售管理** | 圈长 LEL 及以上 | 单院全产品业务分析（五步法）、业绩复盘/达成归因、辖区/资源管理、业务例会/QBR、随访辅导/教练、常规 1:1/发展对话 |
| **内容产出** | 三类通用 | 中英双语汇报、竞品/市场简报、推广物料+MLR 自查、讲者管理+合规、工作邮件、会议纪要、拟人聊天回复、转写校对、文档协作撰写 |
| **赋能/元** | 赋能 | 搭建业务团队智能体、从通用库迁移技能、沉淀/优化 skill |

### 工具技能（含脚本）

| 方向 | 技能 |
|---|---|
| **幻灯/文档** | slidev-authoring（HTML）、pptx-authoring（原生可编辑）、skill-creator |
| **数据/呈现** | data-analysis、dashboard-builder |
| **检索/写作** | literature-research、blog-writer、slide-ocr-verify |
| **Google Workspace** 🔧 | meeting-prep、google-workspace（基建就绪，待一次性 OAuth 授权，见 [`docs/google-workspace-setup.md`](docs/google-workspace-setup.md)）|

> 🔧 = 基建就绪待授权，其余均 ✅ 可用。逐技能的状态、依赖与触发语见 [`skills/README.md`](skills/README.md)。
> 做幻灯有两条落地路径：**slidev**（HTML）/ **pptx**（原生可编辑）。业务内容与合规先走推广物料+MLR 技能，再用工具技能落地为文件。

## 怎么用（示例）

在 ONA 对话里直接说：

- 「帮我给高罗华做一份竞品简报」→ 触发竞品简报技能
- 「把这些进展整理成给 Director 的中英双语汇报」→ 触发双语汇报技能
- 「帮我起草一份佳罗华的推广物料，并做 MLR 送审前自查」→ 触发物料+合规技能
- 「设计高罗华学术会的讲者遴选和场次分配，检查合规」→ 触发讲者管理技能
