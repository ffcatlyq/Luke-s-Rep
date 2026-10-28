# original-reference — DeepSeek-R1论文原图对照

`preview/` 只放**论文原页的缩小PNG**(370px宽，仅供对照差异),不vendor论文全文或高清原图
(版权 + 避免膨胀innersource)。

| 缩略图 | 对应论文位置 | Roche版对应页 |
|---|---|---|
| `fig1_aime_and_length_p4.png` | Figure 1(a) AIME准确率 / (b) 响应长度随训练增长 | [07 self-evolution](../roche/preview/07_self_evolution.png)(重画为原生折线图) |
| `fig2_pipeline_p6.png` | Figure 2多阶段训练管线 | [10 pipeline](../roche/preview/10_pipeline.png)(重画为原生schematic) |
| `main_comparison_table_p40.png` | §4 R1 vs o1与基线主对照表 | [12 benchmark](../roche/preview/12_benchmark.png)(重画为原生表格) |
| `table15_distilled_p61.png` | §F Table 15蒸馏模型对照 | [15 distill-benchmark](../roche/preview/15_distill_benchmark.png)(重画为原生表格) |

## 原版口径

- **出处**:DeepSeek-AI,《DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning》,
  Nature 2026 / arXiv:2501.12948(v2)。公开论文，`research@deepseek.com`。
- **原版视觉**:学术论文排版(双栏、衬线正文、matplotlib风格图表),无统一品牌色。
- **完整论文**:见arXiv `https://arxiv.org/abs/2501.12948`;本目录不留全文PDF。

## 我们做的转换

论文原图 → **原生可编辑矢量重画**(折线图 / schematic / 表格),不嵌原图(见 [../ADAPTATION.md](../ADAPTATION.md))。
块级公式(GRPO目标函数)本地LaTeX渲染，封面氛围图走Galileo。对照即可见：同样的内容，换成一套Roche Blue体系。
