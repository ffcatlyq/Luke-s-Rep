---
name: dashboard-builder
description: >
  把销售/市场数据做成一页式仪表盘：KPI 卡片 + 图表（达成/趋势/排名/份额）
  → 自包含 HTML 文件，可离线打开、可截图、可嵌汇报。是 data-analysis 的呈现层，
  服务销售管理与区域市场的例会/复盘/汇报。
  Use when the user wants a dashboard, KPI overview, one-page visual summary,
  或把一堆数字做成"一眼看全"的仪表盘/看板 to share or screenshot.
  Triggers on "仪表盘", "看板", "dashboard", "KPI 面板", "数据大屏", "一页看全",
  "可视化汇总", "做个 dashboard", "业绩看板", "达成看板".
---

# 仪表盘生成（Dashboard Builder）

把散落的销售/市场数字，拼成一页"一眼看全"的仪表盘——KPI 卡片 + 关键图表，输出自包含 HTML，可离线打开、截图进汇报。

## 何时用

用户要"一页看全"而非逐项分析时：例会/复盘前做业绩看板、给管理层的 KPI 面板、区域达成一览。

- **本技能 = 呈现层**：负责把数字拼成好看、好读的一页。
- **算数交给 `data-analysis`**：清洗/透视/达成/趋势由它算，本技能拿结果作卡片和图。
- 分工：`data-analysis` 出数 → `dashboard-builder` 出面板 →（可选）进 `business-review`/`performance-review` 材料。

## 依赖

需要 `pandas`（读数）+ `matplotlib`（作图）。缺失时先装：

```bash
pip3 install --break-system-packages pandas openpyxl matplotlib
```

图表内嵌为 base64，产出是**单个 HTML 文件**，无外部依赖，可离线打开。

## 工作流

1. **拿到数据**：本地文件直接读；Google Drive 文件先用 `google-workspace` 下载。先用 `data-analysis` 的 `inspect_data.py` 探查结构，不盲做。
2. **和用户确认看板要素**（见下"看板要素"）：放哪些 KPI、哪些图、按什么维度。
3. **算数**：用 `data-analysis` 算出 KPI 值与各图的数据（达成率、环比、排名、份额）。
4. **写 spec**：把要素写成一个 JSON spec（见 `references/spec-format.md`）。
5. **生成**：`python3 scripts/build_dashboard.py spec.json --out outputs/dashboard.html`。
6. **落盘/交付**：存 `outputs/`；含敏感明细的默认内部使用，对外先脱敏。

## 看板要素

| 要素 | 例子 |
|---|---|
| KPI 卡片 | 总达成率、销售额、覆盖率、环比增长 |
| 达成图 | 各大区/产品达成率条形图 |
| 趋势图 | 月度销售/份额折线 |
| 排名图 | Top/Bottom 辖区或医院 |
| 份额图 | 产品/竞品份额饼图 |

维度定义（东/南/西/北/中，C30/T70/T300，6 产品）见 `knowledge-packs/hematology/customers/segmentation.md`。

## 合规注意

- ⚠️ **数据分级（敏感）**：销售数据、医院名单、成员业绩属敏感级。仪表盘 HTML **不外传、不进 git**；含明细的默认内部使用。
- 对外/上会前**脱敏**：去具体医院名、个人名，必要时改用分级/代号。
- 涉及产品声明/份额对比若对外，须循证、走 MLR，不夸大不 off-label。

## 参考文件（progressive disclosure）

| 需要 | 用这个 |
|---|---|
| 生成仪表盘（读 spec → HTML） | `scripts/build_dashboard.py` |
| spec JSON 格式与字段 | `references/spec-format.md` |
| 看板配方（各类卡片/图的组织） | `references/recipes.md` |
