# .claude/hooks/ — 确定性护栏

hook 不是 prompt、不是 LLM，是**代码**，在工具调用前后的事件点强制执行。LLM 没法"说服"hook——这正是价值：靠 prompt 提醒 LLM 遵守协作原则不可靠（长会话会忘），靠 hook 用代码兜底才是真护栏。

本目录把 `AGENTS.md` 第 4 章（协作原则）里最重的两条软约定升级为**运行时强制触发**。

## 当前 hook

| hook | 事件 | 行为 | 类型 |
|------|------|------|------|
| `plan-alignment-guard.sh` | PreToolUse（ExitPlanMode） | 出计划前强制弹五要素对齐清单（目标/上下文/动作/边界/验收），对齐 AGENTS.md 第 4 章 | 提示型 |
| `skill-capture-reminder.sh` | Stop（会话停下） | 干了实质工作的会话停下时，提醒"这次流程要不要沉淀成 skill"；按工作量节流 | 提示型 |

## 能力边界（诚实）

两个都是**提示型护栏，不是验证型**：

- **保证**："停一下 / 提醒可见"——把清单和提醒怼到眼前，逼停一拍，用户也看得见。
- **不保证**：LLM 是否真逐条对齐过五要素、是否真去沉淀 skill——那是思维动作，代码看不到。

对比：验证型护栏（如 secret 扫描）能扫内容判定命中，可靠拦截；提示型只保证提醒出现。这两条打的正是"没停下就 exit plan""干完忘了问 skill"这两个高频失败点。

## 实现约束

本环境基础镜像**无 python / node**，仅有 `bash` + `jq`。因此 hook 用 **bash + jq** 实现，零额外依赖。`jq` 缺失时脚本 fail-open 放行。

## 挂载

挂载点在 `../settings.json` 的 `hooks` 字段。每个 hook 用 `[ -f "$GUARD" ] && bash "$GUARD" || exit 0` 包裹——文件不存在则静默放行，不会因缺文件卡住工具调用。

所有 hook **fail-open**：脚本任何解析/读取失败都放行（`exit 0`），hook 自身的 bug 不该阻断正常工作。

## 节流（skill-capture-reminder）

Stop 每个 turn 都触发，不节流会极吵。两道闸都过才提醒：
1. **实质工作闸**：本会话 Write/Edit/MultiEdit/Bash 累计 < 3 次则静默（纯问答不提醒）。
2. **增量节流闸**：距上次提醒新增 ≥ 10 次工具调用才再提醒（长会话后半程也能被提醒到，又不刷屏）。

cache 存于 `~/.cache/pm-agent-skill-capture/<session_id>`。

## 适用运行时说明

hook 依赖运行时读取 `.claude/settings.json`（Claude Code 机制；本仓库 `CLAUDE.md → AGENTS.md` 软链亦按此设计）。若某运行时不加载该配置，hook 不触发，此时 `AGENTS.md` 第 4 章的文字规则继续作为兜底。

## 测试

无外部依赖，可直接用模拟 stdin 测试：

```bash
# plan-alignment-guard：ExitPlanMode 应输出 ask 清单
echo '{"tool_name":"ExitPlanMode"}' | bash .claude/hooks/plan-alignment-guard.sh
# 其他工具应静默
echo '{"tool_name":"Write"}' | bash .claude/hooks/plan-alignment-guard.sh

# skill-capture-reminder：需造一个 transcript jsonl（含 ≥3 个 tool_use）再喂 session_id + transcript_path
```
