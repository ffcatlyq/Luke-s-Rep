# Google Workspace API 自动化场景深度分析

> **背景**: Silicon Hitchhiker 社区，成员在 Ona 环境中通过自然语言让 AI 操作 Google Workspace。
> 本文覆盖全部 **8 个 API**（Drive、Gmail、Chat、Sheets、Slides、Docs、Calendar、Cloud Search）的完整能力全景和自动化场景。
> 其中 Drive、Gmail、Chat 已有 CLI 脚本覆盖部分场景，本文重点研究脚本未覆盖的 API 能力。

---

## 一、各 API 能力全景

### 1. Google Sheets API v4

**核心操作（batchUpdate 支持 50+ 种 Request）：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **数据读写** | `values.get/update/append/batchGet/batchUpdate` | 高 最基础能力 |
| **结构操作** | `addSheet/deleteSheet/duplicateSheet/insertDimension/deleteDimension` | 中 动态建表 |
| **格式化** | `repeatCell/updateCells/updateBorders/mergeCells/updateDimensionProperties` | 高 报表美化 |
| **数据处理** | `sortRange/findReplace/textToColumns/autoFill/deleteDuplicates/trimWhitespace` | 高 数据清洗 |
| **条件格式** | `addConditionalFormatRule/updateConditionalFormatRule` | 高 智能高亮 |
| **数据验证** | `setDataValidation` | 中 下拉菜单/输入约束 |
| **图表** | `addChart/updateChartSpec` | 高 自动可视化 |
| **筛选** | `setBasicFilter/addFilterView` | 中 视图管理 |
| **保护** | `addProtectedRange/updateProtectedRange` | 中 权限控制 |
| **数据源** | `addDataSource/refreshDataSource` (Connected Sheets) | 低 BigQuery 联动 |
| **切片器** | `addSlicer/updateSlicerSpec` | 低 交互式筛选 |
| **表格** | `addTable/updateTable/deleteTable` | 中 结构化表格 |

### 2. Google Slides API v1

**核心操作（batchUpdate 支持 40+ 种 Request）：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **页面管理** | `createSlide/deleteObject/duplicateObject/updateSlidesPosition` | 高 动态建页 |
| **文本操作** | `insertText/deleteText/replaceAllText` | 高 模板填充 |
| **样式** | `updateTextStyle/updateParagraphStyle/createParagraphBullets` | 中 格式控制 |
| **形状** | `createShape/updateShapeProperties` | 中 布局构建 |
| **表格** | `createTable/insertTableRows/insertTableColumns/updateTableCellProperties/mergeTableCells` | 高 数据表格 |
| **图片** | `createImage/replaceImage/replaceAllShapesWithImage` | 高 图片替换 |
| **图表嵌入** | `createSheetsChart/refreshSheetsChart/replaceAllShapesWithSheetsChart` | 高 Sheets→Slides |
| **页面属性** | `updatePageProperties/updateSlideProperties` | 低 背景/布局 |
| **缩略图** | `pages.getThumbnail` | 中 预览生成 |

### 3. Google Docs API v1

**核心操作（batchUpdate 支持 35+ 种 Request）：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **文本操作** | `insertText/deleteContentRange/replaceAllText` | 高 内容生成 |
| **样式** | `updateTextStyle/updateParagraphStyle/updateNamedStyle` | 中 格式统一 |
| **列表** | `createParagraphBullets/deleteParagraphBullets` | 中 结构化内容 |
| **表格** | `insertTable/insertTableRow/insertTableColumn/updateTableCellStyle/mergeTableCells` | 高 报告表格 |
| **图片** | `insertInlineImage/replaceImage` | 中 图文混排 |
| **命名范围** | `createNamedRange/replaceNamedRangeContent` | 高 模板占位符 |
| **页眉页脚** | `createHeader/createFooter/deleteHeader/deleteFooter` | 中 文档规范 |
| **脚注** | `createFootnote` | 低 学术引用 |
| **分节** | `insertSectionBreak/updateSectionStyle` | 低 文档结构 |
| **文档样式** | `updateDocumentStyle` | 中 页面设置 |
| **标签页** | `addDocumentTab/deleteTab/updateDocumentTabProperties` | 中 多标签管理 |
| **智能插入** | `insertPerson/insertRichLink/insertDate` | 高 @提及/链接 |

### 4. Google Calendar API v3

**核心操作：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **事件 CRUD** | `events.insert/get/update/delete/list` | 高 日程管理 |
| **批量查询** | `events.list` (timeMin/timeMax/q/singleEvents) | 高 日程分析 |
| **快速创建** | `events.quickAdd` (自然语言创建事件) | 高 极简创建 |
| **移动事件** | `events.move` (跨日历移动) | 中 日历整理 |
| **重复事件** | `events.instances` (展开重复事件) | 中 系列管理 |
| **日历管理** | `calendars.insert/get/update/delete` | 低 日历创建 |
| **日历列表** | `calendarList.list/insert/delete` | 中 订阅管理 |
| **ACL** | `acl.insert/list/delete` | 中 共享权限 |
| **空闲/忙碌** | `freebusy.query` | 高 找空闲时间 |
| **状态事件** | Focus Time / Out of Office / Working Location | 中 状态管理 |
| **推送通知** | `events.watch` | 低 变更监听 |

---

## 二、高价值自动化场景（按优先级排序）

### Tier 1：高频 × 高价值 × 适合 AI 按需执行

#### 场景 1：临床试验周报自动生成（Sheets → Docs + Slides）
**痛点**：药企每周需要从多个 Sheets 汇总临床试验进度、不良事件统计、入组率等数据，手动复制粘贴到 Word/PPT 报告中，耗时 2-4 小时。

**API 联动**：
```
Sheets.values.batchGet → 读取多个 Sheet 的数据
  ↓
AI 分析数据趋势、生成摘要文本
  ↓
Docs.batchUpdate (insertText + insertTable + updateTextStyle) → 生成周报文档
  ↓
Slides.batchUpdate (replaceAllText + createSheetsChart + createTable) → 生成汇报 PPT
```

**为什么不适合 CLI 但适合 AI**：
- 每周数据范围不同（哪些 Sheet、哪些列）
- 需要 AI 理解数据含义，生成自然语言摘要
- 报告格式可能因受众不同而调整（给 CRA vs 给 Medical Director）
- 需要判断哪些数据异常值得高亮

**自然语言示例**：
> "从临床试验追踪表里拉取本周的入组数据和 SAE 统计，生成一份给 Medical Director 的周报 PPT，重点标注入组率低于目标的站点"

---

#### 场景 2：会议智能调度 + 议程准备（Calendar + Docs + Sheets）
**痛点**：跨时区团队安排会议需要反复查看多人日历，会前需要手动准备议程文档。

**API 联动**：
```
Calendar.freebusy.query → 查询多人空闲时间
  ↓
AI 推荐最优时间段
  ↓
Calendar.events.insert → 创建会议（含 Meet 链接、议程链接）
  ↓
Docs.create + batchUpdate → 自动创建议程文档（模板填充）
  ↓
Calendar.events.update → 将议程文档链接附到会议描述中
```

