#!/usr/bin/env python3
"""比值/RR 算式交叉验证 —— OCR 读数的第二路径。

思路: 读出的 RR/比例值，用其组成部分独立算一遍，对不上就是读错了。
  ratio = numerator / denominator
  比例 = numerator / denominator

用法:
  python3 verify_ratio.py --num 12.5 --den 40.0 --claim 0.31
  # 算 12.5/40.0=0.3125，与 claim 0.31 比对

注意: CI 例外: 若源 CI 来自 对数尺度合成，不要用点估计除法反推 CI，
   除法会得到不同区间。此脚本只验证点估计比值。
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--num", type=float, required=True, help="分子")
    ap.add_argument("--den", type=float, required=True, help="分母")
    ap.add_argument("--claim", type=float, required=True, help="OCR 读出的比值")
    ap.add_argument("--tol", type=float, default=0.02, help="相对容差(默认2%)")
    a = ap.parse_args()

    calc = a.num / a.den
    rel = abs(calc - a.claim) / a.claim if a.claim else float("inf")
    ok = rel <= a.tol

    print(f"算式结果 : {a.num} / {a.den} = {calc:.4f}")
    print(f"OCR 读值 : {a.claim}")
    print(f"相对偏差 : {rel*100:.2f}%  (容差 {a.tol*100:.0f}%)")
    print("判定    :", "[一致] 读数可信" if ok
          else "[不一致] 很可能OCR读错，回到 crop_zoom 重读")
    if not ok:
        print("提示: 检查是否把相邻数字读错位、小数点漏读、或 9/7 3/8 等易混字符。")


if __name__ == "__main__":
    main()
