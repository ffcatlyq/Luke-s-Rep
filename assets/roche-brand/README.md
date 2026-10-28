# Roche Brand Asset Library

> Self-contained Roche brand assets for the [cd2-ai-hackathon-hub](../../) repo. **Use this directory instead of going to branding.roche.com or fonts.roche.com**——agent 能 commit 的素材直接装 git，太大或受限的留 metadata + 按需取。

**Snapshot date**: 2026-05-17 · **Source**: [_meta.json](./_meta.json) · **Refresh policy**: 季度刷新（下次 ≥ 2026-08-17）

## 为什么要做这个目录

`branding.roche.com` 和 `fonts.roche.com` 都是 **Frontify SaaS**，内容在 Frontify 云数据库 + AWS S3 里，不是任何 git 仓的内容。AI agent 想拿一个 icon、确认一个色值、import 一个字体，要么去 Frontify UI 翻（需要 SSO + JS hydrate），要么调 GraphQL（需要 cookie 注入 + 处理 Cloudflare）——都不是 agent 友好的接口。

这个目录把 Frontify 的状态用 **两层策略**搬进 git：

- **能 commit 进 git 的小素材**（icons / logos / fonts / illustrations / brand guideline pages / design tokens）——直接转移 body 和 metadata，agent 离线可用，clone 即用
- **不能 commit 的大素材**（photos 307 GB / videos / 各种 stock）——只 commit metadata + tag 索引 + downloadUrl + previewUrl，agent 通过 [scripts/download_bodies.py](./scripts/download_bodies.py) 按需调 CDN transform 拿压缩版

不管资产能不能搬进 git，**agent 都能通过纯 git 工件做 query 和 decision**，不用 SSO 登录 Frontify UI。这是把"SaaS 资产"转换成"AI 时代基础设施"的小立项。

## 谁该用这个

- Hackathon 选手做品牌一致的 UI / slides / posters / dashboards
- AI agent 需要可读的 design token JSON + tag-indexed icon / photo search
- 任何需要把 Roche 字体/颜色/icon/logo/photo import 到代码或 slide 的项目

## 库存清单

### 第一层：body 在 git（59 MB）

| 类别 | 数量 | 文件总量 | 路径 |
|---|---|---|---|
| Icons (SVG) | **1525** | 1.85 MB | [icons/svg/](./icons/svg/) |
| Logos (EPS 源 + PNG 200/800/1600px transforms) | 4 + 12 | 4 MB | [logos/](./logos/) |
| Illustrations (PNG) | 97 | 21 MB | [illustrations/png/](./illustrations/png/) |
| Gradients (PNG，4 full + 4 split @ 49°) | 8 | 1.4 MB | [gradients/](./gradients/) |
| Fonts (woff2) | 11 (5 字体族) | 1.1 MB | [fonts/](./fonts/) |
| Brand guidelines (Markdown) | 55 页 | 296 KB | [pages/](./pages/) |
| Design tokens (colors / typography) | — | 20 KB | [tokens/](./tokens/) |

### 第二层：仅 metadata + 按需调 CDN（~30 MB JSON 索引）

| 类别 | 数量 | 索引位置 | 实际取法 |
|---|---|---|---|
| **Photos** (TIF 印刷级 + AdobeStock + 真人 portraits) | 6062（含 1018 受限不可下） | [snapshots/library-photos.json](./snapshots/library-photos.json) + [photos/by-tag.json](./photos/by-tag.json) | `scripts/download_bodies.py photos <out> --transform "format=jpeg&width=1600&quality=85"` |
| Animated icons (GIF, 159 MB body) | 163 | [snapshots/library-animated_icons.json](./snapshots/library-animated_icons.json) | `scripts/download_bodies.py animated_icons <out>` |
| Stock assets (Patients & HCPs, mp4+jpeg) | 429 | [snapshots/library-stock_assets.json](./snapshots/library-stock_assets.json) | `scripts/download_bodies.py stock_assets <out> --max-size-mb 5` |

**总计**：**8280 个资产 metadata + 1648 个文件本体 ≈ 80 MB git 占用**（含 11 MB 的 all-assets-flat.json 统一索引）。原 Frontify 库未压缩总量 ~330 GB。

## 5 秒入门

### Web / Slidev / HTML

```html
<link rel="stylesheet" href="/path/to/assets/roche-brand/fonts/fonts.css" />
<link rel="stylesheet" href="/path/to/assets/roche-brand/tokens/tokens.css" />

<h1 class="roche-h1">Roche Blue</h1>
<button style="background: var(--roche-primary)">Click</button>
<img src="/path/to/assets/roche-brand/icons/svg/<asset_id>__filename.svg" />
<img src="/path/to/assets/roche-brand/logos/Roche_Logo_800px_Blue_RGB_800px.png" />
```