**为什么不适合 CLI 但适合 AI**：
- 需要理解"下周找个大家都有空的时间"这种模糊指令
- 需要考虑时区、工作时间偏好、会议优先级
- 议程内容需要根据会议主题智能生成

**自然语言示例**：
> "帮我约一个 CDE 团队的周会，下周二到周四之间找个大家都有空的 1 小时，自动创建议程文档，包含上次会议的 action items"

---

#### 场景 3：数据质量审计 + 条件格式化（Sheets）
**痛点**：药企数据管理团队需要定期检查 Sheets 中的数据质量——缺失值、格式不一致、超范围值。手动逐列检查极其耗时。

**API 操作**：
```
Sheets.values.batchGet → 读取全部数据
  ↓
AI 分析数据质量问题（缺失率、异常值、格式不一致）
  ↓
Sheets.batchUpdate:
  - addConditionalFormatRule → 红色高亮缺失值
  - addConditionalFormatRule → 黄色高亮异常值
  - setDataValidation → 添加下拉菜单约束
  - addSheet → 创建"审计报告"标签页
  - values.update → 写入审计结果
```

**为什么不适合 CLI 但适合 AI**：
- 每次审计的数据结构不同，需要 AI 理解列含义
- 异常值的判断标准因业务场景而异（年龄 vs 剂量 vs 日期）
- 需要生成人类可读的审计报告

**自然语言示例**：
> "检查这个临床数据表的数据质量，标红所有缺失值，标黄超出正常范围的数值，在新标签页里生成审计摘要"

---

#### 场景 4：模板化文档批量生成（Slides + Docs + Sheets）
**痛点**：药企需要为每个临床试验站点生成独立的启动文档包（Site Initiation Package），包含站点信息、联系人、协议摘要等。

**API 联动**：
```
Sheets.values.get → 读取站点信息表（站点名、PI、地址、联系方式...）
  ↓
Drive.files.copy → 复制模板文档/PPT
  ↓
Docs.batchUpdate (replaceAllText) → 替换 {{site_name}}, {{pi_name}} 等占位符
Slides.batchUpdate (replaceAllText + replaceAllShapesWithImage) → 替换 PPT 模板
  ↓
Drive.permissions.create → 设置共享权限给对应站点团队
```

**为什么不适合 CLI 但适合 AI**：
- 模板字段映射需要理解（"PI" = Principal Investigator = Sheets 中的"主要研究者"列）
- 可能需要根据站点类型选择不同模板
- 生成后可能需要 AI 审查内容完整性

**自然语言示例**：
> "用站点信息表里的数据，为每个新站点生成启动文档包，用 SIV 模板，自动填入站点信息并分享给对应的 CRA"

---

### Tier 2：中频 × 高价值

#### 场景 5：会议纪要自动化（Calendar + Docs）
**痛点**：会后需要手动整理会议纪要，分发给参会者。

**API 联动**：
```
Calendar.events.get → 获取会议信息（参会者、议程链接）
  ↓
Docs.get → 读取议程文档
  ↓
AI 根据用户口述/笔记生成结构化纪要
  ↓
Docs.batchUpdate → 在议程文档中追加纪要部分
  (insertText + insertTable + createParagraphBullets + insertPerson)
  ↓
Calendar.events.update → 在会议描述中标注"纪要已更新"
```

**亮点**：`insertPerson` 可以在文档中 @提及参会者，自动通知。

---

#### 场景 6：项目看板 → 管理层汇报 PPT（Sheets → Slides）
**痛点**：项目经理维护 Sheets 看板，但每次向管理层汇报需要手动做 PPT。

**API 联动**：
```
Sheets.values.batchGet → 读取项目状态、里程碑、风险项
  ↓
Sheets.batchUpdate (addChart) → 在 Sheet 中创建图表（甘特图、饼图）
  ↓
Slides.batchUpdate:
  - createSlide → 创建页面
  - createSheetsChart → 嵌入 Sheets 图表
  - createTable → 插入风险矩阵
  - replaceAllText → 填充项目名称、日期
  - updateTextStyle → 红色标注延期项
```

**自然语言示例**：
> "把项目追踪表做成一个 5 页的管理层汇报 PPT，包含进度概览、里程碑时间线、风险矩阵、资源分配和下一步计划"

---

#### 场景 7：日历分析 + 时间管理建议（Calendar）
**痛点**：知识工作者不知道自己的时间花在哪里，会议过多导致深度工作时间不足。

**API 操作**：
```
Calendar.events.list (过去 4 周) → 获取所有事件
  ↓
AI 分析：
  - 会议时间占比
  - 碎片化程度（连续空闲时间段分布）
  - 重复会议 ROI（参会人数 × 时长）
  - 跨时区会议对工作节奏的影响
  ↓
Sheets.create + values.update → 生成分析数据表
Sheets.batchUpdate (addChart) → 生成可视化图表
```

**自然语言示例**：
> "分析我过去一个月的日历，告诉我会议时间占比、最大的时间黑洞是什么、哪些重复会议可以考虑取消"

---

#### 场景 8：SOP 文档版本对比 + 变更追踪（Docs）
**痛点**：药企 SOP 更新频繁，需要追踪每次变更的具体内容。

**API 操作**：
```
Docs.get → 读取当前版本全文
Drive.revisions.list → 获取历史版本列表
Drive.revisions.get → 获取特定版本内容
  ↓
AI 对比两个版本，生成变更摘要
  ↓
Docs.batchUpdate → 在文档末尾追加"变更记录"章节
  (insertText + insertTable + updateTextStyle)
```

---

#### 场景 9：跨表数据汇总 + 透视分析（Sheets）
**痛点**：多个部门各自维护 Sheets，需要定期汇总到一个总表。

**API 操作**：
```
Drive.files.list → 找到所有相关 Sheets
  ↓
Sheets.values.batchGet (多个 spreadsheetId) → 读取各表数据
  ↓
AI 理解各表结构差异，做字段映射
  ↓
Sheets.create → 创建汇总表
Sheets.values.batchUpdate → 写入合并数据
Sheets.batchUpdate:
  - addChart → 创建汇总图表
  - addConditionalFormatRule → 高亮异常
  - setBasicFilter → 添加筛选器
  - updateDimensionProperties → 自动调整列宽
  - autoResizeDimensions → 自适应
```

---

### Tier 3：低频但高影响

#### 场景 10：培训日历批量创建 + 材料关联（Calendar + Slides + Docs）
**痛点**：组织内部培训需要创建系列日历事件，每个事件关联不同的培训材料。

**API 联动**：
```
Sheets.values.get → 读取培训计划表（日期、主题、讲师、材料链接）
  ↓
Calendar.events.insert (循环) → 批量创建日历事件
  - 设置 attendees（参训人员）
  - 设置 description（含材料链接）
  - 设置 conferenceData（Meet 链接）
  ↓
Docs.create + batchUpdate → 为每次培训创建签到表
```

---

