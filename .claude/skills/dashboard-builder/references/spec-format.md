# Dashboard spec 格式

`build_dashboard.py` 读一个 JSON spec，生成自包含 HTML。字段如下。

## 顶层字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `title` | 是 | 看板标题 |
| `subtitle` | 否 | 副标题（周期/范围/"内部使用"）|
| `banner` | 否 | 顶部提示条；默认已带"内部使用"合规提示，传空串 `""` 可去掉 |
| `kpis` | 否 | KPI 卡片数组 |
| `charts` | 否 | 图表数组 |

## KPI 卡片（`kpis[]`）

| 字段 | 说明 |
|---|---|
| `label` | 指标名（如"总达成率"）|
| `value` | 主数值（字符串，可带单位/千分位，如 `"12,340"`、`"104%"`）|
| `delta` | 变化（如 `"+8% QoQ"`）|
| `trend` | `up` / `down` / 省略——决定箭头与颜色（绿升红降）|

## 图表（`charts[]`）

| 字段 | 说明 |
|---|---|
| `type` | `bar`（竖条）/ `barh`（横条，适合排名）/ `line`（趋势）/ `pie`（份额）|
| `title` | 图标题 |
| `labels` | 类目/x 轴标签数组 |
| `values` | 对应数值数组（与 labels 等长）|

## 完整示例

```json
{
  "title": "Q3 血液业绩看板",
  "subtitle": "2026 Q3 · 5 大区 · 内部使用",
  "kpis": [
    {"label": "总达成率", "value": "104%", "delta": "+6pp QoQ", "trend": "up"},
    {"label": "销售额(万)", "value": "12,340", "delta": "+8% QoQ", "trend": "up"},
    {"label": "T100 覆盖率", "value": "92%", "delta": "-1pp", "trend": "down"},
    {"label": "活跃讲者", "value": "48", "delta": "+5", "trend": "up"}
  ],
  "charts": [
    {"type": "bar",  "title": "各大区达成率(%)",
     "labels": ["东","南","西","北","中"], "values": [104, 98, 92, 110, 101]},
    {"type": "line", "title": "月度销售趋势(万)",
     "labels": ["M1","M2","M3"], "values": [3800, 4100, 4440]},
    {"type": "barh", "title": "Top5 辖区销售(万)",
     "labels": ["辖区A","辖区B","辖区C","辖区D","辖区E"], "values": [980, 910, 870, 840, 790]},
    {"type": "pie",  "title": "产品份额(%)",
     "labels": ["产品A","产品B","产品C"], "values": [45, 35, 20]}
  ]
}
```

## 从 data-analysis 到 spec

典型流程：`data-analysis` 算出数字 → 手工或脚本填进 spec → `build_dashboard.py` 出 HTML。
数字放 spec 前先脱敏（对外时去具体医院名/人名，改用分级或代号）。
