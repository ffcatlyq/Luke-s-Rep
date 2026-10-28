# Roche Blue · 技术公式格 — DeepSeek-R1 design_spec

> 本文件是exemplar「deepseek-r1」的配方(Strategist产出):**身份**引用brand bundle
> [`../../brand/roche-blue/`](../../brand/roche-blue/design_spec.md)(色/字/logo/voice),**版式**沿用技术公式格的
> [`../attention-transformer/design_spec.md`](../attention-transformer/design_spec.md)(§II画布 / §IV字体 / §V版式 / §VIII管线原样保留)。
> 本exemplar是 **from-scratch** 走完主管线的验证样本——Step 1源转换(PDF→md)+ Strategist自动
> 从论文提炼 §IX逐页大纲，attention那份是复用上游 §IX、没测到这两步。
>
> 配色 / 字体的唯一SSOT是hub Roche brand token,经
> [`../../scripts/build_roche_brand_spec.py`](../../scripts/build_roche_brand_spec.py) 派生，brand bundle已固化。本spec不重复定义身份，只记「技术公式格 × 这篇论文」的实例决策。

## I. 项目信息

| 项 | 值 |
|---|---|
| 样例 | deepseek-r1(《DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning》深读) |
| 源 | arXiv:2501.12948v2(Nature 2026版),DeepSeek-AI;PDF → `sources/deepseek-r1.md`(source_to_md.py,Step 1) |
| 画布 | PPT 16:9(1280×720),16页 |
| 风格格位 | 技术公式(technical-formula):学术极简 + 蓝图schematic,白底冷调 |
| 品牌 | Roche Blue brand bundle([`../../brand/roche-blue/`](../../brand/roche-blue/design_spec.md))作为Step 3模板输入 |

## II. 画布规格 / III. 配色 / IV. 字体 / V. 版式

**原样沿用** [`../attention-transformer/design_spec.md`](../attention-transformer/design_spec.md) §II / §III / §IV / §V,
与attention那份是同一套体系(同画布1280×720、同蓝阶 `#0B41CD / #1482fa / #0F5EE1 / #5FAAFC / #95C7FD / #E9EEFA`、
同字体约定Roche Sans Light主导 + Serif仅引言、同页眉6px accent竖条 + Light标题 + Medium eyebrow、
同takeaway带 + 卡片 + 表格规则、同四个cairosvg坑)。**目标：两份deck是一套体系，换论文只换内容不换风格。**

本篇在 §III强调分布上的实例选择(仍在同一蓝阶内，不引第二主色):
- **语义色克制**:绿 `#007A3B` 只标「R1追平/超越o1-1217的读数」与「distill超基线」;红 `#D0021B` 只标R1-Zero的短板(可读性/语言混杂)。
- **蓝阶承载层次**:pipeline四阶段 / distill家族用primary→bright→mid→light→lighter进阶徽章；highlight行用tint `#E9EEFA`。

## VI. 图像策略(本篇实例)

| 类型 | 本篇用途 | 做法 | 工具 |
|---|---|---|---|
| 块级数学公式 | GRPO目标函数J(θ)、ratio ρ 与advantage A | LaTeX → Roche Blue透明PNG(Computer Modern) | `_pipeline/render_formula.py` |
| 氛围背景 | 封面：RL探索reasoning空间的分支搜索树(一条高亮路径=习得的推理轨迹) | Galileo Azure gpt-image `gpt-image-1.5-2025-12-16`,左半留白构图 | `_pipeline/gen_cover_image.py` |
| schematic | reward组成、多阶段pipeline(Figure 2重画)、distillation teacher→students、self-evolution图表 | 纯SVG手写(原生 `<a:custGeom>`,可编辑) | agent手写 |
| 论文原图 | Figure 1/2、benchmark bar | **不嵌**,原生重画替代 | agent手写 |

## VII. 页清单(§IX的视觉执行摘要)

