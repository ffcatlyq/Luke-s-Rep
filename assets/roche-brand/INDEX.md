# Roche Brand Asset Library — Index

**Snapshot date**: 2026-05-17 · **Total assets indexed**: 8280

## Libraries

| Library | Type | Total | Bodies downloaded | Index |
|---|---|---|---|---|
| 4. Icons library - FINAL | IconLibrary | 1525 | 1525 SVG ✅ | [snapshots/library-icons.json](./snapshots/library-icons.json) |
| 3. Logos library - FINAL | LogoLibrary | 4 | 4 EPS + 12 PNG ✅ | [snapshots/library-logos.json](./snapshots/library-logos.json) |
| 1. Photos library - FINAL | MediaLibrary | 6062 |  | [snapshots/library-photos.json](./snapshots/library-photos.json) |
| 5. Animated icons library - FINAL | MediaLibrary | 163 | metadata only (159 MB GIF skipped) | [snapshots/library-animated_icons.json](./snapshots/library-animated_icons.json) |
| 6. Illustration library - FINAL | MediaLibrary | 97 | 97 PNG ✅ | [snapshots/library-illustrations.json](./snapshots/library-illustrations.json) |
| 7. Stock assets library - FINAL | MediaLibrary | 429 | metadata only (11 GB MP4/JPEG skipped) | [snapshots/library-stock_assets.json](./snapshots/library-stock_assets.json) |

## Icon categories

| Category | Count |
|---|---|
| Healthcare | 628 |
| General | 410 |
| Business | 276 |
| Sustainability | 92 |
| Uncategorized | 89 |
| Sites | 30 |

## Top icon tags

| Tag | Count |
|---|---|
| one color | 228 |
| single color | 228 |
| duotone | 227 |
| roche blue | 227 |
| two color | 227 |
| two colour | 227 |
| monotone | 225 |
| single | 206 |
| one | 199 |
| one colour | 197 |
| single colour | 197 |
| patient | 144 |
| person | 141 |
| people | 138 |
| sustainability | 119 |
| healthcare | 119 |
| data | 111 |
| health | 96 |
| finance | 80 |
| research | 77 |
| laboratory | 77 |
| value | 69 |
| medical | 62 |
| disease | 62 |
| lab | 62 |
| digital | 61 |
| care | 61 |
| budget | 60 |
| test | 56 |
| cost | 56 |

## How to query

```python
import json
# Find all icons in 'Healthcare' category
by_cat = json.load(open('assets/roche-brand/icons/by-category.json'))
healthcare_icons = by_cat['groups']['Healthcare']  # list of {id, title, tags, local_path}

# Find icons tagged with 'oncology'
by_tag = json.load(open('assets/roche-brand/icons/by-tag.json'))
oncology_icons = by_tag['tags']['oncology']
```