#### 场景 11：合规文档自动格式化（Docs）
**痛点**：药企提交给监管机构的文档有严格的格式要求（字体、行距、页边距、页眉页脚）。

**API 操作**：
```
Docs.get → 读取文档结构
  ↓
AI 检查格式合规性
  ↓
Docs.batchUpdate:
  - updateDocumentStyle → 设置页边距、页面大小
  - updateNamedStyle → 统一标题/正文样式
  - createHeader/createFooter → 添加页眉页脚
  - updateTextStyle → 修正字体/字号
  - updateParagraphStyle → 修正行距/对齐
  - insertInlineImage → 插入公司 logo
```

---

#### 场景 12：Sheets 数据 → 邮件合并（Sheets + Docs + Gmail）
**痛点**：需要根据 Sheets 中的联系人列表，生成个性化邮件/文档。

**API 联动**：
```
Sheets.values.get → 读取联系人 + 个性化字段
  ↓
Docs.batchUpdate (replaceAllText) → 生成个性化文档
  ↓
Drive.files.export → 导出为 PDF
  ↓
Gmail.messages.send → 发送带附件的邮件
```

---

## 三、"不适合 CLI 但适合 AI" 的判断框架

| 特征 | CLI 脚本 | AI Agent |
|------|---------|---------|
| 输入参数固定 | 适合 | 不需要 |
| 需要理解自然语言意图 | 不适合 | 适合 |
| 需要根据数据内容做判断 | 不适合 | 适合 |
| 操作步骤因上下文而异 | 不适合 | 适合 |
| 需要跨多个 API 编排 | 勉强可以 | 更自然 |
| 输出需要人类可读的解释 | 不适合 | 适合 |
| 一次性/低频操作 | 不值得写脚本 | 适合 |
| 需要与用户多轮交互确认 | 不适合 | 适合 |

**核心洞察**：CLI 脚本适合"参数化的重复操作"（如 `drive_scan.py scan`），AI Agent 适合"需要理解意图 + 数据感知 + 动态编排"的操作。

---

## 四、药企特色场景补充

| 场景 | 涉及 API | 药企特殊性 |
|------|---------|-----------|
| **CAPA 追踪表维护** | Sheets | 纠正和预防措施需要严格的状态流转和到期提醒 |
| **药物警戒报告** | Sheets → Docs | 不良事件数据需要按 CIOMS 格式生成报告 |
| **审计准备** | Docs + Sheets + Calendar | 审计前需要整理文档清单、安排访谈日程 |
| **变更控制记录** | Docs | 每次变更需要记录影响评估、审批链 |
| **培训记录管理** | Sheets + Calendar | GxP 培训需要记录完成情况，关联日历事件 |
| **供应商评估** | Sheets → Slides | 定期评估供应商绩效，生成评审报告 |

---

## 五、技术实现建议

### 推荐的工具封装粒度

**不要**为每个场景写一个独立脚本。而是提供**原子操作工具**，让 AI 自由组合：

```
sheets_ops.py
  - read_range(spreadsheet_id, range)
  - write_range(spreadsheet_id, range, values)
  - append_rows(spreadsheet_id, sheet_name, rows)
  - add_chart(spreadsheet_id, sheet_id, chart_type, data_range)
  - add_conditional_format(spreadsheet_id, sheet_id, rule)
  - create_spreadsheet(title)

slides_ops.py
  - create_presentation(title)
  - add_slide(presentation_id, layout)
  - replace_text(presentation_id, find, replace)
  - add_table(presentation_id, slide_id, rows, cols, data)
  - embed_sheets_chart(presentation_id, slide_id, spreadsheet_id, chart_id)
  - add_image(presentation_id, slide_id, image_url)

docs_ops.py
  - create_document(title)
  - read_document(document_id)
  - insert_text(document_id, text, index)
  - replace_all_text(document_id, find, replace)
  - insert_table(document_id, rows, cols, data)
  - insert_image(document_id, image_url, index)
  - set_document_style(document_id, margins, page_size)

calendar_ops.py
  - list_events(calendar_id, time_min, time_max)
  - create_event(calendar_id, summary, start, end, attendees, description)
  - find_free_time(calendar_ids, time_min, time_max, duration)
  - update_event(calendar_id, event_id, updates)
  - quick_add(calendar_id, text)
```

### 关键设计原则

1. **原子化**：每个函数做一件事，AI 负责编排
2. **幂等性**：重复调用不会产生副作用（或有 dry-run 模式）
3. **可读输出**：返回人类可读的结果，而非原始 JSON
4. **错误友好**：错误信息包含修复建议
5. **链接返回**：操作完成后返回 Google Workspace 文档链接，方便用户直接查看

---

## 六、优先实现路线图

### Phase 1（社区 Demo 核心）
1. `sheets_ops.py` — 读写 + 条件格式 + 图表
2. `calendar_ops.py` — 事件 CRUD + 空闲时间查询
3. **Demo 场景**：从 Sheets 读取数据 → AI 分析 → 写回审计结果 + 条件格式高亮

### Phase 2（跨 API 联动）
4. `slides_ops.py` — 模板填充 + Sheets 图表嵌入
5. `docs_ops.py` — 文档生成 + 模板替换
6. **Demo 场景**：Sheets 数据 → 自动生成汇报 PPT

### Phase 3（完整工作流）
7. 组合场景：会议调度 + 议程生成 + 纪要追踪
8. 组合场景：模板批量生成 + 权限分发

---

# Part 2：Drive / Gmail / Chat — 脚本未覆盖的 API 能力

> 以下三个 API 已有 CLI 脚本覆盖部分场景（Drive 治理、Gmail 分流、Chat 摘要），
> 本部分聚焦脚本未覆盖的能力和自动化场景。## 一、各 API 能力全景

### 5. Google Drive API v3

> **已有脚本覆盖**: `files.list`（全量扫描）、`files.get`（元信息）、`files.export`（内容导出）、`files.delete/update(trashed)`（清理）— 详见 drive_scan / drive_export / drive_cleanup 三个脚本。

