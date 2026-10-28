#!/usr/bin/env python3
"""Extract Brand Elements (doc 26) + Templates (doc 29) page contents from
the Frontify cache (~/.cache/frontify-brand-elements-templates.json) and
render to markdown files under assets/roche-brand/pages/.

Each Frontify page consists of `sections` -> `content` blocks. Block types:
  - text          → HTML in settings.content (legacy plain HTML)
  - custom Text   → SlateJS-style nested array in settings.content
  - reference Embed → assetId reference (image / video)
  - reference Colors → palette ID
  - custom Image  → image with caption
  - custom Callout → SlateJS textValue
  - custom Divider → horizontal rule

Output: one .md per page, named `{document}_{slug}.md`
"""

import json
import re
import html
import sys
from pathlib import Path

CACHE = Path.home() / ".cache" / "frontify-brand-elements-templates.json"
OUT_DIR = Path(__file__).resolve().parent.parent / "pages"


def slate_to_text(node):
    """Recursively flatten SlateJS-style node tree to plain text with newlines."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(slate_to_text(c) for c in node)
    if not isinstance(node, dict):
        return ""

    if "text" in node:
        return node["text"]

    children = node.get("children", [])
    inner = "".join(slate_to_text(c) for c in children)
    t = node.get("type")

    if t == "p":
        return inner + "\n\n"
    if t in ("h1", "heading1"):
        return f"# {inner}\n\n"
    if t in ("h2", "heading2"):
        return f"## {inner}\n\n"
    if t in ("h3", "heading3", "heading4"):
        return f"### {inner}\n\n"
    if t == "ul":
        return inner + "\n"
    if t == "li":
        return f"- {inner.strip()}\n"
    if t == "lic":
        return inner
    if t == "a":
        url = node.get("url", "")
        return f"[{inner}]({url})"
    if t in ("strong", "bold"):
        return f"**{inner}**"
    if t in ("em", "italic"):
        return f"_{inner}_"
    if t in ("imageTitle", "imageCaption", "custom2"):
        return inner
    return inner


def html_to_md(h: str) -> str:
    if not h:
        return ""
    h = re.sub(r"<br\s*/?>", "\n", h)
    h = re.sub(r"</?(p|div)[^>]*>", "\n", h)
    h = re.sub(r"<li[^>]*>", "- ", h)
    h = re.sub(r"</li>", "\n", h)
    h = re.sub(r"</?(ul|ol)[^>]*>", "\n", h)
    h = re.sub(r"<strong[^>]*>", "**", h)
    h = re.sub(r"</strong>", "**", h)
    h = re.sub(r"<em[^>]*>", "_", h)
    h = re.sub(r"</em>", "_", h)
    h = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', r"[\2](\1)", h)
    h = re.sub(r"<[^>]+>", "", h)
    h = html.unescape(h)
    h = re.sub(r"\n{3,}", "\n\n", h.strip())
    return h


def render_block(b: dict) -> str:
    bt = b.get("block_type")
    dn = b.get("display_name", "")
    settings = b.get("settings") or {}

    if bt == "text":
        return html_to_md(settings.get("content", ""))

    if dn == "Text" or bt == "custom" and dn == "Text":
        content = settings.get("content")
        if content:
            return slate_to_text(content).strip() + "\n"

    if dn == "Callout":
        type_ = settings.get("type", "info")
        text_value = settings.get("textValue")
        if isinstance(text_value, str):
            try:
                text_value = json.loads(text_value)
            except Exception:
                pass
        body = slate_to_text(text_value).strip()
        return f"> **[{type_}]** {body}\n"

    if dn == "Divider":
        return "\n---\n"

    if dn == "Image":
        desc = settings.get("description")
        if isinstance(desc, list):
            cap = slate_to_text(desc).strip()
            if cap:
                return f"_(image: {cap})_\n"
        return ""

    if bt == "reference":
        if dn == "Colors":
            return f"_(palette ref: project={settings.get('project')} palette_id={settings.get('palette')})_\n"
        if dn == "Embed":
            return f"_(embed: assetId={settings.get('assetId')})_\n"
        if dn == "Logo":
            return f"_(logo asset ref: {json.dumps(settings, ensure_ascii=False)[:120]})_\n"

    if bt == "video":
        title = settings.get("videoTitle") or ""
        return f"_(video: {title})_\n"

    if bt == "headline":
        return f"## {settings.get('content','')}\n"

    return ""


def render_page(page_dict: dict) -> str:
    p = page_dict.get("page", {})
    parts = [
        f"# {p.get('title') or '?'}",
        "",
        f"- **Document**: {p.get('document_id')}",
        f"- **Page ID**: {p.get('id')}",
        f"- **Slug**: {p.get('slug')}",
        f"- **Heading**: {p.get('heading')}",
        f"- **Modified**: {p.get('modified')}",
        f"- **Source**: https://branding.roche.com/document/{p.get('document_id')}#/{p.get('slug')}",
        "",
        "---",
        "",
    ]
    for sec in p.get("sections", []):
        for blk in sec.get("content", []):
            md = render_block(blk)
            if md:
                parts.append(md)
    return "\n".join(parts).rstrip() + "\n"


def main():
    OUT_DIR.mkdir(exist_ok=True)
    data = json.loads(CACHE.read_text())

    written = 0
    by_doc = {26: "brand-elements", 29: "templates"}
    for key, body in data.items():
        if not key.startswith("doc") or "_page_" not in key:
            continue
        m = re.match(r"doc(\d+)_page_(\d+)", key)
        if not m:
            continue
        doc_id, page_id = int(m.group(1)), int(m.group(2))
        p = body.get("page") or {}
        if not p:
            continue
        slug = p.get("slug") or f"page-{page_id}"
        category = by_doc.get(doc_id, f"doc-{doc_id}")
        out_dir = OUT_DIR / category
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug}.md"
        out_path.write_text(render_page(body))
        written += 1

    print(f"wrote {written} markdown files under {OUT_DIR}/", file=sys.stderr)


if __name__ == "__main__":
    main()
