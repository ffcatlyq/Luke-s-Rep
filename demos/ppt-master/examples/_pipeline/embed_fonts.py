#!/usr/bin/env python3
"""embed_fonts.py — 把 Roche 字体嵌入 .pptx(post-process)。【实测 PowerPoint 拒装,见下】

ppt-master 的 svg_to_pptx 不嵌字体(导出的 pptx `ppt/fonts/` 为空),外发给没装 Roche Sans
的人会回退系统字体。本脚本做一次后处理:扫 pptx 里实际用到的 typeface + 字符,把对应 Roche
字体(可 `--no-subset` 完整、默认子集)按 OOXML 规范嵌进 pptx。

⚠️ 实测结论(2026-07-12,Windows PowerPoint):**PowerPoint 拒装本脚本嵌入的字体**——
  子集嵌入和 `--no-subset` 完整字体嵌入**都**弹"无法安装演示稿中的某些嵌入字体…一般错误"
  (Roche Sans Light / Roche Serif Light;字体本身是 TrueType、fsType=0,已排除 CFF / 许可位)。
  根因:PowerPoint 只认它自己"嵌入字体"功能产的结构,拒装第三方工具程序化嵌入的字体。
  **所以三份 exemplar 一律不嵌**(= 文档定的默认),罗氏机器本有 Roche Sans、优雅回退。
  本脚本保留作参考 + 供非 PowerPoint 阅读器(LibreOffice 等)测试;**默认不进导出管线,
  用前务必在你的目标阅读器实测能装再依赖它**。

许可 stance:Roche 字体 fsType=0(技术可嵌)但**不等于** EULA 允许随 pptx 外发再分发;
  即便哪天技术通了,外发外部方仍须 brand/legal 确认。当前技术 + 许可双重原因 → **不嵌**。

用法:
  python3 embed_fonts.py --in deck.pptx --out deck-embedded.pptx \
      [--fonts assets/roche-brand/fonts] [--no-subset]

依赖: fonttools brotli(woff2 解码)。
"""
import argparse, os, re, shutil, sys, tempfile, zipfile

# family 名(SVG/pptx 里 <a:latin typeface=...>)→ woff2 文件相对 --fonts 的路径
FAMILY_TO_WOFF2 = {
    "Roche Sans Light":   "roche-sans/RocheSans-Light.woff2",
    "Roche Sans Medium":  "roche-sans/RocheSans-Medium.woff2",
    "Roche Sans":         "roche-sans/RocheSans-Regular.woff2",
    "Roche Sans Bold":    "roche-sans/RocheSans-Bold.woff2",
    "Roche Serif Light":  "roche-serif/RocheSerif-Light.woff2",
    "Roche Serif":        "roche-serif/RocheSerif-Regular.woff2",
}
FONT_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"


def used_typefaces_and_chars(z):
    """扫 slides + notesSlides,返回 (用到的 typeface 集合, 用到的字符集合)。"""
    faces, chars = set(), set()
    for name in z.namelist():
        if re.match(r"ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml$", name):
            xml = z.read(name).decode("utf-8", "ignore")
            for m in re.findall(r'typeface="([^"]+)"', xml):
                faces.add(m)
            for t in re.findall(r"<a:t>(.*?)</a:t>", xml, re.S):
                chars.update(t)
    return faces, chars


def make_subset_ttf(woff2_path, chars, subset, out_ttf):
    from fontTools.ttLib import TTFont
    f = TTFont(woff2_path)  # woff2 需 brotli
    f.flavor = None         # 去 woff2 压缩 → 裸 ttf(pptx fntdata 要 ttf/otf)
    if subset and chars:
        from fontTools import subset as ftsubset
        opts = ftsubset.Options()
        opts.name_IDs = ["*"]          # 保留 name 表 → PowerPoint 靠 family 名匹配
        opts.recalc_bounds = True
        opts.drop_tables = []
        ss = ftsubset.Subsetter(options=opts)
        # 加常用 ASCII 兜底,避免子集把空格/标点漏掉
        uni = set(ord(c) for c in chars if ord(c) > 0) | set(range(0x20, 0x7F))
        ss.populate(unicodes=uni)
        ss.subset(f)
    f.save(out_ttf)