**脚本未覆盖的完整能力矩阵：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **文件创建** | `files.create`（上传/创建空白 Google 文档） | 高 自动建文件 |
| **文件复制** | `files.copy`（复制文件，支持跨目录/重命名） | 高 模板克隆 |
| **文件上传** | `files.create` + media upload（二进制上传） | 中 附件上传 |
| **文件下载** | `files.download`（下载二进制文件） | 中 文件提取 |
| **文件监听** | `files.watch`（推送通知文件变更） | 低 变更触发 |
| **ID 预生成** | `files.generateIds`（预生成文件 ID） | 低 批量操作 |
| **清空回收站** | `files.emptyTrash` | 低 彻底清理 |
| **标签管理** | `files.listLabels / files.modifyLabels`（Drive Labels） | 高 分类治理 |
| **权限-创建** | `permissions.create`（授予用户/组/域权限） | 高 自动分享 |
| **权限-查询** | `permissions.list / permissions.get` | 高 权限审计 |
| **权限-更新** | `permissions.update`（变更角色级别） | 中 权限调整 |
| **权限-删除** | `permissions.delete`（撤销共享） | 高 权限回收 |
| **评论-创建** | `comments.create`（在文件上添加评论） | 高 审阅反馈 |
| **评论-查询** | `comments.list / comments.get` | 中 评论汇总 |
| **评论-更新** | `comments.update`（编辑/解决评论） | 中 评论管理 |
| **评论-删除** | `comments.delete` | 低 清理 |
| **回复** | `replies.create/list/get/update/delete` | 中 评论对话 |
| **版本-查询** | `revisions.list / revisions.get` | 高 版本追踪 |
| **版本-更新** | `revisions.update`（设置 keepForever 等） | 中 版本保护 |
| **版本-删除** | `revisions.delete` | 低 版本清理 |
| **共享盘-创建** | `drives.create` | 中 团队空间 |
| **共享盘-查询** | `drives.list / drives.get` | 中 盘点管理 |
| **共享盘-更新** | `drives.update`（名称/限制/主题） | 低 配置管理 |
| **共享盘-隐藏** | `drives.hide / drives.unhide` | 低 视图整理 |
| **共享盘-删除** | `drives.delete` | 低 生命周期 |
| **变更追踪** | `changes.list / changes.getStartPageToken` | 中 增量同步 |
| **变更监听** | `changes.watch`（推送通知 Drive 变更） | 低 实时监控 |
| **频道停止** | `channels.stop`（停止推送通知） | 低 监听管理 |
| **审批-发起** | `approvals.start`（发起文件审批流程） | 高 审批自动化 |
| **审批-操作** | `approvals.approve/decline/comment/reassign/cancel` | 高 审批处理 |
| **审批-查询** | `approvals.list / approvals.get` | 中 审批状态 |
| **访问提案** | `accessproposals.list/get/resolve`（处理访问请求） | 中 权限请求 |
| **应用查询** | `apps.list / apps.get`（已安装的 Drive 应用） | 低 应用管理 |
| **关于** | `about.get`（用户存储配额/功能信息） | 中 配额监控 |

---

### 6. Gmail API v1

> **已有脚本覆盖**: `messages.list/get/modify`（搜索/读取/标签操作）、`messages.batchModify`（批量归档）、`labels.list/get/create`（标签管理）、`settings.filters.create`（过滤器创建）— 详见 gmail_triage 脚本。

**脚本未覆盖的完整能力矩阵：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **发送邮件** | `messages.send`（发送新邮件/回复） | 高 自动发信 |
| **邮件回收站** | `messages.trash / messages.untrash` | 中 邮件清理 |
| **邮件删除** | `messages.delete`（永久删除，不可恢复） | 低 彻底清理 |
| **批量删除** | `messages.batchDelete`（批量永久删除） | 低 批量清理 |
| **邮件导入** | `messages.import`（导入邮件到邮箱） | 低 迁移场景 |
| **邮件插入** | `messages.insert`（直接插入，跳过投递） | 低 归档导入 |
| **附件获取** | `messages.attachments.get`（下载附件内容） | 高 附件处理 |
| **草稿-创建** | `drafts.create`（创建草稿） | 高 AI 起草 |
| **草稿-更新** | `drafts.update`（修改草稿内容） | 中 迭代修改 |
| **草稿-发送** | `drafts.send`（发送已有草稿） | 高 确认后发送 |
| **草稿-查询** | `drafts.list / drafts.get` | 中 草稿管理 |
| **草稿-删除** | `drafts.delete` | 低 清理 |
| **线程-查询** | `threads.list / threads.get`（获取完整对话） | 高 上下文理解 |
| **线程-修改** | `threads.modify`（批量修改线程标签） | 中 线程归类 |
| **线程-回收站** | `threads.trash / threads.untrash` | 中 线程清理 |
| **线程-删除** | `threads.delete`（永久删除整个线程） | 低 彻底清理 |
| **标签-更新** | `labels.patch / labels.update`（修改标签属性） | 中 标签管理 |
| **标签-删除** | `labels.delete` | 低 标签清理 |
| **历史记录** | `history.list`（增量变更记录） | 中 变更追踪 |
| **邮箱监听** | `users.watch`（推送通知邮箱变更） | 低 实时触发 |
| **停止监听** | `users.stop` | 低 监听管理 |
| **用户信息** | `users.getProfile`（邮箱地址/消息总数） | 中 状态查询 |
| **休假回复** | `settings.getVacation / updateVacation` | 高 自动回复 |
| **自动转发** | `settings.getAutoForwarding / updateAutoForwarding` | 中 转发管理 |
| **语言设置** | `settings.getLanguage / updateLanguage` | 低 偏好设置 |
| **IMAP/POP** | `settings.getImap/updateImap, getPop/updatePop` | 低 协议配置 |
| **过滤器-查询** | `settings.filters.list / get` | 中 规则审计 |
| **过滤器-删除** | `settings.filters.delete` | 低 规则清理 |
| **发送身份** | `settings.sendAs.list/get/create/update/delete/verify` | 中 多身份管理 |
| **代理人** | `settings.delegates.list/get/create/delete` | 中 邮箱委托 |
| **转发地址** | `settings.forwardingAddresses.list/get/create/delete` | 低 转发配置 |
| **S/MIME** | `settings.sendAs.smimeInfo.insert/list/get/delete/setDefault` | 低 加密邮件 |
| **CSE 身份** | `settings.cse.identities.create/list/get/patch/delete` | 低 客户端加密 |
| **CSE 密钥对** | `settings.cse.keypairs.create/list/get/enable/disable/obliterate` | 低 密钥管理 |

---

### 7. Google Chat API v1

> **已有脚本覆盖**: `spaces.list`（列出 Space）、`spaces.messages.list`（拉取消息）、`spaces.members.list`（成员列表）、`spaces.findDirectMessage`（查找私信）— 详见 chat_digest 脚本。

**脚本未覆盖的完整能力矩阵：**

