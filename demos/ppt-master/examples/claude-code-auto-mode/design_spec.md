# Claude Code Auto Mode · 暗色科技格 — design_spec

> 本格 = 上游"暗色科技(general dark tech)"× Roche Blue,B类适配(罗氏相关topic深度本地化)。
> 沿用技术公式格模板的 §II画布 / §V版式 / §VIII管线；本格改的是 §III暗底配色 + §IV CJK字体 +
> §VII页清单。配色 / 字体SSOT仍是hub Roche brand token,见 [brand/roche-blue](../../brand/roche-blue/design_spec.md)。

## I. 项目信息

| 项 | 值 |
|---|---|
| 样例 | claude-code-auto-mode(上游general_dark_tech_claude_code_auto_mode的Roche版) |
| 画布 | PPT 16:9(1280×720),10页 |
| 风格格位 | 暗色科技(dark-tech):深空黑底 + 辉光/网格 + 单主色蓝阶 |
| 适配类型 | B类：保暗色骨架(L1/L2)+ 内容本地化为罗氏亲历(L3) |

## II. 画布 / 版式

同技术公式格：viewBox `0 0 1280 720`,安全边距60;内容页页眉(6px accent竖条 + Roche Sans Light标题 +
Medium eyebrow)、页脚(source + 页码);封面单列居中 + 辉光。填充率 ≥ 80%,不动已验证页面。

## III. 配色(Roche Dark,全官方色)

暗色科技风保留(=template多样性的价值),配色 = **Roche官方色板**(brand [`../../brand/roche-dark/`](../../brand/roche-dark/design_spec.md),源colors.json `palette_families`,Frontify认证API拉全)。**两次返工的教训(重要)**:v1照搬上游amber + GitHub灰 + 通用绿橙红 → 用户指"不够罗氏、发花";v2我"罗氏派生"但**自己编了navy暗底 + 以为罗氏无橙把橙并进红** → 仍不对。**真相(拉了官方色板才知道)**:Roche **有官方暖暗底 `#2D3232`**(登录页)+ **有官方橙色族**(`#FF7D29` 等)。所以别猜、别"派生"——**去colors.json取官方值**。

| 角色 | v2(navy猜的，已弃) | Roche Dark官方 | 官方来源 |
|---|---|---|---|
| 背景 | ~~`#0A0E1A`~~ | `#2D3232` | neutral.background_dark(暖灰暗底) |
| 卡面/面板/终端 | ~~navy梯度~~ | `#3A3F3F` / `#353A3A` / `#202525` | grey_1提亮 / 压深 |
| 边框 | ~~`#24304D`~~ | `#544F4F` | grey.grey_1 |
| primary + 蓝阶 | 保留 | `#0B41CD` / `#1482FA` / `#BDE3FF` / `#022366` | blue族 |
| **暖accent** | ~~并进红~~ | **`#FF7D29`**(深 `#ED4A0D`)| **orange族(Roche确有橙！)** |
| 文字 | ~~冷调近白~~ | `#F5F5F2` / `#C2BAB5` / `#706B69` | grey_5/3/2暖灰阶 |
| 语义 | `#2FB56C`/`#E8564A` | 放行 `#4CBB17`(green)/ 拦 `#FF1F26`(red)/ 注意 `#FFC414`(status.yellow) | green/red/status族 |
| tint卡底 | — | blue `#2A3742` / green `#26331F` / orange `#3A2A1C` | 暖暗语义tint |

单主色仍是蓝；orange是暖accent(点缀，非第二主色)。辉光 `radialGradient` 低透明度蓝 + 标题 `feGaussianBlur` glow;网格线 `#544F4F` opacity 0.3。**白logo**(暗底)。

## IV. 字体(中文deck,CJK首位)

本deck中文为主，cairosvg无per-glyph回退 → CJK行字体栈 **`'Noto Sans CJK SC'` 放首位**,拉丁标题
(如 "Claude Code Auto Mode")才 `'Roche Sans Light'` 首位。EU容器需先 `apt-get install fonts-noto-cjk`。

- 标题 / display:`'Roche Sans Light'`(纯拉丁)/ `'Noto Sans CJK SC'`(含CJK)
- 标签 / eyebrow / 强调：`'Noto Sans CJK SC','Roche Sans Medium'`
- 正文：`'Noto Sans CJK SC','Roche Sans'`  ·  代码 / denial:`'Consolas','DejaVu Sans Mono'`
- 引言：`'Roche Serif Light'` italic(纯拉丁)/ `'Noto Sans CJK SC'`(含CJK)

### cairosvg坑(本格新踩，补 `_pipeline/README.md`)

1. **CJK混进mono `<g>`/tspan → 豆腐**(mono无CJK):那几行override成 `'Noto Sans CJK SC','Consolas'`。
2. **缺字形**:`✗`(U+2717)豆腐但 `✓` OK → cross用 `×`;`⏸` 豆腐 → 用 `‖`(U+2016)。
3. **居中文本零tspan(重要)**:`text-anchor="middle"` 里**任何tspan(即便只改fill)都会算错宽度 → 重叠**。
   居中文本用单色单段；要变色 / 上下标就改 `text-anchor="start"` 手动定x。(修正了旧口径"改颜色的tspan安全")。

## V. 图像策略

零AI图。schematic / 流程 / 卡片 / 终端 / 图标全纯SVG(原生可编辑，inline stroke图标);
论文/版权图不涉及。暗色氛围靠radialGradient辉光 + 网格，不用生图。

## VI. 页清单

01封面 · 02审批疲劳 · 03什么是Auto Mode(三态)· 04两道闸架构 · 05威胁模型(三卡)·
06权限(三级 + 代码卡)· 07分类器：真实拦截(step + 终端卡)· 08结果(三段时间线)· 09设计决策(三点)· 10收尾(居中)。

## VII. 管线

同 [`../_pipeline/README.md`](../_pipeline/README.md):init → 逐页手写SVG → `animation_config.py scaffold` →
finalize → `svg_to_pptx.py`(native默认 + 自动挂animations/notes)→ `embed_fonts.py`(可选)。
可编辑性：每页真 `<a:t>` + `<a:custGeom>`/`<a:prstGeom>` + `<p:timing>` + notesSlide。
