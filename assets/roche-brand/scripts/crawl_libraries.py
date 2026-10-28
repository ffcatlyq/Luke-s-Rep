#!/usr/bin/env python3
"""Crawl Frontify Public GraphQL API for all assets in Roche brand libraries.

Endpoint: https://branding.roche.com/graphql (NOT /graphql-internal — that one is
for the SPA only and has tighter permission policies).

Auth: cookie `frontify-session-id` from ~/.config/frontify/cookies.json. The
public GraphQL endpoint accepts the same browser session cookie and exposes
everything the user can see in the UI — including library asset listings that
the SPA-internal REST endpoint (/api/facette/list/{id}) blocks via
`hasPermission: false`.

Output: JSON metadata files in assets/roche-brand/snapshots/. SVG/PNG/EPS
files are NOT downloaded by this script; downloadUrl + previewUrl are saved
in the metadata and a separate download_assets.py handles bulk fetch.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

COOKIE_FILE = Path.home() / ".config" / "frontify" / "cookies.json"
GRAPHQL_URL = "https://branding.roche.com/graphql"
BOOTSTRAP_URL = "https://branding.roche.com/hub/6"
OUT_DIR = Path(__file__).resolve().parent.parent / "snapshots"

# 9 libraries discovered via brand(id:1).libraries query (snapshot 2026-05-17)
LIBRARIES = {
    "icons":           {"gid": "eyJpZGVudGlmaWVyIjozNSwidHlwZSI6InByb2plY3QifQ==",  "type": "IconLibrary",       "name": "4. Icons library - FINAL"},
    "logos":           {"gid": "eyJpZGVudGlmaWVyIjo0MSwidHlwZSI6InByb2plY3QifQ==",  "type": "LogoLibrary",       "name": "3. Logos library - FINAL"},
    "photos":          {"gid": "eyJpZGVudGlmaWVyIjozMCwidHlwZSI6InByb2plY3QifQ==",  "type": "MediaLibrary",      "name": "1. Photos library - FINAL"},
    "videos":          {"gid": "eyJpZGVudGlmaWVyIjo1NSwidHlwZSI6InByb2plY3QifQ==",  "type": "MediaLibrary",      "name": "2. Video library - FINAL"},
    "files":           {"gid": "eyJpZGVudGlmaWVyIjo1MCwidHlwZSI6InByb2plY3QifQ==",  "type": "MediaLibrary",      "name": "File Library"},
    "animated_icons":  {"gid": "eyJpZGVudGlmaWVyIjoyOTA3LCJ0eXBlIjoicHJvamVjdCJ9",  "type": "MediaLibrary",      "name": "5. Animated icons library - FINAL"},
    "illustrations":   {"gid": "eyJpZGVudGlmaWVyIjozODA5LCJ0eXBlIjoicHJvamVjdCJ9",  "type": "MediaLibrary",      "name": "6. Illustration library - FINAL"},
    "stock_assets":    {"gid": "eyJpZGVudGlmaWVyIjozODg5LCJ0eXBlIjoicHJvamVjdCJ9",  "type": "MediaLibrary",      "name": "7. Stock assets library - FINAL"},
    "documents":       {"gid": "eyJpZGVudGlmaWVyIjoxMywidHlwZSI6InByb2plY3QifQ==",  "type": "DocumentLibrary",   "name": "Document Library"},
}

ASSET_FRAGMENT = """
  ... on Image {
    filename extension width height size
    downloadUrl previewUrl thumbnailUrl
    tags { value source }
    customMetadata { property { name } ... on CustomMetadataValue { value } }
    copyright { status notice }
    createdAt modifiedAt
  }
  ... on File {
    filename extension size downloadUrl previewUrl
    tags { value source }
    customMetadata { property { name } ... on CustomMetadataValue { value } }
    copyright { status notice }
    createdAt modifiedAt
  }
  ... on Video {
    filename extension size downloadUrl previewUrl
    tags { value source }
    customMetadata { property { name } ... on CustomMetadataValue { value } }
    copyright { status notice }
    createdAt modifiedAt
  }
"""

QUERY = (
    "query($id: ID!, $page: Int!, $limit: Int!) {"
    "  library(id: $id) {"
    "    __typename name id"
    "    ... on IconLibrary { assets(page:$page, limit:$limit) { total page hasNextPage items { id title " + ASSET_FRAGMENT + " } } }"
    "    ... on LogoLibrary { assets(page:$page, limit:$limit) { total page hasNextPage items { id title " + ASSET_FRAGMENT + " } } }"
    "    ... on MediaLibrary { assets(page:$page, limit:$limit) { total page hasNextPage items { id title " + ASSET_FRAGMENT + " } } }"
    "    ... on DocumentLibrary { assets(page:$page, limit:$limit) { total page hasNextPage items { id title " + ASSET_FRAGMENT + " } } }"
    "  }"
    "}"
)


async def crawl_library(ctx, slug, lib_meta, limit=100):
    page = 1
    all_items = []
    total = None
    while True:
        body = json.dumps({"query": QUERY, "variables": {"id": lib_meta["gid"], "page": page, "limit": limit}})
        r = await ctx.request.post(GRAPHQL_URL, headers={"Content-Type": "application/json", "Accept": "application/json"}, data=body)
        if r.status != 200:
            sys.stderr.write(f"  [{slug}] HTTP {r.status} on page {page}: {(await r.text())[:200]}\n")
            break
        resp = await r.json()
        if "errors" in resp:
            sys.stderr.write(f"  [{slug}] errors: {resp['errors'][:1]}\n")
            break
        lib = (resp.get("data") or {}).get("library")
        if not lib:
            sys.stderr.write(f"  [{slug}] library null\n")
            break
        assets = lib.get("assets") or {}
        items = assets.get("items") or []
        if total is None:
            total = assets.get("total")
            sys.stderr.write(f"  [{slug}] total={total}\n")
        all_items.extend(items)
        sys.stderr.write(f"  [{slug}] page {page}: +{len(items)} (cumulative {len(all_items)}/{total})\n")
        if not assets.get("hasNextPage"):
            break
        page += 1
        await asyncio.sleep(0.2)
    return {"library": lib_meta, "total": total, "items": all_items}


async def main():
    if not COOKIE_FILE.exists():
        sys.exit(f"missing {COOKIE_FILE}")
    session = json.loads(COOKIE_FILE.read_text())["frontify-session-id"]
    OUT_DIR.mkdir(exist_ok=True)

    from playwright.async_api import async_playwright
    cookies = [{"name": "frontify-session-id", "value": session, "domain": "branding.roche.com", "path": "/", "secure": True, "sameSite": "Lax"}]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        await ctx.add_cookies(cookies)
        page_obj = await ctx.new_page()
        await page_obj.goto(BOOTSTRAP_URL, wait_until="domcontentloaded", timeout=20000)

        targets = sys.argv[1:] or list(LIBRARIES.keys())
        for slug in targets:
            if slug not in LIBRARIES:
                print(f"unknown library slug: {slug}", file=sys.stderr)
                continue
            print(f"=== {slug} ({LIBRARIES[slug]['name']}) ===", file=sys.stderr)
            result = await crawl_library(ctx, slug, LIBRARIES[slug])
            out_path = OUT_DIR / f"library-{slug}.json"
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2))
            print(f"  -> {out_path} ({out_path.stat().st_size//1024} KB, {len(result['items'])} items)", file=sys.stderr)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
