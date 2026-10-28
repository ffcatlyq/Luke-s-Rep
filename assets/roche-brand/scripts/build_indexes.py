#!/usr/bin/env python3
"""Build agent-friendly indexes from library JSON metadata.

Reads:
    snapshots/library-icons.json (1525 items)
    snapshots/library-logos.json (4 items)
    snapshots/library-animated_icons.json (163 items)
    snapshots/library-illustrations.json (97 items)
    snapshots/library-stock_assets.json (429 items)

Writes (under assets/roche-brand/):
    icons/index.json          flat title/filename/tags/category index of all icons
    icons/by-category.json    icons grouped by Category custom metadata
    icons/by-tag.json         icons indexed by tag value
    INDEX.md                  human-readable index of the whole library
"""

import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def slim_item(it, source_lib):
    cm = it.get("customMetadata") or []
    category = None
    for entry in cm:
        if (entry.get("property") or {}).get("name") == "Category":
            v = entry.get("value")
            if isinstance(v, dict):
                category = v.get("text")
            elif isinstance(v, str):
                category = v
    return {
        "id": it["id"],
        "title": it.get("title", "").strip(),
        "filename": it.get("filename"),
        "extension": it.get("extension"),
        "size_kb": (it.get("size") or 0) // 1024 if it.get("size") else None,
        "width": it.get("width"),
        "height": it.get("height"),
        "category": category,
        "tags": [t["value"] for t in (it.get("tags") or [])],
        "library": source_lib,
        "local_path": local_path_for(it, source_lib),
        "downloadUrl": it.get("downloadUrl"),
        "previewUrl": it.get("previewUrl"),
    }


def local_path_for(it, source_lib):
    """Path the asset is saved at locally (relative to assets/roche-brand/)."""
    aid_short = it["id"][-12:]
    fn = it.get("filename") or aid_short
    import re
    safe = re.sub(r"[^\w\-.]", "_", fn)[:120]
    if source_lib == "icons":
        return f"icons/svg/{aid_short}__{safe}"
    if source_lib == "illustrations":
        return f"illustrations/png/{aid_short}__{safe}"
    if source_lib == "logos":
        return f"logos/{safe}"
    return None  # animated_icons / stock_assets bodies not downloaded