def embed(in_pptx, out_pptx, fonts_dir, subset=True):
    z = zipfile.ZipFile(in_pptx)
    faces, chars = used_typefaces_and_chars(z)
    targets = [fam for fam in FAMILY_TO_WOFF2 if fam in faces
               and os.path.exists(os.path.join(fonts_dir, FAMILY_TO_WOFF2[fam]))]
    if not targets:
        print("[embed_fonts] 没有可嵌的 Roche 字体(pptx 未用到或字体文件缺失);未改动。")
        return 1
    tmp = tempfile.mkdtemp(prefix="embedfont_")
    try:
        fnt_parts = []  # (part_name, rel_id, family)
        for i, fam in enumerate(sorted(targets), 1):
            ttf = os.path.join(tmp, f"font{i}.ttf")
            make_subset_ttf(os.path.join(fonts_dir, FAMILY_TO_WOFF2[fam]), chars, subset, ttf)
            fnt_parts.append((f"ppt/fonts/font{i}.fntdata", f"rIdFont{i}", fam, ttf,
                              os.path.getsize(ttf)))

        names = z.namelist()
        ct = z.read("[Content_Types].xml").decode("utf-8")
        if "fntdata" not in ct:
            ct = ct.replace("</Types>",
                '<Default Extension="fntdata" ContentType="application/x-fontdata"/></Types>')

        rels_name = "ppt/_rels/presentation.xml.rels"
        rels = z.read(rels_name).decode("utf-8")
        add_rels = "".join(
            f'<Relationship Id="{rid}" Type="{FONT_REL}" Target="fonts/font{i}.fntdata"/>'
            for i, (_, rid, _, _, _) in enumerate(fnt_parts, 1))
        rels = rels.replace("</Relationships>", add_rels + "</Relationships>")

        pres = z.read("ppt/presentation.xml").decode("utf-8")
        if "embedTrueTypeFonts" not in pres:
            pres = re.sub(r"(<p:presentation\b)", r'\1 embedTrueTypeFonts="1"', pres, count=1)
        fontlst = "<p:embeddedFontLst>" + "".join(
            f'<p:embeddedFont><p:font typeface="{fam}"/><p:regular r:id="{rid}"/></p:embeddedFont>'
            for (_, rid, fam, _, _) in fnt_parts) + "</p:embeddedFontLst>"
        # schema 顺序:embeddedFontLst 紧跟 notesSz 之后
        if "<p:notesSz" in pres:
            pres = re.sub(r"(<p:notesSz\b[^>]*/>)", r"\1" + fontlst, pres, count=1)
        else:
            pres = pres.replace("</p:presentation>", fontlst + "</p:presentation>")

        patched = {"[Content_Types].xml": ct, rels_name: rels, "ppt/presentation.xml": pres}
        with zipfile.ZipFile(out_pptx, "w", zipfile.ZIP_DEFLATED) as out:
            for n in names:
                out.writestr(n, patched.get(n, z.read(n)))
            for part, _, _, ttf, _ in fnt_parts:
                out.writestr(part, open(ttf, "rb").read())
        kb = sum(p[4] for p in fnt_parts) / 1024
        print(f"[embed_fonts] 嵌入 {len(fnt_parts)} 个字体子集({kb:.0f} KB): "
              + ", ".join(f[2] for f in fnt_parts))
        print(f"[embed_fonts] -> {out_pptx}")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="Subset-embed Roche fonts into a .pptx")
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    ap.add_argument("--fonts", default="/workspaces/silicon-hitchhiker/assets/roche-brand/fonts")
    ap.add_argument("--no-subset", action="store_true", help="嵌完整字体(不子集化)")
    a = ap.parse_args()
    sys.exit(embed(a.inp, a.out, a.fonts, subset=not a.no_subset))


if __name__ == "__main__":
    main()