| 页 | 标题落点 | 版式 | 图 |
|---|---|---|---|
| 01 cover | DeepSeek-R1 · 纯RL激励推理 | 左标题 / 右分支树氛围 + Serif pull-quote | AI底图 |
| 02 why-it-matters | 追平o1、开源、可蒸馏 | 1×4 KPI卡 + takeaway | 零 |
| 03 central-idea | 跳过SFT,让RL自己发现推理 | 左右双路径对照(conventional vs R1-Zero) | 零(schematic) |
| 04 two-models | R1-Zero vs R1 | 双卡对照 + 桥接结论 | 零 |
| 05 grpo-formula | GRPO目标函数 | LaTeX公式带 + 左4步 / 右PPO→GRPO对照 | 公式PNG |
| 06 reward-design | 规则奖励：准确 + 格式 | schematic(response→两类reward→total)+ 为何不用神经RM | 零(schematic) |
| 07 self-evolution | R1-Zero自演化：准确率与思考长度齐涨 | 双CSS图表(AIME折线 + 响应长度增长)+ 涌现行为 | 零(chart) |
| 08 aha-moment | 涌现的「顿悟时刻」 | Serif大引言页 + 旁注 | 零 |
| 09 zero-to-r1 | R1-Zero的短板 → 为何要R1 | 左问题 / 右解法双栏 | 零 |
| 10 pipeline | R1多阶段训练管线 | 横向4阶段流程schematic(Figure 2重画) | 零(schematic) |
| 11 four-stages | 四阶段逐条读 | 编号图例(1–4)+ 底部d/成本注 | 零 |
| 12 benchmark | R1 vs o1-1217与基线 | 全宽表(R1列高亮) + takeaway | 零 |
| 13 stage-progression | 各阶段checkpoint的进步(Table 3) | 全宽表(Zero→Dev1→Dev2→Dev3→R1) + takeaway | 零 |
| 14 distillation | 大教师 → 小学生 | schematic(R1 671B →800k traces→ 6模型)+ 概念 | 零(schematic) |
| 15 distill-benchmark | 蒸馏模型vs GPT-4o / Claude-3.5 | 全宽表(蒸馏家族，超基线高亮) + takeaway | 零 |
| 16 conclusion | 结论 + 局限 | 左takeaway三条 / 右limitations四条 | 零 |

## VIII. 管线

原样沿用 [`../_pipeline/README.md`](../_pipeline/README.md):`project_manager.py init` → 主agent逐页手写SVG
(公式/氛围图先用 `_pipeline` 脚本产出、`<image>` 引用)→ quality_checker → finalize → svg_to_pptx `--only native` → render_preview。
可编辑性验证：slide XML有真 `<a:t>` + `<a:custGeom>` + logo `<p:pic>`。

## IX. 逐页内容大纲(Strategist从 `sources/deepseek-r1.md` 提炼)

> 这是ppt-master内容SSOT(对应slidev的outline.md)——从源文档提炼，不硬编码。数字全部溯源到论文表/节。

**01 · Cover**
标题「DeepSeek-R1」+ 副题「Incentivizing Reasoning in LLMs via Reinforcement Learning」。作者DeepSeek-AI(research@deepseek.com)。出处Nature 2026 · arXiv:2501.12948。pull-quote(§Abstract精炼):"Incentivize reasoning through pure reinforcement learning — no human reasoning traces."

**02 · Why it matters**(KPI,源：§4 Table / Abstract)
- AIME 2024 `79.8%` pass@1(R1)— on par with OpenAI-o1-1217。
- Codeforces `2029` rating / `96.3` pctl — 竞赛级编程，专家水平。
- License `MIT` — 全量权重 + 6个蒸馏模型公开(huggingface)。
- R1-Zero AIME `15.6 → 77.9%` — 纯RL、零SFT的自演化跃升。
takeaway:开源模型以远低成本追平闭源前沿推理。

**03 · Central idea**(§1 Introduction / §2)
双路径对照。Conventional:pretrain → SFT on human CoT → RL,性能被人类示范**封顶**、引入认知偏置。R1-Zero:pretrain → **纯RL**(reward = 答案正确性，不约束推理过程),绕过SFT → 涌现出人类示范之外的推理路径。核心假设：human-defined reasoning patterns会限制探索。

**04 · Two models**(§2 vs §3)
- DeepSeek-R1-Zero:DeepSeek-V3-Base上**纯RL**(GRPO,规则奖励)。强推理，但可读性差、中英语言混杂、领域窄(仅可验证任务)。
- DeepSeek-R1:**多阶段**(cold-start CoT + 推理RL + 拒绝采样SFT + 全场景RL)。继承Zero的推理力，同时对齐人类偏好、可读、覆盖写作/开放问答。
桥接：Zero证明「RL能激励推理」,R1把它做成「能用」。

**05 · GRPO**(§2.1 eq.1–3)
目标函数J_GRPO(θ):对每个问题采样一组G个输出，用clip代理目标 + KL到参考策略。ρ_i = 新旧策略概率比；A_i = 组内奖励归一化(减mean除std)——**GRPO用组内基线替代PPO的value/critic网络**,省一个同尺寸模型、更省资源。4步读法：①采样一组输出 ②各自打奖励 ③组内归一得advantage ④clip比率 + KL正则更新。超参：lr 3e-6、KL β 0.001、每问采16输出。

**06 · Reward design**(§2.2 eq.4)
Reward_rule = Reward_acc + Reward_format(等权)。Accuracy:数学看boxed答案规则校验、代码用编译器跑测试用例——**可验证**。Format:强制 `<think>…</think>` 包裹推理过程，提升可解释。刻意**不用神经奖励模型**(outcome/process皆不用):大规模RL下神经RM易被reward hacking、且重训成本高。R1阶段另加language-consistency reward(目标语言词占比)治中英混杂。

