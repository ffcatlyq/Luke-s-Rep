#!/usr/bin/env python3
"""smoke_test.py — ppt-master 引擎装完的金丝雀:用一页自造 SVG 跑完整 canonical 导出,
断言产物里 text run / 矢量形状 / 出场动画 / 演讲备注 四样都在。

意义:我们 float 到上游最新(不钉版本),换来的风险是上游悄悄改导出接口(如 `--only native`
在新版已移除)。这个 30 秒测试让"上游变了"在装引擎时当场暴露,而不是等发出坏 deck 才发现。
canonical 导出命令是 SKILL.md 的 SSOT;这里跑的就是那条命令,任一断言失败即返回非零。

用法: python3 smoke_test.py <engine_dir>
"""
import os, re, subprocess, sys, tempfile, zipfile

ENGINE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/ppt-master")
PY = os.path.join(ENGINE, ".venv", "bin", "python")
SCRIPTS = os.path.join(ENGINE, "skills", "ppt-master", "scripts")

SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
  <g id="bg"><rect width="1280" height="720" fill="#FFFFFF"/></g>
  <g id="card">
    <rect x="80" y="120" width="600" height="200" rx="12" fill="#E9EEFA" stroke="#0B41CD" stroke-width="2"/>
    <path d="M110 300 L400 300 L640 260" fill="none" stroke="#1482fa" stroke-width="3"/>
    <text x="110" y="200" font-family="'Roche Sans Light',sans-serif" font-size="40" fill="#0B41CD">Smoke test</text>
    <text x="110" y="250" font-family="'Roche Sans',sans-serif" font-size="20" fill="#333333">native text + vector + timing + notes</text>
  </g>
</svg>'''

ANIM = '''{"version":1,"defaults":{"transition":{"effect":"fade","duration":0.3},
"animation":{"effect":"fade","duration":0.4,"trigger":"after-previous"}},
"slides":{"01_smoke":{"groups":{"card":{"effect":"zoom","order":1,"duration":0.4}}}}}'''


def run(args):
    r = subprocess.run([PY] + args, capture_output=True, text=True)
    if r.returncode != 0:
        print("CMD FAILED:", " ".join(args)); print(r.stdout[-2000:]); print(r.stderr[-2000:])
        raise SystemExit(2)
    return r


def main():
    if not os.path.exists(PY):
        print("no venv python at", PY); return 2
    # clean stale smoke projects from prior runs (init refuses to overwrite)
    import shutil, glob
    for d in glob.glob(os.path.join("projects", "smoke_ppt169*")):
        shutil.rmtree(d, ignore_errors=True)
    run([os.path.join(SCRIPTS, "project_manager.py"), "init", "smoke", "--format", "ppt169"])
    proj = None
    for d in os.listdir("projects"):
        if d.startswith("smoke_ppt169"):
            proj = os.path.join("projects", d)
    if not proj:  # some versions init under cwd; fall back to scanning
        for base in (".", ENGINE):
            for d in os.listdir(base):
                if d.startswith("smoke_ppt169"):
                    proj = os.path.join(base, d)
    assert proj, "project dir not found after init"
    open(os.path.join(proj, "svg_output", "01_smoke.svg"), "w").write(SVG)
    os.makedirs(os.path.join(proj, "notes"), exist_ok=True)
    open(os.path.join(proj, "notes", "01_smoke.md"), "w").write("Smoke speaker note.\n\nKey points: canary\nTime: 0:05\n")
    open(os.path.join(proj, "animations.json"), "w").write(ANIM)

    run([os.path.join(SCRIPTS, "finalize_svg.py"), proj])
    # Upstream now requires an explicit spec_lock.md theme contract before release export.
    # For a fresh free-design / brand-only project (this smoke canary) the flat contract is:
    #   ## pptx_structure  → mode: flat  (structured/template projects instead follow
    #                        workflows/restore-pptx-structure.md)
    #   ## typography      → title/body sizes in px + a font_family (major/minor faces)
    #   ## colors          → bg/text/primary… as HEX (mapped to theme slots)
    # Row format is "- key: value" (see drawingml/theme_fonts.py & theme_colors.py _LOCK_ROW_RE).
    # Values below use Roche Blue brand basics so the canary exercises the real theme path.
    open(os.path.join(proj, "spec_lock.md"), "w").write(
        "## pptx_structure\n"
        "- mode: flat\n"
        "\n"
        "## typography\n"
        "- title: 40\n"
        "- body: 18\n"
        "- font_family: Arial\n"
        "\n"
        "## colors\n"
        "- bg: FFFFFF\n"
        "- text: 1A1A1A\n"
        "- primary: 0B41CD\n"
        "- accent: 00A3E0\n"
        "\n"
        "## canvas\n"
        "- viewBox: 0 0 1280 720\n"
    )
    # canonical export (SSOT — keep in sync with SKILL.md): native default, auto animations.json, auto notes
    run([os.path.join(SCRIPTS, "svg_to_pptx.py"), proj])

    pptx = None
    exp = os.path.join(proj, "exports")
    for f in sorted(os.listdir(exp)):
        if f.endswith(".pptx"):
            pptx = os.path.join(exp, f)
    assert pptx, "no pptx exported"
    z = zipfile.ZipFile(pptx); n = z.namelist()
    slides = [x for x in n if re.match(r"ppt/slides/slide\d+\.xml$", x)]
    xml = z.read(slides[0]).decode("utf-8", "ignore")
    at = xml.count("<a:t>")
    # native editable vector = custom geometry OR preset geometry (both are editable shapes, not images)
    geom = xml.count("<a:custGeom>") + xml.count("<a:prstGeom")
    timing = "<p:timing>" in xml
    notes = [x for x in n if re.match(r"ppt/notesSlides/notesSlide\d+", x)]
    print(f"[smoke] a:t={at} nativeShapes={geom} timing={timing} notesSlides={len(notes)} zip={'OK' if z.testzip() is None else 'BAD'}")

    ok = at > 0 and geom > 0 and timing and len(notes) >= 1 and z.testzip() is None
    if not ok:
        print("[smoke] CANARY FAILED — 上游导出接口可能变了(检查 --animation-config / notes / native 默认)")
        return 1
    print("[smoke] PASS")
    return 0


if __name__ == "__main__":
    # run from engine dir so `projects/` lands there
    os.chdir(ENGINE)
    sys.exit(main())
