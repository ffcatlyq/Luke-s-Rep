# original-reference — 上游原版Claude Code Auto Mode对照

方便你和社区成员**开着两份pptx并排比**"同一份deck换成罗氏后改了什么":

- **`claude-code-auto-mode_20260422_143501.pptx`** — 上游原版**原始pptx**(原名未改，1.6MB,含4张嵌入图)。直接打开跟
  [`../roche/pptx/claude-code-auto-mode-roche.pptx`](../roche/pptx/claude-code-auto-mode-roche.pptx) 并排看。
- **`preview/`** — 上游10页缩小PNG(680px,不开pptx也能快速扫)。

> 约定说明：一般exemplar的original-reference只放缩小PNG(不vendor上游大文件，避免膨胀)。
> 但 **ppt-master类exemplar(上游本身就是一份deck)例外**——放上游**原始pptx**,因为对比"效果"
> 就得能打开真文件。上游MIT许可，允许vendor + 附出处(见下)。

## 出处

- 上游：`hugohe3/ppt-master` example `ppt169_general_dark_tech_claude_code_auto_mode`
  (clone上游后在 `examples/<该目录>/` 可得完整源：svg_final / images / notes / design_spec)。
- 原版题材：Anthropic工程博客的Claude Code Auto Mode讲解；暗色科技风 + amber(Anthropic resonance)。
- gallery:`https://hugohe3.github.io/ppt-master/`。

## 逐页对照(上游原版 → 罗氏版)

这是一个 **B类适配(罗氏相关topic)**:不是换色，是**保留暗色科技骨架 + 逐页把内容本地化成罗氏亲历**。

| 页 | 上游原版 | 罗氏版([../roche/preview/](../roche/preview/)) |
|---|---|---|
| 01 | Cover — "A Safer Way to Skip Permissions" | 封面 — "把审批交给分类器，把安全交给两道闸" |
| 02 | Approval Fatigue(泛泛的审批疲劳) | 审批疲劳 — 用我们的 `/merge-main` 三步机械收尾举例 |
| 03 | What Is Auto Mode | 什么是Auto Mode — 落到build-cli / Ona客户端语境 |
| 04 | **Two Layers of Defense**(input/output classifier防御层) | **两道闸** — auto-mode(本地)≠ GitHub分支保护(服务端)。**同槽位、换含义**:这是我们踩出的结论 |
| 05 | Threat model(通用威胁) | 威胁模型 — 三类都对着**本会话真实拦过**的动作(自我approve / 找token / 外发) |
| 06 | Permissions(三档权限) | 权限 — settings.local.json放行规则 + gitignored/每容器独立的伏笔 |
| 07 | Classifier(分类器原理) | 分类器 — **PR #307 approve被判自审的实录denial文案** |
| 08 | Results(分类器性能指标) | 结果 — 老容器能→搬家丢→加回就好(settings.local.json的一生) |
| 09 | Design Decisions | 设计决策 — 命令/skill不携带授权、护栏分提示型vs验证型 |
| 10 | Closing | 收尾 — 给agent自主权 = 本地放行规则 + GitHub双人review |

## 看点

- **风格(L1/L2)**:暗色科技骨架、辉光、网格、卡片、终端卡都保留；把amber(Anthropic)换成暗底Roche Blue(`#1482fa` 蓝阶)。
- **内容(L3)**:每页含义换成罗氏AI社区能直接用的实战——尤其04/07/08是我们做这套slides时的真实经历，**自我印证**。
- 04页最能说明"适配 ≠ 换色":上游是"分类器的两层防御",罗氏版是"auto-mode vs GitHub两道闸"——占同一个"架构/两-X"槽位，讲完全不同的、对罗氏有用的东西。
