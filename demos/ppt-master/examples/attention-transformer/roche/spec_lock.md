# Execution Lock — Roche Blue · technical-formula

> Roche Blue视觉执行锁。结构照上游 `attention_is_all_you_need/spec_lock.md`，值全部换成本exemplar
> 的Roche Blue派生配色 / 字体 / 蓝阶。颜色·字体唯一SSOT是hub Roche brand token
> (`assets/roche-brand/tokens/` + `slidev/themes/roche-blue/tokens.json`)，经
> `demos/ppt-master/scripts/build_roche_brand_spec.py` 派生；token改了重跑脚本回填。

## canvas
- viewBox: 0 0 1280 720
- format: PPT 16:9

## colors
- bg: #FFFFFF
- bg_cover: #FBFBF9
- bg_secondary: #F5F7FA
- panel_tint: #F7F9FE
- primary: #0B41CD
- primary_hover: #002DB9
- accent: #1482fa
- blue_mid: #0F5EE1
- blue_light: #5FAAFC
- blue_lighter: #95C7FD
- accent_tint: #E9EEFA
- accent_tint_2: #F0F4FC
- text: #333333
- text_secondary: #706B69
- text_tertiary: #A39F9C
- border: #E0E0E0
- success: #007A3B
- warning: #D0021B
- image_rendering: blueprint
- image_palette: cool-corporate (Roche Blue)

> blue_mid / blue_light / blue_lighter / accent_tint非手填 —— 由build_roche_brand_spec.py
> `derive_blue_scale()` 从两个SSOT锚(primary #0B41CD + slidev primaryDim #1482fa)+ 白程序化派生。

## typography
- title_family: 'Roche Sans Light', sans-serif
- emphasis_family: 'Roche Sans Medium', sans-serif
- body_family: 'Roche Sans', sans-serif
- quote_family: 'Roche Serif Light', 'Noto Serif', serif (font-style italic)
- code_family: 'Consolas', 'DejaVu Sans Mono', monospace
- cjk_family: 'Noto Sans CJK SC' (含CJK行放字体栈首位)
- cover_title: 72
- page_title: 34
- section_title: 48
- hero_number: 62
- subtitle: 25
- body: 15
- eyebrow: 13
- footnote: 11

> cairosvg预览：字重只认normal/bold —— Light/Medium/Serif-Light必须用独立family名
> (`'Roche Sans Light'` / `'Roche Sans Medium'` / `'Roche Serif Light'`)，不是font-weight:300。
> Roche Sans缺 `→`(其余 `√ · — × ÷ ² ≤` 都有)与Greek(`ε β π ∞ ↔`) —— 这些字符包进mono
> `<tspan>`(Consolas/DejaVu Mono有)或改记号。居中文本(text-anchor=middle)只用改颜色的tspan。

## icons
- library: tabler-outline
- stroke_width: 2
- inventory: user (BLEU trophy代), star, bolt, eye, cpu, settings, shield-check, hourglass, arrows-horizontal, database, box, brackets, arrow-fork, grid, binary-tree

## images
- cover_bg: roche/assets/cover_bg.png (Galileo Azure gpt-image, blueprint × Roche Blue) | no-crop
- formula_attention: roche/assets/formula_attention.png (P07, LaTeX Computer Modern) | no-crop
- formula_mha_top: roche/assets/formula_mha_top.png (P08 MultiHead) | no-crop
- formula_mha_bot: roche/assets/formula_mha_bot.png (P08 head_i) | no-crop
- formula_pe_sin: roche/assets/formula_pe_sin.png (P11 PE sin) | no-crop
- formula_pe_cos: roche/assets/formula_pe_cos.png (P11 PE cos) | no-crop
- logo: assets/roche-brand/logos/Roche_Logo_800px_Blue_RGB_200px.png

> 图像策略(分层)：块公式 = LaTeX渲染PNG(不可编辑，换数学规范)；封面氛围 = Galileo生图；
> schematic / 架构 / dataflow / 图表 = 纯手写SVG(原生custGeom可编辑)；论文原图不嵌(版权，改重画)。

## page_rhythm
- P01: anchor
- P02: dense
- P03: breathing
- P04: dense
- P05: dense
- P06: dense
- P07: dense
- P08: dense
- P09: dense
- P10: dense
- P11: breathing
- P12: dense
- P13: dense
- P14: dense
- P15: dense
- P16: anchor

## page_charts
- P02: kpi_cards
- P03: three_schematic_motifs (RNN chain / CNN local field / self-attention mesh)
- P04: vertical_pillars + sequential-chain schematic
- P05: node_link_architecture + numbered legend
- P06: comparison_columns
- P07: formula_band + numbered_steps + dataflow
- P08: formula_band + numbered_steps + h-heads dataflow
- P09: vertical_pillars (Q/K/V source diagrams)
- P10: sublayer_cross_section + module_composition
- P11: formula_band + sinusoid_curve
- P12: basic_table
- P13: kpi_cards
- P14: basic_table
- P15: vertical_list
- P16: lineage_tree

## forbidden
- Mixing icon libraries
- rgba()
- `<style>`, `class`, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<script>`, `<iframe>`, `<symbol>`+`<use>`
- `<g opacity>` (set opacity on each child element individually)
- font-weight for Light/Medium — use independent family name instead (cairosvg toy API only normal/bold)
- text-anchor="middle" with font-family/baseline-shift tspan (mis-measures width → text drifts)
- HTML named entities in text — write as raw Unicode; XML reserved chars `& < > " '` escaped as `&amp; &lt; &gt; &quot; &apos;`
