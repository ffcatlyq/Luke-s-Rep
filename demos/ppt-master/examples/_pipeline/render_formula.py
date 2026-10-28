#!/usr/bin/env python3
"""render_formula.py — 把 LaTeX 数学公式渲染成 Roche Blue 透明 PNG。

技术公式格(以及任何有块级公式的 deck)用它替代"通用字体 inline 排数学"——
通用文本字体(Roche Sans/Serif、Georgia)排不出规范数学(斜体变量、正体函数名、
真正的分式/根号)。这里用 matplotlib 内置的 Computer Modern(LaTeX 经典数学体),
不依赖系统安装 LaTeX。产物是透明底 PNG,SVG 里 <image> 引它、finalize 时嵌入 pptx。

取舍:块公式=图片(不可编辑),换来数学规范。行内小数学(d_model=512、O(n))仍用
可编辑 text。可编辑的 PowerPoint 原生公式(OMML)是 follow-up,见 examples/README.md。

用法:
    python3 render_formula.py --out formula.png \
        --expr '\\mathrm{Attention}(Q,K,V)=\\mathrm{softmax}\\!\\left(\\dfrac{QK^{\\mathsf{T}}}{\\sqrt{d_k}}\\right)V'
    # 不给 --expr 时渲染内置的 Attention 示例。

依赖:matplotlib(pip install matplotlib)。颜色默认 Roche Blue #0B41CD。
"""
import argparse

DEFAULT_EXPR = (
    r'\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\!'
    r'\left(\dfrac{QK^{\mathsf{T}}}{\sqrt{d_k}}\right)V'
)


def render(expr: str, out: str, color: str = "#0B41CD", fontsize: int = 34,
           dpi: int = 300, fontset: str = "cm") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["mathtext.fontset"] = fontset  # cm = Computer Modern (LaTeX 经典)
    fig = plt.figure(figsize=(9, 1.6))
    fig.text(0.5, 0.5, f"${expr}$", fontsize=fontsize, color=color,
             ha="center", va="center")
    fig.savefig(out, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Render a LaTeX formula to a Roche-Blue transparent PNG")
    ap.add_argument("--expr", default=DEFAULT_EXPR, help="LaTeX math body (no surrounding $)")
    ap.add_argument("--out", required=True, help="output PNG path")
    ap.add_argument("--color", default="#0B41CD", help="hex color (default Roche Blue)")
    ap.add_argument("--fontsize", type=int, default=34)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()
    render(args.expr, args.out, args.color, args.fontsize, args.dpi)
    print(f"rendered -> {args.out}")
