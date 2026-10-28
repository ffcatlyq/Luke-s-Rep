# 技能与任务流（Skills & Task Flows）

> **通用引擎**的一部分，跨治疗领域复用。每个技能是一套标准执行流程，智能体按此产出高质量、合规的结果。
> 技能**不硬编码产品知识**——运行时从当前知识包（`knowledge-packs/<领域>/`）读取。

## 技能如何被触发

用户在对话中提出诉求，智能体按下表匹配技能，读取相关知识包与合规护栏，按任务流执行。

| 技能 | 角色 | 典型触发语 | 文件 |
|---|---|---|---|
| 中英双语汇报 | 助理 | "给 Director 做一份汇报""整理成双语汇报" | `bilingual-report.md` |
| 竞品/市场简报 | 参谋 | "做一份 X 的竞品简报""分析竞争格局" | `competitive-brief.md` |
| 讲者管理 + 合规 | 赋能+合规 | "设计讲者遴选/场次分配""讲者合规自查" | `speaker-management.md` |
| 推广物料 + MLR 自查 | 助理+合规 | "起草一份 X 的物料/幻灯/话术" | `promo-material-mlr.md` |
| 工作邮件起草 | 助理 | "写邮件""起草邮件""回邮件给 X" | `email-authoring.md` |
| 会议纪要 | 助理 | "整理会议纪要""出英文 minutes""summarize meeting" | `meeting-minutes.md` |
| 拟人聊天回复 | 助理 | "帮我回复""回他""我的回复像 AI" | `chat-reply.md` |
| 转写校对 | 助理 | "校对转写""ASR 专名不对""把转写纠错" | `transcript-cleanup.md` |
| 文档协作撰写 | 助理+参谋 | "写方案/proposal""起草决策文档/PRD/spec" | `doc-coauthoring.md` |
| **随访辅导/教练**（销售管理） | 赋能+助理 | "随访完写辅导反馈""改进计划""陪访/带教" | `field-coaching/` |
| **业绩复盘/达成归因**（销售管理） | 参谋+助理 | "业绩复盘""为什么没达成""目标 vs 实际" | `performance-review/` |
| **辖区/资源管理**（销售管理） | 参谋+助理 | "划分辖区""目标分解""资源/覆盖分配""call plan" | `territory-management/` |
| **客户分层与覆盖**（区域+销售） | 参谋+赋能 | "客户分层""覆盖 gap""分级覆盖策略" | `customer-segmentation/` |
| **全渠道互动规划**（区域+中央） | 参谋+助理 | "客户旅程""触点规划""全渠道""渠道内容匹配" | `omnichannel-engagement/` |
| **一线反馈闭环**（区域+销售+中央） | 参谋 | "一线反馈整理成洞察""区域洞察回流""市场信号汇总" | `field-insight-synthesis/` |
| **区域计划落地**（区域市场） | 助理+参谋 | "区域执行计划""把中央策略本地化落地""cycle plan 本地化" | `regional-plan/` |
| **区域活动执行**（区域市场） | 助理+合规 | "策划区域学术会/科室会/卫星会""活动执行清单""会后跟进" | `regional-event/` |
| **协作对齐**（纵向中央-区域 + 横向跨部门） | 助理+参谋 | "策略下达区域""区域反馈上传""对齐会""闭环跟踪""品牌团队会议""跨部门协作""行动项追踪""RACI" | `central-regional-align/` |
| **项目管理**（三类人群通用） | 助理+参谋 | "项目管理""WBS""甘特""风险管理""里程碑""项目进度""项目复盘"（上市准备/大型巡讲/患者项目） | `project-management/` |
| **单院全产品业务分析**（销售管理） | 参谋+赋能 | "五步法""单院分析""全产品视角""患者流/漏斗""医院卡在哪一步""找漏点/堵漏""单院增长" | `hospital-business-analysis/` |
| **业务例会/QBR**（销售管理） | 助理+参谋 | "业务例会""季度回顾 QBR""月会包""经营分析会" | `business-review/` |
| **常规 1:1/发展对话**（销售管理） | 赋能+助理 | "准备 1:1""发展/职业对话""目标跟进""教练提问" | `one-on-one-coaching/` |
| 搭建业务团队智能体 | 赋能 | "给 MA 从零搭一套""照这套复制到别的团队" | `bootstrap-team-agent.md` |
| 从通用库迁移技能 | 赋能 | "从 silicon 挑技能过来""哪些技能能复用" | `skill-migration.md` |
| 沉淀/优化 skill（元技能） | 赋能 | "把这个流程做成 skill""固化成 SOP" | `_meta-authoring.md` |
| **文档一致性核对**（仓库维护） | 赋能 | "文档过时了吗""核对 README""死链检查""技能清单对不对""文档同步" | `docs-consistency-check/` |
| **GSD 受赠方额度与尽调整理**（区域市场） | 助理+合规 | "GSD 受赠方""受赠方额度""尽调有效期/到期""DD 有效期""Receiver List 导出" | `gsd-receiver-due-diligence/` |

> **技能内按人群分流**：技能对三类人群（中央市场/区域市场/销售管理）通用，SKILL.md 用「何时用/人群」表标出主用人群与各自视角。销售管理三个新技能主要服务圈长 LEL 及以上 people manager。

## 两套技能目录（分工）

本仓库有两处技能，定位不同：