### AI agent 查询 icon / photo

```python
import json
# Find Healthcare icons (628 available)
by_cat = json.load(open('assets/roche-brand/icons/by-category.json'))
healthcare_icons = by_cat['groups']['Healthcare']  # [{id, title, tags, local_path}, ...]

# Find icons tagged 'oncology'
by_tag = json.load(open('assets/roche-brand/icons/by-tag.json'))
oncology_icons = by_tag['tags']['oncology']

# Find lab photos by tag (body NOT in git — get full metadata via id lookup)
photos_by_tag = json.load(open('assets/roche-brand/photos/by-tag.json'))
lab_photo_ids = [p['id'] for p in photos_by_tag['tags']['laboratory']]  # minimal: id+title

# Full unified search across all 6 libraries (icons + logos + photos + illustrations + animated + stock)
flat = json.load(open('assets/roche-brand/snapshots/all-assets-flat.json'))
lab_photos_full = [it for it in flat['items']
                   if it['library']=='photos' and 'laboratory' in it['tags']]
# → it['previewUrl'] + '?format=jpeg&width=1600&quality=85' to fetch a slide-ready jpeg
```

### 取一张大尺寸 photo（按需 CDN transform）

```bash
# 1600px jpeg q=85 ≈ 200 KB/张，slide 投影足够
python3 assets/roche-brand/scripts/download_bodies.py photos /tmp/lab-photos \
    --transform "format=jpeg&width=1600&quality=85" --limit 20
```

### Python 拿 design token
```python
import json
tokens = json.load(open('assets/roche-brand/tokens/colors.json'))
roche_blue = tokens['primary']['roche_blue']['hex']  # '#0B41CD'
```

## 目录结构

```
assets/roche-brand/
├── _meta.json                       抓取元信息
├── README.md                        本文件
├── REFRESH.md                       刷新流程
├── INDEX.md                         全库 markdown index（agent + human 都用）
│
├── tokens/
│   ├── colors.json                  主色 #0B41CD + Callout 4 色 + neutral
│   ├── typography.json              5 字体族 + 9 个 type role
│   └── tokens.css                   CSS variables（@import 即用）
│
├── fonts/                           1.1 MB · 11 woff2
│   ├── fonts.css                    @font-face 声明
│   ├── README.md
│   ├── roche-sans/                  Light/Regular/Medium/Bold
│   ├── roche-serif/                 Light/Regular
│   ├── noto-sans/                   Light/Regular/Bold
│   └── noto-serif/                  Regular/Bold
│
├── logos/                           4 MB
│   ├── *.eps                        4 个矢量源 (Blue/Black/White RGB + Pantone)
│   └── *_{200,800,1600}px.png       12 个 PNG transform（Web 直接可用）
│
├── icons/                           14 MB · 1525 SVG
│   ├── svg/                         1525 SVG 文件本体（{asset_id}__{filename}.svg）
│   ├── index.json                   平面 metadata 索引（含 tags + category）
│   ├── by-category.json             按 6 个 category 分组（Healthcare 628, General 410, ...）
│   └── by-tag.json                  按 tag 反向索引（patient 144, person 141, ...）
│
├── illustrations/                   21 MB · 97 PNG
│   └── png/                         图文混排素材
│
├── gradients/                       1.4 MB · 8 PNG (4 full + 4 split @ 49°)
│   ├── Roche_Full_Grad_*.png        全渐变（Blue/Light Blue/Grey/White × Neutral 4）
│   ├── Roche_Split_Grad_*.png       分割渐变（Grey/Neutral on White/Grey）
│   └── gradients-manifest.json      8 个 gradient 的 asset_id + kind + 起止色描述
│
├── photos/                          7 MB · metadata only（body 不进 git）
│   └── by-tag.json                  按 tag 反向索引（minimal: id+title；详情查 all-assets-flat）
│
├── pages/                           296 KB · 55 markdown
│   ├── README.md                    导航表
│   ├── brand-elements/              30 页（Brand Elements 完整 styleguide）
│   └── templates/                   25 页（含 Google Slides / PPT / Word 等）
│
├── snapshots/                       30 MB
│   ├── library-icons.json           1525 icons 完整 metadata（含 downloadUrl, tags, customMetadata）
│   ├── library-logos.json           4 logos
│   ├── library-photos.json          16 MB · 6062 photos metadata（含 downloadUrl + previewUrl）
│   ├── library-animated_icons.json  163 GIF（body 未下，per asset ~1MB × 163 = 159MB 跳过）
│   ├── library-illustrations.json   97 PNG metadata
│   ├── library-stock_assets.json    429 stock（mp4/jpeg，body 未下）
│   ├── all-assets-flat.json         11 MB · 派生物（不进 git，由 build_indexes.py 本地重建）
│   ├── hub-6-state.json             Frontify SSR brand state
│   ├── portal-navigation.json       Brand portal 导航树
│   ├── page-index.json              59 页 metadata
│   └── palette-refs.json            8 个 palette ID（GraphQL 待解析）
│
└── scripts/
    ├── crawl_libraries.py           Public GraphQL 批量爬 library
    ├── download_svgs.py             1525 SVG 并发下载
    ├── download_bodies.py           通用 body downloader（支持 --transform "format=jpeg&width=N&quality=Q" 走 CDN 拿压缩版 + size 过滤 + limit）
    ├── extract_pages_to_markdown.py JSON cache → markdown 转换
    └── build_indexes.py             从 metadata 生成 by-category / by-tag 索引
```

