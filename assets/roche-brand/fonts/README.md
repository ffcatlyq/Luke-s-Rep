# Roche Brand Fonts

5 个字体族，共 11 个 woff2 文件，约 1.1 MB。

## 字体族

| 字体 | 角色 | 本地 weights | 缺失 |
|---|---|---|---|
| Roche Sans | 主字体（heading/body/UI） | 300, 400, 500, 700 | italic, condensed |
| Roche Serif | 引言/编辑 | 300, 400 | italic, bold |
| Noto Sans | 多语言 fallback | 300, 400, 700 | — |
| Noto Serif | 多语言编辑 | 400, 700 | — |
| Roche Sans Condensed | 紧凑布局 | （无） | 全部（仅 Frontify 列出） |

## 许可

- **Noto Sans / Noto Serif** — SIL Open Font License 1.1（© The Noto Project Authors），许可全文见各字体目录下的`OFL.txt`。可随项目分发。
- **Roche Sans / Roche Serif（含Condensed）** — Roche专有品牌字体，不在开源许可范围。fork或二次分发本项目时须移除，或确保符合Roche内部品牌政策。

完整的第三方许可说明见仓库根的[THIRD-PARTY-NOTICES.md](../../../THIRD-PARTY-NOTICES.md)。

## 用法

### 1. 直接 @import（推荐）
```html
<link rel="stylesheet" href="/path/to/assets/roche-brand/fonts/fonts.css" />

<h1 style="font-family: 'Roche Sans'; font-weight: 300;">Roche Blue</h1>
```

### 2. CDN（如果不想本地拷字体）
把 [fonts.css](./fonts.css) 里 `url('roche-sans/...')` 改成 `url('https://fonts.roche.com/fonts/roche-sans/latest/...')`。fonts.roche.com 是公开 CDN，无需 SSO。

### 3. Slidev / 自定义主题
```css
/* slidev/style.css */
@import '../../assets/roche-brand/fonts/fonts.css';

:root {
  --slidev-font-sans: 'Roche Sans', system-ui, sans-serif;
}
```

## 缺失字重的处理

Italic 和 Condensed 不在 [fonts.roche.com](https://fonts.roche.com) 公开 CDN，但在 Frontify 后台是有的。短期方案：

| 缺失 | 建议替代 |
|---|---|
| Roche Sans Italic | Noto Sans Italic（待下载）/ system italic |
| Roche Serif Italic | Noto Serif Italic（待下载） |
| Roche Sans Condensed | Roche Sans + `font-stretch: condensed`（CSS 模拟） |

如果 PoC 真用到，需要从 Frontify 的 `/api/font-file/{font_id}` 私有 API 拉，font_id 列表在 `/api/portal/6/font-styles` API 响应里。

## 来源

- 公开 CDN: `https://fonts.roche.com/fonts/{family-slug}/latest/{file}.woff2`
  - 字体族 slug: `roche-sans`, `roche-serif`, `noto-sans`, `noto-serif`
  - 字重命名: `{Family}-{Weight}.woff2`（如 `RocheSans-Light.woff2`、`NotoSerif-Bold.woff2`）
- 抓取日期: 2026-05-17
- 抓取方式: 直接 curl，无需 cookie

## 刷新

字体很少变更，但建议每 3-6 个月跑一次：
```bash
cd assets/roche-brand/fonts
for fam in roche-sans roche-serif noto-sans noto-serif; do
  for f in $fam/*.woff2; do
    base=$(basename "$f")
    curl -sL -o "$f" "https://fonts.roche.com/fonts/$fam/latest/$base"
  done
done
```