| 目录 | 定位 | 形态 | 依赖 |
|---|---|---|---|
| `skills/`（本目录） | **CE 部门业务技能** | Markdown 任务流；新技能用渐进式披露目录（见下） | 无运行时依赖 |
| `.claude/skills/` | **工具型技能** | 含脚本，Claude Code 机制 | Python / Node |

**技能形式（渐进式披露）**：新建业务技能采用目录结构——`SKILL.md`（~60-80 行：frontmatter 短 description+触发词、人群分流表、工作流骨架、「读哪个 reference」索引）+ `references/`（详细流程/方法论，按需读）+ `templates/`（可复用产出模板）。旧的单文件 `.md` 技能不强制立即改，触及时顺手迁移。

`.claude/skills/` 下的工具型技能：

| 技能 | 做什么 | 依赖 | 状态 |
|---|---|---|---|
| `data-analysis` | 销售/市场数据分析（读 xlsx/csv→清洗/透视/达成/趋势/图表） | Python（pandas/openpyxl/matplotlib） | ✅ 可用（脚本冒烟已 PASS）｜performance-review / territory-management 的数据引擎 |
| `dashboard-builder` | 把数字做成一页式仪表盘（KPI 卡片+图表→自包含 HTML，可离线/截图） | Python（pandas/matplotlib） | ✅ 可用（脚本冒烟已 PASS）｜data-analysis 的呈现层，供 business-review / performance-review |
| `skill-creator` | 创建/评估/优化 skill（构思→起草→测试→打包） | Python（PyYAML） | ✅ 可用（脚本已验证） |
| `slidev-authoring` | 生成 HTML 幻灯（Roche Blue 主题，可导 PDF） | Node（npx slidev） | ✅ 可用（build 已验证） |
| `pptx-authoring` | 生成原生可编辑 .pptx（Roche Blue） | Python + ppt-master 引擎（按需装） | ✅ 可用（冒烟测已 PASS） |
| `literature-research` | 按试验/干预/项目名做系统文献检索（PubMed 等），血液示例 GALLIUM | 公开 eutils，无需账号 | ✅ 已适配（挂知识包/合规） |
| `blog-writer` | PM 对外科普/案例文章，数字溯源 + MLR/off-label 护栏 | 公开检索 API | ✅ 已适配（挂 MLR/合规） |
| `slide-ocr-verify` | 从图片型幻灯/PDF 逐位读数并交叉验证 | 含脚本（render/crop/verify），依赖装于 automations | ✅ 已适配（依赖就绪+合规钩） |
| `meeting-prep` | 会前 brief（参会人/agenda/相关邮件） | Google Workspace 脚本底座（已搬入） | 🔧 基建就绪，待 OAuth 授权 |
| `google-workspace` | 编程访问 Drive/Docs/Sheets/Gmail/Calendar 等 | demos/ 脚本 + OAuth（已搬入） | 🔧 基建就绪，待 OAuth 授权 |

**pptx-authoring 状态说明**：引擎由 `scripts/setup-engine.sh` 按需下载（约 1.3GB，不进 git，装到 `~/ppt-master`）。上游 `hugohe3/ppt-master` 导出接口要求导出前提供 `spec_lock.md` 主题契约（`## pptx_structure` + `- mode: flat` 等），skill 的冒烟测与 `SKILL.md` Step 5 已按此更新，产出真原生形状（非图片贴图）。若上游再次演进导致冒烟测报红，按 `SKILL.md` Step 5 更新导出流程或参考上游 `restore-pptx-structure.md`。

> 做幻灯的两条路径：**slidev**（HTML）/ **pptx**（原生可编辑），当前均可用。业务侧"起草物料/幻灯"仍走 `promo-material-mlr.md` 做内容与合规，再用上述工具技能落地为文件。

**技能状态说明**：以下来自 silicon-hitchhiker——
- ✅ `literature-research` / `blog-writer` / `slide-ocr-verify`：已适配本仓——剥离外部领域/公司残留，挂 PM 合规护栏与知识包溯源；`slide-ocr-verify` 依赖已装入 `.ona/automations.yaml`（tesseract/poppler/pillow）。
- 🔧 `meeting-prep` / `google-workspace`：脚本底座已搬入 `demos/`（`gw_client.py` / `find-meeting.py` / `build-context.py` 等），Python 依赖由 `.ona/automations.yaml` 环境启动自动装，import 链已实测打通。**只差一次性 OAuth 授权**——由用户按 `docs/google-workspace-setup.md` 配置凭证并跑 `auth.py`（凭证不入库、不能代办）。授权后即可用。

## 通用执行原则（所有技能共享）

1. **先读知识包**：涉及产品先读 `products/<product>/product.md`，涉及组合读 `franchise.md`。
2. **挂载合规护栏**：面向外部的产出全程遵循 `compliance/guardrails.md`。
3. **不臆造**：知识包无的信息标注"待核实"，不编造数据/循证。
4. **结构化产出**：用表格/清单/成稿，可直接用。
5. **沉淀**：重要产出存 `outputs/` 对应子目录。

## 新增技能
新增技能在本目录建 `<skill>/` 目录，用渐进式披露结构（`SKILL.md` + `references/` + `templates/`），SKILL.md 含 frontmatter（name/description+触发词）、人群分流表、工作流骨架、reference 索引、合规注意，并在上表登记。技能对所有治疗领域与三类人群通用（人群差异在 SKILL.md 内分流，不建多套）。