> **文件名前缀 `{asset_id[-12:]}__` 不是噪声，别删。** icon/illustration 文件名形如
> `OiJhc3NldCJ9__investor_relation_ADC_duo.svg`，前缀是 asset id 后 12 位，由
> `download_svgs.py` 与 `build_indexes.py` 共用的命名契约，用于**去重**——多个资产
> 的 `filename` 可能相同，靠 id 前缀保证磁盘文件名唯一、不互相覆盖。索引的 `local_path`
> 字段按带前缀名引用；改名会使索引失效、且下次刷新会重新下载带前缀副本造成重复。
> 要"干净名"用 metadata 里的 `filename` 字段（已去前缀），不要动磁盘文件名。

## 来源 & 抓取关键

| 来源 | URL | 访问 | 关键发现 |
|---|---|---|---|
| Frontify Public GraphQL | `branding.roche.com/graphql`（不是 `/graphql-internal`） | 浏览器 cookie 注入即可 | **关键路径** — 暴露完整 library / asset / metadata schema |
| Frontify SSR state | `branding.roche.com/hub/6` | 同上 | brand color / typography / appearance tokens |
| Roche Fonts Repository | `fonts.roche.com/font/{slug}` | 公开（无需 SSO） | woff2 字体下载（URL 模式 `/fonts/{family}/latest/{file}.woff2`） |

抓取脚本均依赖 `~/.config/frontify/cookies.json` 的 `frontify-session-id` cookie。详见 [REFRESH.md](./REFRESH.md)。

## 已知缺口

| 项 | 状态 | 备注 |
|---|---|---|
| Logo SVG/PNG 源（不是 EPS） | ❌ 不存在 | Frontify 上 Roche logo 仅有 EPS 矢量源；PNG 通过 CDN 实时 transform 获得（已下 200/800/1600 三档） |
| Italic / Condensed 字重 | ❌ 公开 CDN 没有 | 需走 Frontify `/api/font-file/{font_id}` 私有 API |
| 完整 5 色调色板（base/accent/tertiary） | ⚠️ palette ID 已抓 | 8 个 palette ID 在 [snapshots/palette-refs.json](./snapshots/palette-refs.json)；GraphQL `Guideline.colorSchemes.palettes.colors` 待解析 |
| Animated icons (163 GIF) | metadata only | 159 MB 太大；需要时按 ID 用 `download_bodies.py animated_icons` 单下 |
| Stock assets (429 mp4/jpeg) | metadata only | 11 GB；同上 |

## 法律边界

**Roche 内部使用 only**（C2 internal scope）。本目录所有素材是 Roche 知产——**不要 fork 到外部 public repo**。本仓库 `roche-innersource/cd2-ai-hackathon-hub` 是 Roche EMU innersource，仅 Roche 员工可见。

如需在 Roche 外部场合使用 Roche 字体/Logo，请走 [branding.roche.com](https://branding.roche.com) 正式审批流程。

## 关联工作

- [demos/gslide-authoring/](../../demos/gslide-authoring/) — 资产库的初始动机（gslide 模板填充 PoC）
- [demos/gslide-authoring/docs/reference/roche-branding.md](../../demos/gslide-authoring/docs/reference/roche-branding.md) — PoC 视角的更详尽 narrative
- [demos/google-workspace/](../../demos/google-workspace/) — Cloud Search API 备用查询路径（用于内网 gSite mirror）
