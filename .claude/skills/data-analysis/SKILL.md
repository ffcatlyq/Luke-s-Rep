---
name: data-analysis
description: >
  销售/市场数据分析：读 CSV/Excel（销售、份额、IQVIA/Veeva 导出、医院分级表）→
  清洗、透视、达成分析、趋势、图表。服务销售管理与区域市场人群的数据决策，
  是 performance-review / territory-management 技能的数据引擎。
  Use when the user needs to analyze a sales/market spreadsheet, build a pivot,
  compute achievement/growth, rank territories or hospitals, or make charts from data.
  Triggers on "分析数据", "读这个 excel", "拉个透视", "达成分析", "环比同比",
  "画个图", "data analysis", "pivot", "csv", "xlsx", "销售数据", "份额分析".
---

# 销售 / 市场数据分析（Data Analysis）

把一个 Excel/CSV 变成可决策的数字与图——清洗、透视、达成、趋势、可视化。

## 何时用

用户给出（或指向）表格数据，需要计算、透视、排名或作图时。常作为 `performance-review`（达成归因）与 `territory-management`（辖区/覆盖）业务技能的**数据引擎**：业务技能负责解读，本技能负责算数与作图。

## 依赖

需要 `pandas` + `openpyxl`（读 xlsx）+ `matplotlib`（作图）。缺失时先装：

```bash
pip3 install --break-system-packages pandas openpyxl matplotlib
```

## 工作流

1. **拿到数据**：
   - 本地文件 → 直接读路径。
   - Google Drive 文件 → 先用 `google-workspace` 技能下载到本地（见其 SKILL.md），再读。
2. **探查结构**：先看工作表名、表头、行列数、字段类型，不要盲算。用 `scripts/inspect_data.py`。
3. **清洗**：处理空值、类型、重复、口径统一（先和用户确认口径）。
4. **分析**：透视 / 达成率 / 环比同比 / 排名 / 分组聚合。用 `scripts/analyze.py` 作起点，按需改。
5. **可视化**（可选）：条形/折线/饼图，输出 PNG。
6. **落盘**：分析结果存 `outputs/` 或临时目录，作为业务技能的输入。

## 常见分析（血液 CE 场景）

维度定义见 `knowledge-packs/hematology/customers/segmentation.md`：
- **达成分析**：实际/目标，按大区（东/南/西/北/中）、医院分级（C30/T70/T300）、产品、成员拆解。
- **覆盖分析**：目标医院覆盖率、覆盖漏斗转化。
- **趋势**：环比/同比、移动平均。
- **排名**：辖区/医院/成员 Top-Bottom。

## 合规注意

- ⚠️ **数据分级（敏感）**：销售数据、医院名单、成员业绩属敏感级。分析产出**不外传、不写入可外发产出、不进 git**；含明细的中间文件用完清理。
- 图表/结论若要对外或汇报，先脱敏（去具体医院名/个人名），并走对应业务技能的合规检查。

## 参考文件（progressive disclosure）

| 需要 | 用这个 |
|---|---|
| 探查表格结构（工作表/表头/类型） | `scripts/inspect_data.py` |
| 通用分析起点（透视/达成/趋势/图表） | `scripts/analyze.py` |
| 分析配方（各类分析的 pandas 写法） | `references/recipes.md` |
