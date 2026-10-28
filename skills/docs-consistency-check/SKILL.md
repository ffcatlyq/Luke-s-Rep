---
name: docs-consistency-check
description: >
  核对仓库文档与实际结构是否一致——揪出根文档（AGENTS.md / README.md / ONBOARDING.md）
  与 skills/README.md 里的过时项：漏登记的技能、死链、失效的状态图例、引用了不存在的路径。
  属通用引擎的仓库维护元技能，跨治疗领域复用。每次新增/删除技能或改目录结构后跑一遍。
  Use when asked to check docs for staleness, audit README/ONBOARDING/AGENTS against the
  actual repo, find dead links, verify the skill index is complete, or after adding/removing
  a skill. Triggers on "文档过时", "核对文档", "检查 README", "文档一致性", "死链检查",
  "技能清单对不对", "docs consistency", "check docs", "stale docs", "audit docs",
  "dead link", "文档同步", "onboarding 过时".
tier: domain
uses: [_meta-authoring]
freq: 中
---

# 文档一致性核对（Docs Consistency Check）

把"文档说的"和"仓库实际有的"对一遍，揪出漂移。核心一句话：**文档的信源要单一，多处枚举必然漂移——核对时既修当下过时项，也尽量收敛成单一信源防再漂。**

## 何时用

- 新增 / 删除 / 重命名技能后
- 改动目录结构、移动文件后
- 定期体检（如每次较大 PR 合并后）
- 用户说"看看文档有没有过时的""核对下 README"

## 快速开跑

先跑脚本拿到机器可查的问题（死链、漏登记、失效图例、坏路径），再人工判断脚本查不到的语义过时。

```bash
bash skills/docs-consistency-check/scripts/check-docs.sh
```

脚本输出分块列出问题；退出码非 0 = 有硬问题（死链/坏路径/技能漏登记）。

## 五类要核对的过时（检查清单）

| # | 检查项 | 怎么查 | 典型症状 |
|---|---|---|---|
| 1 | **技能清单完整** | 磁盘上 `skills/*/` + `skills/*.md` + `.claude/skills/*/` 是否都在文档里登记 | README 漏了新加的目录型技能 |
| 2 | **引用路径存在** | 文档里提到的每个 `path/to/file` 是否真实存在 | AGENTS.md 指向已删/改名的文件 |
| 3 | **内部链接不死** | 每个 `](target)` 的 target 是否存在 | 移动文件后链接失效 |
| 4 | **状态图例有效** | 图例里的标记（✅/🔧/⏳ 等）是否还有技能在用 | ⏳ 图例但已无技能处于该状态 |
| 5 | **计数声明准确** | "N 个产品""M 个技能"等硬数字是否与实际相符 | README 说"6 个产品"但已增到 7 |

> 脚本覆盖 1-4；第 5 项（计数）脚本给出实际数供人工对比。**语义过时**（描述与技能实际行为不符、示例已失效）脚本查不出，需人工抽样。

## 修复策略：优先收敛单一信源

发现"同一信息在多处枚举"（如根 README 技能表 + `skills/README.md` 两处各列一遍技能）——**别两处都补**，那只会下次再漂。改成：

- **一处为唯一信源**（技能清单以 `skills/README.md` 为准）；
- **其余处改为分类概览 + 指向信源**（覆盖面可见即可，不逐条枚举）。

> 判据：一条信息若需在 ≥2 处保持同步，就是漂移源头——收敛它，而非勤于同步。

## 产出

- 一份**过时项报告**：按五类列出，每项标"在哪个文件、什么问题、建议怎么改"。
- 若用户确认修复 → 按"收敛单一信源"策略改，改完**再跑一次脚本**确认清零。
- 文档改动走 PR（不直接推 main）。

## 合规注意

- 纯仓库维护，不涉及产品事实/患者数据。
- 若核对中发现文档里**写了不该进 git 的敏感信息**（患者个案、MLR 编号原文、真实客户名），一并标出，按 `compliance/guardrails.md` 处理。

## 参考文件

| 需要 | 读这个 |
|---|---|
| 核对脚本（死链/漏登记/失效图例/坏路径）| `scripts/check-docs.sh` |
| 写/优化 skill 的通用 SOP | `../_meta-authoring.md` |