| 类别 | 关键操作 | AI Agent 价值 |
|------|---------|--------------|
| **发送消息** | `spaces.messages.create`（发送文本/卡片消息） | 高 主动通知 |
| **更新消息** | `spaces.messages.update / patch`（编辑已发消息） | 中 状态更新 |
| **删除消息** | `spaces.messages.delete` | 低 消息撤回 |
| **获取消息** | `spaces.messages.get`（获取单条消息详情） | 中 消息引用 |
| **替换卡片** | `spaces.messages.replaceCards`（替换消息中的卡片） | 中 动态卡片 |
| **创建 Space** | `spaces.create`（创建新 Space） | 中 自动建群 |
| **设置 Space** | `spaces.setup`（创建 Space 并添加成员） | 高 一步建群 |
| **获取 Space** | `spaces.get`（获取 Space 详情） | 中 信息查询 |
| **更新 Space** | `spaces.patch`（修改 Space 名称/描述/设置） | 低 配置管理 |
| **删除 Space** | `spaces.delete` | 低 生命周期 |
| **搜索 Space** | `spaces.search`（管理员搜索组织内 Space） | 中 治理审计 |
| **查找群聊** | `spaces.findGroupChats`（按成员查找群聊） | 中 群组发现 |
| **完成导入** | `spaces.completeImport`（完成 Space 数据导入） | 低 迁移场景 |
| **添加成员** | `spaces.members.create`（添加用户/组到 Space） | 高 成员管理 |
| **移除成员** | `spaces.members.delete` | 中 成员管理 |
| **获取成员** | `spaces.members.get`（获取成员详情） | 低 信息查询 |
| **更新成员** | `spaces.members.patch`（修改成员角色） | 中 角色管理 |
| **添加表情** | `spaces.messages.reactions.create`（给消息添加表情） | 中 互动反馈 |
| **删除表情** | `spaces.messages.reactions.delete` | 低 表情管理 |
| **查询表情** | `spaces.messages.reactions.list` | 低 情绪分析 |
| **获取附件** | `spaces.messages.attachments.get` | 中 附件处理 |
| **上传媒体** | `media.upload`（上传附件到 Space） | 中 文件分享 |
| **下载媒体** | `media.download`（下载 Space 中的媒体） | 中 文件提取 |
| **Space 事件** | `spaces.spaceEvents.list / get`（查询 Space 事件流） | 中 活动审计 |
| **已读状态** | `users.spaces.getSpaceReadState / updateSpaceReadState` | 中 已读管理 |
| **线程已读** | `users.spaces.threads.getThreadReadState` | 低 线程追踪 |
| **通知设置** | `users.spaces.spaceNotificationSetting.get / patch` | 中 免打扰 |
| **分区管理** | `users.sections.create/list/patch/delete/position` | 低 Space 分组 |
| **分区项目** | `users.sections.items.list / move` | 低 Space 排序 |
| **自定义表情** | `customEmojis.create/list/get/delete` | 低 团队文化 |

---

## 二、高价值自动化场景（按优先级排序）

> 编号从 13 开始，承接已有文档的场景 1-12（Sheets/Slides/Docs/Calendar）。

### Tier 1：高频 × 高价值 × 适合 AI 按需执行


#### 场景 13：Drive 权限审计 + 自动回收（Drive permissions）
**痛点**：药企合规要求定期审查文件共享权限，确保敏感文档（如临床方案、药物安全数据）没有被过度共享。手动逐文件检查权限不现实。

**API 联动**：
```
Drive.files.list (q="shared=true") → 找到所有已共享文件
  ↓
Drive.permissions.list (逐文件) → 获取每个文件的权限列表
  ↓
AI 分析：
  - 哪些文件共享给了组织外部（anyoneWithLink / 外部邮箱）
  - 哪些敏感文件夹的权限过于宽泛（domain-wide）
  - 哪些共享已超过 N 天未访问
  ↓
Drive.permissions.delete → 自动撤销过期/违规的共享权限
Drive.permissions.update → 降级权限（editor → viewer）
  ↓
Sheets.values.update → 生成权限审计报告
```

**为什么不适合 CLI 但适合 AI**：
- 需要理解"敏感文件"的定义（路径、文件名、标签）
- 权限回收需要判断业务影响（是否还有人在协作）
- 审计报告需要自然语言解释风险等级

**自然语言示例**：
> "审计我 Drive 中所有共享给组织外部的文件，列出风险等级，对超过 90 天未修改的外部共享自动撤销"

---

#### 场景 14：AI 起草邮件 + 人工确认发送（Gmail drafts + send）
**痛点**：日常需要撰写大量格式化邮件（会议跟进、项目更新、供应商沟通），但每封邮件都需要个性化内容。

**API 联动**：
```
Gmail.threads.get → 读取原始邮件线程（获取上下文）
  ↓
AI 理解对话上下文，生成回复草稿
  ↓
Gmail.drafts.create → 创建草稿（含 To/Cc/Subject/Body）
  ↓
用户在 Gmail 中预览、修改
  ↓
Gmail.drafts.send → 确认后发送
```

**为什么不适合 CLI 但适合 AI**：
- 需要理解邮件上下文和对话历史
- 回复内容需要根据语气、受众调整（给老板 vs 给供应商）
- 草稿模式提供安全网，AI 不会直接发送

**自然语言示例**：
> "帮我回复 Dr. Chen 关于临床方案修改的邮件，同意他的建议但提出时间线需要延后两周，语气正式"

---

#### 场景 15：Chat 主动通知 + 状态卡片（Chat messages.create）
**痛点**：团队需要在关键事件发生时（构建完成、审批通过、数据异常）在 Chat 群组中发送结构化通知，而非手动复制粘贴。

**API 操作**：
```
Chat.spaces.messages.create → 发送富文本/卡片消息
  - text: 纯文本消息
  - cardsV2: 结构化卡片（标题、图片、按钮、分栏）
  - thread: 指定线程（回复已有讨论）
  - accessoryWidgets: 附加交互组件
```

**为什么不适合 CLI 但适合 AI**：
- 通知内容需要根据事件类型动态生成
- 卡片结构需要根据数据量自适应
- 需要判断发送到哪个 Space、是否需要 @提及特定人

**自然语言示例**：
> "在 CD2-AI-Hackathon 群里发一条卡片消息，通知大家今天的 demo 改到下午 3 点，附上 Meet 链接"

---

#### 场景 16：文件审批工作流自动化（Drive approvals）
**痛点**：药企文档（SOP、方案、报告）需要多级审批，目前通过邮件/Chat 手动跟踪审批状态，容易遗漏。

**API 联动**：
```
Drive.approvals.start → 发起审批（指定审批人、截止日期）
  ↓
Drive.approvals.list → 查询审批状态
  ↓
AI 监控审批进度：
  - 超时未审批 → Chat.messages.create 发送提醒
  - 审批完成 → Gmail.messages.send 通知发起人
  ↓
Drive.approvals.approve/decline → 审批人通过 AI 执行审批操作
Drive.approvals.comment → 添加审批意见
Drive.approvals.reassign → 转交给其他审批人
```

**为什么不适合 CLI 但适合 AI**：
- 审批流程因文档类型而异（SOP 需要 QA + RA 双签，报告只需 Manager）
- 需要理解"帮我催一下还没审批的人"这种模糊指令
- 审批意见需要 AI 辅助生成

**自然语言示例**：
> "对 SOP-2026-001 发起审批，审批人是 Dr. Wang 和 QA 团队的 Lisa，截止日期下周五"

---

### Tier 2：中频 × 高价值

#### 场景 17：邮件附件自动提取 + 归档到 Drive（Gmail attachments + Drive）
**痛点**：药企经常收到供应商/CRO 通过邮件发送的报告、证书、数据文件，需要手动下载并归档到 Drive 对应文件夹。

**API 联动**：
```
Gmail.messages.list (q="has:attachment from:vendor@cro.com") → 搜索含附件邮件
  ↓
Gmail.messages.get → 获取邮件详情（附件 ID）
  ↓
Gmail.messages.attachments.get → 下载附件内容（base64）
  ↓
AI 分析附件类型和内容，决定归档位置
  ↓
Drive.files.create (media upload) → 上传到 Drive 指定文件夹
  ↓
Gmail.messages.modify → 给已处理邮件添加 "已归档" 标签
```

