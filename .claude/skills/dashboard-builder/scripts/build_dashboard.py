#!/usr/bin/env python3
"""从 JSON spec 生成自包含 HTML 仪表盘（KPI 卡片 + 内嵌图表）。

产出是单个 HTML 文件：图表以 base64 PNG 内嵌，无外部依赖，可离线打开、截图进汇报。

用法:
    python3 build_dashboard.py spec.json --out outputs/dashboard.html

spec 格式见 references/spec-format.md。最小示例:
    {
      "title": "Q3 血液业绩看板",
      "subtitle": "2026 Q3 · 内部使用",
      "kpis": [
        {"label": "总达成率", "value": "104%", "delta": "+6pp", "trend": "up"},
        {"label": "销售额(万)", "value": "12,340", "delta": "+8% QoQ", "trend": "up"}
      ],
      "charts": [
        {"type": "bar",  "title": "各大区达成率",
         "labels": ["东","南","西","北","中"], "values": [104,98,92,110,101]},
        {"type": "line", "title": "月度销售趋势",
         "labels": ["M1","M2","M3"], "values": [3800,4100,4440]},
        {"type": "pie",  "title": "产品份额",
         "labels": ["A","B","C"], "values": [45,35,20]}
      ]
    }

合规：销售/医院/成员数据敏感——产出默认内部使用，不外传、不进 git，对外先脱敏。
"""
import argparse
import base64
import html
import io
import json
import sys
from pathlib import Path


def _lazy_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError:
        sys.exit("需要 matplotlib：pip3 install --break-system-packages matplotlib")


# Roche-ish palette (蓝为主)
PALETTE = ["#0B41CD", "#1482FA", "#00B8B0", "#7D3F98", "#F59E0B", "#EF4444", "#64748B"]


def render_chart(chart, plt):
    """把一个 chart spec 渲染成 base64 PNG data URI。"""
    ctype = chart.get("type", "bar")
    labels = chart.get("labels", [])
    values = chart.get("values", [])
    title = chart.get("title", "")

    fig, ax = plt.subplots(figsize=(5.2, 3.2), dpi=110)

    if ctype == "bar":
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
        bars = ax.bar(labels, values, color=colors)
        for b, v in zip(bars, values):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height(),
                    f"{v}", ha="center", va="bottom", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    elif ctype == "line":
        ax.plot(labels, values, marker="o", color=PALETTE[0], linewidth=2)
        for x, v in zip(labels, values):
            ax.text(x, v, f"{v}", ha="center", va="bottom", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    elif ctype == "pie":
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
        ax.pie(values, labels=labels, autopct="%1.0f%%", colors=colors,
               textprops={"fontsize": 8})
        ax.axis("equal")
    elif ctype == "barh":
        colors = [PALETTE[i % len(PALETTE)] for i in range(len(values))]
        ax.barh(labels, values, color=colors)
        ax.invert_yaxis()
        for i, v in enumerate(values):
            ax.text(v, i, f" {v}", va="center", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    else:
        sys.exit(f"不支持的图表类型: {ctype}（支持 bar/barh/line/pie）")

    if title:
        ax.set_title(title, fontsize=11, fontweight="bold")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def kpi_card_html(kpi):
    label = html.escape(str(kpi.get("label", "")))
    value = html.escape(str(kpi.get("value", "")))
    delta = html.escape(str(kpi.get("delta", "")))
    trend = kpi.get("trend", "")
    arrow = {"up": "▲", "down": "▼"}.get(trend, "")
    dcls = {"up": "up", "down": "down"}.get(trend, "flat")
    delta_html = f'<div class="delta {dcls}">{arrow} {delta}</div>' if delta else ""
    return f"""
      <div class="card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
      </div>"""


def chart_card_html(title, data_uri):
    title = html.escape(str(title))
    return f"""
      <div class="card chart-card">
        <img alt="{title}" src="{data_uri}" />
      </div>"""


CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
         background: #F1F5F9; color: #0F172A; padding: 24px; }
  header { margin-bottom: 20px; }
  h1 { font-size: 22px; color: #0B41CD; }
  .subtitle { color: #64748B; font-size: 13px; margin-top: 4px; }
  .banner { background: #FEF3C7; border: 1px solid #F59E0B; color: #92400E;
            font-size: 12px; padding: 8px 12px; border-radius: 6px; margin: 12px 0; }
  .grid { display: grid; gap: 16px; }
  .kpi-grid { grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-bottom: 16px; }
  .chart-grid { grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); }
  .card { background: #fff; border-radius: 10px; padding: 18px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .kpi-label { font-size: 13px; color: #64748B; }
  .kpi-value { font-size: 30px; font-weight: 700; margin-top: 6px; color: #0F172A; }
  .delta { font-size: 12px; margin-top: 4px; font-weight: 600; }
  .delta.up { color: #059669; }
  .delta.down { color: #DC2626; }
  .delta.flat { color: #64748B; }
  .chart-card img { width: 100%; height: auto; display: block; }
  footer { margin-top: 20px; color: #94A3B8; font-size: 11px; }
"""


def build_html(spec, plt):
    title = html.escape(str(spec.get("title", "仪表盘")))
    subtitle = html.escape(str(spec.get("subtitle", "")))
    banner = spec.get("banner", "⚠️ 内部使用 — 含敏感数据，勿外发、勿进 git")

    kpis = spec.get("kpis", [])
    charts = spec.get("charts", [])

    kpi_html = "".join(kpi_card_html(k) for k in kpis)
    chart_html = "".join(
        chart_card_html(c.get("title", ""), render_chart(c, plt)) for c in charts
    )

    subtitle_html = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    banner_html = f'<div class="banner">{html.escape(str(banner))}</div>' if banner else ""
    kpi_section = f'<div class="grid kpi-grid">{kpi_html}</div>' if kpi_html else ""
    chart_section = f'<div class="grid chart-grid">{chart_html}</div>' if chart_html else ""

    return f"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    {subtitle_html}
    {banner_html}
  </header>
  {kpi_section}
  {chart_section}
  <footer>由 dashboard-builder 生成 · 图表内嵌 · 可离线打开</footer>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description="从 JSON spec 生成自包含 HTML 仪表盘")
    ap.add_argument("spec", help="仪表盘 spec（JSON 文件路径，或 '-' 读 stdin）")
    ap.add_argument("--out", default="outputs/dashboard.html", help="输出 HTML 路径")
    args = ap.parse_args()

    if args.spec == "-":
        spec = json.load(sys.stdin)
    else:
        p = Path(args.spec)
        if not p.exists():
            sys.exit(f"spec 文件不存在: {p}")
        spec = json.loads(p.read_text(encoding="utf-8"))

    plt = _lazy_matplotlib()
    doc = build_html(spec, plt)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")
    print(f"已生成: {out}  ({len(doc)} 字节, "
          f"{len(spec.get('kpis', []))} KPI, {len(spec.get('charts', []))} 图)")


if __name__ == "__main__":
    main()
