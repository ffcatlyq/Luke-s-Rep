# spec_lock — claude-code-auto-mode(暗色科技格执行真相锁)

> 视觉执行值的短表，主agent每页落笔前复读以抗上下文压缩漂移。与 [`../design_spec.md`](../design_spec.md)
> 同步；冲突以本文件为准。值派生自hub Roche Blue token(暗底取向)。

## palette

> 全色=Roche官方色板(colors.json palette_families,Frontify认证API拉全)。底用官方登录页暗底 #2D3232(暖灰非纯黑),accent用官方橙(Roche确有橙族),语义用官方green/orange/status。派生源 [[reference_roche_full_palette_frontify_api]];brand bundle [`../../../brand/roche-dark/`](../../../brand/roche-dark/design_spec.md)。

- bg: 2D3232(官方暗底)· surface: 3A3F3F · panel: 353A3A · terminal: 202525 · border: 544F4F(grey_1)
- primary: 0B41CD · blue_light: 1482FA · blue_extra_light: BDE3FF · blue_dark: 022366
- text: F5F5F2(grey_5)· text_muted: C2BAB5(grey_3)· text_tertiary: 706B69/8A827C(grey_2)
- warm_accent: FF7D29(orange,暖accent/caution)· pass_green: 4CBB17(green)· danger: FF1F26/CC0033
- tint_card: blue 2A3742 · green 26331F · orange 3A2A1C/3A2418

## typography

- display: 58
- title: 34
- kpi: 40
- subtitle: 21
- body: 14
- eyebrow: 13
- footer: 11
- title_family: 'Roche Sans Light'  (纯拉丁) / 'Noto Sans CJK SC' (含CJK)
- label_family: 'Noto Sans CJK SC','Roche Sans Medium'
- body_family: 'Noto Sans CJK SC','Roche Sans'
- quote_family: 'Roche Serif Light'
- mono_family: 'Consolas','DejaVu Sans Mono'
- cjk_family: 'Noto Sans CJK SC'

## rules

- 暗底单主色(蓝阶),语义色只在读数 / 状态处(绿=放行/pass、橙=拦、红=硬拦)。
- 白logo(暗底);辉光radialGradient + 网格线30363D 0.5px opacity 0.3。
- CJK行cjk_family首位；CJK不混进mono组。
- 居中文本零tspan(即便只改色也算错宽);变色/上下标改text-anchor=start定x。
- 缺字形：cross用 ×,pause用 ‖(别用 ✗ / ⏸)。

## image

- 零AI图；schematic / 卡片 / 终端 / 图标全inline SVG(原生可编辑)。
- logo: assets/roche-brand/logos/Roche_Logo_800px_White_RGB_200px.png(绝对路径，finalize嵌入)。