**为什么不适合 CLI 但适合 AI**：
- 附件归档位置需要根据内容智能判断（COA → 质量文件夹，报告 → 项目文件夹）
- 文件命名需要标准化（加日期前缀、项目编号）
- 需要去重检查（同一附件是否已归档）

**自然语言示例**：
> "把过去一周收到的所有 CRO 邮件附件提取出来，按项目分类归档到 Drive 的 Clinical Documents 文件夹"

---

#### 场景 18：Drive 文件版本对比 + 变更日志（Drive revisions）
**痛点**：药企 SOP/方案文档频繁更新，需要追踪每次变更的具体内容，满足 GxP 审计要求。

**API 联动**：
```
Drive.revisions.list → 获取文件所有版本列表
  ↓
Drive.revisions.get (特定版本) → 获取版本元信息（修改人、时间）
  ↓
Drive.files.export (revisionId) → 导出特定版本内容
  ↓
AI 对比两个版本，生成结构化变更摘要
  ↓
Drive.revisions.update (keepForever=true) → 标记关键版本为永久保留
  ↓
Docs.batchUpdate → 在文档中追加变更记录章节
```

**为什么不适合 CLI 但适合 AI**：
- 变更对比需要理解文档结构（哪些是实质性变更 vs 格式调整）
- 变更摘要需要用业务语言描述（"修改了剂量方案" 而非 "第 3 段第 2 行文字变更"）
- 需要判断哪些版本值得永久保留

**自然语言示例**：
> "对比 SOP-001 的最新版本和上一个版本，生成变更摘要，标记关键版本为永久保留"

---

#### 场景 19：Chat Space 自动创建 + 项目团队组建（Chat spaces.setup + members）
**痛点**：新项目启动时需要创建 Chat 群组、添加团队成员、发送欢迎消息和项目资料链接，手动操作繁琐。

**API 联动**：
```
Chat.spaces.setup → 一步创建 Space 并添加初始成员
  - displayName: "Project-ABC 临床试验"
  - spaceType: SPACE
  - memberships: [user1, user2, user3...]
  ↓
Chat.spaces.messages.create → 发送欢迎消息（含项目简介卡片）
  ↓
Chat.spaces.messages.create → 发送项目资料链接
  - Drive 文件夹链接
  - Sheets 追踪表链接
  - 会议日历链接
```

**为什么不适合 CLI 但适合 AI**：
- 成员列表可能来自自然语言描述（"CDE 团队的人加上 QA 的 Lisa"）
- 欢迎消息需要根据项目类型定制
- 可能需要同时创建多个关联 Space（如 #general + #data + #safety）

**自然语言示例**：
> "为 Project-ABC 创建一个 Chat 群组，把临床团队和数据管理团队的人都加进去，发一条欢迎消息附上项目文件夹链接"

---

#### 场景 20：邮件线程摘要 + 行动项提取（Gmail threads）
**痛点**：长邮件线程（10+ 封往来）难以快速理解全貌，关键决策和行动项散落在各封邮件中。

**API 联动**：
```
Gmail.threads.list (q="subject:临床方案") → 搜索相关线程
  ↓
Gmail.threads.get (format=FULL) → 获取完整线程（所有邮件）
  ↓
AI 分析：
  - 对话摘要（谁说了什么，关键决策点）
  - 提取行动项（谁需要做什么，截止日期）
  - 识别未回复/待确认的问题
  ↓
Chat.spaces.messages.create → 在团队群发送摘要
Sheets.values.append → 将行动项写入追踪表
```

**为什么不适合 CLI 但适合 AI**：
- 需要理解邮件上下文和对话逻辑
- 行动项提取需要 NLU 能力
- 摘要粒度因受众而异

**自然语言示例**：
> "帮我总结和 CRO 关于数据清理的邮件线程，提取所有待办事项和截止日期"

---

#### 场景 21：Drive 评论审阅汇总（Drive comments + replies）
**痛点**：文档审阅时，多个审阅者在不同位置留下评论，文档作者需要逐一查看和回复，容易遗漏。

**API 联动**：
```
Drive.comments.list (fileId, includeDeleted=false) → 获取所有评论
  ↓
Drive.replies.list (逐评论) → 获取每条评论的回复
  ↓
AI 分析：
  - 按审阅者分组评论
  - 分类：修改建议 / 疑问 / 赞同
  - 识别未解决的评论
  ↓
Drive.comments.update (resolved=true) → 批量解决已处理的评论
Drive.replies.create → AI 辅助生成回复
  ↓
Sheets.values.update → 生成评论追踪表
```

**为什么不适合 CLI 但适合 AI**：
- 评论分类需要理解内容语义
- 回复生成需要结合文档上下文
- 需要判断哪些评论可以批量解决

**自然语言示例**：
> "汇总 SOP-002 上所有未解决的评论，按审阅者分组，帮我起草回复"

---

### Tier 3：低频但高影响

#### 场景 22：休假自动回复 + 工作交接（Gmail vacation + delegates + Chat）
**痛点**：员工休假前需要设置邮件自动回复、配置邮箱代理人、在 Chat 群通知团队，多个步骤容易遗忘。

**API 联动**：
```
Gmail.settings.updateVacation → 设置休假自动回复
  - enableAutoReply: true
  - responseSubject: "Out of Office: [日期范围]"
  - responseBodyHtml: AI 生成的回复内容（含代理人联系方式）
  - startTime / endTime: 休假时间范围
  - restrictToContacts / restrictToDomain: 回复范围
  ↓
Gmail.settings.delegates.create → 添加邮箱代理人
  ↓
Chat.spaces.messages.create → 在团队群发送休假通知
  - 包含休假时间、代理人、紧急联系方式
  ↓
Calendar.events.insert → 创建 OOO 日历事件（跨 API 联动）
```

**自然语言示例**：
> "我下周一到周五休假，帮我设置邮件自动回复，代理人是 Lisa，在团队群发个通知"

---

#### 场景 23：共享盘生命周期管理（Drive drives + permissions）
**痛点**：药企项目结束后，共享盘需要归档处理——调整权限为只读、移动到归档区、通知相关人员。

**API 联动**：
```
Drive.drives.list → 列出所有共享盘
  ↓
AI 识别已结束的项目共享盘（基于名称/最后活跃时间）
  ↓
Drive.permissions.list → 获取共享盘权限
Drive.permissions.update → 将所有 editor 降级为 viewer
  ↓
Drive.drives.update → 修改共享盘名称（加 [ARCHIVED] 前缀）
  - restrictions.driveMembersOnly: true
  - restrictions.copyRequiresWriterPermission: true
  ↓
Chat.spaces.messages.create → 通知相关团队
Gmail.messages.send → 发送归档确认邮件
```

**自然语言示例**：
> "把 Project-XYZ 的共享盘归档，所有人改为只读，通知团队"

---

