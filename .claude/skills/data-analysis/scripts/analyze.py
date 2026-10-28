#!/usr/bin/env python3
"""通用分析起点——达成分析 + 分组透视 + 可选图表。

这是一个可改的起点，不是万能 CLI。按实际数据结构调整列名与逻辑。

用法示例:
    # 按某列分组求和
    python3 analyze.py data.xlsx --sheet T300 --group 销售大区 --value 实际

    # 达成分析（需 目标列 与 实际列）
    python3 analyze.py sales.csv --group 大区 --actual 实际 --target 目标

    # 加图（条形图，输出 PNG 到 outputs/）
    python3 analyze.py sales.csv --group 大区 --value 实际 --chart bar --out outputs/by_region.png
"""
import argparse
import sys
from pathlib import Path


def load(path, sheet):
    import pandas as pd
    p = Path(path)
    if not p.exists():
        sys.exit(f"文件不存在: {p}")
    if p.suffix.lower() == ".csv":
        return pd.read_csv(p)
    return pd.read_excel(p, sheet_name=sheet or 0)


def main():
    ap = argparse.ArgumentParser(description="通用分析起点")
    ap.add_argument("file")
    ap.add_argument("--sheet", help="Excel 工作表名")
    ap.add_argument("--group", help="分组列")
    ap.add_argument("--value", help="求和的数值列")
    ap.add_argument("--actual", help="达成分析：实际列")
    ap.add_argument("--target", help="达成分析：目标列")
    ap.add_argument("--chart", choices=["bar", "line", "pie"], help="图表类型")
    ap.add_argument("--out", help="图表输出路径（PNG）")
    args = ap.parse_args()

    try:
        import pandas as pd  # noqa: F401
    except ImportError:
        sys.exit("需要 pandas：pip3 install --break-system-packages pandas openpyxl matplotlib")

    df = load(args.file, args.sheet)

    # 达成分析
    if args.actual and args.target:
        g = df.groupby(args.group) if args.group else df
        if args.group:
            res = g[[args.actual, args.target]].sum()
            res["达成率"] = (res[args.actual] / res[args.target] * 100).round(1)
        else:
            a, t = df[args.actual].sum(), df[args.target].sum()
            res = pd.DataFrame({args.actual: [a], args.target: [t],
                                "达成率": [round(a / t * 100, 1)]})
        print(res.to_string())
        _maybe_chart(args, res, "达成率" if args.group else args.actual)
        return

    # 分组求和
    if args.group and args.value:
        res = df.groupby(args.group)[args.value].sum().sort_values(ascending=False)
        print(res.to_string())
        print(f"\n合计: {res.sum()}")
        _maybe_chart(args, res, args.value)
        return

    print("提示：给 --group + --value 做分组求和，或 --group + --actual + --target 做达成分析。")
    print(f"可用列: {list(df.columns)}")


def _maybe_chart(args, res, ylabel):
    if not args.chart:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Noto Sans CJK SC", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    series = res[ylabel] if hasattr(res, "columns") and ylabel in getattr(res, "columns", []) else res
    fig, ax = plt.subplots(figsize=(8, 5))
    if args.chart == "bar":
        series.plot(kind="bar", ax=ax)
    elif args.chart == "line":
        series.plot(kind="line", marker="o", ax=ax)
    elif args.chart == "pie":
        series.plot(kind="pie", ax=ax, autopct="%1.1f%%")
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    out = args.out or "outputs/chart.png"
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out, dpi=120)
    print(f"\n图表已保存: {out}")


if __name__ == "__main__":
    main()
