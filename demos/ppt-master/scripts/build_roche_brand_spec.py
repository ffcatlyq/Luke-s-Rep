#!/usr/bin/env python3
"""build_roche_brand_spec — 从 hub 的 Roche Blue SSOT token 派生一份 ppt-master 品牌 spec。

为什么存在:
  ppt-master(hugohe3/ppt-master)默认 free design,也支持"跟随品牌"。要让它出 Roche
  蓝风格,需要把品牌的颜色/字体/logo 喂给它。Roche Blue 在 hub 已经 codify 过一次
  (assets/roche-brand/tokens + slidev/themes/roche-blue),token 是 SSOT——本脚本从
  这套 token 派生一份 markdown brand spec,而不是另起一个会漂移的品牌定义。

  token 变了重跑本脚本即可,spec 自动跟上(SSOT 派生,不双写)。

用法:
  # 打到 stdout,重定向进你的 ppt-master 项目(spec 是派生物,不进 hub)
  python3 build_roche_brand_spec.py > ~/ppt-master/projects/<p>/roche-blue-brand-spec.md

  # 或写到指定文件
  python3 build_roche_brand_spec.py --out /path/to/roche-blue-brand-spec.md

  产物两种用法(见 ../docs/roche-adaptation.md):
    A. free design:generation 时把这份 spec 一起给 AI,让它按 Roche 蓝配色/字体排版
    B. create-template:先用 spec 做一个 seed .pptx,再跑上游 /create-template 解析成 bundle

纯标准库,无第三方依赖。不联网、不发数据——只读本地 token 文件。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def find_hub_root(start: Path) -> Path:
    """从脚本位置向上找 hub 根(以 assets/roche-brand 为锚)。"""
    for p in [start, *start.parents]:
        if (p / "assets" / "roche-brand" / "tokens" / "colors.json").is_file():
            return p
    raise SystemExit(
        "error: 找不到 hub 根(assets/roche-brand/tokens/colors.json)。"
        "请在 hub 仓库内运行本脚本。"
    )


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise SystemExit(f"error: 缺 SSOT 文件 {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def rel(root: Path, *parts: str) -> str:
    """返回相对 hub 根的 posix 路径,方便 spec 里引用。"""
    return (root.joinpath(*parts)).relative_to(root).as_posix()


def resolve_logo(root: Path) -> str | None:
    """优先蓝色 logo 800px png;找不到退回任一蓝色 png。"""
    logos = root / "assets" / "roche-brand" / "logos"
    preferred = logos / "Roche_Logo_800px_Blue_RGB_800px.png"
    if preferred.is_file():
        return rel(root, "assets", "roche-brand", "logos", preferred.name)
    for cand in sorted(logos.glob("*Blue*RGB*.png")):
        return rel(root, "assets", "roche-brand", "logos", cand.name)
    return None


def build_spec(root: Path) -> str:
    colors = load_json(root / "assets" / "roche-brand" / "tokens" / "colors.json")
    typo = load_json(root / "assets" / "roche-brand" / "tokens" / "typography.json")
    theme = load_json(root / "slidev" / "themes" / "roche-blue" / "tokens.json")

    primary = colors["primary"]["roche_blue"]["hex"]
    primary_hover = colors["primary"]["roche_blue_hover"]["hex"]
    callout = colors["callout"]
    neutral = colors["neutral"]
    theme_colors = theme["colors"]
    scale = typo["type_scale"]

    logo_rel = resolve_logo(root)
    fonts_dir = rel(root, "assets", "roche-brand", "fonts", "roche-sans")

    lines: list[str] = []
    a = lines.append

    a("# Roche Blue — ppt-master brand spec")
    a("")
    a("> 本文件由 `demos/ppt-master/scripts/build_roche_brand_spec.py` 从 hub 的 Roche Blue")
    a("> SSOT token 自动派生。**不要手改**——改 token 后重跑脚本。")
    a(">")
    a(f"> 来源 SSOT:`assets/roche-brand/tokens/`(官方)+ `slidev/themes/roche-blue/tokens.json`")
    a("")
    a("把这份 spec 交给 ppt-master:让它生成的 deck 用下面的配色、字体与 logo。")
    a("用法(free design vs create-template)见 `docs/roche-adaptation.md`。")
    a("")

    a("## 主色(唯一品牌主色)")
    a("")
    a("| 角色 | Hex | 说明 |")
    a("|---|---|---|")
    a(f"| Primary(Roche Blue) | `{primary}` | 唯一品牌主色;标题强调、链接、logo 色 |")
    a(f"| Primary hover | `{primary_hover}` | 交互 hover 态 |")
    a("")
    a("Roche 品牌只有一个主色。**不要**自造第二主色或渐变堆叠——克制留白是 Roche 视觉核心。")
    a("")

    a("## 语义色(callout / 状态)")
    a("")
    a("| 语义 | Hex | 用途 |")
    a("|---|---|---|")
    a(f"| Positive / success | `{callout['tip']['hex']}` | 正向、成功、提示 |")
    a(f"| Neutral info | `{callout['info']['hex']}` | 中性信息 |")
    a(f"| Note | `{callout['note']['hex']}` | 软提醒 |")
    a(f"| Warning / danger | `{callout['warning']['hex']}` | 警告、错误 |")
    a("")

    a("## 中性色(文字 / 背景)")
    a("")
    a("| 角色 | Hex | 用途 |")
    a("|---|---|---|")
    a(f"| 正文/标题文字 | `{neutral['text_primary']['hex']}` | H1-H3、正文、主导航 |")
    a(f"| 次级文字 | `{neutral['text_secondary']['hex']}` | 图注、次级导航 |")
    a(f"| 深色背景(section 页) | `{neutral['background_dark']['hex']}` | 暗色分节页背景 |")
    a(f"| 浅色面板背景 | `{neutral['ui_subtle']['hex']}` | 通知/面板底 |")
    a("")
    a("演示场景补充(来自 slidev roche-blue 主题,与官方 token 一致取向):")
    a("")
    a(f"- 页面背景(亮):`{theme_colors['bg']}`")
    a(f"- section 页背景(暗):`{theme_colors['bgSection']}`")
    a(f"- 边框:`{theme_colors['border']}` / 面板:`{theme_colors['surface']}`")
    a("")

    a("## 字体")
    a("")
    a("| 用途 | 字体 | 字重 |")
    a("|---|---|---|")
    a(f"| 标题 H1 | {scale['heading1']['family']} | {scale['heading1']['weight']}(Light) |")
    a(f"| 标题 H2/H3 | {scale['heading2']['family']} | {scale['heading2']['weight']}(Light) |")
    a(f"| 正文 | {scale['body']['family']} | {scale['body']['weight']}(Light) |")
    a(f"| 引用 | {scale['quote']['family']} | {scale['quote']['weight']} italic |")
    a("| CJK 回退 | Noto Sans SC | — |")
    a("")
    a("Roche 标题惯用 **Light 字重**(不是 Bold),这是 Roche 排版的辨识点。")
    a("")
    a(f"字体文件(hub 内已 vendored,woff2):`{fonts_dir}/`")
    a("- RocheSans-Light / Regular / Medium / Bold")
    a("")
    a("> 生成 .pptx 时,PowerPoint 用 ttf/otf 而非 woff2。如需嵌入字体,先把 woff2 转 ttf")
    a("> (`fonttools`),或在目标机装 Roche Sans。**外发给外部方需对方自备 Roche 字体**")
    a("> (字体有分发许可限制),否则回退系统 sans。")
    a("")

    a("## Logo")
    a("")
    if logo_rel:
        a(f"蓝色 logo(用于亮底页):`{logo_rel}`")
    else:
        a("(未在 assets/roche-brand/logos/ 找到蓝色 logo png)")
    a("")
    a("同目录另有 Black / White RGB 版与多尺寸,暗色 section 页用 White 版。")
    a("logo 放右上或左上角,留足边距,不拉伸不改色。")
    a("")

    a("## 排版取向(Roche 视觉基调)")
    a("")
    a("- 白底为主,大量留白;section 分节页用深色背景反差")
    a("- 单主色克制点缀,不满屏蓝")
    a("- 标题 Light 字重、字号大;正文小而清晰")
    a("- 无 emoji(Roche brand 明确禁用);图标用 outline 线性风(carbon/tabler)")
    a("")

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="从 Roche Blue SSOT token 派生 ppt-master brand spec")
    ap.add_argument("--out", type=Path, help="输出文件路径(默认打到 stdout)")
    args = ap.parse_args()

    root = find_hub_root(Path(__file__).resolve().parent)
    spec = build_spec(root)

    if args.out:
        args.out.write_text(spec, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(spec)


if __name__ == "__main__":
    main()
