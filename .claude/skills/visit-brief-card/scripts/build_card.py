#!/usr/bin/env python3
"""拜访信息卡生成器 —— 把 config JSON + 专家照片渲染成一页海报 PNG。

用法:
    python build_card.py --config card.json --template ../assets/template.html \
        --photo /path/to/photo.jpg --out /workspaces/.../outputs/<名字>拜访准备.png

config JSON 字段(全部为字符串,除 titles/purpose_items/team/tips 为数组):
    date_label       头部日期,如 "9月2日上午"
    hospital_dept    头部医院·科室行,如 "宁波市医疗中心李惠利医院 · 兴宁院区"
    theme            拜访主题一句话
    expert_line      拜访信息栏的对象行,如 "乐静 主任 ｜ 血液科"
    date_full        完整日期,如 "2026年9月2日(星期三)"
    time             拜访时间,如 "10:00"(橙色高亮)
    place            地点(医院/院区)
    location_detail  具体位置,如 "门诊楼 2 楼"
    wx_period        天气时段,"上午"/"下午"
    wx_temp          温度,如 "27°"
    wx_desc          天气描述 HTML(可含 <br> 和 <b>),如 "小雨 · 体感 31°<br>降水概率 <b>79%</b>..."
    expert_name      专家姓名
    expert_rank      职级,如 "主任医师"
    expert_hosp      名片下的医院·职务行
    titles           [学术任职...] 数组
    purpose_title    目的栏标题,如 "拜访目的" 或 "专家需求 · 拜访目的"
    purpose_bar      目的栏顶部聚焦条文案(可空字符串则不显示)
    purpose_items    [目的条...] 数组(自动编号)
    team             [拜访人员...] 数组
    tips             [出行提示 HTML...] 数组(可含 <b>)
    footer           脚注(数据来源+合规提示)

照片经 Pillow 压到 max 600x800、base64 内嵌,避免大图撑爆。
"""
import argparse, base64, html, json, sys
from pathlib import Path

PERSON_SVG = ('<svg viewBox="0 0 24 24" width="15" height="15">'
              '<circle cx="12" cy="8" r="4" fill="#1aa6ad"/>'
              '<path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7" fill="none" stroke="#1aa6ad" stroke-width="2"/></svg>')


def photo_data_uri(path: str) -> str:
    from PIL import Image
    import io
    im = Image.open(path)
    im.thumbnail((600, 800))
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=88)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}"


def build_html(cfg: dict, template: str, photo_uri: str) -> str:
    titles = "".join(f"<li>{html.escape(t)}</li>" for t in cfg.get("titles", []))
    team = "".join(
        f"<div class='pcell'>{PERSON_SVG}<span>{html.escape(p)}</span></div>"
        for p in cfg.get("team", [])
    )
    pitems = "".join(
        f'<div class="pitem"><span class="num">{i+1}</span><span>{html.escape(x)}</span></div>'
        for i, x in enumerate(cfg.get("purpose_items", []))
    )
    pbar = ""
    if cfg.get("purpose_bar"):
        pbar = f'<div class="pbar">{html.escape(cfg["purpose_bar"])}</div>'
    tips = ""
    for t in cfg.get("tips", []):
        tips += ('<li><svg class="ck" viewBox="0 0 24 24" width="18" height="18">'
                 '<path d="M5 12l4 4 10-10" fill="none" stroke="#1aa6ad" stroke-width="2.4" '
                 f'stroke-linecap="round"/></svg><span>{t}</span></li>')

    repl = {
        "{{DATE_LABEL}}": html.escape(cfg.get("date_label", "")),
        "{{HOSPITAL_DEPT}}": html.escape(cfg.get("hospital_dept", "")),
        "{{THEME}}": html.escape(cfg.get("theme", "")),
        "{{EXPERT_LINE}}": html.escape(cfg.get("expert_line", "")),
        "{{DATE_FULL}}": html.escape(cfg.get("date_full", "")),
        "{{TIME}}": html.escape(cfg.get("time", "")),
        "{{PLACE}}": html.escape(cfg.get("place", "")),
        "{{LOCATION_DETAIL}}": html.escape(cfg.get("location_detail", "")),
        "{{WX_PERIOD}}": html.escape(cfg.get("wx_period", "")),
        "{{WX_TEMP}}": html.escape(cfg.get("wx_temp", "")),
        "{{WX_DESC}}": cfg.get("wx_desc", ""),  # allows <br><b>
        "{{PHOTO_SRC}}": photo_uri,
        "{{EXPERT_NAME}}": html.escape(cfg.get("expert_name", "")),
        "{{EXPERT_RANK}}": html.escape(cfg.get("expert_rank", "")),
        "{{EXPERT_HOSP}}": cfg.get("expert_hosp", ""),  # allows <br>
        "{{TITLES}}": titles,
        "{{PURPOSE_TITLE}}": html.escape(cfg.get("purpose_title", "拜访目的")),
        "{{PURPOSE_BAR}}": pbar,
        "{{PURPOSE_ITEMS}}": pitems,
        "{{TEAM}}": team,
        "{{TIPS}}": tips,
        "{{FOOTER}}": cfg.get("footer", ""),
    }
    out = template
    for k, v in repl.items():
        out = out.replace(k, v)
    return out


def render_png(html_path: str, out_png: str):
    from playwright.sync_api import sync_playwright
    uri = Path(html_path).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chromium-headless-shell")
        pg = b.new_page(viewport={"width": 800, "height": 1400}, device_scale_factor=2)
        pg.goto(uri)
        pg.wait_for_timeout(800)
        h = pg.evaluate("document.body.scrollHeight")
        pg.screenshot(path=out_png, full_page=True)
        b.close()
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--template", required=True)
    ap.add_argument("--photo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--html-out", default=None, help="可选:保存中间 HTML 路径")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    template = Path(args.template).read_text(encoding="utf-8")
    photo_uri = photo_data_uri(args.photo)
    doc = build_html(cfg, template, photo_uri)

    html_path = args.html_out or (str(Path(args.out).with_suffix("")) + ".html")
    Path(html_path).write_text(doc, encoding="utf-8")
    h = render_png(html_path, args.out)
    print(f"rendered {args.out}  (page height {h}px)")
    if h > 2200:
        print("WARN: 页面偏长,检查是否有内容过多导致溢出观感", file=sys.stderr)


if __name__ == "__main__":
    main()