#### 场景 24：邮件模板批量发送（Gmail send + Sheets）
**痛点**：药企需要向多个临床试验站点发送标准化通知（如方案修改通知、安全性更新），每封邮件需要个性化站点信息。

**API 联动**：
```
Sheets.values.get → 读取站点联系人表（站点名、PI 邮箱、项目编号...）
  ↓
AI 根据模板 + 站点信息生成个性化邮件内容
  ↓
Gmail.drafts.create (循环) → 为每个站点创建草稿
  ↓
用户批量预览草稿
  ↓
Gmail.drafts.send (循环) → 批量发送
```

**为什么不适合 CLI 但适合 AI**：
- 邮件内容需要根据站点情况个性化（不同站点可能有不同的方案版本）
- 草稿预览环节提供安全保障
- 需要处理发送失败和重试

**自然语言示例**：
> "用站点联系人表，给所有活跃站点的 PI 发送方案修改通知，先创建草稿让我确认"

---

#### 场景 25：Chat 消息情绪分析 + 团队健康度（Chat reactions + messages）
**痛点**：管理者想了解团队沟通氛围，但无法量化分析 Chat 中的互动质量。

**API 联动**：
```
Chat.spaces.messages.list → 拉取指定时间段的消息
  ↓
Chat.spaces.messages.reactions.list → 获取每条消息的表情反应
  ↓
AI 分析：
  - 消息活跃度趋势（每日/每周消息量）
  - 表情反应分布（正面 vs 负面）
  - 回复率（发起讨论 vs 无人回应的比例）
  - 关键话题提取
  ↓
Sheets.values.update → 生成分析数据
Sheets.batchUpdate (addChart) → 可视化图表
Chat.spaces.messages.create → 在群里发送周报卡片
```

**自然语言示例**：
> "分析 CDE Community 群过去一个月的沟通情况，生成团队互动健康度报告"

---

#### 场景 26：Drive 标签分类治理（Drive labels + files.modifyLabels）
**痛点**：药企需要对 Drive 文件按合规分类（如 Confidential / Internal / Public），目前依赖人工标记，覆盖率低。

**API 联动**：
```
Drive.files.list → 全量扫描文件
  ↓
Drive.files.listLabels → 检查已有标签
  ↓
AI 分析文件名、路径、内容，推断分类：
  - 含 "protocol" / "SAE" / "SUSAR" → Confidential
  - 含 "training" / "onboarding" → Internal
  - 含 "publication" / "poster" → Public
  ↓
Drive.files.modifyLabels → 批量打标签
  ↓
Sheets.values.update → 生成分类报告
```

**自然语言示例**：
> "扫描 Clinical Documents 文件夹，根据文件内容自动打上保密等级标签，生成分类报告"

---

## 三、跨 API 联动场景

> 以下场景展示 Drive/Gmail/Chat 与已有 Sheets/Slides/Docs/Calendar API 的深度联动。

### 联动 A：端到端项目启动自动化（7 API 全联动）

```
用户: "启动 Project-ABC 临床试验项目"
  ↓
1. Drive.files.copy → 从模板复制项目文件夹结构
2. Drive.permissions.create → 设置团队权限
3. Sheets.create + values.update → 创建项目追踪表
4. Docs.create + batchUpdate → 创建项目章程文档
5. Calendar.events.insert → 创建 Kick-off 会议
6. Chat.spaces.setup → 创建项目 Chat 群 + 添加成员
7. Chat.spaces.messages.create → 发送欢迎消息（含所有链接）
8. Gmail.messages.send → 给外部合作方发送项目启动通知
```

### 联动 B：文档审阅闭环（Drive + Gmail + Chat + Docs）

```
1. Docs.get → 读取待审阅文档
2. Drive.approvals.start → 发起审批
3. Chat.spaces.messages.create → 在群里通知审阅者
4. Gmail.messages.send → 发送审阅邀请邮件
   ↓ (审阅过程中)
5. Drive.comments.list → 汇总审阅意见
6. Drive.approvals.get → 检查审批状态
7. Chat.spaces.messages.create → 催促未完成的审阅者
   ↓ (审阅完成后)
8. Drive.comments.list → 汇总所有评论
9. Docs.batchUpdate → 根据评论修改文档
10. Drive.approvals.approve → 完成审批
11. Chat.spaces.messages.create → 通知团队审批完成
```

### 联动 C：邮件驱动的数据管道（Gmail + Drive + Sheets + Chat）

```
1. Gmail.messages.list → 搜索含特定附件的邮件
2. Gmail.messages.attachments.get → 提取附件（CSV/Excel）
3. Drive.files.create → 上传到 Drive
4. Sheets.values.update → 将数据写入汇总表
5. Sheets.batchUpdate (addChart) → 生成图表
6. Chat.spaces.messages.create → 在群里发送数据更新通知
```

### 联动 D：智能会议全流程（Calendar + Docs + Chat + Gmail + Drive）

```
会前:
1. Calendar.freebusy.query → 找空闲时间
2. Calendar.events.insert → 创建会议
3. Docs.create → 创建议程文档
4. Chat.spaces.messages.create → 在群里发送会议通知

会后:
5. Docs.batchUpdate → 写入会议纪要
6. Drive.permissions.create → 分享纪要给参会者
7. Gmail.messages.send → 发送纪要邮件
8. Sheets.values.append → 将 Action Items 写入追踪表
9. Chat.spaces.messages.create → 在群里发送纪要摘要
```

---

## 四、药企特色场景

| 场景 | 涉及 API | 药企特殊性 | 优先级 |
|------|---------|-----------|--------|
| **临床方案审批流** | Drive approvals + Gmail + Chat | 方案需要 Medical Monitor → RA → QA 三级审批，每级有不同的审阅重点 | 高 |
| **SUSAR 紧急通知** | Gmail send + Chat messages.create | 严重不良事件需要在 24h 内通知所有相关方，邮件+Chat 双通道确保送达 | 高 |
| **TMF 文档归档** | Drive files.copy + permissions + labels | Trial Master File 文档需要按 DIA 参考模型分类，设置只读权限，打上合规标签 | 高 |
| **供应商资质到期提醒** | Sheets + Gmail send + Chat | 供应商 GMP 证书/审计报告到期前 90/60/30 天自动发送提醒邮件和 Chat 通知 | 中 |
| **药物警戒邮件监控** | Gmail threads + attachments | 监控特定邮箱的 ICSR 报告邮件，提取附件，按严重程度分类标记 | 中 |
| **培训记录合规** | Drive permissions + Sheets + Gmail | GxP 培训完成后自动更新培训记录表，发送完成确认邮件，设置培训材料权限 | 中 |
| **变更控制文档包** | Drive files.copy + revisions + Docs | 变更控制需要冻结当前版本（keepForever）、创建变更评估文档、启动审批流 | 中 |
| **IND/NDA 提交文档检查** | Drive files.list + labels + comments | 提交前检查文档完整性、格式合规性、标签分类，在缺失文档上添加评论提醒 | 低 |
| **KOL 沟通记录** | Gmail threads + Sheets + Drive | 汇总与关键意见领袖的邮件往来，提取关键信息写入 CRM 追踪表 | 低 |
| **实验室数据邮件解析** | Gmail attachments + Sheets | 解析实验室发来的检测报告邮件附件（PDF/CSV），提取关键数据写入汇总表 | 低 |