**07 · Self-evolution**(§2.3 Figure 1)
AIME 2024 pass@1随RL训练从 `15.6% → 77.9%`,self-consistency(cons@16)再到 `86.7%`,超人类选手均值。响应长度同步自然增长(数千token)——模型自发用更多「思考时间」。涌现行为：反思(reflection)、验证(verification)、探索替代解。8.2k step处性能与长度出现跃升。

**08 · Aha moment**(§2.3 Table 2)
中间版R1-Zero解方程时突然写下 "Wait, wait. Wait. That's an aha moment I can flag here." 并回头重估步骤——以拟人语气学会「重新思考」。不是被教的，是RL激励下涌现的。作者：见证RL的力量与优美。

**09 · From Zero to R1**(§3)
左(问题):R1-Zero可读性差 / 中英混杂 / 领域窄(写作、开放问答弱)。右(解法):R1多阶段——① 千级cold-start长CoT数据做SFT打底 ② 推理导向RL + 语言一致性奖励 ③ 拒绝采样 + SFT(掺入非推理数据)④ 全场景RL对齐helpfulness/harmlessness。

**10 · Multi-stage pipeline**(§3 Figure 2,重画)
横向流程：DeepSeek-V3-Base →【Cold Start:长CoT SFT】→【Reasoning RL:规则奖励 + 语言一致性】→【Rejection Sampling + SFT:推理 + 非推理数据】→【All-scenario RL:偏好 + 规则奖励】→ DeepSeek-R1。中间checkpoint:Dev1 / Dev2 / Dev3。

**11 · Four stages**(§3.1–3.2,编号图例)
1 Cold start——少量高质量长CoT,给对齐人类的思考起点，治Zero的冷启动可读性。
2 Reasoning-oriented RL——沿Zero的规则奖励(数学/代码/逻辑)+ 语言一致性奖励。
3 Rejection sampling + SFT——用当前模型采样、筛优质轨迹，掺入非推理数据(写作/QA)再SFT。
4 All-scenario RL——规则奖励(推理)+ 模型奖励(helpful/safety)混合，最终对齐。
底注：DeepSeek-V3-Base = 671B总 / 37B激活(MoE);R1训练 ≈ 64×8 H800 · ~80h。

**12 · Benchmark: R1 vs o1**(§4主对照表)
列：Claude-3.5-Sonnet-1022 / GPT-4o-0513 / DeepSeek-V3 / o1-mini / o1-1217 / **R1**。行(pass@1等):AIME 2024、MATH-500、GPQA Diamond、LiveCodeBench、Codeforces rating、MMLU。R1列高亮；绿标R1追平/超o1-1217处(AIME 79.8 vs 79.2、MATH 97.3 vs 96.4、Codeforces 2029 vs 2061近平)。

**13 · Stage progression**(§4 Table 3)
列：R1-Zero / Dev1 / Dev2 / Dev3 / **R1**。行：AIME 2024、MATH-500、Codeforces rating、GPQA Diamond、AlpacaEval2.0、ArenaHard。读法：推理分在早阶段(Zero/Dev2)就高，后阶段(Dev3/R1)主要拉起对齐类(AlpacaEval +25%、ArenaHard +17%),推理不掉。

**14 · Distillation**(§F / §3末，概念schematic)
把R1的推理能力**蒸馏**给小模型：R1(teacher)生成800k reasoning traces → 对Qwen2.5(1.5B/7B/14B/32B)与Llama-3.x(8B/70B)做 **SFT-only**(不加RL,把RL空间留给社区)。动机：LLM能耗高，蒸馏让小模型也具强推理、降低门槛。结论：蒸馏自高质量教师输出 > 直接在人类数据上训。

**15 · Distilled benchmark**(§F Table 15)
基线GPT-4o-0513 / Claude-3.5-Sonnet-1022对比蒸馏家族。列(pass@1):AIME 2024、MATH-500、GPQA Diamond、LiveCodeBench、Codeforces rating。读法：Distill-Qwen-7B数学(MATH 92.8 / AIME 55.5)已远超GPT-4o(74.6 / 9.3);32B(72.6/94.3)与70B(70.0/94.5)逼近o1-mini档。

**16 · Conclusion & limitations**(§6)
Takeaways(左):① RL单独即可激励推理，关键不在大规模人工标注，而在「难题 + 可靠验证器 + 足够算力」。② 自验证 / 反思等复杂行为自发涌现。③ 蒸馏把前沿推理民主化到小模型。
Limitations(右):① 结构化输出与工具使用(搜索/计算器)仍弱。② token效率——简单题过度思考。③ 语言混杂(仅中英优化)。④ prompt敏感，few-shot反而降分，建议zero-shot。