def main():
    snapshots = ROOT / "snapshots"
    libs = {}
    for slug in ["icons", "logos", "photos", "animated_icons", "illustrations", "stock_assets"]:
        p = snapshots / f"library-{slug}.json"
        if p.exists():
            libs[slug] = json.loads(p.read_text())

    # Flat icons index
    icons_index = [slim_item(it, "icons") for it in libs["icons"]["items"]]
    (ROOT / "icons" / "index.json").write_text(json.dumps(
        {"_doc": "Flat metadata index of all 1525 Roche icons. Use to find icons by title/category/tags.",
         "_total": len(icons_index),
         "items": icons_index},
        ensure_ascii=False, indent=2))

    # Group by Category
    by_cat = defaultdict(list)
    for it in icons_index:
        by_cat[it["category"] or "Uncategorized"].append({
            "id": it["id"], "title": it["title"], "tags": it["tags"], "local_path": it["local_path"],
        })
    (ROOT / "icons" / "by-category.json").write_text(json.dumps(
        {"_doc": "Icons grouped by Category custom metadata. Categories: " + ", ".join(sorted(by_cat.keys())),
         "_categories": {k: len(v) for k, v in sorted(by_cat.items())},
         "groups": {k: v for k, v in sorted(by_cat.items())}},
        ensure_ascii=False, indent=2))

    # Index by tag
    by_tag = defaultdict(list)
    for it in icons_index:
        for tag in it["tags"]:
            by_tag[tag].append({"id": it["id"], "title": it["title"], "category": it["category"], "local_path": it["local_path"]})
    (ROOT / "icons" / "by-tag.json").write_text(json.dumps(
        {"_doc": "Icons indexed by tag. Most common tags first.",
         "_total_tags": len(by_tag),
         "_top_tags": dict(sorted({k: len(v) for k, v in by_tag.items()}.items(), key=lambda x: -x[1])[:50]),
         "tags": {k: v for k, v in sorted(by_tag.items(), key=lambda x: -len(x[1]))}},
        ensure_ascii=False, indent=2))

    # Photos by-tag index (photos: 6062 items × ~1674 tags; bodies NOT in git, fetch via download_bodies.py + transform on demand)
    if "photos" in libs:
        photos_index = [slim_item(it, "photos") for it in libs["photos"]["items"]]
        photos_by_tag = defaultdict(list)
        for it in photos_index:
            for tag in it["tags"]:
                photos_by_tag[tag].append({"id": it["id"], "title": it["title"]})
        (ROOT / "photos").mkdir(exist_ok=True)
        (ROOT / "photos" / "by-tag.json").write_text(json.dumps(
            {"_doc": "Photos indexed by tag (minimal: id+title only). Full metadata (downloadUrl, previewUrl, size, dimensions) — look up id in snapshots/all-assets-flat.json or library-photos.json. Bodies NOT in git (307 GB original / TIF 印刷级原图). To use a photo: take its previewUrl and append ?format=jpeg&width=1600&quality=85 (Frontify CDN transform), or call scripts/download_bodies.py photos <out_dir> --transform 'format=jpeg&width=1600&quality=85'.",
             "_total_tags": len(photos_by_tag),
             "_total_items": len(photos_index),
             "_top_tags": dict(sorted({k: len(v) for k, v in photos_by_tag.items()}.items(), key=lambda x: -x[1])[:50]),
             "tags": {k: v for k, v in sorted(photos_by_tag.items(), key=lambda x: -len(x[1]))}},
            ensure_ascii=False, indent=2))

    # Flat unified index for ALL libraries
    flat = []
    for slug, body in libs.items():
        for it in body["items"]:
            flat.append(slim_item(it, slug))
    (ROOT / "snapshots" / "all-assets-flat.json").write_text(json.dumps(
        {"_doc": "Flat unified index across all 6 crawled libraries (icons + logos + photos + animated_icons + illustrations + stock_assets).",
         "_total": len(flat),
         "_by_library": {slug: sum(1 for it in flat if it["library"] == slug) for slug in libs.keys()},
         "items": flat},
        ensure_ascii=False, indent=2))

    # Human-readable INDEX.md
    md = ["# Roche Brand Asset Library — Index\n"]
    md.append(f"**Snapshot date**: 2026-05-17 · **Total assets indexed**: {len(flat)}\n")
    md.append("## Libraries\n")
    md.append("| Library | Type | Total | Bodies downloaded | Index |")
    md.append("|---|---|---|---|---|")
    for slug, body in libs.items():
        downloaded = ""
        if slug == "icons": downloaded = "1525 SVG ✅"
        elif slug == "logos": downloaded = "4 EPS + 12 PNG ✅"
        elif slug == "illustrations": downloaded = "97 PNG ✅"
        elif slug == "animated_icons": downloaded = "metadata only (159 MB GIF skipped)"
        elif slug == "stock_assets": downloaded = "metadata only (11 GB MP4/JPEG skipped)"
        md.append(f"| {body['library']['name']} | {body['library']['type']} | {body['total']} | {downloaded} | [snapshots/library-{slug}.json](./snapshots/library-{slug}.json) |")
    md.append("")
    md.append("## Icon categories\n")
    md.append("| Category | Count |")
    md.append("|---|---|")
    for cat, count in sorted(((k, len(v)) for k, v in by_cat.items()), key=lambda x: -x[1]):
        md.append(f"| {cat} | {count} |")
    md.append("")
    md.append("## Top icon tags\n")
    md.append("| Tag | Count |")
    md.append("|---|---|")
    for tag, count in sorted({k: len(v) for k, v in by_tag.items()}.items(), key=lambda x: -x[1])[:30]:
        md.append(f"| {tag} | {count} |")
    md.append("")
    md.append("## How to query\n")
    md.append("```python")
    md.append("import json")
    md.append("# Find all icons in 'Healthcare' category")
    md.append("by_cat = json.load(open('assets/roche-brand/icons/by-category.json'))")
    md.append("healthcare_icons = by_cat['groups']['Healthcare']  # list of {id, title, tags, local_path}")
    md.append("")
    md.append("# Find icons tagged with 'oncology'")
    md.append("by_tag = json.load(open('assets/roche-brand/icons/by-tag.json'))")
    md.append("oncology_icons = by_tag['tags']['oncology']")
    md.append("```")

    (ROOT / "INDEX.md").write_text("\n".join(md))
    print(f"Built: icons/index.json, icons/by-category.json, icons/by-tag.json, snapshots/all-assets-flat.json, INDEX.md")


if __name__ == "__main__":
    main()