---

## 五、能力覆盖总结

### 现有脚本 vs 未覆盖能力对比

| API | 已有脚本覆盖 | 未覆盖的高价值能力 | 扩展潜力 |
|-----|------------|------------------|---------|
| **Drive** | files.list/get/export/delete（治理扫描） | permissions（权限审计）、approvals（审批流）、comments（评论管理）、revisions（版本追踪）、files.copy（模板克隆）、labels（分类治理） | 极高 |
| **Gmail** | messages.list/get/modify、labels、filters（分流归档） | messages.send（发信）、drafts（草稿）、threads（线程摘要）、attachments（附件提取）、vacation（休假回复）、delegates（代理人） | 极高 |
| **Chat** | spaces.list、messages.list、members.list（消息摘要） | messages.create（主动通知）、spaces.setup（建群）、members.create/delete（成员管理）、reactions（表情分析）、media.upload（文件分享） | 高 |

### 推荐的工具封装优先级

```
Phase 1（社区核心 Demo）:
  已有: drive_scan, drive_export, drive_cleanup, gmail_triage, chat_digest, gmail_compose
  新增:
    - gmail_compose.py  → drafts.create/update/send + md SoT（已实现 2026-05-17，配套 .claude/skills/email-authoring）
    - chat_notify.py    → messages.create（主动通知 + 卡片消息）
    - drive_permissions.py → permissions.list/create/delete（权限审计）

Phase 2（跨 API 联动）:
    - drive_approvals.py → approvals.start/list/approve（审批流）
    - gmail_attachments.py → attachments.get + Drive upload（附件归档）
    - drive_revisions.py → revisions.list/get（版本追踪）

Phase 3（完整工作流）:
    - project_setup.py → 8 API 联动的项目启动自动化
    - doc_review.py → 文档审阅闭环
    - vacation_setup.py → 休假全自动配置
```

---

## 八、Cloud Search API

### 能力概述

Cloud Search 提供 Roche 内网（RocheHome）的统一搜索能力，覆盖 Google Sites、Drive 文档、Wiki (Confluence) 等已索引内容。

| 操作 | 端点 | AI Agent 价值 |
|------|------|--------------|
| 搜索查询 | `query.search` | 用自然语言搜索内部系统文档、培训材料、公告 |
| 搜索建议 | `query.suggest` | 输入时自动补全，提升搜索效率 |

### 自动化场景

| 场景 | 描述 | 复杂度 |
|------|------|--------|
| 内部文档检索 | "在 RocheHome 搜索 ROMINE 相关文档" | 低 |
| 知识库问答 | 搜索内部文档 → 提取关键信息 → 结构化回答 | 中 |
| 跨源信息汇总 | 搜索多个关键词 → 汇总来自不同 gSite 的结果 | 中 |

### 局限

- 只能搜索 RocheHome 已索引的内容，不覆盖所有 Roche 内部系统
- 返回的 URL 是 Google redirect 链接，需要解析 `url` 参数获取实际地址
- 返回的 snippet 是 HTML 片段，需要清理

详细的使用示例和前置配置见 [Cloud Search 集成文档](cloud-search.md)。

---

## 九、进阶：用官方 gws CLI

完成本 demo 的首次授权之后，可以用 Google 官方的 [`gws`](https://github.com/googleworkspace/cli) 做更复杂的操作。它是 Google DevRel 维护的 Rust CLI（Apache-2.0，~26k stars），覆盖**全部 Workspace API**，并且支持 NDJSON 流式分页、`schema` 自省、跨服务 helper（`+agenda` / `+triage` / `+weekly-digest` 等）—— 比我们 Python 脚本更适合临时查询和喂给 agent。

> 不替代本 demo：gws 不解决首次 OAuth 授权（Ona 的"浏览器→localhost→SSH 隧道"回调、build-cli 的 client JSON 配置都得先用 demo 的 `auth.py` 走通），也没有 Cloud Search (RocheHome) 的封装。先用 demo 完成 OAuth，再装 gws 做进阶。

### 安装（实测步骤）

`npm i -g @googleworkspace/cli` 在 Ona 容器里会失败（Node fetch 拉 release 二进制时网络出错）；curl 直装 release binary 最稳（build-cli WSL2 同样适用）：

```bash
curl -fsSL -o /tmp/gws.tar.gz \
  https://github.com/googleworkspace/cli/releases/download/v0.22.5/google-workspace-cli-x86_64-unknown-linux-gnu.tar.gz
tar -xzf /tmp/gws.tar.gz -C /tmp/
mkdir -p ~/.local/bin && cp /tmp/gws ~/.local/bin/
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"
gws --version  # gws 0.22.5
```

### 复用 demo 的 access token（零授权成本）

gws 用 `GOOGLE_WORKSPACE_CLI_TOKEN` 环境变量传入预获取的 access token。复用 demo 的 token——下面这行幂等触发 refresh，access token（1 小时寿命）过期会自动续期（别直接读 `/tmp/google_token.json` 的 token 字段，可能已过期）：

```bash
export GOOGLE_WORKSPACE_CLI_TOKEN=$(cd demos/google-workspace/scripts && python3 -c "from gw_client import get_credentials; print(get_credentials().token)")
```

### 实测可用的命令

```bash
# 通用 REST 调用（任何 API 任何方法都行）
gws drive files list --params '{"pageSize": 5}' --format table
gws sheets spreadsheets values get --params '{"spreadsheetId": "...", "range": "A1:C10"}'

# 高层 helper（多 API 编排好的常用工作流）
gws calendar +agenda                 # 今日日程
gws gmail +triage --max 10           # 未读邮件摘要
gws workflow +weekly-digest          # 本周会议 + 未读邮件统计
gws workflow +meeting-prep           # 下一场会的议程、参会者、关联文档
gws workflow +standup-report         # 站会汇报：今日会议 + 待办

# Schema 自省（不上手就能看清参数）
gws schema drive.files.list

# NDJSON 流式分页（适合喂给 agent 处理大数据集）
gws drive files list --page-all --page-limit 50 > files.ndjson
```

### 何时用 gws / 何时用 demo 脚本

gws vs demo/Python 的路由决策表是 SKILL 的「工具选择优先级」（agent SSOT）：`.claude/skills/google-workspace/SKILL.md`。一句话——一次性查询和标准工作流（议程 / 邮件摘要 / 周报）走 gws；Drive 治理 / Chat 摘要 / Forms 等已封装业务逻辑、Cloud Search、跨 API 编排、首次 OAuth 授权走 demo 脚本。

### 进一步看

- 完整命令列表：`gws --help`、`gws <service> --help`
- 95 个内置 Skills（每个 API 一份 SKILL.md）：仓库 `skills/` 目录
- 50 个 Recipes（具体场景的 cookbook）：仓库 `skills/recipe-*` 目录

