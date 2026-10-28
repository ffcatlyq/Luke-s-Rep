# ppt-master · Roche brand bundles

ppt-master原生 `kind: brand` 机制的Roche品牌包目录。一个bundle只锁**身份**(配色 / 字体 /
logo / voice / 图标),不含页面——把目录路径当主管线 **Step 3** 模板输入，任意论文/内容都会套上
这套身份。版式风格与图像策略是**页面层约定**(见 `../examples/`),不在bundle里。

| Bundle | 定位 |
|---|---|
| [`roche-blue/`](roche-blue/) | Roche Blue身份(亮底)——技术/科学分享、论文深读、内部培训、研究进展 |
| [`roche-dark/`](roche-dark/) | Roche Dark身份(暗底)——暗色科技风、technical deep-read、需暗底反差的场合；与roche-blue共用官方色板，只是明暗取向不同 |

## SSOT

配色 / 字体的唯一来源是hub Roche brand token(`assets/roche-brand/tokens/` +
`slidev/themes/roche-blue/tokens.json`),经 [`../scripts/build_roche_brand_spec.py`](../scripts/build_roche_brand_spec.py)
派生。token改了重跑脚本、回填bundle的 `design_spec.md`——不手改、不另立会漂移的定义。

图标 / 渐变 / 插画等更丰富的官方素材见 `assets/roche-brand/`(1454图标 / 9渐变 / 93插画，
索引 `assets/roche-brand/INDEX.md`),bundle的 §VI指过去。

## 用法

主管线Step 3把 `roche-blue/` 目录路径作为brand模板；每篇论文 = 本bundle(身份)+ 技术公式格
版式约定([`../examples/attention-transformer/design_spec.md`](../examples/attention-transformer/design_spec.md))+ 主管线(内容)。
