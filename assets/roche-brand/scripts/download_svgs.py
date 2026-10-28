#!/usr/bin/env python3
"""Download SVG bodies for icons in library-icons.json.

downloadUrl is a presigned AWS S3 URL (no Cloudflare/Frontify gate, no cookie),
so plain urllib works. Files are saved under assets/roche-brand/icons/svg/
with unique filename: {asset_id}__{sanitized_filename}.svg
"""

import json
import re
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META_PATH = ROOT / "snapshots" / "library-icons.json"
OUT_DIR = ROOT / "icons" / "svg"


def sanitize(s):
    s = re.sub(r"[^\w\-.]", "_", s)
    return s[:120]


def fetch(item, out_dir):
    aid_full = item["id"]
    aid_short = aid_full[-12:]
    filename = item.get("filename") or f"{aid_short}.svg"
    safe = sanitize(filename)
    out_path = out_dir / f"{aid_short}__{safe}"
    if out_path.exists() and out_path.stat().st_size > 0:
        return ("skip", out_path)
    url = item.get("downloadUrl")
    if not url:
        return ("no-url", out_path)
    try:
        urllib.request.urlretrieve(url, out_path)
        return ("ok", out_path)
    except Exception as e:
        return (f"err: {e}", out_path)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta = json.loads(META_PATH.read_text())
    items = meta["items"]
    sys.stderr.write(f"downloading {len(items)} SVG files...\n")
    counts = {"ok": 0, "skip": 0, "err": 0, "no-url": 0}
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = [ex.submit(fetch, item, OUT_DIR) for item in items]
        for i, f in enumerate(as_completed(futures), 1):
            status, path = f.result()
            key = "err" if status.startswith("err") else status
            counts[key] = counts.get(key, 0) + 1
            if i % 100 == 0:
                sys.stderr.write(f"  {i}/{len(items)} {counts}\n")
    sys.stderr.write(f"done: {counts}\n")
    total_size = sum(p.stat().st_size for p in OUT_DIR.glob("*"))
    sys.stderr.write(f"total dir size: {total_size//1024} KB ({len(list(OUT_DIR.glob('*')))} files)\n")


if __name__ == "__main__":
    main()
