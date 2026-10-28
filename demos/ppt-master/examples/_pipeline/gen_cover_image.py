#!/usr/bin/env python3
"""gen_cover_image.py — 用 Galileo(Azure gpt-image)生成氛围/装饰配图。

混合图像策略里"氛围背景/装饰图"这一类走它(封面蓝图氛围、正弦波氛围等);
schematic / 架构 / 公式仍用纯可编辑 SVG(锐利 + 可编辑 = ppt-master 卖点),
论文原图有版权不嵌。

合规:数据出境经 Galileo gateway(公司合规通道),用的是你自己的 Galileo key
(GALILEO_AZURE_API_KEY),不是任何 harness token。默认关,按需生成。

安全(务必):key **只从环境变量读**,绝不硬编码进脚本、绝不 commit 进任何 repo。
Galileo key 通常是按项目申请的(有归属与配额),开源/分享本 demo 时**只带这份脚本,
不带 key**;fork 的人用自己的 key 走 `export GALILEO_AZURE_API_KEY=...`。hub 的
secret-guard hook + GHAS secret scanning 是兜底,但正确做法是它压根不进文件。

已验证(2026-07):
  - 可用模型:gpt-image-1-mini-2025-10-06 / gpt-image-1 / gpt-image-1.5-2025-12-16
    (质量:1.5 > 1 > mini;封面这种精度用 1.5)。
  - gpt-image-2 那个带日期的 ID 当前 Azure 端不认(unknown_model),别用。
  - Gemini 原生生图走 /chat/completions 不走 /images/generations,且需 GCP 集成开权限。
提示词经验:要精致 schematic 就把"块内部结构 / 双描边 / 输入输出引脚 / 网格密度 /
留白构图"写具体——只说"六个矩形+连线"会得到空心块。

用法:
    export GALILEO_ENDPOINT=...              # 形如 https://us.aigw.galileo.roche.com/v1
    export GALILEO_AZURE_API_KEY=...
    python3 gen_cover_image.py --out cover_bg_raw.png --prompt-file prompt.txt
    # 或 --prompt "..."；默认 size 1536x1024(封面用),之后自行 center-crop 到 16:9。
"""
import argparse
import base64
import json
import os
import ssl
import urllib.request


def generate(prompt: str, out: str, model: str, size: str, timeout: int = 240) -> None:
    ep = os.environ["GALILEO_ENDPOINT"].rstrip("/")
    key = os.environ["GALILEO_AZURE_API_KEY"]
    body = json.dumps({"model": model, "prompt": prompt, "size": size, "n": 1}).encode()
    req = urllib.request.Request(
        ep + "/images/generations", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as f:
        d0 = json.loads(f.read())["data"][0]
    if d0.get("b64_json"):
        open(out, "wb").write(base64.b64decode(d0["b64_json"]))
        print(f"generated -> {out} ({os.path.getsize(out)//1024} KB)")
    else:
        print("returned URL instead of b64:", d0.get("url"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Generate an atmosphere image via Galileo Azure gpt-image")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prompt", help="prompt text")
    g.add_argument("--prompt-file", help="path to a file containing the prompt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt-image-1.5-2025-12-16")
    ap.add_argument("--size", default="1536x1024", help="1536x1024 (landscape) / 1024x1024 / 1024x1536")
    args = ap.parse_args()
    prompt = args.prompt if args.prompt else open(args.prompt_file).read().strip()
    generate(prompt, args.out, args.model, args.size)
