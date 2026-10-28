#!/usr/bin/env python3
"""Generic body downloader. Reads library-<slug>.json, downloads each asset's
downloadUrl into assets/roche-brand/<out_dir>/.

Two modes:
- Default (no --transform):     download original via downloadUrl (S3 presigned).
- --transform "<query>":         fetch a Frontify CDN transform of previewUrl,
                                 e.g. "format=jpeg&width=1600&quality=85". Original
                                 stays on Frontify; only the transform is saved.
                                 Use this for photos (307 GB original → 1600px jpeg
                                 ~200 KB/file, suitable for slide use).

Usage:
    python3 download_bodies.py <library_slug> <out_subdir> [--max-size-mb N]
                                                            [--transform <query>]
                                                            [--limit N]

Examples:
    python3 download_bodies.py illustrations illustrations/png
    python3 download_bodies.py logos logos --include-preview-png
    python3 download_bodies.py photos photos/jpeg-1600 \
        --transform "format=jpeg&width=1600&quality=85" --limit 50
"""

import argparse
import json
import re
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def sanitize(s):
    return re.sub(r"[^\w\-.]", "_", s)[:120]


def fetch(item, out_dir, prefer_preview_png=False, transform=None):
    aid_short = item["id"][-12:]
    filename = item.get("filename") or f"{aid_short}"
    safe = sanitize(filename)

    if transform:
        # Transform mode: hit Frontify CDN previewUrl with query params; output
        # extension follows the transform's "format=" (default jpeg).
        url = item.get("previewUrl")
        if not url:
            return ("no-url", out_dir / f"{aid_short}__{safe}")
        fmt = "jpeg"
        for kv in transform.split("&"):
            if kv.startswith("format="):
                fmt = kv.split("=", 1)[1]
        stem = Path(safe).stem
        out_path = out_dir / f"{aid_short}__{stem}.{fmt}"
        if out_path.exists() and out_path.stat().st_size > 0:
            return ("skip", out_path)
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}{transform}"
    else:
        out_path = out_dir / f"{aid_short}__{safe}"
        if out_path.exists() and out_path.stat().st_size > 0:
            return ("skip", out_path)
        full_url = item.get("downloadUrl")
        if not full_url:
            return ("no-url", out_path)

    try:
        urllib.request.urlretrieve(full_url, out_path)
        if prefer_preview_png and not transform and item.get("previewUrl"):
            png_path = out_dir / f"{aid_short}__{Path(safe).stem}.png"
            if not png_path.exists():
                preview_url = item["previewUrl"] + ("&" if "?" in item["previewUrl"] else "?") + "format=png&width=1200"
                try:
                    urllib.request.urlretrieve(preview_url, png_path)
                except Exception:
                    pass
        return ("ok", out_path)
    except Exception as e:
        return (f"err: {e}", out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug")
    parser.add_argument("out_subdir")
    parser.add_argument("--max-size-mb", type=int, help="Skip items above this size")
    parser.add_argument("--include-preview-png", action="store_true")
    parser.add_argument("--transform", help="Frontify CDN transform query (e.g. 'format=jpeg&width=1600&quality=85'). When set, downloads previewUrl + transform instead of original downloadUrl.")
    parser.add_argument("--limit", type=int, help="Only download the first N items (after size filter).")
    args = parser.parse_args()

    meta_path = ROOT / "snapshots" / f"library-{args.slug}.json"
    out_dir = ROOT / args.out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)
    items = json.loads(meta_path.read_text())["items"]

    # Filter out items without the URL we need (some assets are URL-redacted by
    # Frontify due to portrait rights / 3rd-party licensing).
    url_field = "previewUrl" if args.transform else "downloadUrl"
    before = len(items)
    items = [it for it in items if it.get(url_field)]
    if len(items) < before:
        sys.stderr.write(f"url filter: {len(items)}/{before} have {url_field} (rest are redacted by Frontify)\n")

    if args.max_size_mb:
        threshold = args.max_size_mb * 1024 * 1024
        before = len(items)
        items = [it for it in items if not it.get("size") or it["size"] <= threshold]
        sys.stderr.write(f"size filter: {len(items)}/{before} (max {args.max_size_mb}MB)\n")

    if args.limit:
        items = items[: args.limit]
        sys.stderr.write(f"limit: first {len(items)}\n")

    mode = f"transform={args.transform}" if args.transform else "original (downloadUrl)"
    sys.stderr.write(f"downloading {len(items)} files into {out_dir} [{mode}]\n")
    counts = {"ok": 0, "skip": 0, "err": 0, "no-url": 0}
    with ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(fetch, it, out_dir, args.include_preview_png, args.transform) for it in items]
        for i, f in enumerate(as_completed(futures), 1):
            status, _ = f.result()
            key = "err" if status.startswith("err") else status
            counts[key] = counts.get(key, 0) + 1
            if i % 50 == 0:
                sys.stderr.write(f"  {i}/{len(items)} {counts}\n")
    sys.stderr.write(f"done: {counts}\n")


if __name__ == "__main__":
    main()
