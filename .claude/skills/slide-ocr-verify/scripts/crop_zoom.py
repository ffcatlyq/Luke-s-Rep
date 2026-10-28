#!/usr/bin/env python3
"""裁剪 + 放大提纯 + OCR —— 图片型幻灯/PDF 数字识别的核心工具。

用法:
  python3 crop_zoom.py page.png --box 0.03 0.28 0.40 0.32 --name extC
  # box = x0 y0 x1 y1 (相对坐标 0~1)
  # 输出 v_<name>.png，并直接跑 tesseract 打印读数

依赖: pip install pillow pytesseract ; 系统装 tesseract-ocr
"""
import argparse
import subprocess
import sys

from PIL import Image


def crop_zoom(img_path, box, name, target_w=1150, y_stretch=1.6):
    im = Image.open(img_path)
    w, h = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))
    if c.size[0] == 0 or c.size[1] == 0:
        sys.exit("裁剪区域为空，检查 box 坐标")
    # 等比放大到目标宽，纵向再拉伸让字符分离
    scale = target_w / c.size[0]
    new_h = int(c.size[1] * scale * y_stretch)
    c = c.resize((target_w, new_h))
    out = f"v_{name}.png"
    c.save(out)
    return out, c.size


def ocr(png, psm=6):
    try:
        r = subprocess.run(
            ["tesseract", png, "stdout", "--psm", str(psm)],
            capture_output=True, text=True, check=True,
        )
        return r.stdout.strip()
    except FileNotFoundError:
        return "(tesseract 未安装)"
    except subprocess.CalledProcessError as e:
        return f"(OCR 失败: {e})"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--box", nargs=4, type=float, required=True,
                    metavar=("x0", "y0", "x1", "y1"))
    ap.add_argument("--name", default="block")
    ap.add_argument("--width", type=int, default=1150)
    ap.add_argument("--ystretch", type=float, default=1.6)
    ap.add_argument("--psm", type=int, default=6)
    a = ap.parse_args()

    out, size = crop_zoom(a.image, a.box, a.name, a.width, a.ystretch)
    print(f"裁剪放大 -> {out} {size}")
    print("=== OCR ===")
    print(ocr(out, a.psm))
    print("\n提醒: 单次 OCR 不可信，务必用 verify_ratio.py 或多处读值交叉验证。")
