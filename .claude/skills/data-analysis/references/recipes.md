# 分析配方（pandas）

常见分析的写法，按需复制改。前提：`import pandas as pd`，`df` 已加载。

## 读数据

```python
df = pd.read_csv("data.csv")                    # CSV
df = pd.read_excel("data.xlsx", sheet_name="T300")  # Excel 指定表
xls = pd.ExcelFile("data.xlsx"); xls.sheet_names # 列出工作表
```

## 清洗

```python
df.columns = df.columns.str.strip()             # 去表头空格
df = df.dropna(subset=["医院编码"])              # 删关键列空行
df["实际"] = pd.to_numeric(df["实际"], errors="coerce")  # 转数值
df = df.drop_duplicates(subset=["医院编码"])     # 去重
```

## 分组透视

```python
df.groupby("销售大区")["实际"].sum().sort_values(ascending=False)
df.pivot_table(index="销售大区", columns="分级", values="实际", aggfunc="sum", margins=True)
df.groupby(["销售大区", "分级"]).agg(医院数=("医院编码","nunique"), 销量=("实际","sum"))
```

## 达成分析

```python
g = df.groupby("销售大区")[["实际","目标"]].sum()
g["达成率%"] = (g["实际"] / g["目标"] * 100).round(1)
g["差距"] = g["实际"] - g["目标"]
```

## 环比 / 同比 / 趋势

```python
m = df.groupby("月份")["实际"].sum().sort_index()
m_mom = m.pct_change() * 100                     # 环比
m_yoy = m.pct_change(periods=12) * 100           # 同比（月度数据）
m_ma3 = m.rolling(3).mean()                      # 3 期移动平均
```

## 排名 / Top-Bottom

```python
r = df.groupby("辖区")["实际"].sum().sort_values(ascending=False)
r.head(5)     # Top 5
r.tail(5)     # Bottom 5
df["排名"] = df["实际"].rank(ascending=False, method="min")
```

## 覆盖分析（漏斗）

```python
funnel = {
    "目标医院": df["医院编码"].nunique(),
    "已覆盖":  df.loc[df["已拜访"]=="是","医院编码"].nunique(),
    "已进药":  df.loc[df["进药"]=="是","医院编码"].nunique(),
    "有处方":  df.loc[df["处方"]=="是","医院编码"].nunique(),
}
# 逐级转化率
vals = list(funnel.values())
conv = [None] + [round(vals[i]/vals[i-1]*100,1) for i in range(1,len(vals))]
```

## 中文图表（避免乱码）

```python
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False
```

## 血液 CE 常用维度

- 销售大区：东 / 南 / 西 / 北 / 中
- 医院分级：C30 / T70 / T300（嵌套，见 `knowledge-packs/hematology/customers/segmentation.md`）
- 产品：rituximab / obinutuzumab / polatuzumab_vedotin / glofitamab / mosunetuzumab / emicizumab

> ⚠️ 含明细的敏感数据分析产出不进 git、不外发；中间文件用完清理。
