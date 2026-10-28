#!/usr/bin/env python3
"""探查表格结构——分析前先看清楚，不要盲算。

用法:
    python3 inspect_data.py <file.xlsx|file.csv> [sheet]

注意：文件名刻意不叫 inspect.py，避免遮蔽 Python 标准库的 inspect 模块
（numpy/pandas 内部会 import inspect，同名会导致 AttributeError）。

输出每个工作表的：形状、列名、每列类型、非空计数、前几行样本。
"""
import sys
from pathlib import Path


def inspect_df(df, name):
    print(f"===== [{name}]  shape={df.shape[0]}行 x {df.shape[1]}列 =====")
    print("列:")
    for col in df.columns:
        nn = df[col].notna().sum()
        dtype = str(df[col].dtype)
        sample = df[col].dropna().head(2).tolist()
        print(f"  - {col!r:30} type={dtype:10} 非空={nn:<6} 样本={sample}")
    print("前 3 行:")
    print(df.head(3).to_string(max_colwidth=20))
    print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    try:
        import pandas as pd
    except ImportError:
        sys.exit("需要 pandas：pip3 install --break-system-packages pandas openpyxl")

    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"文件不存在: {path}")

    if path.suffix.lower() == ".csv":
        inspect_df(pd.read_csv(path), path.name)
    else:
        sheet = sys.argv[2] if len(sys.argv) > 2 else None
        xls = pd.ExcelFile(path)
        print(f"工作表: {xls.sheet_names}\n")
        sheets = [sheet] if sheet else xls.sheet_names
        for s in sheets:
            try:
                inspect_df(pd.read_excel(path, sheet_name=s), s)
            except Exception as e:  # noqa: BLE001
                print(f"[{s}] 读取失败: {e}\n")


if __name__ == "__main__":
    main()
