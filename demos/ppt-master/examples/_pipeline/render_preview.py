#!/usr/bin/env python3
"""render_preview.py — 把 exemplar 的 SVG 渲染成 PNG 预览。

cairosvg 关键坑(必须知道,否则 logo/封面底图/公式图全渲染不出来):
  1. unsafe=True 必开——cairosvg 默认禁止加载外部 file 图片(安全策略),
     <image href=...> 的 logo / cover_bg / formula 会静默不渲染(白块)。
  2. 字体 per-glyph 不回退——cairosvg 用 cairo toy font API,字体栈第一个"存在的
     字体"整段套用,缺的字形渲成空心圈(tofu)。故:纯拉丁行 Roche Sans 首位;
     含 CJK 行把 'Noto Sans CJK SC' 放首位;Roche Sans 缺 → 把箭头包进 mono tspan。
  3. 字重只认 normal/bold——font-weight:300 在 cairosvg 里不是 Light!要真 Light
     必须用独立 family 名 'Roche Sans Light'(同理 'Roche Sans Medium'/'Roche Serif Light')。
  4. text-anchor="middle" 的 <text> 里含改 font-family / baseline-shift 的 tspan 会
     算错宽度→文字甩偏。居中文本只用"改颜色"的 tspan;要上下标/换字体的行用
     text-anchor="start" 手动定 x。

这里渲染的是 svg_final(finalize 后的,圆角 rect 已转 path、图已对齐);也可直接渲
svg_output。pptx 的真实排版由 svg_to_pptx 生成,预览只是快速视觉校对。

用法:
    python3 render_preview.py --in <svg文件或目录> --out <png输出目录> [--width 1280 --height 720]
"""
import argparse
import glob
import os


def render_one(src: str, out: str, w: int, h: int) -> None:
    import cairosvg
    cairosvg.svg2png(url=src, write_to=out, output_width=w, output_height=h, unsafe=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render exemplar SVG(s) to PNG (cairosvg, unsafe=True)")
    ap.add_argument("--in", dest="inp", required=True, help="SVG file or directory of *.svg")
    ap.add_argument("--out", required=True, help="output directory")
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=720)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    srcs = ([args.inp] if args.inp.endswith(".svg")
            else sorted(glob.glob(os.path.join(args.inp, "*.svg"))))
    for s in srcs:
        dst = os.path.join(args.out, os.path.basename(s)[:-4] + ".png")
        render_one(s, dst, args.width, args.height)
        print(f"rendered -> {dst}")
